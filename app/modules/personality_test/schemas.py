"""
PersonalityTest Pydantic Schemas

This module defines request/response schemas for the personality test API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator, field_validator

from app.core.validators import (
    EmailStrOptional,
    FieldLimits,
    sanitize_string,
)


# =============================================================================
# Base Schemas
# =============================================================================

class PersonalityTestParticipantBase(BaseModel):
    """Base schema with common participant fields."""
    
    full_name: str | None = Field(default=None, max_length=FieldLimits.SHORT_TEXT_MAX)
    student_number: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    email: EmailStrOptional = Field(default=None, max_length=FieldLimits.EMAIL_MAX)
    age: int | None = Field(default=None, ge=1, le=150)
    gender: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    education: str | None = Field(default=None, max_length=FieldLimits.SHORT_TEXT_MAX)
    income: int | None = Field(default=None, ge=0)
    star_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    rising_sign: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    workload: int | None = Field(default=None, ge=1, le=10)
    career_start: int | None = Field(default=None, ge=1, le=10)
    flexibility: int | None = Field(default=None, ge=1, le=10)

    @field_validator("full_name", "gender", "education", "star_sign", "rising_sign", "student_number", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


# =============================================================================
# Create/Update Schemas
# =============================================================================

class PersonalityTestParticipantCreate(PersonalityTestParticipantBase):
    """Schema for creating a new personality test participant."""
    
    test_room_id: int = Field(description="The test room ID")
    student_user_id: int | None = Field(
        default=None,
        description="The authenticated student user ID (from device-login or real login)"
    )
    device_fingerprint: str | None = Field(
        default=None, 
        max_length=255,
        description="Browser fingerprint for device tracking"
    )
    device_info: dict[str, Any] | None = Field(
        default=None,
        description="Additional device information"
    )


class PersonalityTestSubmit(BaseModel):
    """Schema for submitting personality test answers."""
    
    answers: list[int] = Field(
        min_length=60, 
        max_length=60,
        description="Array of 60 personality test answers (1-5 scale)"
    )

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: list[int]) -> list[int]:
        if not all(1 <= a <= 5 for a in v):
            raise ValueError("All answers must be between 1 and 5")
        return v


# =============================================================================
# Response Schemas
# =============================================================================

class PersonalityTraits(BaseModel):
    """Personality trait scores response."""
    
    extroversion: float | None = Field(default=None, ge=0, le=100)
    agreeableness: float | None = Field(default=None, ge=0, le=100)
    conscientiousness: float | None = Field(default=None, ge=0, le=100)
    negative_emotionality: float | None = Field(default=None, ge=0, le=100)
    open_mindedness: float | None = Field(default=None, ge=0, le=100)


class PersonalityTestResult(BaseModel):
    """Full personality test result with analysis."""
    
    traits: PersonalityTraits
    job_recommendation: str | None = Field(
        default=None, 
        max_length=FieldLimits.LONG_TEXT_MAX
    )
    compatibility_analysis: str | None = Field(
        default=None, 
        max_length=FieldLimits.LONG_TEXT_MAX
    )


class PersonalityTestParticipantResponse(PersonalityTestParticipantBase):
    """Full participant response schema."""
    
    model_config = ConfigDict(ser_json_timedelta="iso8601", from_attributes=True)

    id: int
    test_room_id: int | None = None
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    # Personality traits
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None
    
    # Analysis
    job_recommendation: str | None = None
    compatibility_analysis: str | None = None
    
    # Test completion status
    has_completed: bool = False

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.isoformat()

    @model_validator(mode="after")
    def set_completion_status(self):
        self.has_completed = self.extroversion is not None
        return self


class PersonalityTestParticipantPublic(BaseModel):
    """Public response for anonymous participants (minimal data)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    traits: PersonalityTraits | None = None
    job_recommendation: str | None = None
    compatibility_analysis: str | None = None
    has_completed: bool = False


class PersonalityTestParticipantList(BaseModel):
    """Paginated list of participants."""
    
    items: list[PersonalityTestParticipantResponse]
    total: int
    skip: int
    limit: int
