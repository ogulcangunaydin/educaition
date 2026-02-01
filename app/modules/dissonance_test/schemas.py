from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer

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
