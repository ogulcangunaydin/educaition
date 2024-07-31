# routers.py

from fastapi import APIRouter, Depends, Form, BackgroundTasks
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
def create_room(request: Request, name: str = Form(...), db: Session = Depends(db_operations.get_db)):
    return controllers.create_room(name, request, db)

@router.get("/rooms/", response_model=List[schemas.Room])
def get_rooms(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)):
    return controllers.get_rooms(request, skip, limit, db)

@router.get("/rooms/{room_id}", response_model=schemas.Room)
def read_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.read_room(room_id, db)

@router.post("/rooms/delete/{room_id}", response_model=schemas.Room)
def delete_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_room(room_id, db)

@router_without_auth.post("/players/", response_model=schemas.Player)
def create_player(player_name: str = Form(...), room_id: int = Form(...), db: Session = Depends(db_operations.get_db)):
    player = schemas.PlayerCreate(player_name=player_name, room_id=room_id)
    return controllers.create_player(player, db)

@router_without_auth.get("/players/room/{room_id}", response_model=List[schemas.Player])
def get_players_by_room(room_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)):
    return controllers.get_players_by_room(room_id, skip, limit, db)

@router_without_auth.post("/players/{player_id}/tactic", response_model=schemas.Player)
def update_player_tactic(player_id: int, player_tactic: str = Form(...), db: Session = Depends(db_operations.get_db)):
    return controllers.update_player_tactic(player_id, player_tactic, db)

@router_without_auth.post("/players/{player_id}/personality", response_model=schemas.Player)
def update_player_personality_traits(player_id: int, answers: str = Form(...), db: Session = Depends(db_operations.get_db)):
    return controllers.update_player_personality_traits(player_id, answers, db)

@router.get("/players/{player_ids}", response_model=List[schemas.Player])
def get_players_by_ids(player_ids: str, db: Session = Depends(db_operations.get_db)):
    return controllers.get_players_by_ids(player_ids, db)

@router.post("/rooms/{room_id}/ready", response_model=schemas.SessionCreate)
def start_game(room_id: int, background_tasks: BackgroundTasks,  db: Session = Depends(db_operations.get_db), name: str = Form(...)):
    return controllers.start_game(room_id, name, db, background_tasks)

@router.get("/rooms/{session_id}/results", response_model=schemas.Room)
def get_game_results(session_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_game_results(session_id, db)

@router.get("/rooms/{room_id}/sessions", response_model=List[schemas.SessionCreate])
def get_sessions_by_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_sessions_by_room(room_id, db)

@router.get("/sessions/{session_id}", response_model=schemas.SessionCreate)
def show_session(session_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_session(session_id, db)

@router.get("/auth/", response_model=schemas.User)
def authenticate_user(request: Request, db: Session = Depends(db_operations.get_db)):
    return controllers.authenticate(request, db)