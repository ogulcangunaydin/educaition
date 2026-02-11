from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core import settings
from app.dependencies.auth import AdminUser, TeacherOrAdmin, get_current_active_user, get_db
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
    ProgramInteractionLogCreate,
    ProgramInteractionLogResponse,
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


# =============================================================================
# PUBLIC ROUTER (No authentication - for students taking the test)
# =============================================================================

program_suggestion_public_router = APIRouter(
    prefix="/program-suggestion/students",
    tags=["program_suggestion"],
)


@program_suggestion_public_router.post("/")
def create_student(
    student: ProgramSuggestionStudentCreate,
    db: Session = Depends(get_db),
):
    """Create a new student for a program suggestion test."""
    created_student = ProgramSuggestionService.create_student(
        student.test_room_id, db
    )
    token = create_participant_token(
        participant_id=created_student.id,
        participant_type=ParticipantType.PROGRAM_SUGGESTION,
        room_id=student.test_room_id,
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


@program_suggestion_public_router.get("/riasec-averages")
def get_riasec_averages(db: Session = Depends(get_db)):
    """
    Get platform-wide average RIASEC scores.
    
    Returns average scores based on all completed tests on the platform,
    along with the sample size used to calculate these averages.
    """
    return ProgramSuggestionService.get_riasec_averages(db)


@program_suggestion_public_router.get(
    "/{student_id}",
    response_model=ProgramSuggestionStudent,
)
def get_student(
    student_id: int,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
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
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.get_student_result(student_id, db)


@program_suggestion_public_router.post(
    "/{student_id}/log-interaction",
    response_model=ProgramInteractionLogResponse,
)
def log_interaction(
    student_id: int,
    data: ProgramInteractionLogCreate,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    """Log a student's interaction with a suggested program (google search, add to basket)."""
    verify_participant_ownership(participant.participant_id, student_id)
    return ProgramSuggestionService.log_interaction(student_id, data, db)


# =============================================================================
# PROTECTED ROUTER (Authentication required - for teachers/admins)
# =============================================================================

program_suggestion_protected_router = APIRouter(
    prefix="/program-suggestion",
    tags=["program_suggestion"],
    dependencies=[Depends(get_current_active_user)],
)


@program_suggestion_protected_router.get(
    "/students/{student_id}/debug",
    response_model=ProgramSuggestionStudentDebug,
)
def get_student_debug(
    student_id: int, current_user: AdminUser, db: Session = Depends(get_db)
):
    return ProgramSuggestionService.get_student_debug(student_id, db)


@program_suggestion_protected_router.get(
    "/rooms/{room_id}/participants",
    response_model=list[ProgramSuggestionStudent],
)
def get_room_participants(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Get all participants for a program suggestion room."""
    return ProgramSuggestionService.get_participants(room_id, db)


@program_suggestion_protected_router.get(
    "/students/{student_id}/admin-result",
    response_model=ProgramSuggestionStudentResult,
)
def get_student_result_admin(
    student_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Get student result (teacher/admin access)."""
    return ProgramSuggestionService.get_student_result(student_id, db)


@program_suggestion_protected_router.delete(
    "/students/{student_id}",
)
def delete_student(
    student_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Soft delete a program suggestion student."""
    return ProgramSuggestionService.delete_student(student_id, db)


@program_suggestion_protected_router.get(
    "/students/{student_id}/interactions",
    response_model=list[ProgramInteractionLogResponse],
)
def get_student_interactions(
    student_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Get all interaction logs for a specific student."""
    return ProgramSuggestionService.get_student_interactions(student_id, db)


@program_suggestion_protected_router.get(
    "/rooms/{room_id}/interactions",
    response_model=list[ProgramInteractionLogResponse],
)
def get_room_interactions(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Get all interaction logs for all students in a room."""
    return ProgramSuggestionService.get_room_interactions(room_id, db)


router = APIRouter()
router.include_router(program_suggestion_public_router)
router.include_router(program_suggestion_protected_router)
