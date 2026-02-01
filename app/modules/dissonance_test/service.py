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

    @staticmethod
    def create_participant(db: Session, participant: DissonanceTestParticipantCreate):
        db_participant = models.DissonanceTestParticipant(**participant.dict())
        db.add(db_participant)
        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def get_participant(db: Session, participant_id: int):
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
    def update_participant_personality_traits(db: Session, participant_id: int, answers: str):
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

        personality_scores = calculate_personality_traits(parsed_answers)

        job_recommendation = get_job_recommendation(
            personality_scores,
            db_participant.gender,
            db_participant.age,
            db_participant.education,
        )
        compatibility_analysis = get_compatibility_analysis(
            personality_scores, db_participant.star_sign, db_participant.rising_sign
        )

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
