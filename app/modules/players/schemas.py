from pydantic import BaseModel, Field, field_validator

from app.core.validators import FieldLimits, sanitize_string


class PlayerBase(BaseModel):
    player_name: str = Field(
        min_length=FieldLimits.NAME_MIN,
        max_length=FieldLimits.NAME_MAX,
    )
    player_function_name: str | None = Field(
        default=None, max_length=FieldLimits.SHORT_TEXT_MAX
    )
    player_tactic: str | None = Field(
        default=None, max_length=FieldLimits.LONG_TEXT_MAX
    )
    player_code: str | None = Field(
        default=None, max_length=FieldLimits.CODE_MAX
    )
    short_tactic: str | None = Field(
        default=None, max_length=FieldLimits.MEDIUM_TEXT_MAX
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


class Player(PlayerBase):
    id: int
    room_id: int

    class Config:
        from_attributes = True


class PlayerTacticUpdate(BaseModel):
    player_tactic: str = Field(max_length=FieldLimits.LONG_TEXT_MAX)


class PlayerPersonalityUpdate(BaseModel):
    answers: str = Field(max_length=FieldLimits.MEDIUM_TEXT_MAX)
