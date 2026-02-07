from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core import settings
from app.dependencies.auth import TeacherOrAdmin, get_current_active_user, get_db
from app.dependencies.participant import CurrentPlayer, verify_participant_ownership
from app.services.participant_token_service import (
    ParticipantType,
    create_participant_token,
    get_token_expiry_seconds,
)
from app.modules.users.models import User
from app.core.enums import UserRole
from .schemas import Player, PlayerRegister
from .service import PlayerService

players_public_router = APIRouter(prefix="/players", tags=["players"])
players_protected_router = APIRouter(
    prefix="/players",
    tags=["players"],
    dependencies=[Depends(get_current_active_user)],
)

@players_public_router.post("/")
def create_player(
    player_name: str = Form(...),
    room_id: int = Form(...),
    db: Session = Depends(get_db),
):
    created_player = PlayerService.create_player(db, player_name, room_id)
    token = create_participant_token(
        participant_id=created_player.id,
        participant_type=ParticipantType.PLAYER,
        room_id=room_id,
    )
    response = JSONResponse(
        content={
            "player": Player.model_validate(created_player).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PLAYER),
        }
    )
    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PLAYER),
    )

    return response


@players_public_router.post("/register")
def register_player(
    data: PlayerRegister,
    db: Session = Depends(get_db),
):
    """
    Standardized registration endpoint used by TestRegistrationCard.
    Accepts JSON with test_room_id, full_name, student_number,
    device_fingerprint, student_user_id.
    Returns response compatible with TestRegistrationCard's onSuccess.
    """
    # Admin/teacher bypass — privileged users can retake without device restrictions
    is_privileged = False
    if data.student_user_id:
        stu = db.query(User).filter(User.id == data.student_user_id).first()
        if stu and stu.role in (UserRole.ADMIN.value, UserRole.TEACHER.value):
            is_privileged = True

    created_player = PlayerService.register_player(db, data, is_privileged=is_privileged)
    token = create_participant_token(
        participant_id=created_player.id,
        participant_type=ParticipantType.PLAYER,
        room_id=created_player.room_id,
    )
    response = JSONResponse(
        content={
            "participant": {
                "id": created_player.id,
                **Player.model_validate(created_player).model_dump(mode="json"),
            },
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PLAYER),
        }
    )
    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PLAYER),
    )

    return response

@players_public_router.get("/room/{room_id}", response_model=list[Player])
def get_players_by_room(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return PlayerService.get_players_by_room(db, room_id, skip, limit)

@players_public_router.post("/{player_id}/tactic", response_model=Player)
def update_player_tactic(
    player_id: int,
    participant: CurrentPlayer,
    player_tactic: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    return PlayerService.update_player_tactic(db, player_id, player_tactic)

@players_public_router.post("/{player_id}/personality", response_model=Player)
def update_player_personality_traits(
    player_id: int,
    participant: CurrentPlayer,
    answers: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    return PlayerService.update_player_personality_traits(db, player_id, answers)


@players_public_router.post("/{player_id}/tactic-reasons")
def get_tactic_reasons(
    player_id: int,
    participant: CurrentPlayer,
    language: str = Form(default="tr"),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    reasons = PlayerService.get_tactic_reasons(db, player_id, language)
    return {"reasons": reasons}


@players_public_router.post("/{player_id}/tactic-reason", response_model=Player)
def submit_tactic_reason(
    player_id: int,
    participant: CurrentPlayer,
    reason: str = Form(...),
    language: str = Form(default="tr"),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    return PlayerService.submit_tactic_reason(db, player_id, reason, language)


@players_protected_router.get("/{player_ids}", response_model=list[Player])
def get_players_by_ids(player_ids: str, db: Session = Depends(get_db)):
    return PlayerService.get_players_by_ids(db, player_ids)

@players_protected_router.post("/delete/{player_id}", response_model=Player)
def delete_player(player_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)):
    return PlayerService.delete_player(db, player_id)

router = APIRouter()
router.include_router(players_public_router)
router.include_router(players_protected_router)
