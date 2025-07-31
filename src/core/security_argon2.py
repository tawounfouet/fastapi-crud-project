"""
Modern Security Module using Argon2 - 2025 Best Practices

Argon2 is the winner of the Password Hashing Competition (PHC) and is
considered the gold standard for password hashing in modern applications.
It provides better security than bcrypt with built-in protection against
side-channel attacks and better resistance to specialized hardware attacks.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError

from src.core.config import settings

# Initialize Argon2 password hasher with secure defaults
# These parameters provide excellent security vs performance balance
ph = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=1,  # Number of parallel threads
    hash_len=32,  # Length of hash in bytes
    salt_len=16,  # Length of salt in bytes
)

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its Argon2 hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The Argon2 hashed password to verify against

    Returns:
        True if password matches, False otherwise

    Raises:
        ValueError: If verification fails due to invalid input
    """
    try:
        # Argon2 handles string inputs directly
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        # Password doesn't match
        return False
    except Exception as e:
        # Invalid hash format or other errors
        raise ValueError(f"Password verification failed: {e}")


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2 with secure defaults.

    Args:
        password: The plain text password to hash

    Returns:
        The Argon2 hashed password as a string

    Raises:
        ValueError: If hashing fails due to invalid input
    """
    try:
        return ph.hash(password)
    except HashingError as e:
        raise ValueError(f"Password hashing failed: {e}")


def check_needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed with current parameters.

    This is useful for gradually upgrading hash parameters over time
    without forcing all users to reset their passwords.

    Args:
        hashed_password: The existing hash to check

    Returns:
        True if the hash should be regenerated with current parameters
    """
    try:
        return ph.check_needs_rehash(hashed_password)
    except Exception:
        # If we can't parse the hash, it definitely needs rehashing
        return True


def rehash_password_if_needed(plain_password: str, current_hash: str) -> str | None:
    """
    Rehash a password if the current hash uses outdated parameters.

    This should be called during successful login to gradually upgrade
    password hashes to current security parameters.

    Args:
        plain_password: The plain text password
        current_hash: The current hash

    Returns:
        New hash if rehashing was needed, None if current hash is fine
    """
    if check_needs_rehash(current_hash):
        return get_password_hash(plain_password)
    return None


# Configuration info for logging/monitoring
def get_hash_info() -> dict[str, Any]:
    """Get information about current hashing configuration."""
    return {
        "algorithm": "Argon2id",
        "time_cost": ph.time_cost,
        "memory_cost": ph.memory_cost,
        "parallelism": ph.parallelism,
        "hash_len": ph.hash_len,
        "salt_len": ph.salt_len,
        "version": argon2.__version__,
    }
