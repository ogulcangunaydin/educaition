"""
Game router - API endpoints for game data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user, get_db
from app.modules.rooms.schemas import SessionCreate

from .schemas import Game, Round
from .service import GameService

router = APIRouter(
    prefix="/sessions",
    tags=["games"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("/{session_id}", response_model=SessionCreate)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a session by ID."""
    return GameService.get_session(db, session_id)


@router.get("/{session_id}/games", response_model=list[Game])
def get_games_by_session(session_id: int, db: Session = Depends(get_db)):
    """Get all games for a session."""
    return GameService.get_games_by_session(db, session_id)


@router.get("/{session_id}/games/{game_id}", response_model=Game)
def get_game(session_id: int, game_id: int, db: Session = Depends(get_db)):
    """Get a specific game."""
    return GameService.get_game(db, game_id)


@router.get("/{session_id}/games/{game_id}/rounds", response_model=list[Round])
def get_rounds_by_game(
    session_id: int, game_id: int, db: Session = Depends(get_db)
):
    """Get all rounds for a game."""
    return GameService.get_rounds_by_game(db, game_id)
