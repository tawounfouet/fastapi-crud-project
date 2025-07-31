"""
User Service Module

This module contains the business logic for user operations following DDD principles.
It encapsulates all user-related operations and business rules.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from src.core.config import settings
from src.core.security_unified import (
    create_access_token,
    get_password_hash,
    upgrade_password_hash,
    verify_password,
)

from .models import User, UserProfile, UserSession
from .schemas import (
    UpdatePassword,
    UserCreate,
    UserProfileUpdate,
    UserSessionCreate,
    UserUpdate,
)


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    pass


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when authentication fails."""

    pass


class InactiveUserError(Exception):
    """Raised when trying to authenticate an inactive user."""

    pass


class UserService:
    """
    Service class for user operations.

    This class encapsulates all business logic related to users,
    following Domain-Driven Design principles.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user instance

        Raises:
            UserAlreadyExistsError: If user with email already exists
        """
        # Check if user with email already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists"
            )

        # Create user with hashed password
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = get_password_hash(user_data.password)

        user = User(**user_dict)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """
        Create a superuser account.

        This method is similar to Django's create_superuser and provides
        a dedicated API for creating superuser accounts during initialization
        or management commands.

        Args:
            email: Superuser email address
            password: Superuser password
            first_name: Optional first name
            last_name: Optional last name

        Returns:
            Created superuser instance

        Raises:
            UserAlreadyExistsError: If user with email already exists
        """
        # Check if user with email already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        # Create superuser with hashed password
        user_dict = {
            "email": email,
            "hashed_password": get_password_hash(password),
            "is_active": True,
            "is_superuser": True,
            "first_name": first_name,
            "last_name": last_name,
        }

        user = User(**user_dict)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User instance or None if not found
        """
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> list[User]:
        """
        Get a list of users with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            is_superuser: Filter by superuser status

        Returns:
            List of user instances
        """
        statement = select(User)

        if is_active is not None:
            statement = statement.where(User.is_active == is_active)

        if is_superuser is not None:
            statement = statement.where(User.is_superuser == is_superuser)

        statement = statement.offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def get_users_with_count(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> tuple[list[User], int]:
        """
        Get a list of users with total count for pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            is_superuser: Filter by superuser status

        Returns:
            Tuple of (users list, total count)
        """
        from sqlmodel import func

        # Build base query for filtering
        where_conditions = []
        if is_active is not None:
            where_conditions.append(User.is_active == is_active)
        if is_superuser is not None:
            where_conditions.append(User.is_superuser == is_superuser)

        # Get total count
        count_statement = select(func.count()).select_from(User)
        for condition in where_conditions:
            count_statement = count_statement.where(condition)

        total_count = self.session.exec(count_statement).one()

        # Get users with pagination
        users_statement = select(User)
        for condition in where_conditions:
            users_statement = users_statement.where(condition)

        users_statement = users_statement.offset(skip).limit(limit)
        users = list(self.session.exec(users_statement).all())

        return users, total_count

    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        """
        Update a user.

        Args:
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        update_data = user_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "password":
                # Hash password before setting it
                user.hashed_password = get_password_hash(value)
            else:
                setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def update_user_password(
        self, user_id: uuid.UUID, password_data: UpdatePassword
    ) -> User:
        """
        Update a user's password.

        Args:
            user_id: User ID
            password_data: Password update data

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If current password is incorrect
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Delete a user (soft delete by setting is_active to False).

        Args:
            user_id: User ID

        Returns:
            True if user was deleted, False if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()

        return True

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate a user with email and password.

        This method also automatically upgrades password hashes to the current
        algorithm/parameters if needed, providing seamless security improvements.

        Args:
            email: User email
            password: User password

        Returns:
            Authenticated user instance

        Raises:
            InvalidCredentialsError: If credentials are invalid
            InactiveUserError: If user is not active
        """
        user = self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        # Check if password hash needs upgrading (modern security best practice)
        new_hash = upgrade_password_hash(password, user.hashed_password)
        if new_hash:
            # Upgrade to current algorithm/parameters
            user.hashed_password = new_hash
            user.updated_at = datetime.now(timezone.utc)
            self.session.add(user)
            self.session.commit()
            # Note: We don't refresh here to avoid extra DB query during login

        return user

    def create_access_token_for_user(self, user: User) -> str:
        """
        Create an access token for a user.

        Args:
            user: User instance

        Returns:
            JWT access token string
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

    def activate_user(self, user_id: uuid.UUID) -> User:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def deactivate_user(self, user_id: uuid.UUID) -> User:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def promote_to_superuser(self, user_id: uuid.UUID) -> User:
        """
        Promote a user to superuser.

        Args:
            user_id: User ID

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        user.is_superuser = True
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    # Session management methods
    def create_user_session(
        self, user_id: uuid.UUID, session_data: UserSessionCreate
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user_id: User ID
            session_data: Session creation data

        Returns:
            Created session instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        session_dict = session_data.model_dump()
        session_dict["user_id"] = user_id

        user_session = UserSession(**session_dict)
        self.session.add(user_session)
        self.session.commit()
        self.session.refresh(user_session)

        return user_session

    def get_active_sessions(self, user_id: uuid.UUID) -> list[UserSession]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active session instances
        """
        statement = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active is True,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        return list(self.session.exec(statement).all())

    def invalidate_user_sessions(self, user_id: uuid.UUID) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        sessions = self.get_active_sessions(user_id)
        count = 0

        for session in sessions:
            session.is_active = False
            self.session.add(session)
            count += 1

        self.session.commit()
        return count

    # Profile management methods
    def get_user_profile(self, user_id: uuid.UUID) -> UserProfile | None:
        """
        Get a user's profile.

        Args:
            user_id: User ID

        Returns:
            User profile instance or None if not found
        """
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.session.exec(statement).first()

    def update_user_profile(
        self, user_id: uuid.UUID, profile_data: UserProfileUpdate
    ) -> UserProfile:
        """
        Update or create a user's profile.

        Args:
            user_id: User ID
            profile_data: Profile update data

        Returns:
            Updated or created profile instance

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        profile = self.get_user_profile(user_id)

        if profile:
            # Update existing profile
            update_data = profile_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(profile, field, value)
            profile.updated_at = datetime.now(timezone.utc)
        else:
            # Create new profile
            profile_dict = profile_data.model_dump(exclude_unset=True)
            profile_dict["user_id"] = user_id
            profile = UserProfile(**profile_dict)

        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)

        return profile
