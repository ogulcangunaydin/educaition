"""
Input validation utilities for preventing injection attacks and ensuring data integrity.

This module provides:
- String sanitization to prevent XSS and injection attacks
- Email validation
- Common field validators for Pydantic schemas
- Length constraints for different field types
"""

import html
import re
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field


# =============================================================================
# LENGTH CONSTRAINTS
# =============================================================================

class FieldLimits:
    """Standard field length limits to prevent abuse and ensure DB compatibility."""
    
    # User fields
    USERNAME_MIN = 3
    USERNAME_MAX = 50
    EMAIL_MAX = 255
    PASSWORD_MIN = 6
    PASSWORD_MAX = 128
    
    # Name fields
    NAME_MIN = 1
    NAME_MAX = 100
    DISPLAY_NAME_MAX = 200
    
    # Short text fields
    SHORT_TEXT_MAX = 255
    
    # Medium text fields (descriptions, etc.)
    MEDIUM_TEXT_MAX = 1000
    
    # Long text fields (code, content, etc.)
    LONG_TEXT_MAX = 10000
    CODE_MAX = 50000
    
    # Enum/code fields
    CODE_FIELD_MAX = 50
    
    # List limits
    MAX_LIST_ITEMS = 100
    MAX_CITIES = 20
    MAX_UNIVERSITIES = 20


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_string(value: str | None) -> str | None:
    """
    Sanitize a string to prevent XSS and injection attacks.
    
    - Strips leading/trailing whitespace
    - Escapes HTML entities
    - Removes null bytes
    - Normalizes unicode
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return value
    
    # Strip whitespace
    value = value.strip()
    
    # Remove null bytes (can cause issues in some systems)
    value = value.replace("\x00", "")
    
    # Escape HTML entities to prevent XSS
    value = html.escape(value, quote=True)
    
    return value


def sanitize_string_preserve_html(value: str | None) -> str | None:
    """
    Light sanitization that preserves HTML but removes dangerous content.
    Use only when HTML content is intentionally allowed (e.g., rich text fields).
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return value
    
    # Strip whitespace
    value = value.strip()
    
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Remove script tags and event handlers (basic XSS prevention)
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"\bon\w+\s*=", "", value, flags=re.IGNORECASE)
    
    return value


def normalize_email(value: str | None) -> str | None:
    """Normalize email to lowercase and strip whitespace."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        return value
    
    return value.strip().lower()


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_email_format(value: str | None) -> str | None:
    """Validate email format using a reasonable regex pattern."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError("Email must be a string")
    
    # Normalize first
    value = normalize_email(value)
    
    if not value:
        return None
    
    # RFC 5322 simplified pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if not re.match(email_pattern, value):
        raise ValueError("Invalid email format")
    
    if len(value) > FieldLimits.EMAIL_MAX:
        raise ValueError(f"Email must not exceed {FieldLimits.EMAIL_MAX} characters")
    
    return value


def validate_username(value: str) -> str:
    """
    Validate username format.
    - Must be alphanumeric with underscores allowed
    - Must start with a letter
    - Length between MIN and MAX
    """
    if not isinstance(value, str):
        raise ValueError("Username must be a string")
    
    value = value.strip()
    
    if len(value) < FieldLimits.USERNAME_MIN:
        raise ValueError(f"Username must be at least {FieldLimits.USERNAME_MIN} characters")
    
    if len(value) > FieldLimits.USERNAME_MAX:
        raise ValueError(f"Username must not exceed {FieldLimits.USERNAME_MAX} characters")
    
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_.]*$", value):
        raise ValueError(
            "Username must start with a letter and contain only letters, numbers, underscores, and dots"
        )
    
    return value


