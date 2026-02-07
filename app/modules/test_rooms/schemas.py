"""
TestRoom Schemas - Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.enums import TestType


# =============================================================================
# BASE SCHEMAS
# =============================================================================


class TestRoomBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name for the room",
    )
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Test-specific configuration",
    )


class TestRoomCreate(TestRoomBase):
    """Schema for creating a new test room."""
    test_type: TestType = Field(
        ...,
        description="Type of test for this room",
    )

    @field_validator("test_type", mode="before")
    @classmethod
    def validate_test_type(cls, v):
        if isinstance(v, str):
            try:
                return TestType(v)
            except ValueError:
                raise ValueError(f"Invalid test type: {v}")
        return v


class TestRoomUpdate(BaseModel):
    """Schema for updating a test room."""
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class TestRoomResponse(BaseModel):
    """Response schema for a single test room."""
    id: int
    name: str
    test_type: str
    is_active: bool
    settings: dict[str, Any] | None
    created_by: int
    legacy_room_id: int | None = None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class TestRoomWithStats(TestRoomResponse):
    """Response schema with participant statistics."""
    participant_count: int = 0
    completed_count: int = 0

    class Config:
        from_attributes = True


class TestRoomList(BaseModel):
    """Response schema for listing test rooms."""
    items: list[TestRoomResponse]
    total: int
    skip: int
    limit: int


# =============================================================================
# SETTINGS SCHEMAS (Test-specific)
# =============================================================================


class PrisonersDilemmaSettings(BaseModel):
    """Settings specific to Prisoners' Dilemma test."""
    rounds: int = Field(default=10, ge=1, le=100)
    max_players: int = Field(default=50, ge=2, le=200)


class DissonanceTestSettings(BaseModel):
    """Settings specific to Dissonance Test."""
    include_personality_test: bool = Field(default=True)


class ProgramSuggestionSettings(BaseModel):
    """Settings specific to Program Suggestion test."""
    high_school_code: str | None = None


class PersonalityTestSettings(BaseModel):
    """Settings specific to Personality Test."""
    test_version: str = Field(default="big5")


# =============================================================================
# PUBLIC SCHEMAS
# =============================================================================


class TestRoomPublicInfo(BaseModel):
    """Public information about a room (for anonymous users via QR)."""
    id: int
    name: str
    test_type: str
    is_active: bool
    legacy_room_id: int | None = None

    class Config:
        from_attributes = True
