"""
Auth Models Module

This module contains authentication-related database models.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, DateTime, Boolean, Relationship

if TYPE_CHECKING:
    from src.apps.users.models import User

# Constants
USER_ID_FK = "users.id"


# Base model with UUID for consistency with User model
class BaseAuthModel(SQLModel):
    """Base model with UUID for auth entities to match User model"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RefreshToken(BaseAuthModel, table=True):
    """
    Refresh Token Model

    Stores refresh tokens for extended authentication sessions.
    Separate from user sessions for better security control.
    """

    __tablename__ = "auth_refresh_tokens"

    # Token data
    token_hash: str = Field(max_length=255, unique=True, index=True)
    user_id: uuid.UUID = Field(foreign_key=USER_ID_FK, index=True)

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="refresh_tokens")

    # Token lifecycle
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    revoked: bool = Field(default=False)
    revoked_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Metadata
    device_id: Optional[str] = Field(default=None, max_length=255)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)

    def is_valid(self) -> bool:
        """Check if the refresh token is still valid."""
        now = datetime.now(timezone.utc)
        return not self.revoked and self.expires_at > now

    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.revoked = True
        self.revoked_at = datetime.now(timezone.utc)


class PasswordResetToken(BaseAuthModel, table=True):
    """
    Password Reset Token Model

    Temporary tokens for password reset functionality.
    """

    __tablename__ = "auth_password_reset_tokens"

    # Token data
    token_hash: str = Field(max_length=255, unique=True, index=True)
    user_id: uuid.UUID = Field(foreign_key=USER_ID_FK, index=True)
    email: str = Field(max_length=255, index=True)

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="password_reset_tokens")

    # Token lifecycle
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    used: bool = Field(default=False)
    used_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Metadata
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    def is_valid(self) -> bool:
        """Check if the password reset token is still valid."""
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at

        # Ensure both datetimes have timezone info for comparison
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return not self.used and expires_at > now

    def mark_used(self) -> None:
        """Mark the token as used."""
        self.used = True
        self.used_at = datetime.now(timezone.utc)


class LoginAttempt(BaseAuthModel, table=True):
    """
    Login Attempt Model

    Track login attempts for security monitoring and rate limiting.
    """

    __tablename__ = "auth_login_attempts"

    # Attempt data
    email: str = Field(max_length=255, index=True)
    successful: bool = Field(default=False)
    failure_reason: Optional[str] = Field(default=None, max_length=255)

    # Request metadata
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # User reference (optional - may not exist if email is invalid)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key=USER_ID_FK)

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="login_attempts")
