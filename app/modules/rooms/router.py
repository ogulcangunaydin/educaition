"""
Room router - API endpoints for room management.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Form
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.dependencies.auth import TeacherOrAdmin, get_current_active_user, get_db

from .schemas import Room, SessionCreate
from .service import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=Room, dependencies=[Depends(get_current_active_user)])
def create_room(
    request: Request,
    current_user: TeacherOrAdmin,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Create a new room (teacher/admin only).

    - **name**: Room name
    """
    return RoomService.create_room(db, name, request)


@router.get("/", response_model=list[Room], dependencies=[Depends(get_current_active_user)])
def get_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all rooms for the current user.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    return RoomService.get_rooms(db, request, skip, limit)


@router.get("/{room_id}", response_model=Room, dependencies=[Depends(get_current_active_user)])
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room by ID."""
    return RoomService.get_room(db, room_id)


@router.post("/delete/{room_id}", response_model=Room)
def delete_room(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Delete a room (teacher/admin only)."""
    return RoomService.delete_room(db, room_id)


@router.post("/{room_id}/ready", response_model=SessionCreate)
def start_game(
    room_id: int,
    background_tasks: BackgroundTasks,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
    name: str = Form(...),
):
    """
    Start a game session for a room (teacher/admin only).

    - **name**: Session name
    """
    return RoomService.start_game(db, room_id, name, background_tasks)


@router.get("/{session_id}/results", response_model=Room, dependencies=[Depends(get_current_active_user)])
def get_game_results(session_id: int, db: Session = Depends(get_db)):
    """Get game results for a session."""
    return RoomService.get_game_results(db, session_id)


@router.get("/{room_id}/sessions", response_model=list[SessionCreate], dependencies=[Depends(get_current_active_user)])
def get_sessions_by_room(room_id: int, db: Session = Depends(get_db)):
    """Get all sessions for a room."""
    return RoomService.get_sessions_by_room(db, room_id)
