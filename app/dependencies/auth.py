from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import UniversityKey, User, UserRole
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

def require_role(*allowed_roles: UserRole):
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role = UserRole(current_user.role)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker

async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

async def require_teacher_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    allowed = {UserRole.ADMIN.value, UserRole.TEACHER.value}
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required",
        )
    return current_user


def require_university(*allowed_universities: UniversityKey):
    async def university_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        user_university = UniversityKey(current_user.university)
        if user_university not in allowed_universities:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {[u.value for u in allowed_universities]}",
            )
        return current_user

    return university_checker


def require_same_university(resource_university: str) -> None:
    def checker(current_user: User) -> None:
        if current_user.role == UserRole.ADMIN.value:
            return

        if current_user.university != resource_university:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this university's data",
            )
    return checker


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN.value


def is_teacher_or_admin(user: User) -> bool:
    return user.role in {UserRole.ADMIN.value, UserRole.TEACHER.value}

AdminUser = Annotated[User, Depends(require_admin)]
TeacherOrAdmin = Annotated[User, Depends(require_teacher_or_admin)]

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
    # role based dependencies
    "require_role",
    "require_admin",
    "require_teacher_or_admin",
    "require_university",
    "require_same_university",
    "is_admin",
    "is_teacher_or_admin",
    "AdminUser",
    "TeacherOrAdmin",
    "UserRole",
    "UniversityKey",
]
