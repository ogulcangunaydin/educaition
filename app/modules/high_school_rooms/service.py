import bleach
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models


class HighSchoolRoomService:

    @staticmethod
    def create_room(
        high_school_name: str,
        high_school_code: str | None,
        request: Request,
        db: Session,
    ):
        user_id = request.session["current_user"]["id"]
        clean_name = bleach.clean(high_school_name, strip=True)
        clean_code = (
            bleach.clean(high_school_code, strip=True) if high_school_code else None
        )

        room = models.HighSchoolRoom(
            user_id=user_id, high_school_name=clean_name, high_school_code=clean_code
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def get_rooms_by_user(request: Request, skip: int, limit: int, db: Session):
        user_id = request.session["current_user"]["id"]
        return (
            db.query(models.HighSchoolRoom)
            .filter(models.HighSchoolRoom.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_room(room_id: int, db: Session):
        room = (
            db.query(models.HighSchoolRoom)
            .filter(models.HighSchoolRoom.id == room_id)
            .first()
        )
        if room is None:
            raise HTTPException(status_code=404, detail="High school room not found")
        return room

    @staticmethod
    def delete_room(room_id: int, db: Session):
        room = (
            db.query(models.HighSchoolRoom)
            .filter(models.HighSchoolRoom.id == room_id)
            .first()
        )
        if room is None:
            raise HTTPException(status_code=404, detail="High school room not found")
        db.delete(room)
        db.commit()
        return room

    @staticmethod
    def get_room_students(room_id: int, db: Session):
        all_students = (
            db.query(models.ProgramSuggestionStudent)
            .filter(models.ProgramSuggestionStudent.high_school_room_id == room_id)
            .all()
        )

        completed_times = set()
        for student in all_students:
            if student.status != "started" and student.created_at:
                completed_times.add(student.created_at)

        filtered_students = []
        for student in all_students:
            if student.status != "started":
                filtered_students.append(student)
            else:
                is_orphan_duplicate = False
                if student.created_at:
                    for completed_time in completed_times:
                        time_diff = abs(
                            (student.created_at - completed_time).total_seconds()
                        )
                        if time_diff <= 5:
                            is_orphan_duplicate = True
                            break

                if not is_orphan_duplicate:
                    filtered_students.append(student)

        return filtered_students
