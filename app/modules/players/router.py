"""
Player router - API endpoints for player management.
"""

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

from .schemas import Player
from .service import PlayerService

# Public routes (no auth required, but some require participant token)
players_public_router = APIRouter(prefix="/players", tags=["players"])

# Protected routes (require user auth)
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
    """
    Create a new player in a room (public).

    Returns player data with session token for subsequent requests.
    """
    created_player = PlayerService.create_player(db, player_name, room_id)

    # Create participant token
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


@players_public_router.get("/room/{room_id}", response_model=list[Player])
def get_players_by_room(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all players in a room (public)."""
    return PlayerService.get_players_by_room(db, room_id, skip, limit)


@players_public_router.post("/{player_id}/tactic", response_model=Player)
def update_player_tactic(
    player_id: int,
    participant: CurrentPlayer,
    player_tactic: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Update a player's tactic (requires participant token).

    The participant token must match the player being updated.
    """
    verify_participant_ownership(participant.participant_id, player_id)
    return PlayerService.update_player_tactic(db, player_id, player_tactic)


@players_public_router.post("/{player_id}/personality", response_model=Player)
def update_player_personality_traits(
    player_id: int,
    participant: CurrentPlayer,
    answers: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Update a player's personality traits (requires participant token).

    The participant token must match the player being updated.
    """
    verify_participant_ownership(participant.participant_id, player_id)
    return PlayerService.update_player_personality_traits(db, player_id, answers)


@players_protected_router.get("/{player_ids}", response_model=list[Player])
def get_players_by_ids(player_ids: str, db: Session = Depends(get_db)):
    """Get players by comma-separated IDs (authenticated users only)."""
    return PlayerService.get_players_by_ids(db, player_ids)


@players_protected_router.post("/delete/{player_id}", response_model=Player)
def delete_player(
    player_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """Delete a player (teacher/admin only)."""
    return PlayerService.delete_player(db, player_id)


# Combined router for easy import
router = APIRouter()
router.include_router(players_public_router)
router.include_router(players_protected_router)
