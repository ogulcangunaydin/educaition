from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import models, schemas, security
from .database import SessionLocal
from starlette.requests import Request
from .utils import to_dict
import os
from .schemas import *

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    request.session["current_user"] = to_dict(user)
    return user

def create_initial_user():
    db = SessionLocal()
    user = db.query(models.User).filter_by(username="johndoe").first()
    if not user:
        hashed_password = security.get_password_hash("1234aA")
        user = models.User(username="johndoe", hashed_password=hashed_password)
        db.add(user)
        db.commit()

def authenticate_user(db: Session, login_request: LoginRequest):
    user = get_user(db, login_request.email)
    if not user:
        return False
    if not security.verify_password(login_request.password, user.hashed_password):
        return False
    return user

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()