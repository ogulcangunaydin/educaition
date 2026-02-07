from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core import settings
from app.dependencies.auth import TeacherOrAdmin, get_current_active_user, get_db
from app.dependencies.participant import (
    CurrentTestParticipant,
    verify_participant_ownership,
)
from app.services.participant_token_service import (
    ParticipantType,
    create_participant_token,
    get_token_expiry_seconds,
)
from app.modules.test_rooms.service import TestRoomService
from app.modules.users.models import User
from app.core.enums import UserRole
from .schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantList,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateFirst,
    DissonanceTestParticipantUpdateSecond,
)
from .service import DissonanceTestService

dissonance_test_public_router = APIRouter(
    prefix="/dissonance_test_participants",
    tags=["dissonance_test"],
)
dissonance_test_protected_router = APIRouter(
    prefix="/dissonance_test_participants",
    tags=["dissonance_test"],
    dependencies=[Depends(get_current_active_user)],
)

@dissonance_test_public_router.post("/")
def create_participant(
    participant: DissonanceTestParticipantCreate,
    db: Session = Depends(get_db),
):
    # Determine if the student_user_id belongs to a privileged user (admin/teacher)
    # who is allowed to retake tests without device restrictions.
    is_privileged = False
    if participant.student_user_id:
        stu = db.query(User).filter(User.id == participant.student_user_id).first()
        if stu and stu.role in (UserRole.ADMIN.value, UserRole.TEACHER.value):
            is_privileged = True

    # Check if device has already completed the test (skip for admin/teacher)
    if participant.device_fingerprint and not is_privileged:
        has_completed = DissonanceTestService.check_device_completion(
            db,
            participant.test_room_id,
            participant.device_fingerprint,
        )
        if has_completed:
            return JSONResponse(
                status_code=409,
                content={"detail": "Device has already completed this test"},
            )

        # Check for an existing in-progress participant (e.g. page reload)
        existing = DissonanceTestService.find_in_progress_participant(
            db,
            participant.test_room_id,
            participant.device_fingerprint,
            participant.student_user_id,
        )
        if existing:
            token = create_participant_token(
                participant_id=existing.id,
                participant_type=ParticipantType.DISSONANCE_TEST,
                room_id=existing.user_id,
            )
            response = JSONResponse(
                status_code=200,
                content={
                    "participant": DissonanceTestParticipant.model_validate(
                        existing
                    ).model_dump(mode="json"),
                    "session_token": token,
                    "expires_in": get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
                    "resumed": True,
                },
            )
            response.set_cookie(
                key="participant_token",
                value=token,
                httponly=True,
                secure=not settings.is_development,
                samesite="strict",
                max_age=get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
            )
            return response

    created_participant = DissonanceTestService.create_participant(db, participant)
    token = create_participant_token(
        participant_id=created_participant.id,
        participant_type=ParticipantType.DISSONANCE_TEST,
        room_id=created_participant.user_id,
    )
    response = JSONResponse(
        content={
            "participant": DissonanceTestParticipant.model_validate(
                created_participant
            ).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
        }
    )
    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
    )

    return response

@dissonance_test_public_router.get(
    "/{participant_id}",
    response_model=DissonanceTestParticipantResult,
)
def get_participant(
    participant_id: int,
    participant: CurrentTestParticipant,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.get_participant(db, participant_id)

@dissonance_test_public_router.post(
    "/{participant_id}",
    response_model=DissonanceTestParticipant,
)
def update_participant_second_answers(
    participant_id: int,
    participant_data: DissonanceTestParticipantUpdateSecond,
    participant: CurrentTestParticipant,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.update_participant_second_answers(
        db, participant_id, participant_data
    )

@dissonance_test_public_router.post(
    "/{participant_id}/first-answers",
    response_model=DissonanceTestParticipant,
)
def update_participant_first_answers(
    participant_id: int,
    participant_data: DissonanceTestParticipantUpdateFirst,
    participant: CurrentTestParticipant,
    db: Session = Depends(get_db),
):
    """Update demographics + first-round taxi answers after registration."""
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.update_participant_first_answers(
        db, participant_id, participant_data
    )

@dissonance_test_public_router.post(
    "/{participant_id}/personality",
    response_model=DissonanceTestParticipant,
)
def update_participant_personality_traits(
    participant_id: int,
    participant: CurrentTestParticipant,
    answers: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.update_participant_personality_traits(
        db, participant_id, answers
    )

@dissonance_test_protected_router.get(
    "/",
    response_model=list[DissonanceTestParticipant],
)
def get_participants(current_user: TeacherOrAdmin, db: Session = Depends(get_db)):
    return DissonanceTestService.get_participants_by_user(db, current_user.id)


@dissonance_test_protected_router.get(
    "/rooms/{room_id}",
    response_model=DissonanceTestParticipantList,
)
def get_room_participants(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """Get all participants for a specific dissonance test room."""
    TestRoomService.verify_room_ownership(db, room_id, current_user.id)
    participants, total = DissonanceTestService.get_participants_by_room(
        db, room_id, skip, limit
    )
    return DissonanceTestParticipantList(
        items=[
            DissonanceTestParticipant.model_validate(p) for p in participants
        ],
        total=total,
    )


@dissonance_test_protected_router.delete(
    "/participants/{participant_id}",
    response_model=DissonanceTestParticipant,
)
def soft_delete_participant(
    participant_id: int,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """Delete a dissonance test participant (soft delete)."""
    return DissonanceTestService.delete_participant(db, participant_id, current_user.id)


@dissonance_test_protected_router.post(
    "/{participant_id}/delete",
    response_model=DissonanceTestParticipant,
)
def delete_participant(
    participant_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Legacy delete endpoint (POST). Use DELETE /participants/{id} instead."""
    return DissonanceTestService.delete_participant(db, participant_id, current_user.id)

router = APIRouter()
router.include_router(dissonance_test_public_router)
router.include_router(dissonance_test_protected_router)
