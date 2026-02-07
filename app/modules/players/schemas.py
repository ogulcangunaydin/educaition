from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.validators import FieldLimits, sanitize_string


class PlayerBase(BaseModel):
    player_name: str = Field(
        min_length=FieldLimits.NAME_MIN,
        max_length=FieldLimits.NAME_MAX,
    )
    player_function_name: str | None = Field(
        default=None, max_length=FieldLimits.SHORT_TEXT_MAX
    )
    student_number: str | None = Field(
        default=None, max_length=FieldLimits.SHORT_TEXT_MAX
    )
    device_fingerprint: str | None = Field(
        default=None, max_length=255
    )
    student_user_id: int | None = None
    player_tactic: str | None = Field(
        default=None, max_length=FieldLimits.LONG_TEXT_MAX
    )
    player_code: str | None = Field(
        default=None, max_length=FieldLimits.CODE_MAX
    )
    short_tactic: str | None = Field(
        default=None, max_length=FieldLimits.MEDIUM_TEXT_MAX
    )
    tactic_reason: str | None = Field(
        default=None, max_length=FieldLimits.LONG_TEXT_MAX
    )
    job_recommendation: str | None = Field(
        default=None, max_length=FieldLimits.CODE_MAX
    )
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None

    @field_validator("player_name", mode="before")
    @classmethod
    def sanitize_player_name(cls, v: str) -> str:
        return sanitize_string(v) or ""


class PlayerCreate(PlayerBase):
    room_id: int


class PlayerRegister(BaseModel):
    """Schema for the standardized registration from TestRegistrationCard."""
    test_room_id: int
    full_name: str = Field(
        min_length=FieldLimits.NAME_MIN,
        max_length=FieldLimits.NAME_MAX,
    )
    student_number: str | None = Field(
        default=None, max_length=FieldLimits.SHORT_TEXT_MAX
    )
    device_fingerprint: str | None = Field(
        default=None, max_length=255
    )
    student_user_id: int | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        return sanitize_string(v) or ""


class Player(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime | None, _info):
        if created_at is None:
            return None
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")


class PlayerTacticUpdate(BaseModel):
    player_tactic: str = Field(max_length=FieldLimits.LONG_TEXT_MAX)


class PlayerPersonalityUpdate(BaseModel):
    answers: str = Field(max_length=FieldLimits.MEDIUM_TEXT_MAX)
