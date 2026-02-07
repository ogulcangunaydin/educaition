from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.validators import (
    EmailStrOptional,
    FieldLimits,
    sanitize_string,
    validate_year,
)


class DissonanceTestParticipantBase(BaseModel):
    full_name: str | None = Field(default=None, max_length=FieldLimits.SHORT_TEXT_MAX)
    student_number: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    email: EmailStrOptional = Field(default=None, max_length=FieldLimits.EMAIL_MAX)
    age: int | None = Field(default=None, ge=1, le=150)
    gender: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    education: str | None = Field(default=None, max_length=FieldLimits.SHORT_TEXT_MAX)
    sentiment: int | None = Field(default=None, ge=1, le=10)
    comfort_question_first_answer: int | None = Field(default=None, ge=1, le=10)
    fare_question_first_answer: int | None = Field(default=None, ge=1, le=10)
    comfort_question_second_answer: int | None = Field(default=None, ge=1, le=10)
    fare_question_second_answer: int | None = Field(default=None, ge=1, le=10)
    fare_question_displayed_average: float | None = Field(default=None, ge=0, le=10)
    comfort_question_displayed_average: float | None = Field(default=None, ge=0, le=10)
    workload: int | None = Field(default=None, ge=1, le=10)
    career_start: int | None = Field(default=None, ge=1, le=10)
    flexibility: int | None = Field(default=None, ge=1, le=10)
    star_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    rising_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    user_id: int
    test_room_id: int | None = Field(default=None)
    device_fingerprint: str | None = Field(default=None, max_length=255)
    student_user_id: int | None = Field(
        default=None,
        description="The authenticated student user ID (from device-login or real login)"
    )

    @field_validator("full_name", "gender", "education", "star_sign", "rising_sign", "student_number", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


class DissonanceTestParticipantCreate(DissonanceTestParticipantBase):
    pass


class DissonanceTestParticipantUpdateSecond(BaseModel):
    fare_question_second_answer: int = Field(ge=1, le=10)
    comfort_question_second_answer: int = Field(ge=1, le=10)
    fare_question_displayed_average: float = Field(ge=0, le=10)
    comfort_question_displayed_average: float = Field(ge=0, le=10)


class DissonanceTestParticipantUpdateFirst(BaseModel):
    """Update demographics + first-round taxi answers after initial registration."""
    gender: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    education: str | None = Field(default=None, max_length=FieldLimits.SHORT_TEXT_MAX)
    comfort_question_first_answer: int | None = Field(default=None, ge=1, le=10)
    fare_question_first_answer: int | None = Field(default=None, ge=1, le=10)
    workload: int | None = Field(default=None, ge=1, le=10)
    career_start: int | None = Field(default=None, ge=1, le=10)
    flexibility: int | None = Field(default=None, ge=1, le=10)
    star_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    rising_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)

    @field_validator("gender", "education", "star_sign", "rising_sign", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


class DissonanceTestParticipantResult(BaseModel):
    compatibility_analysis: str | None = Field(
        default=None, max_length=FieldLimits.LONG_TEXT_MAX
    )
    job_recommendation: str | None = Field(
        default=None, max_length=FieldLimits.LONG_TEXT_MAX
    )
    extroversion: float | None = Field(default=None, ge=0, le=1)
    agreeableness: float | None = Field(default=None, ge=0, le=1)
    conscientiousness: float | None = Field(default=None, ge=0, le=1)
    negative_emotionality: float | None = Field(default=None, ge=0, le=1)
    open_mindedness: float | None = Field(default=None, ge=0, le=1)

class DissonanceTestParticipant(DissonanceTestParticipantBase):
    model_config = ConfigDict(ser_json_timedelta="iso8601", from_attributes=True)

    id: int
    created_at: datetime
    has_completed: int | None = None
    job_recommendation: str | None = None
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None
    personality_test_answers: dict[str, int] | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")


class DissonanceTestParticipantList(BaseModel):
    """Paginated list of dissonance test participants."""
    items: list[DissonanceTestParticipant] = []
    total: int = 0
