from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.validators import FieldLimits, sanitize_string


class HighSchoolRoomBase(BaseModel):
    high_school_name: str = Field(
        min_length=FieldLimits.NAME_MIN,
        max_length=FieldLimits.NAME_MAX,
    )
    high_school_code: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )

    @field_validator("high_school_name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v) or ""

    @field_validator("high_school_code", mode="before")
    @classmethod
    def sanitize_code(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


class HighSchoolRoomCreate(HighSchoolRoomBase):
    pass


class HighSchoolRoom(HighSchoolRoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")
