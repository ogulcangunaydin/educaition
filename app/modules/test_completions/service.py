"""
Test Completions Service

Checks participant tables to determine if a user has completed a given test type.
"""

from sqlalchemy.orm import Session

from app.modules.dissonance_test.models import DissonanceTestParticipant
from app.modules.personality_test.models import PersonalityTestParticipant


class TestCompletionService:
    """Service for checking user test completions across all test types."""

    @staticmethod
    def check_completion(
        db: Session,
        user_id: int,
        test_type: str,
        room_id: int | None = None,
    ) -> dict:
        """
        Check if a user has completed a specific test type.

        Args:
            db: Database session
            user_id: Authenticated user's ID
            test_type: One of the TestType enum values
            room_id: Optional room filter

        Returns:
            Dict with has_completed, participant_id (if completed)
        """
        if test_type == "personality_test":
            return TestCompletionService._check_personality_test(db, user_id, room_id)
        elif test_type == "dissonance_test":
            return TestCompletionService._check_dissonance_test(db, user_id, room_id)
        else:
            # For test types we haven't integrated yet (prisoners_dilemma,
            # program_suggestion) — allow by default
            return {"has_completed": False}

    @staticmethod
    def _check_personality_test(
        db: Session, user_id: int, room_id: int | None
    ) -> dict:
        query = db.query(PersonalityTestParticipant).filter(
            PersonalityTestParticipant.student_user_id == user_id,
            PersonalityTestParticipant.extroversion.isnot(None),  # completed
        )
        if room_id is not None:
            query = query.filter(
                PersonalityTestParticipant.test_room_id == room_id
            )

        participant = query.order_by(
            PersonalityTestParticipant.created_at.desc()
        ).first()

        if participant:
            return {
                "has_completed": True,
                "participant_id": participant.id,
            }
        return {"has_completed": False}

    @staticmethod
    def _check_dissonance_test(
        db: Session, user_id: int, room_id: int | None
    ) -> dict:
        query = db.query(DissonanceTestParticipant).filter(
            DissonanceTestParticipant.student_user_id == user_id,
            DissonanceTestParticipant.comfort_question_second_answer.isnot(
                None
            ),  # completed both rounds
        )
        if room_id is not None:
            query = query.filter(
                DissonanceTestParticipant.user_id == user_id
            )

        participant = query.order_by(
            DissonanceTestParticipant.created_at.desc()
        ).first()

        if participant:
            return {
                "has_completed": True,
                "participant_id": participant.id,
            }
        return {"has_completed": False}
