"""
Player schemas - Request/response models for player management.
"""

from pydantic import BaseModel


class PlayerBase(BaseModel):
    """Base player model with common fields."""

    player_name: str
    player_function_name: str | None = None
    player_tactic: str | None = None
    player_code: str | None = None
    short_tactic: str | None = None
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None


class PlayerCreate(PlayerBase):
    """Request model for creating a player."""

    room_id: int


class Player(PlayerBase):
    """Response model for player data."""

    id: int
    room_id: int

    class Config:
        from_attributes = True


class PlayerTacticUpdate(BaseModel):
    """Request model for updating player tactic."""

    player_tactic: str


class PlayerPersonalityUpdate(BaseModel):
    """Request model for updating player personality."""

    answers: str
