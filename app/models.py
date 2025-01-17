from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    rooms = relationship("Room", back_populates="user")
    dissonance_test_participants = relationship("DissonanceTestParticipant", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="rooms")
    players = relationship("Player", back_populates="room")
    sessions = relationship("Session", back_populates="room")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_function_name = Column(String)
    player_tactic = Column(String)
    short_tactic = Column(String)
    player_code = Column(String)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    extroversion = Column(Float)
    agreeableness = Column(Float)
    conscientiousness = Column(Float)
    negative_emotionality = Column(Float)
    open_mindedness = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    game = relationship("Game", back_populates="rounds")
    
class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    name = Column(String, nullable=True)
    status = Column(String, default='started')
    player_ids = Column(String, nullable=True)
    results = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    games = relationship("Game", back_populates="session")
    room = relationship("Room", back_populates="sessions")

class DissonanceTestParticipant(Base):
    __tablename__ = 'dissonance_test_participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    education = Column(String(255), nullable=True)
    income = Column(Integer, nullable=True)
    sentiment = Column(Integer, nullable=True)
    comfort_question_first_answer = Column(Integer, nullable=True)
    fare_question_first_answer = Column(Integer, nullable=True)
    comfort_question_second_answer = Column(Integer, nullable=True)
    fare_question_second_answer = Column(Integer, nullable=True)
    extroversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    negative_emotionality = Column(Float, nullable=True)
    open_mindedness = Column(Float, nullable=True)
    job_recommendation = Column(String, nullable=True)
    compatibility_analysis = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    workload = Column(Integer, nullable=True)
    career_start = Column(Integer, nullable=True)
    flexibility = Column(Integer, nullable=True)
    star_sign = Column(String(50), nullable=True)
    rising_sign = Column(String(50), nullable=True)
    personality_test_answers = Column(JSONB, nullable=True)
    comfort_question_displayed_average = Column(Float, nullable=True)  # New field
    fare_question_displayed_average = Column(Float, nullable=True)  # New field
    
    user = relationship("User", back_populates="dissonance_test_participants")
    