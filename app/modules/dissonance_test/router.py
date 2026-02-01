"""
Dissonance test router - API endpoints for dissonance test.
"""

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

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

from .schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateSecond,
)
from .service import DissonanceTestService

# Public routes (no auth required, but some require participant token)
dissonance_test_public_router = APIRouter(
    prefix="/dissonance_test_participants",
    tags=["dissonance_test"],
)

# Protected routes (require user auth)
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
    """
    Create a new dissonance test participant (public).

    Returns participant data with session token for subsequent requests.
    """
    created_participant = DissonanceTestService.create_participant(db, participant)

    # Create participant token
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
    """Get participant results (requires participant token)."""
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
    """Update participant's second round answers (requires participant token)."""
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.update_participant_second_answers(
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
    """Update participant's personality traits (requires participant token)."""
    verify_participant_ownership(participant.participant_id, participant_id)
    return DissonanceTestService.update_participant_personality_traits(
        db, participant_id, answers
    )


@dissonance_test_protected_router.get(
    "/",
    response_model=list[DissonanceTestParticipant],
)
def get_participants(request: Request, db: Session = Depends(get_db)):
    """Get all participants for the current user (authenticated users only)."""
    return DissonanceTestService.get_participants_by_user(db, request)


@dissonance_test_protected_router.post(
    "/{participant_id}/delete",
    response_model=DissonanceTestParticipant,
)
def delete_participant(
    participant_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Delete a participant (teacher/admin only)."""
    return DissonanceTestService.delete_participant(db, participant_id)


# Combined router for easy import
router = APIRouter()
router.include_router(dissonance_test_public_router)
router.include_router(dissonance_test_protected_router)
