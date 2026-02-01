from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"  # Full system access
    TEACHER = "teacher"  # Can create rooms, manage students
    STUDENT = "student"  # Can participate in tests/games
    VIEWER = "viewer"  # Read-only access


class UniversityKey(str, PyEnum):
    HALIC = "halic"
    IBNHALDUN = "ibnhaldun"
    FSM = "fsm"
    IZU = "izu"
    MAYIS = "mayis"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(
        String(20),
        default=UserRole.STUDENT.value,
        nullable=False,
    )
    # University the user belongs to (controls data access)
    university = Column(
        String(20),
        default=UniversityKey.HALIC.value,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    rooms = relationship("Room", back_populates="user")
    dissonance_test_participants = relationship(
        "DissonanceTestParticipant", back_populates="user"
    )
    high_school_rooms = relationship("HighSchoolRoom", back_populates="user")


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)  # JWT ID
    token_type = Column(String, nullable=False)  # "access" or "refresh"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # For cleanup
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
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
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
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


class DissonanceTestParticipant(Base):
    __tablename__ = "dissonance_test_participants"

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
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workload = Column(Integer, nullable=True)
    career_start = Column(Integer, nullable=True)
    flexibility = Column(Integer, nullable=True)
    star_sign = Column(String(50), nullable=True)
    rising_sign = Column(String(50), nullable=True)
    personality_test_answers = Column(JSONB, nullable=True)
    comfort_question_displayed_average = Column(Float, nullable=True)  # New field
    fare_question_displayed_average = Column(Float, nullable=True)  # New field

    user = relationship("User", back_populates="dissonance_test_participants")


class HighSchoolRoom(Base):
    __tablename__ = "high_school_rooms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    high_school_name = Column(String, nullable=False)
    high_school_code = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="high_school_rooms")
    students = relationship(
        "ProgramSuggestionStudent", back_populates="high_school_room"
    )


class ProgramSuggestionStudent(Base):
    __tablename__ = "program_suggestion_students"

    id = Column(Integer, primary_key=True, index=True)
    high_school_room_id = Column(
        Integer, ForeignKey("high_school_rooms.id"), nullable=False
    )

    # Step 1.1 - Personal Info
    name = Column(String(100), nullable=True)
    birth_year = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)

    # Step 1.2 - Education Info
    class_year = Column(String(20), nullable=True)  # 9, 10, 11, 12, mezun
    will_take_exam = Column(Boolean, default=True)
    average_grade = Column(Float, nullable=True)  # Optional
    area = Column(String(50), nullable=True)  # say, ea, söz, dil
    wants_foreign_language = Column(Boolean, default=False)

    # Step 1.3 - Score Expectations
    expected_score_min = Column(Float, nullable=True)
    expected_score_max = Column(Float, nullable=True)
    expected_score_distribution = Column(String(20), nullable=True)  # low, medium, high
    alternative_area = Column(String(50), nullable=True)
    alternative_score_min = Column(Float, nullable=True)
    alternative_score_max = Column(Float, nullable=True)
    alternative_score_distribution = Column(String(20), nullable=True)

    # Step 1.4 - Preferences
    preferred_language = Column(String(50), nullable=True)  # Türkçe, İngilizce, etc.
    desired_universities = Column(JSONB, nullable=True)  # List of university names
    desired_cities = Column(
        JSONB, nullable=True
    )  # List of cities: istanbul, ankara, izmir, other

    # RIASEC Test Results
    riasec_answers = Column(JSONB, nullable=True)
    riasec_scores = Column(JSONB, nullable=True)  # {R: x, I: x, A: x, S: x, E: x, C: x}
    suggested_jobs = Column(JSONB, nullable=True)  # Top 3 jobs from RIASEC

    # Final Results
    suggested_programs = Column(JSONB, nullable=True)  # Final 9 program suggestions

    # GPT Debug Info
    gpt_prompt = Column(Text, nullable=True)
    gpt_response = Column(Text, nullable=True)

    # Status
    status = Column(
        String(50), default="started"
    )  # started, step1_completed, step2_completed, riasec_completed, completed

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    high_school_room = relationship("HighSchoolRoom", back_populates="students")
