"""
Users App Models - Database entities and domain models
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import EmailStr
from sqlmodel import Field, Index, Relationship, SQLModel

if TYPE_CHECKING:
    pass


class BaseUserModel(SQLModel):
    """Base model for user-related entities"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Note: SQLModel uses model_config differently than Pydantic
    # model_config = ConfigDict(arbitrary_types_allowed=True)


class User(BaseUserModel, table=True):
    """
    User domain model representing users in the system

    Contains core user information, authentication details,
    and relationships to other entities.
    """

    __tablename__ = "users"  # Clean table name following DDD approach

    # Core user information
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)

    # Authentication and authorization
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True, index=True)
    is_superuser: bool = Field(default=False, index=True)

    # Database optimization
    __table_args__ = (
        Index("ix_user_email_active", "email", "is_active"),
        Index("ix_user_super_active", "is_superuser", "is_active"),
    )

    @property
    def full_name(self) -> str:
        """Computed property for full name combining first and last name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""

    def __repr__(self) -> str:
        return f"<User(email='{self.email}', full_name='{self.full_name}')>"

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (active)"""
        return self.is_active

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        # Superusers have all permissions
        if self.is_superuser:
            return True

        # Define permission logic here
        # For now, only basic permissions
        basic_permissions = ["read_own_data", "update_own_data"]

        if not self.is_active:
            return False

        return permission in basic_permissions

    def can_access_admin(self) -> bool:
        """Check if user can access admin features"""
        return self.is_superuser and self.is_active

    def update_last_activity(self) -> None:
        """Update the last activity timestamp"""
        self.updated_at = datetime.now(timezone.utc)

    # Relationships
    sessions: list["UserSession"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    profile: Optional["UserProfile"] = Relationship(back_populates="user")

    # Auth-related relationships will be added after model resolution
    # refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    # password_reset_tokens: List["PasswordResetToken"] = Relationship(back_populates="user")
    # login_attempts: List["LoginAttempt"] = Relationship(back_populates="user")


class UserSession(BaseUserModel, table=True):
    """
    User session model for tracking active sessions
    Optional: for more advanced session management
    """

    __tablename__ = "user_sessions"

    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    session_token: str = Field(max_length=255, unique=True, index=True)
    expires_at: datetime = Field(index=True)
    is_active: bool = Field(default=True, index=True)
    user_agent: str | None = Field(default=None, max_length=500)
    ip_address: str | None = Field(default=None, max_length=45)

    # Relationships
    user: User = Relationship()

    # Database optimization
    __table_args__ = (
        Index("ix_session_user_active", "user_id", "is_active"),
        Index("ix_session_expires", "expires_at", "is_active"),
    )

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired()


class UserProfile(BaseUserModel, table=True):
    """
    Extended user profile information
    Separate from core User model for optional profile data
    """

    __tablename__ = "user_profiles"

    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, unique=True)
    bio: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=500)

    # Social links
    twitter_handle: str | None = Field(default=None, max_length=50)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_username: str | None = Field(default=None, max_length=50)

    # Preferences
    timezone: str | None = Field(default="UTC", max_length=50)
    language: str | None = Field(default="en", max_length=10)
    theme: str | None = Field(default="light", max_length=20)

    # Privacy settings
    profile_public: bool = Field(default=True)
    show_email: bool = Field(default=False)

    # Relationships
    user: User = Relationship()

    def __repr__(self) -> str:
        return f"<UserProfile(user_id='{self.user_id}')>"
