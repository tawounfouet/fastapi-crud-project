"""
User Views Module

This module contains the FastAPI endpoints for user operations.
It acts as the presentation layer in the DDD architecture.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from src.core.config import settings
from src.utils import generate_new_account_email, send_email

from .schemas import (
    MessageOutput,
    UpdatePassword,
    UserCreate,
    UserProfileOutput,
    UserProfileUpdate,
    UserPublicOutput,
    UserSessionResponse,
    UsersListOutput,
    UserUpdate,
    UserUpdateMe,
)
from .services import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)

# Constants for error messages and responses
USER_NOT_FOUND_MSG = "User not found"
INSUFFICIENT_PRIVILEGES_MSG = "Not enough permissions to access this user"
EMAIL_EXISTS_MSG = "User with this email already exists"
SUPERUSER_DELETE_SELF_MSG = "Super users are not allowed to delete themselves"
USER_DELETED_MSG = "User deleted successfully"
PASSWORD_UPDATED_MSG = "Password updated successfully"
PROFILE_NOT_FOUND_MSG = "Profile not found"

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: SessionDep) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(session)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersListOutput,
    summary="Get all users",
    description="Retrieve a list of all users. Requires superuser privileges.",
)
def get_users(
    user_service: UserService = Depends(get_user_service),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of users to return"
    ),
    is_active: bool = Query(None, description="Filter by active status"),
    is_superuser: bool = Query(None, description="Filter by superuser status"),
) -> Any:
    """
    Retrieve users with optional filtering.

    This endpoint allows superusers to get a paginated list of users
    with optional filtering by active status and superuser status.
    """
    try:
        users, total_count = user_service.get_users_with_count(
            skip=skip, limit=limit, is_active=is_active, is_superuser=is_superuser
        )

        return UsersListOutput(
            data=[UserPublicOutput.model_validate(user) for user in users],
            count=total_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublicOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user. Requires superuser privileges.",
)
def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Create a new user.

    This endpoint allows superusers to create new users.
    An email notification will be sent if email is configured.
    """
    try:
        user = user_service.create_user(user_data)

        # Send welcome email if configured
        if settings.emails_enabled and user_data.email:
            email_data = generate_new_account_email(
                email_to=user_data.email,
                username=user_data.email,
                password=user_data.password,
            )
            send_email(
                email_to=user_data.email,
                subject=email_data.subject,
                html_content=email_data.html_content,
            )

        return UserPublicOutput.model_validate(user)

    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.get(
    "/me",
    response_model=UserPublicOutput,
    summary="Get current user",
    description="Get the current authenticated user's information.",
)
def get_current_user_info(current_user: CurrentUser) -> Any:
    """
    Get current user information.

    Returns the profile information of the currently authenticated user.
    """
    return UserPublicOutput.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserPublicOutput,
    summary="Update current user",
    description="Update the current authenticated user's information.",
)
def update_current_user(
    user_data: UserUpdateMe,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Update current user's information.

    Allows the authenticated user to update their own profile information.
    """
    try:
        # Check if email is being changed and if it's already taken
        if user_data.email and user_data.email != current_user.email:
            existing_user = user_service.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=EMAIL_EXISTS_MSG
                )

        # Convert to UserUpdate for service
        update_data = UserUpdate(**user_data.model_dump(exclude_unset=True))
        updated_user = user_service.update_user(current_user.id, update_data)

        return UserPublicOutput.model_validate(updated_user)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.patch(
    "/me/password",
    response_model=MessageOutput,
    summary="Update current user password",
    description="Update the current authenticated user's password.",
)
def update_current_user_password(
    password_data: UpdatePassword,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Update current user's password.

    Requires the current password for verification.
    """
    try:
        user_service.update_user_password(current_user.id, password_data)
        return MessageOutput(message=PASSWORD_UPDATED_MSG)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}",
        )


@router.delete(
    "/me",
    response_model=MessageOutput,
    summary="Delete current user",
    description="Delete the current authenticated user's account.",
)
def delete_current_user(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Delete current user's account.

    Superusers cannot delete themselves for security reasons.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=SUPERUSER_DELETE_SELF_MSG
        )

    try:
        user_service.delete_user(current_user.id)
        return MessageOutput(message=USER_DELETED_MSG)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


