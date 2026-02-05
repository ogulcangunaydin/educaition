from pydantic import BaseModel, Field


class GameBase(BaseModel):
    home_player_id: int
    away_player_id: int
    home_player_score: int = Field(ge=0)
    away_player_score: int = Field(ge=0)
    session_id: int


class GameCreate(GameBase):
    pass


class Game(GameBase):
    id: int

    class Config:
        from_attributes = True


class RoundBase(BaseModel):
    round_number: int = Field(ge=1, le=1000)
    home_choice: str = Field(max_length=50)
    away_choice: str = Field(max_length=50)
    game_id: int


class RoundCreate(RoundBase):
    pass


class Round(RoundBase):
    id: int

    class Config:
        from_attributes = True
