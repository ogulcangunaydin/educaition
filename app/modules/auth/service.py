from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models
from app.core.security import verify_password
from app.services.token_service import (
    TokenError,
    create_token_pair,
    refresh_tokens,
    revoke_token,
)

def _get_user_by_username_or_email(db: Session, identifier: str):
    return (
        db.query(models.User)
        .filter(
            (models.User.username == identifier) | (models.User.email == identifier)
        )
        .first()
    )

def _verify_user_credentials(db: Session, username: str, password: str):
    user = _get_user_by_username_or_email(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

class AuthService:
    @staticmethod
    def authenticate_user(form_data: OAuth2PasswordRequestForm, db: Session) -> dict:
        user = _verify_user_credentials(db, form_data.username, form_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_pair = create_token_pair(user.username, user.id)

        return {
            "access_token": token_pair.access_token,
            "refresh_token": token_pair.refresh_token,
            "current_user_id": user.id,
            "token_type": "bearer",
            "expires_in": token_pair.expires_in,
            "role": user.role,
            "university": user.university,
        }

    @staticmethod
    def refresh_access_token(refresh_token: str, db: Session) -> dict:
        try:
            token_pair = refresh_tokens(refresh_token)

            user = db.query(models.User).filter(models.User.id == token_pair.user_id).first()

            return {
                "access_token": token_pair.access_token,
                "refresh_token": token_pair.refresh_token,
                "current_user_id": token_pair.user_id,
                "token_type": "bearer",
                "expires_in": token_pair.expires_in,
                "role": user.role if user else None,
                "university": user.university if user else None,
            }
        except TokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def logout_user(access_token: str, refresh_token: str | None = None) -> dict:
        revoke_token(access_token)

        if refresh_token:
            revoke_token(refresh_token)

        return {"message": "Successfully logged out"}
