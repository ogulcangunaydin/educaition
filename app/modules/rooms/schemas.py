"""
Room schemas - Request/response models for room management.
"""

from pydantic import BaseModel


class RoomBase(BaseModel):
    """Base room model."""

    pass


class RoomCreate(RoomBase):
    """Request model for creating a room."""

    pass


class Room(RoomBase):
    """Response model for room data."""

    id: int
    user_id: int
    name: str | None

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    """Base session model."""

    pass


class SessionCreate(SessionBase):
    """Response model for session data."""

    id: int
    room_id: int
    name: str
    status: str
    player_ids: str
    # TODO: This union is for getting also old data which is dict type
    results: str | dict | None = None
