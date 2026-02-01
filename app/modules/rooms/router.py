from fastapi import APIRouter, BackgroundTasks, Depends, Form
from sqlalchemy.orm import Session
from app.dependencies.auth import TeacherOrAdmin, get_current_active_user, get_db
from .schemas import Room, Session
from .service import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("/", response_model=Room, dependencies=[Depends(get_current_active_user)])
def create_room(
    current_user: TeacherOrAdmin,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    return RoomService.create_room(db, name, current_user.id)

@router.get("/", response_model=list[Room], dependencies=[Depends(get_current_active_user)])
def get_rooms(
    current_user: TeacherOrAdmin,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return RoomService.get_rooms(db, current_user.id, skip, limit)

@router.get("/{room_id}", response_model=Room, dependencies=[Depends(get_current_active_user)])
def get_room(room_id: int, db: Session = Depends(get_db)):
    return RoomService.get_room(db, room_id)

@router.post("/delete/{room_id}", response_model=Room)
def delete_room(room_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)):
    return RoomService.delete_room(db, room_id)

@router.post("/{room_id}/ready", response_model=Session)
def start_game(
    room_id: int,
    background_tasks: BackgroundTasks,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
    name: str = Form(...),
):
    return RoomService.start_game(db, room_id, name, background_tasks)

@router.get("/{session_id}/results", response_model=Room, dependencies=[Depends(get_current_active_user)])
def get_game_results(session_id: int, db: Session = Depends(get_db)):
    return RoomService.get_game_results(db, session_id)

@router.get("/{room_id}/sessions", response_model=list[Session], dependencies=[Depends(get_current_active_user)])
def get_sessions_by_room(room_id: int, db: Session = Depends(get_db)):
    return RoomService.get_sessions_by_room(db, room_id)
