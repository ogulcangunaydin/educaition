from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
from app.core.database import SessionLocal
from app.models import TokenBlacklist


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenConfig:
    ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        settings.REFRESH_TOKEN_EXPIRE_DAYS
        if hasattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS")
        else 7
    )
    ALGORITHM: str = settings.ALGORITHM
    SECRET_KEY: str = settings.SECRET_KEY


class TokenPayload(BaseModel):
    sub: str  # Subject (username)
    user_id: int
    type: TokenType
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for blacklisting


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int


class TokenError(Exception):
    def __init__(self, message: str, error_code: str = "token_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TokenExpiredError(TokenError):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "token_expired")


class TokenInvalidError(TokenError):
    def __init__(self, message: str = "Token is invalid"):
        super().__init__(message, "token_invalid")


class TokenBlacklistedError(TokenError):
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message, "token_blacklisted")


def create_token(
    subject: str,
    user_id: int,
    token_type: TokenType,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    # Determine expiration based on token type
    if expires_delta:
        expire = now + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = now + timedelta(minutes=TokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # REFRESH
        expire = now + timedelta(days=TokenConfig.REFRESH_TOKEN_EXPIRE_DAYS)

    # Build the payload
    payload = {
        "sub": subject,
        "user_id": user_id,
        "type": token_type.value,
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),  # Unique token ID for blacklisting
    }

    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, TokenConfig.SECRET_KEY, algorithm=TokenConfig.ALGORITHM)


def create_access_token(
    subject: str,
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create an access token."""
    return create_token(subject, user_id, TokenType.ACCESS, expires_delta)


def create_refresh_token(
    subject: str,
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a refresh token."""
    return create_token(subject, user_id, TokenType.REFRESH, expires_delta)


def create_token_pair(subject: str, user_id: int) -> TokenPair:
    """
    Create both access and refresh tokens for a user.

    Args:
        subject: The subject (username) for the tokens
        user_id: The user's database ID

    Returns:
        TokenPair with access token, refresh token, and metadata
    """
    access_token = create_access_token(subject, user_id)
    refresh_token = create_refresh_token(subject, user_id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=TokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user_id,
    )


def decode_token(token: str, verify_exp: bool = True) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode
        verify_exp: Whether to verify expiration (default True)

    Returns:
        TokenPayload with decoded token data

    Raises:
        TokenExpiredError: If the token has expired
        TokenInvalidError: If the token is malformed or invalid
        TokenBlacklistedError: If the token has been revoked
    """
    try:
        payload = jwt.decode(
            token,
            TokenConfig.SECRET_KEY,
            algorithms=[TokenConfig.ALGORITHM],
            options={"verify_exp": verify_exp},
        )

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            raise TokenBlacklistedError()

        return TokenPayload(
            sub=payload["sub"],
            user_id=payload["user_id"],
            type=TokenType(payload["type"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload["jti"],
        )

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError as e:
        raise TokenInvalidError(f"Token validation failed: {e!s}")


def verify_access_token(token: str) -> TokenPayload:
    """
    Verify that a token is a valid access token.

    Args:
        token: The JWT token string

    Returns:
        TokenPayload if valid

    Raises:
        TokenInvalidError: If not an access token
    """
    payload = decode_token(token)
    if payload.type != TokenType.ACCESS:
        raise TokenInvalidError("Expected access token")
    return payload


def verify_refresh_token(token: str) -> TokenPayload:
    """
    Verify that a token is a valid refresh token.

    Args:
        token: The JWT token string

    Returns:
        TokenPayload if valid

    Raises:
        TokenInvalidError: If not a refresh token
    """
    payload = decode_token(token)
    if payload.type != TokenType.REFRESH:
        raise TokenInvalidError("Expected refresh token")
    return payload


def blacklist_token(
    jti: str,
    token_type: TokenType,
    user_id: int,
    expires_at: datetime,
) -> None:
    """
    Add a token to the blacklist in the database.

    Args:
        jti: The JWT ID to blacklist
        token_type: Type of token (access or refresh)
        user_id: The user's ID
        expires_at: When the token expires (for cleanup)
    """
    db = SessionLocal()
    try:
        blacklisted = TokenBlacklist(
            jti=jti,
            token_type=token_type.value,
            user_id=user_id,
            expires_at=expires_at,
        )
        db.add(blacklisted)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if a token is blacklisted in the database.

    Args:
        jti: The JWT ID to check

    Returns:
        True if blacklisted, False otherwise
    """
    db = SessionLocal()
    try:
        exists = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
        return exists is not None
    finally:
        db.close()


def revoke_token(token: str) -> bool:
    """
    Revoke a token by adding it to the blacklist.

    Args:
        token: The JWT token string to revoke

    Returns:
        True if successfully revoked, False if token was invalid
    """
    try:
        # Decode without verifying expiration (we want to blacklist even expired tokens)
        payload = decode_token(token, verify_exp=False)
        blacklist_token(
            jti=payload.jti,
            token_type=payload.type,
            user_id=payload.user_id,
            expires_at=payload.exp,
        )
        return True
    except TokenError:
        return False


def refresh_tokens(refresh_token: str) -> TokenPair:
    """
    Use a refresh token to get a new token pair.

    Args:
        refresh_token: The refresh token string

    Returns:
        New TokenPair with fresh access and refresh tokens

    Raises:
        TokenInvalidError: If refresh token is invalid
        TokenExpiredError: If refresh token has expired
        TokenBlacklistedError: If refresh token has been revoked
    """
    # Verify the refresh token
    payload = verify_refresh_token(refresh_token)

    # Blacklist the old refresh token (one-time use)
    blacklist_token(
        jti=payload.jti,
        token_type=payload.type,
        user_id=payload.user_id,
        expires_at=payload.exp,
    )

    # Create new token pair
    return create_token_pair(payload.sub, payload.user_id)


def get_token_expiry_seconds(token_type: TokenType) -> int:
    """Get the expiry time in seconds for a token type."""
    if token_type == TokenType.ACCESS:
        return TokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return TokenConfig.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


__all__ = [
    "TokenType",
    "TokenConfig",
    "TokenPayload",
    "TokenPair",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenBlacklistedError",
    "create_token",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "verify_access_token",
    "verify_refresh_token",
    "blacklist_token",
    "is_token_blacklisted",
    "revoke_token",
    "refresh_tokens",
    "get_token_expiry_seconds",
]
