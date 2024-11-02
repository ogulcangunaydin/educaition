from pydantic import BaseModel, field_serializer, ConfigDict
from typing import Optional, Union, Dict
from datetime import datetime
import json

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

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
    username: Optional[str] = None

class RoomBase(BaseModel):
    pass

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    user_id: int
    name: Optional[str]

    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    player_name: str
    player_function_name: Optional[str] = None
    player_tactic: Optional[str] = None
    player_code: Optional[str] = None
    short_tactic: Optional[str] = None
    extroversion: Optional[float] = None
    agreeableness: Optional[float] = None
    conscientiousness: Optional[float] = None
    negative_emotionality: Optional[float] = None
    open_mindedness: Optional[float] = None

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
    results: Optional[Union[str, dict]] = None
    
class DissonanceTestParticipantBase(BaseModel):
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    sentiment: Optional[int] = None
    comfort_question_first_answer: Optional[int] = None
    fare_question_first_answer: Optional[int] = None
    comfort_question_second_answer: Optional[int] = None
    fare_question_second_answer: Optional[int] = None
    workload: Optional[int] = None
    career_start: Optional[int] = None
    flexibility: Optional[int] = None
    star_sign: Optional[str] = None
    rising_sign: Optional[str] = None
    user_id: int

class DissonanceTestParticipantCreate(DissonanceTestParticipantBase):
    pass

class DissonanceTestParticipantUpdateSecond(BaseModel):
    fare_question_second_answer: int
    comfort_question_second_answer: int

class DissonanceTestParticipantResult(BaseModel):
    compatibility_analysis: Optional[str] = None
    job_recommendation: Optional[str] = None
    extroversion: Optional[float] = None
    agreeableness: Optional[float] = None
    conscientiousness: Optional[float] = None
    negative_emotionality: Optional[float] = None
    open_mindedness: Optional[float] = None

class DissonanceTestParticipant(DissonanceTestParticipantBase):
    model_config = ConfigDict(ser_json_timedelta='iso8601', from_attributes=True)

    id: int
    created_at: datetime
    extroversion: Optional[float] = None
    agreeableness: Optional[float] = None
    conscientiousness: Optional[float] = None
    negative_emotionality: Optional[float] = None
    open_mindedness: Optional[float] = None
    personality_test_answers: Optional[Dict[str, int]] = None
        
    @field_serializer('created_at')
    def serialize_created_at(self, created_at: datetime, _info):
        return created_at.strftime('%d/%m/%Y  %H:%M:%S')
