"""
PersonalityTest Service Layer

This module handles business logic for personality test operations.
"""

import json
from typing import Any

import bleach
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import TestType
from app.modules.test_rooms.models import TestRoom
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.compatibility_analysis_service import get_compatibility_analysis
from app.services.job_recommendation_service import get_job_recommendation

from .models import PersonalityTestParticipant
from .schemas import (
    PersonalityTestParticipantCreate,
    PersonalityTestSubmit,
)


class PersonalityTestService:
    """Service class for personality test operations."""

    @staticmethod
    def create_participant(
        db: Session,
        participant_data: PersonalityTestParticipantCreate,
    ) -> PersonalityTestParticipant:
        """
        Create a new personality test participant.
        
        Args:
            db: Database session
            participant_data: Participant creation data
            
        Returns:
            Created PersonalityTestParticipant
            
        Raises:
            HTTPException: If room not found or not a personality test room
        """
        # Verify the room exists and is a personality test room
        room = db.query(TestRoom).filter(
            TestRoom.id == participant_data.test_room_id,
            TestRoom.is_active == True,
        ).first()
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test room not found or inactive",
            )
        
        if room.test_type != TestType.PERSONALITY_TEST.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room is not a personality test room",
            )
        
        # Create participant with room owner as user_id
        participant = PersonalityTestParticipant(
            test_room_id=participant_data.test_room_id,
            user_id=room.created_by,
            student_user_id=participant_data.student_user_id,
            full_name=bleach.clean(participant_data.full_name, strip=True) if participant_data.full_name else None,
            student_number=bleach.clean(participant_data.student_number, strip=True) if participant_data.student_number else None,
            email=participant_data.email,
            age=participant_data.age,
            gender=bleach.clean(participant_data.gender, strip=True) if participant_data.gender else None,
            education=bleach.clean(participant_data.education, strip=True) if participant_data.education else None,
            income=participant_data.income,
            star_sign=bleach.clean(participant_data.star_sign, strip=True) if participant_data.star_sign else None,
            rising_sign=bleach.clean(participant_data.rising_sign, strip=True) if participant_data.rising_sign else None,
            workload=participant_data.workload,
            career_start=participant_data.career_start,
            flexibility=participant_data.flexibility,
            device_fingerprint=participant_data.device_fingerprint,
            device_info=participant_data.device_info,
        )
        
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        return participant

    @staticmethod
    def get_participant(db: Session, participant_id: int) -> PersonalityTestParticipant:
        """
        Get a participant by ID.
        
        Args:
            db: Database session
            participant_id: Participant ID
            
        Returns:
            PersonalityTestParticipant instance
            
        Raises:
            HTTPException: If participant not found
        """
        participant = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.id == participant_id
        ).first()
        
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )
        
        return participant

    @staticmethod
    def get_participants_by_room(
        db: Session,
        room_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PersonalityTestParticipant], int]:
        """
        Get all participants for a room.
        
        Args:
            db: Database session
            room_id: Room ID
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (participants list, total count)
        """
        query = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.test_room_id == room_id
        )
        
        total = query.count()
        participants = query.order_by(
            PersonalityTestParticipant.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return participants, total

    @staticmethod
    def get_participants_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PersonalityTestParticipant], int]:
        """
        Get all participants created by a user (across all their rooms).
        
        Args:
            db: Database session
            user_id: User ID (teacher/admin)
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (participants list, total count)
        """
        query = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.user_id == user_id
        )
        
        total = query.count()
        participants = query.order_by(
            PersonalityTestParticipant.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return participants, total

    @staticmethod
    def submit_test_answers(
        db: Session,
        participant_id: int,
        test_data: PersonalityTestSubmit,
    ) -> PersonalityTestParticipant:
        """
        Submit personality test answers and calculate results.
        
        Args:
            db: Database session
            participant_id: Participant ID
            test_data: Test submission data with answers
            
        Returns:
            Updated PersonalityTestParticipant with calculated traits
            
        Raises:
            HTTPException: If participant not found
        """
        participant = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.id == participant_id
        ).first()
        
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )
        
        # Store raw answers
        answers_dict = {
            f"q{i + 1}": answer for i, answer in enumerate(test_data.answers)
        }
        participant.personality_test_answers = answers_dict
        
        # Calculate personality traits
        personality_scores = calculate_personality_traits(test_data.answers)
        
        participant.extroversion = personality_scores["extroversion"]
        participant.agreeableness = personality_scores["agreeableness"]
        participant.conscientiousness = personality_scores["conscientiousness"]
        participant.negative_emotionality = personality_scores["negative_emotionality"]
        participant.open_mindedness = personality_scores["open_mindedness"]
        
        # Generate job recommendation
        participant.job_recommendation = get_job_recommendation(
            personality_scores,
            participant.gender,
            participant.age,
            participant.education,
        )
        
        # Generate compatibility analysis if astrological info is provided
        if participant.star_sign or participant.rising_sign:
            participant.compatibility_analysis = get_compatibility_analysis(
                personality_scores,
                participant.star_sign,
                participant.rising_sign,
            )
        
        db.commit()
        db.refresh(participant)
        
        return participant

    @staticmethod
    def delete_participant(
        db: Session,
        participant_id: int,
        user_id: int,
    ) -> PersonalityTestParticipant:
        """
        Soft delete a participant.
        
        Args:
            db: Database session
            participant_id: Participant ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Deleted participant
            
        Raises:
            HTTPException: If participant not found or not owned by user
        """
        participant = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.id == participant_id,
            PersonalityTestParticipant.user_id == user_id,
        ).first()
        
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )
        
        participant.soft_delete()
        db.commit()
        
        return participant

    @staticmethod
    def check_device_completion(
        db: Session,
        room_id: int,
        device_fingerprint: str,
    ) -> bool:
        """
        Check if a device has already completed the test for a room.
        
        Args:
            db: Database session
            room_id: Test room ID
            device_fingerprint: Device fingerprint
            
        Returns:
            True if device has completed the test
        """
        if not device_fingerprint:
            return False
        
        existing = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.test_room_id == room_id,
            PersonalityTestParticipant.device_fingerprint == device_fingerprint,
            PersonalityTestParticipant.extroversion.isnot(None),  # Test completed
        ).first()
        
        return existing is not None

    @staticmethod
    def find_in_progress_participant(
        db: Session,
        room_id: int,
        device_fingerprint: str,
        student_user_id: int | None = None,
    ) -> PersonalityTestParticipant | None:
        """
        Find an existing in-progress (not yet completed) participant
        for the given device/student and room.
        """
        if not device_fingerprint and not student_user_id:
            return None

        query = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.test_room_id == room_id,
            PersonalityTestParticipant.extroversion.is_(None),  # Not completed
        )

        # Prefer student_user_id match if available
        if student_user_id:
            query = query.filter(
                PersonalityTestParticipant.student_user_id == student_user_id
            )
        elif device_fingerprint:
            query = query.filter(
                PersonalityTestParticipant.device_fingerprint == device_fingerprint
            )

        return query.order_by(
            PersonalityTestParticipant.created_at.desc()
        ).first()

    @staticmethod
    def get_room_statistics(db: Session, room_id: int) -> dict[str, Any]:
        """
        Get statistics for a room.
        
        Args:
            db: Database session
            room_id: Room ID
            
        Returns:
            Dictionary with room statistics
        """
        from sqlalchemy import func
        
        query = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.test_room_id == room_id
        )
        
        total = query.count()
        completed = query.filter(
            PersonalityTestParticipant.extroversion.isnot(None)
        ).count()
        
        # Calculate average traits for completed participants
        avg_traits = db.query(
            func.avg(PersonalityTestParticipant.extroversion),
            func.avg(PersonalityTestParticipant.agreeableness),
            func.avg(PersonalityTestParticipant.conscientiousness),
            func.avg(PersonalityTestParticipant.negative_emotionality),
            func.avg(PersonalityTestParticipant.open_mindedness),
        ).filter(
            PersonalityTestParticipant.test_room_id == room_id,
            PersonalityTestParticipant.extroversion.isnot(None),
        ).first()
        
        return {
            "total_participants": total,
            "completed_count": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "average_traits": {
                "extroversion": avg_traits[0],
                "agreeableness": avg_traits[1],
                "conscientiousness": avg_traits[2],
                "negative_emotionality": avg_traits[3],
                "open_mindedness": avg_traits[4],
            } if avg_traits[0] else None,
        }
