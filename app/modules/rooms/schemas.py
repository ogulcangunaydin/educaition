from pydantic import BaseModel, Field, field_validator

from app.core.validators import FieldLimits, NameStrOptional, sanitize_string


class RoomCreate(BaseModel):
    """Schema for creating a new room."""

    name: str = Field(
        min_length=FieldLimits.NAME_MIN,
        max_length=FieldLimits.NAME_MAX,
        description="Room name",
    )

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v) or ""


class Room(BaseModel):
    id: int
    user_id: int
    name: str | None

    class Config:
        from_attributes = True


class Session(BaseModel):
    id: int
    room_id: int
    name: str
    status: str
    player_ids: str
    # TODO: This union is for getting also old data which is dict type
    results: str | dict | None = None

    class Config:
        from_attributes = True
