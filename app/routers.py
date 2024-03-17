# routers.py

from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing import List
from . import schemas, db_operations, controllers

router = APIRouter(
    dependencies=[Depends(db_operations.get_current_user)]
)

router_without_auth = APIRouter()

@router_without_auth.post("/authenticate", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_operations.get_db)):
    return controllers.login_for_access_token(form_data, db)

@router.get("/users/", response_model=List[schemas.User])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)):
    return controllers.read_users(skip, limit, db)

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.read_user(user_id, db)

@router.post("/users/", response_model=schemas.User)
def create_user(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(db_operations.get_db)):
    user = schemas.UserCreate(username=username, email=email, password=password)
    return controllers.create_user(user, db)

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(db_operations.get_db)):
    user = schemas.UserCreate(username=username, email=email, password=password)
    return controllers.update_user(user_id, user, db)

@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_user(user_id, db)

@router.post("/rooms/", response_model=schemas.Room)
def create_room(request: Request, db: Session = Depends(db_operations.get_db)):
    return controllers.create_room(request, db)

@router.get("/rooms/", response_model=List[schemas.Room])
def get_rooms(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)):
    return controllers.get_rooms(request, skip, limit, db)

@router.get("/rooms/{room_id}", response_model=schemas.Room)
def read_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.read_room(room_id, db)

@router.post("/players/", response_model=schemas.Player)
def create_player(player_name: str = Form(...), room_id: int = Form(...), db: Session = Depends(db_operations.get_db)):
    player = schemas.PlayerCreate(player_name=player_name, room_id=room_id)
    return controllers.create_player(player, db)

@router.get("/players/", response_model=List[schemas.Player])
def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)):
    return controllers.get_players(skip, limit, db)

@router.post("/players/{player_id}/tactic", response_model=schemas.Player)
def update_player_tactic(player_id: int, player_tactic: str = Form(...), db: Session = Depends(db_operations.get_db)):
    return controllers.update_player_tactic(player_id, player_tactic, db)

@router.post("/rooms/{room_id}/ready", response_model=schemas.Room)
def start_game(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.start_game(room_id, db)