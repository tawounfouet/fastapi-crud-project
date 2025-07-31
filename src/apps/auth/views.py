"""
Auth Views Module

This module contains the FastAPI endpoints for authentication operations.
It acts as the presentation layer for authentication in the DDD architecture.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.deps import CurrentUser, SessionDep
from src.apps.users.schemas import UserPublicOutput
from src.apps.users.services import InvalidCredentialsError
from src.core.config import settings
from src.utils import (
    generate_new_account_email,
    generate_reset_password_email,
    send_email,
)

from .schemas import (
    AuthMessage,
    AuthStatusResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetTokenResponse,
    SignupRequest,
    SignupResponse,
    TokenRefreshRequest,
    TokenResponse,
)
from .services import (
    AuthenticationError,
    AuthService,
    InvalidTokenError,
    TooManyLoginAttemptsError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: SessionDep) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(session)


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post(
    "/login",
    response_model=dict,  # Use dict instead of LoginResponse for now
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return access token with optional refresh token.",
)
def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Login endpoint for user authentication.

    Features:
    - Email/password authentication
    - Optional "remember me" functionality with refresh tokens
    - Device tracking
    - Failed login attempt monitoring
    - Session creation
    """
    ip_address, user_agent = get_client_info(request)

    try:
        result = auth_service.authenticate_user(
            login_data=login_data, ip_address=ip_address, user_agent=user_agent
        )
        return result

    except TooManyLoginAttemptsError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )
    except (AuthenticationError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )


@router.post(
    "/login/access-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 compatible login",
    description="OAuth2 compatible token login, get an access token for future requests.",
)
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    OAuth2 compatible login endpoint.

    This endpoint maintains compatibility with OAuth2PasswordRequestForm
    and standard FastAPI OAuth2 flows.
    """
    ip_address, user_agent = get_client_info(request)

    # Convert OAuth2 form data to LoginRequest
    login_data = LoginRequest(
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
        remember_me=False,  # OAuth2 doesn't support remember me
    )

    try:
        result = auth_service.authenticate_user(
            login_data=login_data, ip_address=ip_address, user_agent=user_agent
        )
        # Return only the tokens part for OAuth2 compatibility
        return result.tokens

    except TooManyLoginAttemptsError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )
    except (AuthenticationError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
)
def refresh_token(
    refresh_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Refresh access token using a refresh token.
    """
    try:
        result = auth_service.refresh_access_token(refresh_data.refresh_token)
        return result

    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account.",
)
def signup(
    request: Request,
    signup_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    User registration endpoint.

    Features:
    - Email validation
    - Password strength requirements
    - Terms acceptance tracking
    - Welcome email (optional)
    """
    ip_address, user_agent = get_client_info(request)

    try:
        user = auth_service.register_user(
            signup_data=signup_data, ip_address=ip_address, user_agent=user_agent
        )

        # Send welcome email if configured
        if settings.SMTP_HOST:
            try:
                email_data = generate_new_account_email(
                    email_to=user.email,
                    username=user.email,
                    password="[Hidden for security]",  # Don't send password in email
                )
                send_email(
                    email_to=user.email,
                    subject=email_data.subject,
                    html_content=email_data.html_content,
                )
            except Exception:
                # Don't fail registration if email fails
                pass

        return SignupResponse(
            user=UserPublicOutput.model_validate(user),
            message="Account created successfully",
            email_verification_required=False,  # Future feature
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/logout",
    response_model=AuthMessage,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout user and invalidate tokens.",
)
def logout(
    logout_data: LogoutRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Logout endpoint.

    Features:
    - Single device logout
    - All devices logout option
    - Token revocation
    - Session invalidation
    """
    try:
        auth_service.logout_user(
            user_id=current_user.id, all_devices=logout_data.all_devices
        )

        message = "Logged out successfully"
        if logout_data.all_devices:
            message = "Logged out from all devices successfully"

        return AuthMessage(message=message)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to logout"
        )


@router.post(
    "/password-recovery",
    response_model=PasswordResetTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset token.",
)
def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Password reset request endpoint.

    Features:
    - Email validation
    - Reset token generation
    - Email notification
    - Rate limiting protection
    """
    ip_address, user_agent = get_client_info(request)

    try:
        reset_token = auth_service.request_password_reset(
            email=reset_data.email, ip_address=ip_address, user_agent=user_agent
        )

        # Send reset email
        email_data = generate_reset_password_email(
            email_to=reset_data.email, email=reset_data.email, token=reset_token
        )
        send_email(
            email_to=reset_data.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

        return PasswordResetTokenResponse(
            message="Password recovery email sent",
            expires_in=60,  # 1 hour in minutes
        )

    except Exception:
        # Don't reveal if email exists for security
        return PasswordResetTokenResponse(
            message="If the email exists, a reset link has been sent", expires_in=60
        )


@router.post(
    "/reset-password",
    response_model=AuthMessage,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using a reset token.",
)
def reset_password(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Password reset confirmation endpoint.

    Features:
    - Token validation
    - Password strength validation
    - Automatic token invalidation
    - Session invalidation for security
    """
    try:
        auth_service.reset_password(
            token=reset_data.token, new_password=reset_data.new_password
        )

        return AuthMessage(message="Password updated successfully")

    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


@router.post(
    "/change-password",
    response_model=AuthMessage,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change password for authenticated user.",
)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Password change endpoint for authenticated users.

    Features:
    - Current password verification
    - New password strength validation
    - Automatic session refresh
    """
    try:
        auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )

        return AuthMessage(message="Password changed successfully")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authentication status",
    description="Get current authentication status and permissions.",
)
def get_auth_status(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Authentication status endpoint.

    Returns current authentication status, permissions, and session info.
    """
    try:
        status_info = auth_service.get_auth_status(current_user.id)
        return status_info

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authentication status",
        )


@router.post(
    "/test-token",
    response_model=UserPublicOutput,
    status_code=status.HTTP_200_OK,
    summary="Test access token",
    description="Test if the current access token is valid.",
)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test token endpoint.

    Returns current user information if token is valid.
    """
    return UserPublicOutput.model_validate(current_user, from_attributes=True)
