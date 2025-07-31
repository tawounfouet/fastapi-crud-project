"""
Tests for User Services

This module contains unit tests for the UserService class.
"""

import uuid
from datetime import datetime

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

# Only import what we need for testing to avoid model conflicts
from src.apps.users.models import User, UserProfile, UserSession
from src.apps.users.schemas import (
    UpdatePassword,
    UserCreate,
    UserUpdate,
)
from src.apps.users.services import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)


@pytest.fixture
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import only our DDD models

    # Create only the DDD user tables
    User.__table__.create(engine, checkfirst=True)
    UserProfile.__table__.create(engine, checkfirst=True)
    UserSession.__table__.create(engine, checkfirst=True)

    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def user_service(test_session):
    """Create UserService instance."""
    return UserService(test_session)


@pytest.fixture
def sample_user_data():
    """Sample user creation data."""
    return UserCreate(
        email="test@example.com",
        password="SecurePassword123!",
        first_name="Test",
        last_name="User",
        is_active=True,
    )


@pytest.fixture
def sample_user(user_service, sample_user_data):
    """Create a sample user in the database."""
    return user_service.create_user(sample_user_data)


class TestUserService:
    """Test cases for UserService."""

    def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation."""
        user = user_service.create_user(sample_user_data)

        assert user.email == sample_user_data.email
        assert user.first_name == sample_user_data.first_name
        assert user.last_name == sample_user_data.last_name
        assert user.full_name == "Test User"  # Test the computed property
        assert user.is_active == sample_user_data.is_active
        assert user.is_superuser is False  # Default value for new users
        assert user.hashed_password is not None
        assert user.hashed_password != sample_user_data.password
        assert user.id is not None
        assert isinstance(user.created_at, datetime)

    def test_create_user_duplicate_email(
        self, user_service, sample_user_data, sample_user
    ):
        """Test creating user with duplicate email raises error."""
        with pytest.raises(UserAlreadyExistsError):
            user_service.create_user(sample_user_data)

    def test_get_user_by_id_success(self, user_service, sample_user):
        """Test successful user retrieval by ID."""
        retrieved_user = user_service.get_user_by_id(sample_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == sample_user.id
        assert retrieved_user.email == sample_user.email

    def test_get_user_by_id_not_found(self, user_service):
        """Test user retrieval with non-existent ID."""
        non_existent_id = uuid.uuid4()
        user = user_service.get_user_by_id(non_existent_id)

        assert user is None

    def test_get_user_by_email_success(self, user_service, sample_user):
        """Test successful user retrieval by email."""
        retrieved_user = user_service.get_user_by_email(sample_user.email)

        assert retrieved_user is not None
        assert retrieved_user.email == sample_user.email
        assert retrieved_user.id == sample_user.id

    def test_get_user_by_email_not_found(self, user_service):
        """Test user retrieval with non-existent email."""
        user = user_service.get_user_by_email("nonexistent@example.com")

        assert user is None

    def test_update_user_success(self, user_service, sample_user):
        """Test successful user update."""
        update_data = UserUpdate(
            first_name="Updated", last_name="Name", is_active=False
        )

        updated_user = user_service.update_user(sample_user.id, update_data)

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.full_name == "Updated Name"  # Test computed property
        assert updated_user.is_active is False
        assert updated_user.email == sample_user.email  # unchanged
        assert updated_user.updated_at > sample_user.created_at

    def test_update_user_not_found(self, user_service):
        """Test updating non-existent user raises error."""
        non_existent_id = uuid.uuid4()
        update_data = UserUpdate(first_name="New", last_name="Name")

        with pytest.raises(UserNotFoundError):
            user_service.update_user(non_existent_id, update_data)

    def test_update_user_password_success(self, user_service, sample_user):
        """Test successful password update."""
        # Store original password hash for comparison
        original_password_hash = sample_user.hashed_password

        password_data = UpdatePassword(
            current_password="SecurePassword123!", new_password="NewSecurePassword456!"
        )

        updated_user = user_service.update_user_password(sample_user.id, password_data)

        assert updated_user.hashed_password != original_password_hash
        assert updated_user.updated_at > sample_user.created_at

    def test_update_user_password_wrong_current(self, user_service, sample_user):
        """Test password update with wrong current password."""
        password_data = UpdatePassword(
            current_password="WrongPassword", new_password="NewSecurePassword456!"
        )

        with pytest.raises(InvalidCredentialsError):
            user_service.update_user_password(sample_user.id, password_data)

    def test_authenticate_user_success(self, user_service, sample_user):
        """Test successful user authentication."""
        authenticated_user = user_service.authenticate_user(
            sample_user.email, "SecurePassword123!"
        )

        assert authenticated_user.id == sample_user.id
        assert authenticated_user.email == sample_user.email

    def test_authenticate_user_wrong_password(self, user_service, sample_user):
        """Test authentication with wrong password."""
        with pytest.raises(InvalidCredentialsError):
            user_service.authenticate_user(sample_user.email, "WrongPassword")

    def test_authenticate_user_wrong_email(self, user_service):
        """Test authentication with wrong email."""
        with pytest.raises(InvalidCredentialsError):
            user_service.authenticate_user("wrong@example.com", "AnyPassword")

    def test_delete_user_success(self, user_service, sample_user):
        """Test successful user deletion (soft delete)."""
        success = user_service.delete_user(sample_user.id)

        assert success is True

        # User should still exist but be inactive
        user = user_service.get_user_by_id(sample_user.id)
        assert user is not None
        assert user.is_active is False

    def test_delete_user_not_found(self, user_service):
        """Test deleting non-existent user."""
        non_existent_id = uuid.uuid4()
        success = user_service.delete_user(non_existent_id)

        assert success is False

    def test_activate_user(self, user_service, sample_user):
        """Test user activation."""
        # First deactivate
        user_service.deactivate_user(sample_user.id)

        # Then activate
        activated_user = user_service.activate_user(sample_user.id)

        assert activated_user.is_active is True

    def test_deactivate_user(self, user_service, sample_user):
        """Test user deactivation."""
        deactivated_user = user_service.deactivate_user(sample_user.id)

        assert deactivated_user.is_active is False

    def test_promote_to_superuser(self, user_service, sample_user):
        """Test promoting user to superuser."""
        promoted_user = user_service.promote_to_superuser(sample_user.id)

        assert promoted_user.is_superuser is True

    def test_create_access_token_for_user(self, user_service, sample_user):
        """Test access token creation."""
        token = user_service.create_access_token_for_user(sample_user)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_get_users_with_filters(self, user_service, test_session):
        """Test getting users with filters."""
        # Create multiple users
        user_service.create_user(
            UserCreate(
                email="active@example.com",
                password="Password123!",
                first_name="Active",
                last_name="User",
                is_active=True,
            )
        )

        user_service.create_user(
            UserCreate(
                email="inactive@example.com",
                password="Password123!",
                first_name="Inactive",
                last_name="User",
                is_active=False,
            )
        )

        super_user = user_service.create_user(
            UserCreate(
                email="super@example.com",
                password="Password123!",
                first_name="Super",
                last_name="User",
                is_active=True,
            )
        )
        # Promote to superuser
        user_service.promote_to_superuser(super_user.id)

        # Test filtering by active status
        active_users = user_service.get_users(is_active=True)
        assert len(active_users) >= 2  # active_user and superuser

        inactive_users = user_service.get_users(is_active=False)
        assert len(inactive_users) >= 1  # inactive_user

        # Test filtering by superuser status
        superusers = user_service.get_users(is_superuser=True)
        assert len(superusers) >= 1  # superuser

        regular_users = user_service.get_users(is_superuser=False)
        assert len(regular_users) >= 2  # active_user and inactive_user
