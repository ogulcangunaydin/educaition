from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings

from app.services.password_service import (
    hash_password,
    verify_password,
    validate_password_strength,
    check_password_strength,
    PasswordValidationError,
    PasswordStrength
)


class SecurityConfig:
    SECRET_KEY: str = settings.SECRET_KEY
    ALGORITHM: str = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        SecurityConfig.SECRET_KEY, 
        algorithm=SecurityConfig.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str, validate: bool = True) -> str:
    return hash_password(password, validate=validate)


__all__ = [
    'create_access_token',
    'get_password_hash',
    'verify_password',
    'validate_password_strength',
    'check_password_strength',
    'PasswordValidationError',
    'PasswordStrength',
    'SecurityConfig'
]