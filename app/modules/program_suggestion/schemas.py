from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from app.core.validators import FieldLimits, sanitize_string


class ProgramSuggestionStudentBase(BaseModel):
    name: str | None = Field(default=None, max_length=FieldLimits.NAME_MAX)
    birth_year: int | None = Field(default=None, ge=1950, le=2025)
    gender: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    class_year: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    will_take_exam: bool | None = True
    average_grade: float | None = Field(default=None, ge=0, le=100)
    area: str | None = Field(default=None, max_length=FieldLimits.CODE_FIELD_MAX)
    wants_foreign_language: bool | None = False
    expected_score_min: float | None = Field(default=None, ge=0, le=600)
    expected_score_max: float | None = Field(default=None, ge=0, le=600)
    expected_score_distribution: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )
    alternative_area: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )
    alternative_score_min: float | None = Field(default=None, ge=0, le=600)
    alternative_score_max: float | None = Field(default=None, ge=0, le=600)
    alternative_score_distribution: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )
    preferred_language: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )
    desired_universities: list[str] | None = Field(
        default=None, max_length=FieldLimits.MAX_UNIVERSITIES
    )
    desired_cities: list[str] | None = Field(
        default=None, max_length=FieldLimits.MAX_CITIES
    )

    @field_validator("name", "gender", "class_year", "area", "alternative_area", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v

    @field_validator("desired_universities", "desired_cities", mode="before")
    @classmethod
    def sanitize_list_items(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return [sanitize_string(item) or "" for item in v if item]


class ProgramSuggestionStudentCreate(BaseModel):
    """Create a new program suggestion student. Uses test_room_id (unified system)."""
    test_room_id: int = Field(..., description="The test room ID")


class ProgramSuggestionStudentUpdateStep1(BaseModel):
    name: str = Field(min_length=1, max_length=FieldLimits.NAME_MAX)
    birth_year: int = Field(ge=1950, le=2025)
    gender: str = Field(max_length=FieldLimits.CODE_FIELD_MAX)

    @field_validator("name", "gender", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return sanitize_string(v) or ""


class ProgramSuggestionStudentUpdateStep2(BaseModel):
    class_year: str = Field(max_length=FieldLimits.CODE_FIELD_MAX)
    will_take_exam: bool
    average_grade: float | None = Field(default=None, ge=0, le=100)
    area: str = Field(max_length=FieldLimits.CODE_FIELD_MAX)
    wants_foreign_language: bool

    @field_validator("class_year", "area", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return sanitize_string(v) or ""


class ProgramSuggestionStudentUpdateStep3(BaseModel):
    expected_score_min: float = Field(ge=0, le=600)
    expected_score_max: float = Field(ge=0, le=600)
    expected_score_distribution: str = Field(max_length=FieldLimits.CODE_FIELD_MAX)
    alternative_area: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )
    alternative_score_min: float | None = Field(default=None, ge=0, le=600)
    alternative_score_max: float | None = Field(default=None, ge=0, le=600)
    alternative_score_distribution: str | None = Field(
        default=None, max_length=FieldLimits.CODE_FIELD_MAX
    )

    @field_validator(
        "expected_score_distribution",
        "alternative_area",
        "alternative_score_distribution",
        mode="before",
    )
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


class ProgramSuggestionStudentUpdateStep4(BaseModel):
    preferred_language: str = Field(max_length=FieldLimits.CODE_FIELD_MAX)
    desired_universities: list[str] | None = Field(
        default=None, max_length=FieldLimits.MAX_UNIVERSITIES
    )
    desired_cities: list[str] = Field(max_length=FieldLimits.MAX_CITIES)

    @field_validator("preferred_language", mode="before")
    @classmethod
    def sanitize_language(cls, v: str) -> str:
        return sanitize_string(v) or ""

    @field_validator("desired_universities", "desired_cities", mode="before")
    @classmethod
    def sanitize_list_items(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return [sanitize_string(item) or "" for item in v if item]


class ProgramSuggestionStudentUpdateRiasec(BaseModel):
    riasec_answers: dict[str, int]  # {question_id: score}

    @field_validator("riasec_answers")
    @classmethod
    def validate_riasec_answers(cls, v: dict[str, int]) -> dict[str, int]:
        if len(v) > 100:  # Reasonable limit for RIASEC questions
            raise ValueError("Too many RIASEC answers")
        for key, value in v.items():
            if not isinstance(key, str) or len(key) > 50:
                raise ValueError("Invalid question ID format")
            if not isinstance(value, int) or value < -2 or value > 2:
                raise ValueError("Score must be an integer between -2 and 2")
        return v

class ProgramSuggestionStudent(ProgramSuggestionStudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_room_id: int | None = None
    high_school_room_id: int | None = None  # Legacy field, kept for backward compatibility
    riasec_answers: dict[str, int] | None = None
    riasec_scores: dict[str, float] | None = None
    suggested_jobs: list[dict] | None = None
    suggested_programs: list[dict] | None = None
    status: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")

class ProgramSuggestionStudentResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    riasec_scores: dict[str, float] | None = None
    suggested_jobs: list[dict] | None = None
    suggested_programs: list[dict] | None = None
    area: str | None = None
    expected_score_min: float | None = None
    expected_score_max: float | None = None
    alternative_area: str | None = None
    alternative_score_min: float | None = None
    alternative_score_max: float | None = None

class ProgramSuggestionStudentDebug(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    riasec_scores: dict[str, float] | None = None
    suggested_jobs: list[dict] | None = None
    gpt_prompt: str | None = None
    gpt_response: str | None = None


# =============================================================================
# Program Interaction Log Schemas
# =============================================================================

class ProgramInteractionLogCreate(BaseModel):
    action: str = Field(max_length=50)  # google_search, add_to_basket
    program_name: str = Field(max_length=255)
    university: str = Field(max_length=255)
    scholarship: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"google_search", "add_to_basket", "remove_from_basket", "view_details"}
        if v not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v


class ProgramInteractionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    action: str
    program_name: str
    university: str
    scholarship: str | None = None
    city: str | None = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y %H:%M:%S")
