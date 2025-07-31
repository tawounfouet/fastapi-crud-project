from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from src.core.config import settings

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    plain_password_bytes = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt with secure defaults.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password as a string
    """
    password_bytes = password.encode("utf-8")

    # Use a cost factor of 12 for good security vs performance balance
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")
