"""
User router - API endpoints for user management.
"""

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.dependencies.auth import AdminUser, get_db

from .schemas import User, UserCreate, UserUpdate
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[User])
def get_users(
    current_user: AdminUser,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all users (admin only).

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    return UserService.get_users(db, skip, limit)


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Get a specific user by ID (admin only)."""
    return UserService.get_user(db, user_id)


@router.post("/", response_model=User)
def create_user(
    current_user: AdminUser,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    university: str = Form("halic"),
    db: Session = Depends(get_db),
):
    """
    Create a new user (admin only).

    - **username**: Unique username
    - **email**: User email
    - **password**: User password (must meet security requirements)
    - **role**: User role (admin, teacher, student, viewer)
    - **university**: University key
    """
    user = UserCreate(
        username=username,
        email=email,
        password=password,
        role=role,
        university=university,
    )
    return UserService.create_user(db, user)


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    current_user: AdminUser,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    role: str = Form(None),
    university: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Update an existing user (admin only).

    - **user_id**: ID of user to update
    - **username**: New username
    - **email**: New email
    - **password**: New password (optional)
    - **role**: New role (optional)
    - **university**: New university (optional)
    """
    user = UserUpdate(
        username=username,
        email=email,
        password=password if password else None,
        role=role,
        university=university,
    )
    return UserService.update_user(db, user_id, user)


@router.delete("/{user_id}", response_model=User)
def delete_user(
    user_id: int,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Delete a user (admin only)."""
    return UserService.delete_user(db, user_id)