@router.get(
    "/{user_id}",
    response_model=UserPublicOutput,
    summary="Get user by ID",
    description="Get a specific user by their ID.",
)
def get_user_by_id(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Get a specific user by ID.

    Users can only access their own profile unless they are superusers.
    """
    try:
        user = user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
            )

        # Check permissions
        if user.id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this user",
            )

        return UserPublicOutput.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}",
        )


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublicOutput,
    summary="Update user by ID",
    description="Update a specific user by their ID. Requires superuser privileges.",
)
def update_user_by_id(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Update a specific user by ID.

    This endpoint allows superusers to update any user.
    """
    try:
        # Check if email is being changed and if it's already taken
        if user_data.email:
            existing_user = user_service.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=EMAIL_EXISTS_MSG
                )

        updated_user = user_service.update_user(user_id, user_data)
        return UserPublicOutput.model_validate(updated_user)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=MessageOutput,
    summary="Delete user by ID",
    description="Delete a specific user by their ID. Requires superuser privileges.",
)
def delete_user_by_id(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """
    Delete a specific user by ID.

    Superusers cannot delete themselves for security reasons.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=SUPERUSER_DELETE_SELF_MSG
        )

    try:
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
            )

        return MessageOutput(message=USER_DELETED_MSG)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


# Additional user management endpoints


@router.patch(
    "/{user_id}/activate",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublicOutput,
    summary="Activate user",
    description="Activate a user account. Requires superuser privileges.",
)
def activate_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Activate a user account."""
    try:
        user = user_service.activate_user(user_id)
        return UserPublicOutput.model_validate(user)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}",
        )


@router.patch(
    "/{user_id}/deactivate",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublicOutput,
    summary="Deactivate user",
    description="Deactivate a user account. Requires superuser privileges.",
)
def deactivate_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Deactivate a user account."""
    try:
        user = user_service.deactivate_user(user_id)
        return UserPublicOutput.model_validate(user)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        )


@router.patch(
    "/{user_id}/promote",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublicOutput,
    summary="Promote user to superuser",
    description="Promote a user to superuser status. Requires superuser privileges.",
)
def promote_user_to_superuser(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Promote a user to superuser status."""
    try:
        user = user_service.promote_to_superuser(user_id)
        return UserPublicOutput.model_validate(user)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote user: {str(e)}",
        )


# Session management endpoints


@router.get(
    "/me/sessions",
    response_model=list[UserSessionResponse],
    summary="Get current user sessions",
    description="Get all active sessions for the current user.",
)
def get_current_user_sessions(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Get all active sessions for the current user."""
    try:
        sessions = user_service.get_active_sessions(current_user.id)
        return [UserSessionResponse.model_validate(session) for session in sessions]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        )


@router.delete(
    "/me/sessions",
    response_model=MessageOutput,
    summary="Invalidate all user sessions",
    description="Invalidate all active sessions for the current user.",
)
def invalidate_current_user_sessions(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Invalidate all active sessions for the current user."""
    try:
        count = user_service.invalidate_user_sessions(current_user.id)
        return MessageOutput(message=f"Invalidated {count} sessions")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate sessions: {str(e)}",
        )


# Profile management endpoints


@router.get(
    "/me/profile",
    response_model=UserProfileOutput,
    summary="Get current user profile",
    description="Get the current user's profile information.",
)
def get_current_user_profile(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Get the current user's profile."""
    try:
        profile = user_service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND_MSG
            )

        return UserProfileOutput.model_validate(profile)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}",
        )


@router.patch(
    "/me/profile",
    response_model=UserProfileOutput,
    summary="Update current user profile",
    description="Update the current user's profile information.",
)
def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Update the current user's profile."""
    try:
        profile = user_service.update_user_profile(current_user.id, profile_data)
        return UserProfileOutput.model_validate(profile)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_MSG
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        )
