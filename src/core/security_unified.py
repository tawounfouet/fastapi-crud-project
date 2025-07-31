"""
Unified Modern Security Module - 2025 Best Practices

This module provides a configurable interface for password hashing
supporting both bcrypt and Argon2 algorithms. Choose based on your needs:

- bcrypt: Mature, widely supported, good for most applications
- Argon2: State-of-the-art, winner of Password Hashing Competition,
         best security but newer

Usage:
    from src.core.security_unified import get_password_hash, verify_password

    # Hash a password
    hashed = get_password_hash("my_password")

    # Verify a password
    is_valid = verify_password("my_password", hashed)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from src.core.config import settings

# Import both implementations
from src.core.security import (
    get_password_hash as bcrypt_hash,
    verify_password as bcrypt_verify,
)

try:
    from src.core.security_argon2 import (
        get_password_hash as argon2_hash,
        verify_password as argon2_verify,
        check_needs_rehash,
        rehash_password_if_needed,
        get_hash_info,
    )

    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

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


def get_password_hash(password: str) -> str:
    """
    Hash a password using the configured algorithm.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password as a string

    Raises:
        ValueError: If hashing fails or algorithm is not supported
    """
    algorithm = settings.PASSWORD_HASH_ALGORITHM.lower()

    if algorithm == "bcrypt":
        return bcrypt_hash(password)
    elif algorithm == "argon2":
        if not ARGON2_AVAILABLE:
            raise ValueError(
                "Argon2 is not available. Install with: pip install argon2-cffi"
            )
        return argon2_hash(password)
    else:
        raise ValueError(f"Unsupported password hash algorithm: {algorithm}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    This function automatically detects the hash format and uses the
    appropriate verification method.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    # Auto-detect hash format
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        # bcrypt hash
        return bcrypt_verify(plain_password, hashed_password)
    elif hashed_password.startswith("$argon2"):
        # Argon2 hash
        if not ARGON2_AVAILABLE:
            raise ValueError("Argon2 hashes found but argon2-cffi is not installed")
        return argon2_verify(plain_password, hashed_password)
    else:
        # Try configured algorithm as fallback
        algorithm = settings.PASSWORD_HASH_ALGORITHM.lower()
        if algorithm == "bcrypt":
            return bcrypt_verify(plain_password, hashed_password)
        elif algorithm == "argon2" and ARGON2_AVAILABLE:
            return argon2_verify(plain_password, hashed_password)
        else:
            raise ValueError(f"Unknown hash format: {hashed_password[:20]}...")


def upgrade_password_hash(plain_password: str, current_hash: str) -> str | None:
    """
    Upgrade a password hash if needed.

    This function checks if a hash uses outdated parameters and rehashes
    it with current settings if necessary. Call this during successful login.

    Args:
        plain_password: The plain text password
        current_hash: The current hash

    Returns:
        New hash if upgrade was needed, None if current hash is fine
    """
    # Check if we need to upgrade between algorithms
    current_algorithm = settings.PASSWORD_HASH_ALGORITHM.lower()

    # Detect current hash type
    if current_hash.startswith("$2b$") or current_hash.startswith("$2a$"):
        current_type = "bcrypt"
    elif current_hash.startswith("$argon2"):
        current_type = "argon2"
    else:
        current_type = "unknown"

    # If algorithm changed, rehash with new algorithm
    if current_type != current_algorithm and current_algorithm in ["bcrypt", "argon2"]:
        return get_password_hash(plain_password)

    # If using Argon2, check if parameters need updating
    if current_type == "argon2" and ARGON2_AVAILABLE:
        return rehash_password_if_needed(plain_password, current_hash)

    # bcrypt doesn't have automatic parameter checking, but you could implement it
    # For now, we'll just return None (no upgrade needed)
    return None


def get_security_info() -> dict[str, Any]:
    """Get information about current security configuration."""
    info = {
        "algorithm": settings.PASSWORD_HASH_ALGORITHM,
        "bcrypt_available": True,
        "argon2_available": ARGON2_AVAILABLE,
    }

    if settings.PASSWORD_HASH_ALGORITHM == "bcrypt":
        info["bcrypt_rounds"] = settings.BCRYPT_ROUNDS
    elif settings.PASSWORD_HASH_ALGORITHM == "argon2" and ARGON2_AVAILABLE:
        info.update(get_hash_info())

    return info


# For backward compatibility, expose the functions directly
__all__ = [
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "upgrade_password_hash",
    "get_security_info",
]
