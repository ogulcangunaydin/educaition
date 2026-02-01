from pydantic import BaseModel

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
