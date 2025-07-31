"""
Auth Schemas Module

This module contains Pydantic schemas for authentication operations.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field, ConfigDict

if TYPE_CHECKING:
    from src.apps.users.schemas import UserPublicOutput


# Input Schemas
class LoginRequest(BaseModel):
    """Schema for login requests"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    remember_me: bool = Field(default=False)
    device_id: Optional[str] = Field(default=None, max_length=255)


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh requests"""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""

    token: str
    new_password: str = Field(min_length=8, max_length=100)


class SignupRequest(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    terms_accepted: bool = Field(default=False)


class ChangePasswordRequest(BaseModel):
    """Schema for password change requests"""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class LogoutRequest(BaseModel):
    """Schema for logout requests"""

    all_devices: bool = Field(default=False)


# Output Schemas
class TokenResponse(BaseModel):
    """Schema for token responses"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = Field(default="bearer")
    expires_in: int  # seconds
    scope: Optional[str] = None


class LoginResponse(BaseModel):
    """Schema for login responses"""

    user: "UserPublicOutput"  # Forward reference - will be resolved at runtime
    tokens: TokenResponse
    session_id: str

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token responses"""

    id: str
    device_id: Optional[str]
    created_at: datetime
    expires_at: datetime
    user_agent: Optional[str]
    ip_address: Optional[str]
    revoked: bool

    model_config = ConfigDict(from_attributes=True)


class LoginAttemptResponse(BaseModel):
    """Schema for login attempt responses"""

    id: str
    email: str
    successful: bool
    failure_reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordResetTokenResponse(BaseModel):
    """Schema for password reset token responses"""

    message: str
    expires_in: int  # minutes


class AuthStatusResponse(BaseModel):
    """Schema for authentication status responses"""

    authenticated: bool
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class SecurityEventResponse(BaseModel):
    """Schema for security event responses"""

    event_type: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: dict = Field(default_factory=dict)


# Message Schemas
class AuthMessage(BaseModel):
    """Generic message schema for auth operations"""

    message: str
    success: bool = True


class SignupResponse(BaseModel):
    """Schema for signup responses"""

    user: "UserPublicOutput"  # Forward reference - will be resolved at runtime
    message: str
    email_verification_required: bool = False

    model_config = ConfigDict(from_attributes=True)


# Token Claims Schema
class TokenClaims(BaseModel):
    """Schema for JWT token claims"""

    sub: str  # user_id
    email: str
    is_superuser: bool = False
    is_active: bool = True
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    scope: str = "access"
    iat: int  # issued at
    exp: int  # expires at
    jti: Optional[str] = None  # JWT ID for revocation


# Rebuild models with forward references after all imports are available
def rebuild_models():
    """Rebuild models to resolve forward references"""
    try:
        from src.apps.users.schemas import UserPublicOutput

        LoginResponse.model_rebuild()
        SignupResponse.model_rebuild()
    except ImportError:
        # Handle cases where UserPublicOutput might not be available
        pass


# Call rebuild when module is imported
rebuild_models()
