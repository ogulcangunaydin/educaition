"""
DEPRECATED: Import from app.core.security instead.

This module re-exports from app.core.security for backward compatibility.
"""

from app.core.security import (
    PasswordStrength,
    PasswordValidationError,
    SecurityConfig,
    check_password_strength,
    create_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)

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
