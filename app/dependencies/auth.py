from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.services.token_service import (
    TokenBlacklistedError,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    verify_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/authenticate")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/authenticate", auto_error=False
)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
        username = payload.sub
        user_id = payload.user_id

        if username is None:
            raise credentials_exception

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer", "X-Token-Expired": "true"},
        )
    except TokenBlacklistedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e.message}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user_id = user.id
    request.state.username = user.username

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_user_optional(
    request: Request,
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Optional authentication dependency.
    Returns the user if authenticated, None otherwise.
    Does not raise exceptions for missing/invalid tokens.
    Useful for endpoints that work differently for authenticated users.
    """
    if not token:
        return None

    try:
        payload = verify_access_token(token)
        user = db.query(User).filter(User.id == payload.user_id).first()

        if user:
            request.state.user_id = user.id
            request.state.username = user.username

        return user
    except TokenError:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


def require_user_ownership(resource_user_id: int, current_user: User) -> None:
    if resource_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )


__all__ = [
    "get_db",
    "DbSession",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
    "CurrentUser",
    "CurrentActiveUser",
    "OptionalUser",
    "require_user_ownership",
    "oauth2_scheme",
]
