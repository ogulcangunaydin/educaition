from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models
from app.modules.test_rooms.models import TestRoom
from app.services.program_suggestion_service import get_suggested_programs
from app.services.riasec_service import calculate_riasec_scores
from .schemas import (
    ProgramSuggestionStudentUpdateRiasec,
    ProgramSuggestionStudentUpdateStep1,
    ProgramSuggestionStudentUpdateStep2,
    ProgramSuggestionStudentUpdateStep3,
    ProgramSuggestionStudentUpdateStep4,
)

class ProgramSuggestionService:
    @staticmethod
    def create_student(test_room_id: int, db: Session):
        """Create a new student for a test room."""
        room = (
            db.query(TestRoom)
            .filter(TestRoom.id == test_room_id, TestRoom.is_active == True)
            .first()
        )
        if room is None:
            raise HTTPException(status_code=404, detail="Test room not found or inactive")

        five_seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=5)

        # Check for recently created student to prevent duplicates
        recent_started = (
            db.query(models.ProgramSuggestionStudent)
            .filter(
                models.ProgramSuggestionStudent.test_room_id == test_room_id,
                models.ProgramSuggestionStudent.status == "started",
                models.ProgramSuggestionStudent.created_at >= five_seconds_ago,
            )
            .order_by(models.ProgramSuggestionStudent.created_at.desc())
            .all()
        )

        if recent_started:
            return recent_started[0]

        student = models.ProgramSuggestionStudent(
            test_room_id=test_room_id, status="started"
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def get_participants(test_room_id: int, db: Session):
        """Get all participants for a test room."""
        room = db.query(TestRoom).filter(TestRoom.id == test_room_id).first()
        if room is None:
            raise HTTPException(status_code=404, detail="Test room not found")

        students = (
            db.query(models.ProgramSuggestionStudent)
            .filter(
                models.ProgramSuggestionStudent.test_room_id == test_room_id,
            )
            .order_by(models.ProgramSuggestionStudent.created_at.desc())
            .all()
        )
        return students

    @staticmethod
    def delete_student(student_id: int, db: Session):
        """Soft delete a student."""
        student = ProgramSuggestionService.get_student(student_id, db)
        student.soft_delete()
        db.commit()
        return student

    @staticmethod
    def get_student(student_id: int, db: Session):
        student = (
            db.query(models.ProgramSuggestionStudent)
            .filter(models.ProgramSuggestionStudent.id == student_id)
            .first()
        )
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return student

    @staticmethod
    def update_step1(student_id: int, data: ProgramSuggestionStudentUpdateStep1, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        student.name = data.name
        student.birth_year = data.birth_year
        student.gender = data.gender
        student.status = "step1_completed"

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update_step2(student_id: int, data: ProgramSuggestionStudentUpdateStep2, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        student.class_year = data.class_year
        student.will_take_exam = data.will_take_exam
        student.average_grade = data.average_grade
        student.area = data.area
        student.wants_foreign_language = data.wants_foreign_language
        student.status = "step2_completed"

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update_step3(student_id: int, data: ProgramSuggestionStudentUpdateStep3, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        student.expected_score_min = data.expected_score_min
        student.expected_score_max = data.expected_score_max
        student.expected_score_distribution = data.expected_score_distribution
        student.alternative_area = data.alternative_area
        student.alternative_score_min = data.alternative_score_min
        student.alternative_score_max = data.alternative_score_max
        student.alternative_score_distribution = data.alternative_score_distribution
        student.status = "step3_completed"

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update_step4(student_id: int, data: ProgramSuggestionStudentUpdateStep4, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        student.preferred_language = data.preferred_language
        student.desired_universities = data.desired_universities
        student.desired_cities = data.desired_cities
        student.status = "step4_completed"

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def _calculate_expected_score(min_score: float, max_score: float, distribution: str) -> float:
        if not min_score or not max_score:
            return 0

        range_val = max_score - min_score

        if distribution == "low":
            return min_score + (range_val * 0.25)
        elif distribution == "high":
            return min_score + (range_val * 0.75)
        else:
            return min_score + (range_val * 0.5)

    @staticmethod
    def update_riasec(student_id: int, data: ProgramSuggestionStudentUpdateRiasec, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        riasec_scores = calculate_riasec_scores(data.riasec_answers)

        expected_score = ProgramSuggestionService._calculate_expected_score(
            student.expected_score_min,
            student.expected_score_max,
            student.expected_score_distribution,
        )

        alternative_score = None
        if student.alternative_area:
            alternative_score = ProgramSuggestionService._calculate_expected_score(
                student.alternative_score_min,
                student.alternative_score_max,
                student.alternative_score_distribution,
            )

        result = get_suggested_programs(
            riasec_scores=riasec_scores,
            expected_score=expected_score,
            area=student.area,
            alternative_score=alternative_score,
            alternative_area=student.alternative_area,
            preferred_language=student.preferred_language,
            desired_universities=student.desired_universities,
            desired_cities=student.desired_cities,
            db=db,
        )

        student.riasec_answers = data.riasec_answers
        student.riasec_scores = result["riasec_scores"]
        student.suggested_jobs = result["suggested_jobs"]
        student.suggested_programs = result["suggested_programs"]
        student.gpt_prompt = result.get("gpt_prompt")
        student.gpt_response = result.get("gpt_response")
        student.status = "completed"

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def get_student_result(student_id: int, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        return {
            "id": student.id,
            "name": student.name,
            "expected_score_min": student.expected_score_min,
            "expected_score_max": student.expected_score_max,
            "alternative_area": student.alternative_area,
            "alternative_score_min": student.alternative_score_min,
            "alternative_score_max": student.alternative_score_max,
            "riasec_scores": student.riasec_scores,
            "suggested_jobs": student.suggested_jobs,
            "suggested_programs": student.suggested_programs,
            "area": student.area,
        }

    @staticmethod
    def get_student_debug(student_id: int, db: Session):
        student = ProgramSuggestionService.get_student(student_id, db)

        return {
            "id": student.id,
            "name": student.name,
            "riasec_scores": student.riasec_scores,
            "suggested_jobs": student.suggested_jobs,
            "gpt_prompt": student.gpt_prompt,
            "gpt_response": student.gpt_response,
        }
