from pydantic import BaseModel
from typing import Optional

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

    class Config:
        from_attributes = True

class PlayerBase(BaseModel):
    player_name: str
    player_tactic: Optional[str] = None
    player_code: Optional[str] = None

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