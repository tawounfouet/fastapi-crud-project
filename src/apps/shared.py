"""
Shared Models and Schemas

This module contains shared schemas and models that are used across multiple apps.
"""

import uuid
from datetime import datetime, timezone
from pydantic import EmailStr
from sqlmodel import SQLModel, Field


# Base models for common functionality
class BaseModel(SQLModel):
    """
    Base model with common fields for all database entities.

    Provides:
    - UUID primary keys for better scalability
    - Timezone-aware timestamps with proper indexing
    - Soft delete capability
    - Audit trail support
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    is_active: bool = Field(default=True, index=True)


class AuditMixin(SQLModel):
    """
    Mixin for audit trail functionality.

    Tracks who created and last updated records.
    """

    created_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="users.id", index=True
    )
    updated_by_id: uuid.UUID | None = Field(
        default=None, foreign_key="users.id", index=True
    )


# Generic message schema
class Message(SQLModel):
    """Generic message response"""

    message: str


# Authentication schemas
class Token(SQLModel):
    """JSON payload containing access token"""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    """Contents of JWT token"""

    sub: str | None = None


class NewPassword(SQLModel):
    """New password schema for password reset"""

    token: str
    new_password: str = Field(min_length=8, max_length=40)


# User registration and update schemas for backward compatibility
class UserRegister(SQLModel):
    """User registration schema"""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UserUpdateMe(SQLModel):
    """User self-update schema"""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=255)