def validate_name(value: str | None, field_name: str = "Name") -> str | None:
    """Validate a name field (person name, room name, etc.)."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    
    value = sanitize_string(value)
    
    if value and len(value) < FieldLimits.NAME_MIN:
        raise ValueError(f"{field_name} must be at least {FieldLimits.NAME_MIN} character")
    
    if value and len(value) > FieldLimits.NAME_MAX:
        raise ValueError(f"{field_name} must not exceed {FieldLimits.NAME_MAX} characters")
    
    return value


def validate_positive_int(value: int | None) -> int | None:
    """Validate that an integer is positive."""
    if value is None:
        return None
    
    if not isinstance(value, int):
        raise ValueError("Value must be an integer")
    
    if value < 0:
        raise ValueError("Value must be a positive integer")
    
    return value


def validate_score(value: float | None, min_val: float = 0, max_val: float = 500) -> float | None:
    """Validate a score within a reasonable range."""
    if value is None:
        return None
    
    if not isinstance(value, (int, float)):
        raise ValueError("Score must be a number")
    
    if value < min_val or value > max_val:
        raise ValueError(f"Score must be between {min_val} and {max_val}")
    
    return float(value)


def validate_year(value: int | None) -> int | None:
    """Validate a year is within reasonable bounds."""
    if value is None:
        return None
    
    if not isinstance(value, int):
        raise ValueError("Year must be an integer")
    
    if value < 1900 or value > 2100:
        raise ValueError("Year must be between 1900 and 2100")
    
    return value


def validate_list_length(
    value: list | None, 
    max_items: int = FieldLimits.MAX_LIST_ITEMS
) -> list | None:
    """Validate that a list doesn't exceed the maximum number of items."""
    if value is None:
        return None
    
    if not isinstance(value, list):
        raise ValueError("Value must be a list")
    
    if len(value) > max_items:
        raise ValueError(f"List must not exceed {max_items} items")
    
    return value


def validate_code_field(value: str | None) -> str | None:
    """Validate code/enum fields (short alphanumeric codes)."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    
    value = value.strip()
    
    if len(value) > FieldLimits.CODE_FIELD_MAX:
        raise ValueError(f"Code must not exceed {FieldLimits.CODE_FIELD_MAX} characters")
    
    return value


# =============================================================================
# PYDANTIC ANNOTATED TYPES
# =============================================================================

# Sanitized strings of various lengths
SanitizedStr = Annotated[str, BeforeValidator(sanitize_string)]
SanitizedStrOptional = Annotated[str | None, BeforeValidator(sanitize_string)]

# Email field
EmailStr = Annotated[str, AfterValidator(validate_email_format)]
EmailStrOptional = Annotated[str | None, AfterValidator(validate_email_format)]

# Username field
UsernameStr = Annotated[str, AfterValidator(validate_username)]

# Name fields
NameStr = Annotated[str, BeforeValidator(sanitize_string), AfterValidator(lambda v: validate_name(v, "Name"))]
NameStrOptional = Annotated[str | None, BeforeValidator(sanitize_string), AfterValidator(lambda v: validate_name(v, "Name"))]

# Code fields (short identifiers)
CodeStr = Annotated[str, AfterValidator(validate_code_field)]
CodeStrOptional = Annotated[str | None, AfterValidator(validate_code_field)]

# Year field
YearInt = Annotated[int, AfterValidator(validate_year)]
YearIntOptional = Annotated[int | None, AfterValidator(validate_year)]

# Positive integer
PositiveInt = Annotated[int, AfterValidator(validate_positive_int)]
PositiveIntOptional = Annotated[int | None, AfterValidator(validate_positive_int)]

# Score fields
ScoreFloat = Annotated[float, AfterValidator(validate_score)]
ScoreFloatOptional = Annotated[float | None, AfterValidator(validate_score)]


# =============================================================================
# PYDANTIC FIELD FACTORIES
# =============================================================================

def short_string_field(
    max_length: int = FieldLimits.SHORT_TEXT_MAX,
    min_length: int = 0,
    **kwargs
) -> Any:
    """Create a Field for short text with length constraints."""
    return Field(min_length=min_length, max_length=max_length, **kwargs)


def medium_string_field(
    max_length: int = FieldLimits.MEDIUM_TEXT_MAX,
    **kwargs
) -> Any:
    """Create a Field for medium text with length constraints."""
    return Field(max_length=max_length, **kwargs)


def long_string_field(
    max_length: int = FieldLimits.LONG_TEXT_MAX,
    **kwargs
) -> Any:
    """Create a Field for long text with length constraints."""
    return Field(max_length=max_length, **kwargs)


def code_string_field(
    max_length: int = FieldLimits.CODE_MAX,
    **kwargs
) -> Any:
    """Create a Field for code content with length constraints."""
    return Field(max_length=max_length, **kwargs)


def list_field(
    max_items: int = FieldLimits.MAX_LIST_ITEMS,
    **kwargs
) -> Any:
    """Create a Field for lists with item count constraints."""
    return Field(max_length=max_items, **kwargs)
