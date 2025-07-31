"""
Authentication and security utilities.

This module handles authentication-related utility functions including:
- Password reset token generation and verification
- JWT token operations for security
- Other auth-related utility functions
"""

from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from src.core import security
from src.core.config import settings


def generate_password_reset_token(email: str) -> str:
    """
    Generate a secure JWT token for password reset.

    Args:
        email: User's email address to encode in the token

    Returns:
        Encoded JWT token string
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    Verify and decode a password reset token.

    Args:
        token: JWT token to verify

    Returns:
        User's email if token is valid, None if invalid or expired
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
