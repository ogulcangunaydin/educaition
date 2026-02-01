from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    home_player_id = Column(Integer, ForeignKey("players.id"))
    away_player_id = Column(Integer, ForeignKey("players.id"))
    home_player_score = Column(Integer, default=0)
    away_player_score = Column(Integer, default=0)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
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
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    game = relationship("Game", back_populates="rounds")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    name = Column(String, nullable=True)
    status = Column(String, default="started")
    player_ids = Column(String, nullable=True)
    results = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    games = relationship("Game", back_populates="session")
    room = relationship("Room", back_populates="sessions")
