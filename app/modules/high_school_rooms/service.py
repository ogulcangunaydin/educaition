"""
High school room service - Business logic for high school room operations.
"""

import bleach
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models


class HighSchoolRoomService:
    """Service class for high school room operations."""

    @staticmethod
    def create_room(
        high_school_name: str,
        high_school_code: str | None,
        request: Request,
        db: Session,
    ):
        """
        Create a new high school room.

        Args:
            high_school_name: Name of the high school
            high_school_code: Optional school code
            request: Request object (contains user session)
            db: Database session

        Returns:
            Created room object
        """
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
    def get_rooms_by_user(
        request: Request, skip: int, limit: int, db: Session
    ):
        """
        Get all rooms for the current user.

        Args:
            request: Request object (contains user session)
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Database session

        Returns:
            List of room objects
        """
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
        """
        Get a room by ID.

        Args:
            room_id: Room ID
            db: Database session

        Returns:
            Room object

        Raises:
            HTTPException: If room not found
        """
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
        """
        Delete a room.

        Args:
            room_id: Room ID
            db: Database session

        Returns:
            Deleted room object

        Raises:
            HTTPException: If room not found
        """
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
        """
        Get all students in a room, filtering out duplicate orphan records.

        Args:
            room_id: Room ID
            db: Database session

        Returns:
            List of filtered student objects
        """
        # Get all students
        all_students = (
            db.query(models.ProgramSuggestionStudent)
            .filter(models.ProgramSuggestionStudent.high_school_room_id == room_id)
            .all()
        )

        # Filter out orphaned 'started' records that have a sibling with same created_at
        # This handles the duplicate issue caused by React StrictMode

        # Group by created_at timestamp (within 2 second window)
        completed_times = set()
        for student in all_students:
            if student.status != "started" and student.created_at:
                # Add a time window around completed records
                completed_times.add(student.created_at)

        filtered_students = []
        for student in all_students:
            # Keep all non-started records
            if student.status != "started":
                filtered_students.append(student)
            else:
                # For 'started' records, check if there's a completed sibling within 5 seconds
                is_orphan_duplicate = False
                if student.created_at:
                    for completed_time in completed_times:
                        time_diff = abs(
                            (student.created_at - completed_time).total_seconds()
                        )
                        if time_diff <= 5:  # Within 5 seconds
                            is_orphan_duplicate = True
                            break

                if not is_orphan_duplicate:
                    filtered_students.append(student)

        return filtered_students
