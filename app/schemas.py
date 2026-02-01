from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.password_service import (
    PasswordConfig,
    validate_password_strength,
)

# Re-export auth schemas for backward compatibility
from app.modules.auth.schemas import (
    PasswordRequirements,
    Token,
    TokenRefreshRequest,
    TokenRefreshResponse,
)

# Re-export user schemas for backward compatibility
from app.modules.users.schemas import (
    User,
    UserBase,
    UserCreate,
    UserRoleEnum,
    UserUpdate,
    UniversityKeyEnum,
)

# Re-export room schemas for backward compatibility
from app.modules.rooms.schemas import (
    Room,
    RoomBase,
    RoomCreate,
    SessionBase,
    SessionCreate,
)

# Re-export player schemas for backward compatibility
from app.modules.players.schemas import (
    Player,
    PlayerBase,
    PlayerCreate,
)

# Re-export game schemas for backward compatibility
from app.modules.games.schemas import (
    Game,
    GameBase,
    GameCreate,
    Round,
    RoundBase,
    RoundCreate,
)

# Re-export dissonance test schemas for backward compatibility
from app.modules.dissonance_test.schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantBase,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateSecond,
)


def _validate_password_field(password: str) -> str:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password


# UserRoleEnum, UniversityKeyEnum, UserBase, UserCreate, UserUpdate, User
# moved to app.modules.users.schemas (re-exported above for compatibility)

# Token, TokenRefreshRequest, TokenRefreshResponse, PasswordRequirements
# moved to app.modules.auth.schemas (re-exported above for compatibility)

# Room, RoomBase, RoomCreate, SessionBase, SessionCreate
# moved to app.modules.rooms.schemas (re-exported above for compatibility)

# Player, PlayerBase, PlayerCreate
# moved to app.modules.players.schemas (re-exported above for compatibility)

# Game, GameBase, GameCreate, Round, RoundBase, RoundCreate
# moved to app.modules.games.schemas (re-exported above for compatibility)

# DissonanceTestParticipant, DissonanceTestParticipantBase, DissonanceTestParticipantCreate,
# DissonanceTestParticipantResult, DissonanceTestParticipantUpdateSecond
# moved to app.modules.dissonance_test.schemas (re-exported above for compatibility)


class ParticipantSessionResponse(BaseModel):
    participant_id: int
    session_token: str
    expires_in: int


# High School Room Schemas
class HighSchoolRoomBase(BaseModel):
    high_school_name: str
    high_school_code: str | None = None


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


# Program Suggestion Student Schemas
class ProgramSuggestionStudentBase(BaseModel):
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
    high_school_room_id: int


class ProgramSuggestionStudentUpdateStep1(BaseModel):
    name: str
    birth_year: int
    gender: str


class ProgramSuggestionStudentUpdateStep2(BaseModel):
    class_year: str
    will_take_exam: bool
    average_grade: float | None = None
    area: str
    wants_foreign_language: bool


class ProgramSuggestionStudentUpdateStep3(BaseModel):
    expected_score_min: float
    expected_score_max: float
    expected_score_distribution: str
    alternative_area: str | None = None
    alternative_score_min: float | None = None
    alternative_score_max: float | None = None
    alternative_score_distribution: str | None = None


class ProgramSuggestionStudentUpdateStep4(BaseModel):
    preferred_language: str
    desired_universities: list[str] | None = None
    desired_cities: list[str]


class ProgramSuggestionStudentUpdateRiasec(BaseModel):
    riasec_answers: dict[str, int]  # {question_id: score}


class ProgramSuggestionStudent(ProgramSuggestionStudentBase):
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
