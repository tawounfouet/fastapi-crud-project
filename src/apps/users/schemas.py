"""
Users App Schemas - API input/output data models
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Constants for field descriptions
EMAIL_DESC = "User's email address"
FIRST_NAME_DESC = "User's first name"
LAST_NAME_DESC = "User's last name"
PASSWORD_DESC = "User's password"
PASSWORD_MIN_LENGTH_MSG = "Password must be at least 8 characters long"
USER_ID_DESC = "User ID"
LIST_OF_USERS_DESC = "List of users"
TOTAL_USERS_DESC = "Total number of users"
PAGE_SIZE_DESC = "Page size"
SESSION_EXPIRATION_DESC = "Session expiration time"

# Constants for validation
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 40
MAX_NAME_LENGTH = 100


# Base schemas
class UserBase(BaseModel):
    """Base user schema with shared properties"""

    email: EmailStr = Field(..., description=EMAIL_DESC)
    first_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=FIRST_NAME_DESC
    )
    last_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=LAST_NAME_DESC
    )
    is_active: bool = Field(True, description="Whether the user account is active")


# Input schemas (for API requests)
class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description=PASSWORD_DESC,
    )
    is_superuser: bool = Field(
        False, description="Whether the user has superuser privileges"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(PASSWORD_MIN_LENGTH_MSG)
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower() if v else v


class UserRegister(BaseModel):
    """Schema for user registration (public registration)"""

    email: EmailStr = Field(..., max_length=MAX_NAME_LENGTH, description=EMAIL_DESC)
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description=PASSWORD_DESC,
    )
    first_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=FIRST_NAME_DESC
    )
    last_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=LAST_NAME_DESC
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(PASSWORD_MIN_LENGTH_MSG)
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower() if v else v


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: EmailStr | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=EMAIL_DESC
    )
    first_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=FIRST_NAME_DESC
    )
    last_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=LAST_NAME_DESC
    )
    password: str | None = Field(
        None,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description=PASSWORD_DESC,
    )
    is_active: bool | None = Field(
        None, description="Whether the user account is active"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Validate password strength if provided"""
        if v is not None and len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(PASSWORD_MIN_LENGTH_MSG)
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        """Normalize email to lowercase"""
        return v.lower() if v else v

    model_config = ConfigDict(extra="forbid")


class UserUpdateMe(BaseModel):
    """Schema for users updating their own profile"""

    first_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=FIRST_NAME_DESC
    )
    last_name: str | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=LAST_NAME_DESC
    )
    email: EmailStr | None = Field(
        None, max_length=MAX_NAME_LENGTH, description=EMAIL_DESC
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        """Normalize email to lowercase"""
        return v.lower() if v else v


class UpdatePassword(BaseModel):
    """Schema for password updates"""

    current_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="Current password",
    )
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(PASSWORD_MIN_LENGTH_MSG)
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


# Output schemas (for API responses)
class UserResponse(UserBase):
    """Schema for user API responses"""

    id: uuid.UUID = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    is_superuser: bool = Field(
        ..., description="Whether the user has superuser privileges"
    )

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Schema for public user information (limited data)"""

    id: uuid.UUID = Field(..., description="User's unique identifier")
    first_name: str | None = Field(None, description=FIRST_NAME_DESC)
    last_name: str | None = Field(None, description=LAST_NAME_DESC)

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

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for paginated user list responses"""

    users: list[UserResponse] = Field(..., description=LIST_OF_USERS_DESC)
    total: int = Field(..., description=TOTAL_USERS_DESC)
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description=PAGE_SIZE_DESC)
    pages: int = Field(..., description="Total number of pages")


class UsersPublic(BaseModel):
    """Schema for public user collection"""

    data: list[UserPublic] = Field(..., description=LIST_OF_USERS_DESC)
    count: int = Field(..., description="Total count of users")


