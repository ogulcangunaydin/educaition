import json
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app import models
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.compatibility_analysis_service import get_compatibility_analysis
from app.services.dissonance_analysis_service import get_dissonance_analysis
from app.services.job_recommendation_service import get_job_recommendation
from .schemas import (
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantUpdateFirst,
    DissonanceTestParticipantUpdateSecond,
)

class DissonanceTestService:
    @staticmethod
    def create_participant(db: Session, participant: DissonanceTestParticipantCreate):
        db_participant = models.DissonanceTestParticipant(**participant.model_dump())
        db.add(db_participant)
        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def update_participant_first_answers(
        db: Session,
        participant_id: int,
        participant_data: DissonanceTestParticipantUpdateFirst,
    ):
        """Update demographics + first-round taxi answers after registration."""
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.id == participant_id)
            .first()
        )

        if db_participant is None:
            raise HTTPException(status_code=404, detail="Participant not found")

        update_data = participant_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_participant, key, value)

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
    def get_participants_by_user(db: Session, user_id: int):
        return (
            db.query(models.DissonanceTestParticipant)
            .filter(models.DissonanceTestParticipant.user_id == user_id)
            .all()
        )

    @staticmethod
    def get_participants_by_room(
        db: Session,
        room_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list, int]:
        """Get all participants for a specific test room."""
        query = db.query(models.DissonanceTestParticipant).filter(
            models.DissonanceTestParticipant.test_room_id == room_id
        )
        total = query.count()
        participants = (
            query.order_by(models.DissonanceTestParticipant.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return participants, total

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

        update_data = participant_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_participant, key, value)

        # Generate GPT dissonance analysis & job recommendation
        try:
            participant_dict = {
                "education": db_participant.education,
                "gender": db_participant.gender,
                "star_sign": db_participant.star_sign,
                "rising_sign": db_participant.rising_sign,
                "workload": db_participant.workload,
                "career_start": db_participant.career_start,
                "flexibility": db_participant.flexibility,
                "comfort_question_first_answer": db_participant.comfort_question_first_answer,
                "comfort_question_displayed_average": db_participant.comfort_question_displayed_average,
                "comfort_question_second_answer": db_participant.comfort_question_second_answer,
                "fare_question_first_answer": db_participant.fare_question_first_answer,
                "fare_question_displayed_average": db_participant.fare_question_displayed_average,
                "fare_question_second_answer": db_participant.fare_question_second_answer,
            }
            analysis = get_dissonance_analysis(participant_dict)
            if analysis:
                db_participant.job_recommendation = analysis
        except Exception as e:
            logging.error(f"Failed to generate dissonance analysis: {e}")

        db_participant.has_completed = 1

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
    def delete_participant(db: Session, participant_id: int, user_id: int):
        db_participant = (
            db.query(models.DissonanceTestParticipant)
            .filter(
                models.DissonanceTestParticipant.id == participant_id,
                models.DissonanceTestParticipant.user_id == user_id,
            )
            .first()
        )
        if db_participant is None:
            raise HTTPException(status_code=404, detail="Participant not found")
        db_participant.soft_delete()
        db.commit()
        return db_participant
