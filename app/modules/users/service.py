import bleach
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app import models
from app.core.security import get_password_hash
from app.services.password_service import PasswordValidationError
from .schemas import UserCreate, UserUpdate

class UserService:
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        return db.query(models.User).offset(skip).limit(limit).all()

    @staticmethod
    def get_user(db: Session, user_id: int):
        db_user = db.query(models.User).get(user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(models.User).filter(models.User.username == username).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate):
        clean_name = bleach.clean(user.username, strip=True)
        clean_email = bleach.clean(user.email, strip=True) if user.email else None

        existing_user = (
            db.query(models.User)
            .filter(
                (models.User.username == clean_name)
                | (models.User.email == clean_email)
            )
            .first()
        )

        if existing_user:
            if existing_user.username == clean_name:
                raise HTTPException(status_code=400, detail="Username already exists")
            raise HTTPException(status_code=400, detail="Email already exists")

        try:
            hashed_password = get_password_hash(user.password)
        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password validation failed", "errors": e.errors},
            )

        db_user = models.User(
            username=clean_name,
            email=clean_email,
            hashed_password=hashed_password,
            role=user.role.value if hasattr(user, "role") and user.role else "student",
            university=user.university.value
            if hasattr(user, "university") and user.university
            else "halic",
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, user_id: int, user: UserUpdate):
        db_user = db.query(models.User).get(user_id)

        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.username:
            cleaned_username = bleach.clean(user.username, strip=True)
            existing_user = (
                db.query(models.User)
                .filter(
                    models.User.username == cleaned_username,
                    models.User.id != user_id,
                )
                .first()
            )

            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")

            db_user.username = cleaned_username

        if user.email is not None:
            db_user.email = user.email

        if user.password:
            try:
                hashed_password = get_password_hash(user.password)
                db_user.hashed_password = hashed_password
            except PasswordValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Password validation failed", "errors": e.errors},
                )

        if user.role:
            db_user.role = (
                user.role.value if hasattr(user.role, "value") else user.role
            )

        if user.university:
            db_user.university = (
                user.university.value
                if hasattr(user.university, "value")
                else user.university
            )

        db.commit()
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int):
        db_user = db.query(models.User).get(user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(db_user)
        db.commit()
        return db_user
