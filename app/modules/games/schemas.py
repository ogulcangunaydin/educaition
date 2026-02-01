"""
Game schemas - Request/response models for game data.
"""

from pydantic import BaseModel


class GameBase(BaseModel):
    """Base game model with score tracking."""

    home_player_id: int
    away_player_id: int
    home_player_score: int
    away_player_score: int
    session_id: int


class GameCreate(GameBase):
    """Request model for creating a game."""

    pass


class Game(GameBase):
    """Response model for game data."""

    id: int

    class Config:
        from_attributes = True


class RoundBase(BaseModel):
    """Base round model with player choices."""

    round_number: int
    home_choice: str
    away_choice: str
    game_id: int


class RoundCreate(RoundBase):
    """Request model for creating a round."""

    pass


class Round(RoundBase):
    """Response model for round data."""

    id: int

    class Config:
        from_attributes = True
