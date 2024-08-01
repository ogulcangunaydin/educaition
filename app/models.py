from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    rooms = relationship("Room", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)

    user = relationship("User", back_populates="rooms")
    players = relationship("Player", back_populates="room")
    sessions = relationship("Session", back_populates="room")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_tactic = Column(String)
    player_code = Column(String)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    extroversion = Column(Float)
    agreeableness = Column(Float)
    conscientiousness = Column(Float)
    negative_emotionality = Column(Float)
    open_mindedness = Column(Float)

    room = relationship("Room", back_populates="players")
    
    @property
    def is_ready(self):
        return bool(self.player_tactic and self.player_code)
    
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    home_player_id = Column(Integer, ForeignKey("players.id"))
    away_player_id = Column(Integer, ForeignKey("players.id"))
    home_player_score = Column(Integer, default=0)
    away_player_score = Column(Integer, default=0)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    home_player = relationship("Player", foreign_keys=[home_player_id])
    away_player = relationship("Player", foreign_keys=[away_player_id])
    rounds = relationship("Round", back_populates="game")
    session = relationship("Session", back_populates="games")

class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer)
    home_choice = Column(String)
    away_choice = Column(String)
    game_id = Column(Integer, ForeignKey("games.id"))

    game = relationship("Game", back_populates="rounds")
    
class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    name = Column(String, nullable=True)
    status = Column(String, default='started')
    player_ids = Column(String, nullable=True)
    results = Column(JSONB, nullable=True)

    games = relationship("Game", back_populates="session")
    room = relationship("Room", back_populates="sessions")