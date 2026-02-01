from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from app.dependencies.auth import get_db, require_admin
from .schemas import User, UserCreate, UserUpdate
from .service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)

@router.get("/", response_model=list[User])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return UserService.get_users(db, skip, limit)

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return UserService.get_user(db, user_id)

@router.post("/", response_model=User)
def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    university: str = Form("halic"),
    db: Session = Depends(get_db),
):
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
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    role: str = Form(None),
    university: str = Form(None),
    db: Session = Depends(get_db),
):
    user = UserUpdate(
        username=username,
        email=email,
        password=password if password else None,
        role=role,
        university=university,
    )
    return UserService.update_user(db, user_id, user)

@router.delete("/{user_id}", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return UserService.delete_user(db, user_id)
