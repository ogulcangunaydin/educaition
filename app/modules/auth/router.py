"""
Auth router - API endpoints for authentication.
"""

from fastapi import APIRouter, Body, Cookie, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import settings
from app.dependencies.auth import get_current_active_user, get_db
from app.services.token_service import TokenConfig

from .schemas import PasswordRequirements
from .service import AuthService

# Router for public auth endpoints (no auth required)
auth_public_router = APIRouter(tags=["auth"])

# Router for protected auth endpoints (auth required)
auth_protected_router = APIRouter(
    tags=["auth"],
    dependencies=[Depends(get_current_active_user)],
)


def _create_auth_response(token_data: dict) -> JSONResponse:
    """Create JSON response with refresh token cookie."""
    response = JSONResponse(
        content={
            "access_token": token_data["access_token"],
            "current_user_id": token_data["current_user_id"],
            "token_type": "bearer",
            "expires_in": token_data["expires_in"],
            "role": token_data.get("role"),
            "university": token_data.get("university"),
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=TokenConfig.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api",
    )

    return response


@auth_public_router.post("/authenticate")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return access token.

    - **username**: User's username
    - **password**: User's password

    Returns access token in body and refresh token as HttpOnly cookie.
    """
    token_data = AuthService.authenticate_user(form_data, db)
    return _create_auth_response(token_data)


@auth_public_router.post("/refresh")
def refresh_token(
    refresh_token: str | None = Cookie(None),
    body_refresh_token: dict | None = Body(None),
):
    """
    Refresh access token using refresh token.

    Refresh token can be provided via:
    - HttpOnly cookie (preferred)
    - Request body: {"refresh_token": "..."}
    """
    token = refresh_token
    if not token and body_refresh_token:
        token = body_refresh_token.get("refresh_token")

    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Refresh token required"},
        )

    new_tokens = AuthService.refresh_access_token(token)
    return _create_auth_response(new_tokens)


@auth_protected_router.post("/logout")
def logout(
    authorization: str = Header(..., description="Bearer token"),
    refresh_token: str | None = Cookie(None),
    body_refresh_token: str | None = Body(None, embed=True),
):
    """
    Logout user by revoking tokens.

    Revokes both access token and refresh token (if provided).
    """
    access_token = authorization.replace("Bearer ", "")
    token_to_revoke = refresh_token or body_refresh_token
    result = AuthService.logout_user(access_token, token_to_revoke)

    response = JSONResponse(content=result)
    response.delete_cookie(
        key="refresh_token",
        path="/api",
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
    )

    return response


@auth_public_router.get(
    "/password-requirements",
    response_model=PasswordRequirements,
)
def get_password_requirements():
    """Get password requirements for user registration/password change."""
    return PasswordRequirements()


# Combined router for easy import
router = APIRouter()
router.include_router(auth_public_router)
router.include_router(auth_protected_router)