# Profile schemas
class UserProfileBase(BaseModel):
    """Base user profile schema"""

    bio: str | None = Field(None, max_length=1000, description="User's biography")
    avatar_url: str | None = Field(
        None, max_length=500, description="User's avatar URL"
    )
    phone: str | None = Field(None, max_length=20, description="User's phone number")
    location: str | None = Field(None, max_length=100, description="User's location")
    website: str | None = Field(None, max_length=500, description="User's website URL")

    # Social links
    twitter_handle: str | None = Field(
        None, max_length=50, description="Twitter handle"
    )
    linkedin_url: str | None = Field(
        None, max_length=500, description="LinkedIn profile URL"
    )
    github_username: str | None = Field(
        None, max_length=50, description="GitHub username"
    )

    # Preferences
    timezone: str | None = Field("UTC", max_length=50, description="User's timezone")
    language: str | None = Field(
        "en", max_length=10, description="User's preferred language"
    )
    theme: str | None = Field(
        "light", max_length=20, description="User's UI theme preference"
    )

    # Privacy settings
    profile_public: bool = Field(True, description="Whether profile is public")
    show_email: bool = Field(False, description="Whether to show email publicly")


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile"""

    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile"""

    model_config = ConfigDict(extra="forbid")


class UserProfileResponse(UserProfileBase):
    """Schema for user profile API responses"""

    id: uuid.UUID = Field(..., description="Profile's unique identifier")
    user_id: uuid.UUID = Field(..., description="Associated user ID")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# Statistics and admin schemas
class UserStats(BaseModel):
    """Schema for user statistics"""

    total_users: int = Field(..., description=TOTAL_USERS_DESC)
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    superusers: int = Field(..., description="Number of superusers")
    users_this_month: int = Field(..., description="Users registered this month")
    users_this_week: int = Field(..., description="Users registered this week")


# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower() if v else v


class UserTokenResponse(BaseModel):
    """Schema for authentication token response"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


# Search and filtering schemas
class UserSearchRequest(BaseModel):
    """Schema for user search requests"""

    query: str | None = Field(None, min_length=2, description="Search query")
    is_active: bool | None = Field(None, description="Filter by active status")
    is_superuser: bool | None = Field(None, description="Filter by superuser status")
    created_after: datetime | None = Field(None, description="Filter by creation date")
    created_before: datetime | None = Field(None, description="Filter by creation date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description=PAGE_SIZE_DESC)

    # Sorting
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        """Validate sort field"""
        allowed_fields = [
            "created_at",
            "updated_at",
            "email",
            "first_name",
            "last_name",
            "is_active",
        ]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v


# Session management schemas
class UserSessionCreate(BaseModel):
    """Schema for creating a user session"""

    ip_address: str | None = Field(None, description="IP address of the session")
    user_agent: str | None = Field(None, description="User agent string")
    expires_at: datetime | None = Field(None, description=SESSION_EXPIRATION_DESC)
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional session metadata"
    )


class UserSessionResponse(BaseModel):
    """Schema for user session response"""

    id: uuid.UUID = Field(..., description="Session ID")
    user_id: uuid.UUID = Field(..., description=USER_ID_DESC)
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    is_active: bool = Field(..., description="Session active status")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description=SESSION_EXPIRATION_DESC)
    last_activity: datetime | None = Field(None, description="Last activity time")


# Output schemas for API responses
class MessageOutput(BaseModel):
    """Schema for simple message responses"""

    message: str = Field(..., description="Response message")


class UserPublicOutput(UserBase):
    """Schema for public user information output"""

    id: uuid.UUID = Field(..., description=USER_ID_DESC)
    is_superuser: bool = Field(..., description="Whether user is a superuser")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class UsersListOutput(BaseModel):
    """Schema for paginated user list output"""

    data: list[UserPublicOutput] = Field(..., description=LIST_OF_USERS_DESC)
    count: int = Field(..., description=TOTAL_USERS_DESC)
    page: int = Field(1, description="Current page number")
    size: int = Field(20, description=PAGE_SIZE_DESC)


class UserSessionOutput(BaseModel):
    """Schema for user session output"""

    id: uuid.UUID = Field(..., description="Session ID")
    user_id: uuid.UUID = Field(..., description=USER_ID_DESC)
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    is_active: bool = Field(..., description="Session active status")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description=SESSION_EXPIRATION_DESC)
    last_activity: datetime | None = Field(None, description="Last activity time")


class UserProfileOutput(BaseModel):
    """Schema for user profile output"""

    id: uuid.UUID = Field(..., description="Profile ID")
    user_id: uuid.UUID = Field(..., description=USER_ID_DESC)
    bio: str | None = Field(None, description="User bio")
    avatar_url: str | None = Field(None, description="Avatar URL")
    website_url: str | None = Field(None, description="Website URL")
    location: str | None = Field(None, description="User location")
    birth_date: datetime | None = Field(None, description="Birth date")
    phone: str | None = Field(None, description="Phone number")
    preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences"
    )
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
