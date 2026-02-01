from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.dependencies.auth import TeacherOrAdmin, get_current_active_user, get_db
from app.modules.program_suggestion.schemas import ProgramSuggestionStudent

from .schemas import HighSchoolRoom
from .service import HighSchoolRoomService

router = APIRouter(
    prefix="/high-school-rooms",
    tags=["high_school_rooms"],
    dependencies=[Depends(get_current_active_user)],
)


@router.post("/", response_model=HighSchoolRoom)
def create_high_school_room(
    request: Request,
    current_user: TeacherOrAdmin,
    high_school_name: str = Form(...),
    high_school_code: str = Form(None),
    db: Session = Depends(get_db),
):
    return HighSchoolRoomService.create_room(
        high_school_name, high_school_code, request, db
    )


@router.get("/", response_model=list[HighSchoolRoom])
def get_high_school_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return HighSchoolRoomService.get_rooms_by_user(request, skip, limit, db)


@router.get("/{room_id}", response_model=HighSchoolRoom)
def get_high_school_room(room_id: int, db: Session = Depends(get_db)):
    return HighSchoolRoomService.get_room(room_id, db)


@router.delete("/{room_id}", response_model=HighSchoolRoom)
def delete_high_school_room(
    room_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)
):
    return HighSchoolRoomService.delete_room(room_id, db)


@router.get("/{room_id}/students", response_model=list[ProgramSuggestionStudent])
def get_high_school_room_students(room_id: int, db: Session = Depends(get_db)):
    return HighSchoolRoomService.get_room_students(room_id, db)
