"""
Program suggestion schemas - Request/response models for program suggestions.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class ProgramSuggestionStudentBase(BaseModel):
    """Base model for program suggestion student."""

    name: str | None = None
    birth_year: int | None = None
    gender: str | None = None
    class_year: str | None = None
    will_take_exam: bool | None = True
    average_grade: float | None = None
    area: str | None = None
    wants_foreign_language: bool | None = False
    expected_score_min: float | None = None
    expected_score_max: float | None = None
    expected_score_distribution: str | None = None
    alternative_area: str | None = None
    alternative_score_min: float | None = None
    alternative_score_max: float | None = None
    alternative_score_distribution: str | None = None
    preferred_language: str | None = None
    desired_universities: list[str] | None = None
    desired_cities: list[str] | None = None


class ProgramSuggestionStudentCreate(BaseModel):
    """Request model for creating a student."""

    high_school_room_id: int


class ProgramSuggestionStudentUpdateStep1(BaseModel):
    """Request model for step 1 update (personal info)."""

    name: str
    birth_year: int
    gender: str


class ProgramSuggestionStudentUpdateStep2(BaseModel):
    """Request model for step 2 update (academic info)."""

    class_year: str
    will_take_exam: bool
    average_grade: float | None = None
    area: str
    wants_foreign_language: bool


class ProgramSuggestionStudentUpdateStep3(BaseModel):
    """Request model for step 3 update (score expectations)."""

    expected_score_min: float
    expected_score_max: float
    expected_score_distribution: str
    alternative_area: str | None = None
    alternative_score_min: float | None = None
    alternative_score_max: float | None = None
    alternative_score_distribution: str | None = None


class ProgramSuggestionStudentUpdateStep4(BaseModel):
    """Request model for step 4 update (preferences)."""

    preferred_language: str
    desired_universities: list[str] | None = None
    desired_cities: list[str]


class ProgramSuggestionStudentUpdateRiasec(BaseModel):
    """Request model for RIASEC assessment update."""

    riasec_answers: dict[str, int]  # {question_id: score}


class ProgramSuggestionStudent(ProgramSuggestionStudentBase):
    """Full response model for program suggestion student."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    high_school_room_id: int
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
    """Response model for student results."""

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
    """Debug response model for admin inspection."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    riasec_scores: dict[str, float] | None = None
    suggested_jobs: list[dict] | None = None
    gpt_prompt: str | None = None
    gpt_response: str | None = None
