"""
Security utilities for authentication and password handling.

Provides JWT token creation and password hashing/validation functions.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt

from .config import settings
from app.services.password_service import (
    PasswordStrength,
    PasswordValidationError,
    check_password_strength,
    hash_password,
    validate_password_strength,
    verify_password,
)


class SecurityConfig:
    """Security configuration constants."""

    SECRET_KEY: str = settings.SECRET_KEY
    ALGORITHM: str = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
    )

    encoded_jwt = jwt.encode(
        to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str, validate: bool = True) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password
        validate: Whether to validate password strength (default: True)

    Returns:
        Hashed password string
    """
    return hash_password(password, validate=validate)


__all__ = [
    "create_access_token",
    "get_password_hash",
    "verify_password",
    "validate_password_strength",
    "check_password_strength",
    "PasswordValidationError",
    "PasswordStrength",
    "SecurityConfig",
]
