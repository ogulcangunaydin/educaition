from pydantic import BaseModel

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

class PlayerTacticUpdate(BaseModel):
    player_tactic: str

class PlayerPersonalityUpdate(BaseModel):
    answers: str
