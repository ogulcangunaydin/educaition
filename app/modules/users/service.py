"""
User service - Business logic for user management.
"""

import bleach
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.core.security import get_password_hash
from app.services.password_service import PasswordValidationError

from .schemas import UserCreate, UserUpdate


class UserService:
    """Service class for user operations."""

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        """
        Get all users with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User objects
        """
        return db.query(models.User).offset(skip).limit(limit).all()

    @staticmethod
    def get_user(db: Session, user_id: int):
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object

        Raises:
            HTTPException: If user not found
        """
        db_user = db.query(models.User).get(user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        """
        Get a user by username.

        Args:
            db: Database session
            username: Username to search for

        Returns:
            User object or None
        """
        return db.query(models.User).filter(models.User.username == username).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate):
        """
        Create a new user.

        Args:
            db: Database session
            user: User creation data

        Returns:
            Created User object

        Raises:
            HTTPException: If username or email already exists
        """
        clean_name = bleach.clean(user.username, strip=True)
        clean_email = bleach.clean(user.email, strip=True) if user.email else None

        # Check for existing user
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

        # Hash password
        try:
            hashed_password = get_password_hash(user.password)
        except PasswordValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password validation failed", "errors": e.errors},
            )

        # Create user
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
        """
        Update an existing user.

        Args:
            db: Database session
            user_id: User ID to update
            user: User update data

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found or username taken
        """
        db_user = db.query(models.User).get(user_id)

        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Check for username conflict
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

        # Update email
        if user.email is not None:
            db_user.email = user.email

        # Update password if provided
        if user.password:
            try:
                hashed_password = get_password_hash(user.password)
                db_user.hashed_password = hashed_password
            except PasswordValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Password validation failed", "errors": e.errors},
                )

        # Update role
        if user.role:
            db_user.role = (
                user.role.value if hasattr(user.role, "value") else user.role
            )

        # Update university
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
        """
        Delete a user.

        Args:
            db: Database session
            user_id: User ID to delete

        Returns:
            Deleted User object

        Raises:
            HTTPException: If user not found
        """
        db_user = db.query(models.User).get(user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(db_user)
        db.commit()
        return db_user
