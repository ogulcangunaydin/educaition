from fastapi import APIRouter, Depends, HTTPException
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


def _resolve_high_school_room_id(
    student: ProgramSuggestionStudentCreate,
    db: Session,
) -> int:
    """
    Resolve a high_school_room_id from the request payload.

    If ``high_school_room_id`` is given directly, use it.
    Otherwise, look up the unified ``TestRoom`` by ``test_room_id`` and
    auto-create a legacy ``HighSchoolRoom`` when one doesn't exist yet
    (same pattern as Prisoner's Dilemma legacy room auto-creation).
    """
    from app.modules.high_school_rooms.models import HighSchoolRoom
    from app.modules.test_rooms.models import TestRoom

    if student.high_school_room_id is not None:
        return student.high_school_room_id

    # Resolve via TestRoom
    test_room = (
        db.query(TestRoom)
        .filter(TestRoom.id == student.test_room_id, TestRoom.is_active == True)
        .first()
    )
    if test_room is None:
        raise HTTPException(status_code=404, detail="Test room not found or inactive")

    # If legacy mapping already exists, use it
    if test_room.legacy_room_id is not None:
        return test_room.legacy_room_id

    # Auto-create a HighSchoolRoom from the TestRoom data
    legacy_room = HighSchoolRoom(
        user_id=test_room.created_by,
        high_school_name=test_room.name,
        high_school_code=test_room.get_setting("high_school_code"),
    )
    db.add(legacy_room)
    db.flush()

    # Store the mapping so future requests skip creation
    test_room.legacy_room_id = legacy_room.id
    test_room.legacy_table = "high_school_rooms"
    db.commit()
    db.refresh(legacy_room)

    return legacy_room.id


program_suggestion_public_router = APIRouter(
    prefix="/program-suggestion/students",
    tags=["program_suggestion"],
)
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
    high_school_room_id = _resolve_high_school_room_id(student, db)
    created_student = ProgramSuggestionService.create_student(
        high_school_room_id, db
    )
    token = create_participant_token(
        participant_id=created_student.id,
        participant_type=ParticipantType.PROGRAM_SUGGESTION,
        room_id=high_school_room_id,
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


@program_suggestion_protected_router.get(
    "/{student_id}/debug",
    response_model=ProgramSuggestionStudentDebug,
)
def get_student_debug(
    student_id: int, current_user: AdminUser, db: Session = Depends(get_db)
):
    return ProgramSuggestionService.get_student_debug(student_id, db)

router = APIRouter()
router.include_router(program_suggestion_public_router)
router.include_router(program_suggestion_protected_router)
