"""
Program suggestion router - API endpoints for program suggestions.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core import settings
from app.dependencies.auth import AdminUser, get_current_active_user, get_db
from app.dependencies.participant import (
    CurrentProgramStudent,
    verify_participant_ownership,
)
from app.services.participant_token_service import (
    ParticipantType,
    create_participant_token,
    get_token_expiry_seconds,
)

from .schemas import (
    ProgramSuggestionStudent,
    ProgramSuggestionStudentCreate,
    ProgramSuggestionStudentDebug,
    ProgramSuggestionStudentResult,
    ProgramSuggestionStudentUpdateRiasec,
    ProgramSuggestionStudentUpdateStep1,
    ProgramSuggestionStudentUpdateStep2,
    ProgramSuggestionStudentUpdateStep3,
    ProgramSuggestionStudentUpdateStep4,
)
from .service import ProgramSuggestionService

# Public routes (no auth required, but some require participant token)
program_suggestion_public_router = APIRouter(
    prefix="/program-suggestion/students",
    tags=["program_suggestion"],
)

# Protected routes (require user auth)
program_suggestion_protected_router = APIRouter(
    prefix="/program-suggestion/students",
    tags=["program_suggestion"],
    dependencies=[Depends(get_current_active_user)],
)


@program_suggestion_public_router.post("/")
def create_student(
    student: ProgramSuggestionStudentCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new student for program suggestions (public).

    Returns student data with session token for subsequent requests.
    """
    created_student = ProgramSuggestionService.create_student(
        student.high_school_room_id, db
    )

    token = create_participant_token(
        participant_id=created_student.id,
        participant_type=ParticipantType.PROGRAM_SUGGESTION,
        room_id=student.high_school_room_id,
    )

    response = JSONResponse(
        content={
            "student": ProgramSuggestionStudent.model_validate(
                created_student
            ).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PROGRAM_SUGGESTION),
        }
    )

    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PROGRAM_SUGGESTION),
    )

    return response


@program_suggestion_public_router.get(
    "/{student_id}",
    response_model=ProgramSuggestionStudent,
)
def get_student(
    student_id: int,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Get student data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.get_student(student_id, db)


@program_suggestion_public_router.post(
    "/{student_id}/step1",
    response_model=ProgramSuggestionStudent,
)
def update_student_step1(
    student_id: int,
    data: ProgramSuggestionStudentUpdateStep1,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Update student with step 1 data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.update_step1(student_id, data, db)


@program_suggestion_public_router.post(
    "/{student_id}/step2",
    response_model=ProgramSuggestionStudent,
)
def update_student_step2(
    student_id: int,
    data: ProgramSuggestionStudentUpdateStep2,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Update student with step 2 data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.update_step2(student_id, data, db)


@program_suggestion_public_router.post(
    "/{student_id}/step3",
    response_model=ProgramSuggestionStudent,
)
def update_student_step3(
    student_id: int,
    data: ProgramSuggestionStudentUpdateStep3,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Update student with step 3 data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.update_step3(student_id, data, db)


@program_suggestion_public_router.post(
    "/{student_id}/step4",
    response_model=ProgramSuggestionStudent,
)
def update_student_step4(
    student_id: int,
    data: ProgramSuggestionStudentUpdateStep4,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Update student with step 4 data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.update_step4(student_id, data, db)


@program_suggestion_public_router.post(
    "/{student_id}/riasec",
    response_model=ProgramSuggestionStudent,
)
def update_student_riasec(
    student_id: int,
    data: ProgramSuggestionStudentUpdateRiasec,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Update student with RIASEC assessment (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.update_riasec(student_id, data, db)


@program_suggestion_public_router.get(
    "/{student_id}/result",
    response_model=ProgramSuggestionStudentResult,
)
def get_student_result(
    student_id: int,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Get student result data (requires participant token)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.get_student_result(student_id, db)


@program_suggestion_protected_router.get(
    "/{student_id}/debug",
    response_model=ProgramSuggestionStudentDebug,
)
def get_student_debug(
    student_id: int, current_user: AdminUser, db: Session = Depends(get_db)
):
    """Get student debug data (admin only)."""
    return ProgramSuggestionService.get_student_debug(student_id, db)


# Combined router for easy import
router = APIRouter()
router.include_router(program_suggestion_public_router)
router.include_router(program_suggestion_protected_router)
