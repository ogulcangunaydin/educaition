"""
Dissonance test service - Business logic for dissonance test operations.
"""

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.compatibility_analysis_service import get_compatibility_analysis
from app.services.job_recommendation_service import get_job_recommendation

from .schemas import DissonanceTestParticipantCreate, DissonanceTestParticipantUpdateSecond


class DissonanceTestService:
    """Service class for dissonance test operations."""

    @staticmethod
    def create_participant(
        db: Session, participant: DissonanceTestParticipantCreate
    ):
        """
        Create a new dissonance test participant.

        Args:
            db: Database session
            participant: Participant creation data

        Returns:
            Created participant object
        """
        db_participant = models.DissonanceTestParticipant(**participant.dict())
        db.add(db_participant)
        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def get_participant(db: Session, participant_id: int):
        """
        Get a participant by ID.

        Args:
            db: Database session
            participant_id: Participant ID

        Returns:
            Participant object

        Raises:
            HTTPException: If participant not found
        """
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.id == participant_id)
            .first()
        )
        if db_participant is None:
            raise HTTPException(status_code=404, detail="Participant not found")
        return db_participant

    @staticmethod
    def get_participants_by_user(db: Session, request: Request):
        """
        Get all participants for the current user.

        Args:
            db: Database session
            request: Request object (contains user session)

        Returns:
            List of participant objects
        """
        user_id = request.session["current_user"]["id"]
        return (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.user_id == user_id)
            .all()
        )

    @staticmethod
    def update_participant_second_answers(
        db: Session,
        participant_id: int,
        participant_data: DissonanceTestParticipantUpdateSecond,
    ):
        """
        Update participant's second round answers.

        Args:
            db: Database session
            participant_id: Participant ID
            participant_data: Second round answer data

        Returns:
            Updated participant object

        Raises:
            HTTPException: If participant not found
        """
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.id == participant_id)
            .first()
        )
        if db_participant is None:
            raise HTTPException(status_code=404, detail="Participant not found")

        update_data = participant_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_participant, key, value)

        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def update_participant_personality_traits(
        db: Session, participant_id: int, answers: str
    ):
        """
        Update participant's personality traits based on test answers.

        Args:
            db: Database session
            participant_id: Participant ID
            answers: JSON string of personality test answers

        Returns:
            Updated participant object

        Raises:
            HTTPException: If participant not found
        """
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.id == participant_id)
            .first()
        )

        if db_participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )

        parsed_answers = json.loads(answers)
        answers_dict = {
            f"q{i + 1}": int(answer) for i, answer in enumerate(parsed_answers)
        }

        # Calculate personality scores
        personality_scores = calculate_personality_traits(parsed_answers)

        # Get recommendations
        job_recommendation = get_job_recommendation(
            personality_scores,
            db_participant.gender,
            db_participant.age,
            db_participant.education,
        )
        compatibility_analysis = get_compatibility_analysis(
            personality_scores, db_participant.star_sign, db_participant.rising_sign
        )

        # Update participant
        db_participant.extroversion = personality_scores["extroversion"]
        db_participant.agreeableness = personality_scores["agreeableness"]
        db_participant.conscientiousness = personality_scores["conscientiousness"]
        db_participant.negative_emotionality = personality_scores["negative_emotionality"]
        db_participant.open_mindedness = personality_scores["open_mindedness"]
        db_participant.job_recommendation = job_recommendation
        db_participant.compatibility_analysis = compatibility_analysis
        db_participant.personality_test_answers = answers_dict

        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def delete_participant(db: Session, participant_id: int):
        """
        Delete a participant.

        Args:
            db: Database session
            participant_id: Participant ID

        Returns:
            Deleted participant object

        Raises:
            HTTPException: If participant not found
        """
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.id == participant_id)
            .first()
        )
        if db_participant is None:
            raise HTTPException(status_code=404, detail="Participant not found")
        db.delete(db_participant)
        db.commit()
        return db_participant
