from fastapi import APIRouter, Body, Cookie, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import settings
from app.dependencies.auth import get_current_active_user, get_db
from app.modules.users.models import User
from app.modules.users.schemas import User as UserSchema
from app.services.token_service import TokenConfig
from .schemas import PasswordRequirements
from .service import AuthService

auth_public_router = APIRouter(tags=["auth"])
auth_protected_router = APIRouter(
    tags=["auth"],
    dependencies=[Depends(get_current_active_user)],
)

def _create_auth_response(token_data: dict) -> JSONResponse:
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
    token_data = AuthService.authenticate_user(form_data, db)
    return _create_auth_response(token_data)


@auth_public_router.post("/refresh")
def refresh_token(
    refresh_token: str | None = Cookie(None),
    body_refresh_token: dict | None = Body(None),
):
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
    authorization: str = Header(...),
    refresh_token: str | None = Cookie(None),
    body_refresh_token: str | None = Body(None, embed=True),
):
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

@auth_public_router.get("/password-requirements", response_model=PasswordRequirements)
def get_password_requirements():
    return PasswordRequirements()

@auth_protected_router.get("/auth/", response_model=UserSchema)
def get_current_authenticated_user(
    current_user: User = Depends(get_current_active_user),
):
    return current_user

router = APIRouter()
router.include_router(auth_public_router)
router.include_router(auth_protected_router)
