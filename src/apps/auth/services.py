"""
Auth Services Module

This module contains the business logic for authentication operations.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlmodel import Session, and_, select

from src.apps.users.models import User
from src.apps.users.services import (
    InvalidCredentialsError,
    UserNotFoundError,
    UserService,
)
from src.core.config import settings
from src.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from src.utils import generate_password_reset_token, verify_password_reset_token

from .models import LoginAttempt, PasswordResetToken, RefreshToken
from .schemas import (
    AuthStatusResponse,
    LoginRequest,
    SignupRequest,
    TokenResponse,
)


# Simple result classes to avoid Pydantic forward reference issues
class AuthResult(NamedTuple):
    """Simple result for authentication operations"""

    user: User
    tokens: TokenResponse
    session_id: str


class AuthenticationError(Exception):
    """Base exception for authentication errors"""

    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid or expired"""

    pass


class TooManyLoginAttemptsError(AuthenticationError):
    """Raised when too many failed login attempts are detected"""

    pass


class AuthService:
    """
    Authentication Service

    Handles all authentication-related business logic including:
    - Login/logout operations
    - Token management
    - Password reset
    - User registration
    - Session management
    """

    # Constants
    USER_NOT_FOUND_MSG = "User not found"

    def __init__(self, session: Session):
        self.session = session
        self.user_service = UserService(session)

    def authenticate_user(
        self,
        login_data: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        """
        Authenticate a user and create session.

        Args:
            login_data: Login credentials
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            AuthResult with user data and tokens

        Raises:
            InvalidCredentialsError: Invalid email or password
            TooManyLoginAttemptsError: Too many failed attempts
            AuthenticationError: Other authentication issues
        """
        # Check for too many failed attempts
        self._check_login_attempts(login_data.email, ip_address)

        try:
            # Authenticate user
            user = self.user_service.authenticate_user(
                login_data.email, login_data.password
            )

            # Create tokens
            tokens = self._create_tokens(
                user,
                login_data.remember_me,
                login_data.device_id,
                ip_address,
                user_agent,
            )

            # Create user session
            session_id = self._create_user_session(user.id, ip_address, user_agent)

            # Log successful attempt
            self._log_login_attempt(
                email=login_data.email,
                user_id=user.id,
                successful=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return AuthResult(user=user, tokens=tokens, session_id=session_id)

        except (UserNotFoundError, InvalidCredentialsError) as e:
            # Log failed attempt
            self._log_login_attempt(
                email=login_data.email,
                successful=False,
                failure_reason=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise InvalidCredentialsError("Invalid email or password")

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            New TokenResponse

        Raises:
            InvalidTokenError: Token is invalid or expired
        """
        # Verify and get refresh token from database
        token_hash = self._hash_token(refresh_token)
        db_token = self.session.exec(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash, RefreshToken.revoked is False
                )
            )
        ).first()

        if not db_token or not db_token.is_valid():
            raise InvalidTokenError("Invalid or expired refresh token")

        # Get user
        user = self.session.get(User, db_token.user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(user.id, expires_delta=access_token_expires)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
        )

    def register_user(
        self,
        signup_data: SignupRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """
        Register a new user.

        Args:
            signup_data: Registration data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created User object

        Raises:
            UserAlreadyExistsError: User with email already exists
        """
        from src.apps.users.schemas import UserCreate

        # Create user via UserService
        user_create = UserCreate(
            email=signup_data.email,
            password=signup_data.password,
            first_name=signup_data.first_name,
            last_name=signup_data.last_name,
        )

        user = self.user_service.create_user(user_create)

        # Log the registration
        self._log_login_attempt(
            email=signup_data.email,
            user_id=user.id,
            successful=True,
            failure_reason="user_registration",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user

    def logout_user(
        self,
        user_id: uuid.UUID,
        refresh_token: str | None = None,
        all_devices: bool = False,
    ) -> bool:
        """
        Logout a user by revoking tokens.

        Args:
            user_id: User ID
            refresh_token: Specific refresh token to revoke
            all_devices: Whether to logout from all devices

        Returns:
            True if successful
        """
        if all_devices:
            # Revoke all refresh tokens for user
            tokens = self.session.exec(
                select(RefreshToken).where(
                    and_(RefreshToken.user_id == user_id, RefreshToken.revoked is False)
                )
            ).all()

            for token in tokens:
                token.revoke()
                self.session.add(token)

        elif refresh_token:
            # Revoke specific refresh token
            token_hash = self._hash_token(refresh_token)
            db_token = self.session.exec(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.token_hash == token_hash,
                        RefreshToken.user_id == user_id,
                        RefreshToken.revoked is False,
                    )
                )
            ).first()

            if db_token:
                db_token.revoke()
                self.session.add(db_token)

        # Also invalidate user sessions
        self.user_service.invalidate_user_sessions(uuid.UUID(user_id))

        self.session.commit()
        return True

    def request_password_reset(
        self,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """
        Request a password reset for a user.

        Args:
            email: User email
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Reset token (for testing, in production should be sent via email)

        Raises:
            UserNotFoundError: User not found
        """
        user = self.user_service.get_user_by_email(email)
        if not user:
            raise UserNotFoundError(self.USER_NOT_FOUND_MSG)

        # Generate reset token
        reset_token = generate_password_reset_token(email)
        token_hash = self._hash_token(reset_token)

        # Store in database
        db_token = PasswordResetToken(
            token_hash=token_hash,
            user_id=user.id,  # Now using UUID directly
            email=email,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.session.add(db_token)
        self.session.commit()

        return reset_token

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a reset token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            True if successful

        Raises:
            InvalidTokenError: Token is invalid or expired
        """
        # Verify token
        email = verify_password_reset_token(token)
        if not email:
            raise InvalidTokenError("Invalid or expired reset token")

        # Get and validate database token
        token_hash = self._hash_token(token)
        db_token = self.session.exec(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.email == email,
                    PasswordResetToken.used is False,
                )
            )
        ).first()

        if not db_token or not db_token.is_valid():
            raise InvalidTokenError("Invalid or expired reset token")

        # Get user and update password
        user_id = db_token.user_id  # Already a UUID
        user = self.session.get(User, user_id)
        if not user:
            raise UserNotFoundError(self.USER_NOT_FOUND_MSG)

        # Update password
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password

        # Mark token as used
        db_token.mark_used()

        self.session.add(user)
        self.session.add(db_token)
        self.session.commit()

        return True

    def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            InvalidCredentialsError: Current password is incorrect
            UserNotFoundError: User not found
        """
        user = self.session.get(User, user_id)
        if not user:
            raise UserNotFoundError(self.USER_NOT_FOUND_MSG)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        # Update password
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password

        self.session.add(user)
        self.session.commit()

        return True

    def get_auth_status(self, user_id: uuid.UUID) -> AuthStatusResponse:
        """
        Get authentication status for a user.

        Args:
            user_id: User ID

        Returns:
            AuthStatusResponse with current status
        """
        user = self.session.get(User, user_id)
        if not user:
            return AuthStatusResponse(authenticated=False)

        # Get active sessions
        active_sessions = self.user_service.get_active_sessions(user_id)
        session_id = active_sessions[0].id if active_sessions else None

        # Determine permissions
        permissions = ["user"]
        if user.is_superuser:
            permissions.append("admin")

        return AuthStatusResponse(
            authenticated=True,
            user_id=user_id,
            session_id=session_id,
            permissions=permissions,
            expires_at=active_sessions[0].expires_at if active_sessions else None,
        )

    # Private helper methods

    def _create_tokens(
        self,
        user: User,
        remember_me: bool = False,
        device_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(user.id, expires_delta=access_token_expires)

        # Create refresh token if remember_me is True
        refresh_token = None
        if remember_me:
            refresh_token_expires = timedelta(days=30)  # 30 days
            refresh_token = secrets.token_urlsafe(32)

            # Store refresh token in database
            token_hash = self._hash_token(refresh_token)
            db_token = RefreshToken(
                token_hash=token_hash,
                user_id=user.id,
                expires_at=datetime.now(timezone.utc) + refresh_token_expires,
                device_id=device_id,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            self.session.add(db_token)
            self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
        )

    def _create_user_session(
        self,
        user_id: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """Create a user session."""
        from src.apps.users.models import UserSession

        session = UserSession(
            user_id=user_id,  # Already a UUID
            session_token=secrets.token_urlsafe(32),  # Generate unique session token
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return str(session.id)

    def _hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _check_login_attempts(self, email: str, ip_address: str | None = None) -> None:
        """Check for too many failed login attempts."""
        # Check attempts in the last 15 minutes
        since = datetime.now(timezone.utc) - timedelta(minutes=15)

        # Build conditions for checking attempts
        conditions = [
            LoginAttempt.email == email,
            LoginAttempt.successful is False,
            LoginAttempt.created_at >= since,
        ]

        # Add IP address condition if provided for stricter rate limiting
        if ip_address:
            conditions.append(LoginAttempt.ip_address == ip_address)

        failed_attempts = self.session.exec(
            select(LoginAttempt).where(and_(*conditions))
        ).all()

        if len(failed_attempts) >= 5:  # Max 5 attempts per 15 minutes
            raise TooManyLoginAttemptsError(
                "Too many failed login attempts. Please try again later."
            )

    def _log_login_attempt(
        self,
        email: str,
        successful: bool,
        user_id: uuid.UUID | None = None,
        failure_reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log a login attempt."""

        attempt = LoginAttempt(
            email=email,
            successful=successful,
            user_id=user_id,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.session.add(attempt)
        self.session.commit()
