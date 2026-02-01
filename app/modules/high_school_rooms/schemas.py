"""
High school room schemas - Request/response models for high school rooms.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class HighSchoolRoomBase(BaseModel):
    """Base model for high school room."""

    high_school_name: str
    high_school_code: str | None = None


class HighSchoolRoomCreate(HighSchoolRoomBase):
    """Request model for creating a high school room."""

    pass


class HighSchoolRoom(HighSchoolRoomBase):
    """Full response model for high school room."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")
