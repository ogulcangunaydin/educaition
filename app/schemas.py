from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.password_service import (
    PasswordConfig,
    validate_password_strength,
)


def _validate_password_field(password: str) -> str:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password


class UserBase(BaseModel):
    username: str
    email: str | None = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_field(v)


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_password_field(v)
        return v


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    current_user_id: int
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class PasswordRequirements(BaseModel):
    min_length: int = PasswordConfig.MIN_LENGTH
    max_length: int = PasswordConfig.MAX_LENGTH
    require_uppercase: bool = PasswordConfig.REQUIRE_UPPERCASE
    require_lowercase: bool = PasswordConfig.REQUIRE_LOWERCASE
    require_digit: bool = PasswordConfig.REQUIRE_DIGIT
    require_special: bool = PasswordConfig.REQUIRE_SPECIAL
    special_characters: str = PasswordConfig.SPECIAL_CHARACTERS
    message: str = (
        f"Password must be {PasswordConfig.MIN_LENGTH}-{PasswordConfig.MAX_LENGTH} characters, "
        "with at least one uppercase letter, one lowercase letter, "
        "one digit, and one special character."
    )


class RoomBase(BaseModel):
    pass


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: int
    user_id: int
    name: str | None

    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    player_name: str
    player_function_name: str | None = None
    player_tactic: str | None = None
    player_code: str | None = None
    short_tactic: str | None = None
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None


class PlayerCreate(PlayerBase):
    room_id: int


class Player(PlayerBase):
    id: int
    room_id: int

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    home_player_id: int
    away_player_id: int
    home_player_score: int
    away_player_score: int
    session_id: int


class GameCreate(GameBase):
    pass


class Game(GameBase):
    id: int

    class Config:
        from_attributes = True


class RoundBase(BaseModel):
    round_number: int
    home_choice: str
    away_choice: str
    game_id: int


class RoundCreate(RoundBase):
    pass


class Round(RoundBase):
    id: int

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    pass


class SessionCreate(SessionBase):
    id: int
    room_id: int
    name: str
    status: str
    player_ids: str
    # TODO: This union is for getting also old data which is dict type
    results: str | dict | None = None


class DissonanceTestParticipantBase(BaseModel):
    email: str | None = None
    age: int | None = None
    gender: str | None = None
    education: str | None = None
    sentiment: int | None = None
    comfort_question_first_answer: int | None = None
    fare_question_first_answer: int | None = None
    comfort_question_second_answer: int | None = None
    fare_question_second_answer: int | None = None
    fare_question_displayed_average: float | None = None
    comfort_question_displayed_average: float | None = None
    workload: int | None = None
    career_start: int | None = None
    flexibility: int | None = None
    star_sign: str | None = None
    rising_sign: str | None = None
    user_id: int


class DissonanceTestParticipantCreate(DissonanceTestParticipantBase):
    pass


class DissonanceTestParticipantUpdateSecond(BaseModel):
    fare_question_second_answer: int
    comfort_question_second_answer: int
    fare_question_displayed_average: float
    comfort_question_displayed_average: float


class DissonanceTestParticipantResult(BaseModel):
    compatibility_analysis: str | None = None
    job_recommendation: str | None = None
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None


class DissonanceTestParticipant(DissonanceTestParticipantBase):
    model_config = ConfigDict(ser_json_timedelta="iso8601", from_attributes=True)

    id: int
    created_at: datetime
    extroversion: float | None = None
    agreeableness: float | None = None
    conscientiousness: float | None = None
    negative_emotionality: float | None = None
    open_mindedness: float | None = None
    personality_test_answers: dict[str, int] | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime("%d/%m/%Y  %H:%M:%S")


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
