"""
PersonalityTest API Router

This module defines the API endpoints for the personality test.
"""

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core import settings
from app.dependencies.auth import TeacherOrAdmin, get_db
from app.dependencies.participant import (
    CurrentPersonalityTestParticipant,
    verify_participant_ownership,
)
from app.modules.users.models import User
from app.core.enums import UserRole
from app.modules.test_rooms.service import TestRoomService
from app.services.participant_token_service import (
    ParticipantType,
    create_participant_token,
    get_token_expiry_seconds,
)

from .schemas import (
    PersonalityTestParticipantCreate,
    PersonalityTestParticipantList,
    PersonalityTestParticipantPublic,
    PersonalityTestParticipantResponse,
    PersonalityTestResult,
    PersonalityTestSubmit,
    PersonalityTraits,
)
from .service import PersonalityTestService


# =============================================================================
# Public Router - Anonymous access for participants
# =============================================================================

personality_test_public_router = APIRouter(
    prefix="/personality-test",
    tags=["personality-test"],
)


@personality_test_public_router.post(
    "/participants",
    response_model=None,
    status_code=201,
)
def create_participant(
    participant_data: PersonalityTestParticipantCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new personality test participant.
    
    This endpoint is called when a participant starts the test via QR code.
    Returns a session token for subsequent requests.
    """
    # Determine if the student_user_id belongs to a privileged user (admin/teacher)
    # who is allowed to retake tests without device restrictions.
    is_privileged = False
    if participant_data.student_user_id:
        stu = db.query(User).filter(User.id == participant_data.student_user_id).first()
        if stu and stu.role in (UserRole.ADMIN.value, UserRole.TEACHER.value):
            is_privileged = True

    # Check if device has already completed the test (skip for admin/teacher)
    if participant_data.device_fingerprint and not is_privileged:
        has_completed = PersonalityTestService.check_device_completion(
            db,
            participant_data.test_room_id,
            participant_data.device_fingerprint,
        )
        if has_completed:
            return JSONResponse(
                status_code=409,
                content={"detail": "Device has already completed this test"},
            )

        # Check for an existing in-progress participant (e.g. page reload)
        existing = PersonalityTestService.find_in_progress_participant(
            db,
            participant_data.test_room_id,
            participant_data.device_fingerprint,
            participant_data.student_user_id,
        )
        if existing:
            # Return the existing participant instead of creating a duplicate
            token = create_participant_token(
                participant_id=existing.id,
                participant_type=ParticipantType.PERSONALITY_TEST,
                room_id=existing.test_room_id,
            )

            response = JSONResponse(
                status_code=200,
                content={
                    "participant": PersonalityTestParticipantResponse.model_validate(
                        existing
                    ).model_dump(mode="json"),
                    "session_token": token,
                    "expires_in": get_token_expiry_seconds(ParticipantType.PERSONALITY_TEST),
                    "resumed": True,
                },
            )

            response.set_cookie(
                key="participant_token",
                value=token,
                httponly=True,
                secure=not settings.is_development,
                samesite="strict",
                max_age=get_token_expiry_seconds(ParticipantType.PERSONALITY_TEST),
            )

            return response

    participant = PersonalityTestService.create_participant(db, participant_data)
    
    # Create session token
    token = create_participant_token(
        participant_id=participant.id,
        participant_type=ParticipantType.PERSONALITY_TEST,
        room_id=participant.test_room_id,
    )
    
    response = JSONResponse(
        content={
            "participant": PersonalityTestParticipantResponse.model_validate(
                participant
            ).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PERSONALITY_TEST),
        }
    )
    
    # Set session cookie
    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PERSONALITY_TEST),
    )
    
    return response


@personality_test_public_router.post(
    "/participants/{participant_id}/submit",
    response_model=PersonalityTestResult,
)
def submit_test_answers(
    participant_id: int,
    test_data: PersonalityTestSubmit,
    participant: CurrentPersonalityTestParticipant,
    db: Session = Depends(get_db),
):
    """
    Submit personality test answers and get results.
    
    This endpoint calculates personality traits based on the 60-question
    Big Five personality test and generates recommendations.
    """
    verify_participant_ownership(participant.participant_id, participant_id)
    
    updated_participant = PersonalityTestService.submit_test_answers(
        db, participant_id, test_data
    )
    
    return PersonalityTestResult(
        traits=PersonalityTraits(
            extroversion=updated_participant.extroversion,
            agreeableness=updated_participant.agreeableness,
            conscientiousness=updated_participant.conscientiousness,
            negative_emotionality=updated_participant.negative_emotionality,
            open_mindedness=updated_participant.open_mindedness,
        ),
        job_recommendation=updated_participant.job_recommendation,
        compatibility_analysis=updated_participant.compatibility_analysis,
    )


@personality_test_public_router.get(
    "/participants/{participant_id}/results",
    response_model=PersonalityTestResult,
)
def get_participant_results(
    participant_id: int,
    participant: CurrentPersonalityTestParticipant,
    db: Session = Depends(get_db),
):
    """
    Get results for a completed personality test.
    """
    verify_participant_ownership(participant.participant_id, participant_id)
    
    db_participant = PersonalityTestService.get_participant(db, participant_id)
    
    return PersonalityTestResult(
        traits=PersonalityTraits(
            extroversion=db_participant.extroversion,
            agreeableness=db_participant.agreeableness,
            conscientiousness=db_participant.conscientiousness,
            negative_emotionality=db_participant.negative_emotionality,
            open_mindedness=db_participant.open_mindedness,
        ),
        job_recommendation=db_participant.job_recommendation,
        compatibility_analysis=db_participant.compatibility_analysis,
    )


@personality_test_public_router.get(
    "/rooms/{room_id}/check-device",
)
def check_device_completion(
    room_id: int,
    device_fingerprint: str,
    db: Session = Depends(get_db),
):
    """
    Check if a device has already completed the test for a room.
    """
    has_completed = PersonalityTestService.check_device_completion(
        db, room_id, device_fingerprint
    )
    
    return {"has_completed": has_completed}


# =============================================================================
# Protected Router - Teacher/Admin access
# =============================================================================

personality_test_protected_router = APIRouter(
    prefix="/personality-test",
    tags=["personality-test"],
)


@personality_test_protected_router.get(
    "/participants",
    response_model=PersonalityTestParticipantList,
)
def get_my_participants(
    skip: int = 0,
    limit: int = 100,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Get all personality test participants for the current user.
    """
    participants, total = PersonalityTestService.get_participants_by_user(
        db, current_user.id, skip, limit
    )
    
    return PersonalityTestParticipantList(
        items=[
            PersonalityTestParticipantResponse.model_validate(p)
            for p in participants
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@personality_test_protected_router.get(
    "/rooms/{room_id}/participants",
    response_model=PersonalityTestParticipantList,
)
def get_room_participants(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Get all participants for a specific room.
    """
    # Verify room ownership
    TestRoomService.verify_room_ownership(db, room_id, current_user.id)
    
    participants, total = PersonalityTestService.get_participants_by_room(
        db, room_id, skip, limit
    )
    
    return PersonalityTestParticipantList(
        items=[
            PersonalityTestParticipantResponse.model_validate(p)
            for p in participants
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@personality_test_protected_router.get(
    "/rooms/{room_id}/statistics",
)
def get_room_statistics(
    room_id: int,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Get statistics for a room's personality test participants.
    """
    # Verify room ownership
    TestRoomService.verify_room_ownership(db, room_id, current_user.id)
    
    return PersonalityTestService.get_room_statistics(db, room_id)


@personality_test_protected_router.delete(
    "/participants/{participant_id}",
    response_model=PersonalityTestParticipantResponse,
)
def delete_participant(
    participant_id: int,
    current_user: TeacherOrAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Delete a personality test participant (soft delete).
    """
    participant = PersonalityTestService.delete_participant(
        db, participant_id, current_user.id
    )
    
    return PersonalityTestParticipantResponse.model_validate(participant)


# =============================================================================
# Combined Router
# =============================================================================

router = APIRouter()
router.include_router(personality_test_public_router)
router.include_router(personality_test_protected_router)
