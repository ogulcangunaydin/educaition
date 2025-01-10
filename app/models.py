import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .schemas import Theme, Role
from .models.helpers.mixins import SoftDeleteMixin
from .relationships import has_many, has_one, belongs_to

# Association table for many-to-many relationship between users and rooms
user_room_association = Table(
    'user_room_associations',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('room_id', UUID(as_uuid=True), ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
)

class User(Base, AllFeaturesMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    token = Column(String, nullable=True)
    username = Column(String, unique=True, index=True)
    language_id = Column(
        Integer, ForeignKey('languages.id', ondelete='SET NULL'),
        nullable=True
    )
    theme = Column(Enum(Theme), nullable=False)
    role = Column(Enum(Role), nullable=False)
    avatar_color = Column(String, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    language = has_one("Language", back_populates="users")

    admin_rooms = has_many(
        "Room", back_populates="admin_user", foreign_keys="[Room.admin_user_id]",
        cascade="all, delete-orphan"
    )
    participant_rooms = has_many(
        "Room", secondary=user_room_association, back_populates="participants"
    )
  
    big_five_personality = has_one(
        "BigFivePersonality", back_populates="user",
        cascade="all, delete-orphan"
    )
    horoscope = has_one(
        "Horoscope", back_populates="user",
        cascade="all, delete-orphan"
    )
    personal_detail = has_one(
        "PersonalDetail", back_populates="user",
        cascade="all, delete-orphan"
    )
    career_detail = has_one(
        "CareerDetail", back_populates="user",
        cascade="all, delete-orphan"
    )
    dissonance_test_detail = has_one(
        "DissonanceTestDetail", back_populates="user",
        cascade="all, delete-orphan"
    )

class Language(Base, AllFeaturesMixin):
    __tablename__ = 'languages'

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    users = has_many("User", back_populates="language")

class Room(Base, AllFeaturesMixin, SoftDeleteMixin):
    __tablename__ = "rooms"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    admin_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    name = Column(String, nullable=False)

    type = Column(String(50))  # Polymorphic type field
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    admin_user = belongs_to(
        "User", back_populates="admin_rooms", foreign_keys=[admin_user_id]
    )
    participants = has_many(
        "User", secondary=user_room_association, back_populates="participant_rooms"
    )
    sessions = has_many(
        "Session", back_populates="room", cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'room'
    }

class GameRoom(Room):
    # Use the same table as Room
    __tablename__ = None

    __mapper_args__ = {
        'polymorphic_identity': 'game_room'
    }

class TestRoom(Room):
    # Use the same table as Room
    __tablename__ = None

    __mapper_args__ = {
        'polymorphic_identity': 'test_room'
    }

class BigFivePersonality(Base, AllFeaturesMixin):
    __tablename__ = "big_five_personalities"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    extroversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    negative_emotionality = Column(Float, nullable=True)
    open_mindedness = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user = belongs_to(
        "User", back_populates="big_five_personality"
    )

class Horoscope(Base, AllFeaturesMixin):
    __tablename__ = "horoscopes"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    star_sign = Column(String(50), nullable=True)
    rising_sign = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user = belongs_to(
        "User", back_populates="horoscope"
    )

class PersonalDetail(Base, AllFeaturesMixin):
    __tablename__ = "personal_details"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    email = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    education = Column(String(255), nullable=True)
    income = Column(Integer, nullable=True)
    sentiment = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user = belongs_to(
        "User", back_populates="personal_details"
    )

class CareerDetail(Base, AllFeaturesMixin):
    __tablename__ = "career_details"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    job_recommendation = Column(String, nullable=True)
    compatibility_analysis = Column(String, nullable=True)
    workload = Column(Integer, nullable=True)
    career_start = Column(Integer, nullable=True)
    flexibility = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user = belongs_to(
        "User", back_populates="career_details"
    )

class DissonanceTestDetail(Base, AllFeaturesMixin):
    __tablename__ = "dissonance_test_details"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    comfort_question_first_answer = Column(Integer, nullable=True)
    fare_question_first_answer = Column(Integer, nullable=True)
    comfort_question_second_answer = Column(Integer, nullable=True)
    fare_question_second_answer = Column(Integer, nullable=True)
    personality_test_answers = Column(JSONB, nullable=True)
    comfort_question_displayed_average = Column(Float, nullable=True)
    fare_question_displayed_average = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user = belongs_to(
        "User", back_populates="dissonance_test_details"
    )

class Game(Base, AllFeaturesMixin):
    __tablename__ = "games"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    home_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    away_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False
    )
    home_user_score = Column(Integer, default=0)
    away_user_score = Column(Integer, default=0)

    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete='CASCADE'),
        nullable=False
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    home_user = belongs_to("User", foreign_keys=[home_user_id])
    away_user = belongs_to("User", foreign_keys=[away_user_id])
    rounds = has_many(
        "Round", back_populates="game", cascade="all, delete-orphan"
    )
    session = belongs_to("Session", back_populates="games")

class Round(Base, AllFeaturesMixin):
    __tablename__ = "rounds"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    round_number = Column(Integer)
    home_choice = Column(String)
    away_choice = Column(String)
    game_id = Column(
        UUID(as_uuid=True), ForeignKey("games.id", ondelete='CASCADE'),
        nullable=False
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    game = belongs_to("Game", back_populates="rounds")

class Session(Base, AllFeaturesMixin):
    __tablename__ = 'sessions'

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    room_id = Column(
        UUID(as_uuid=True), ForeignKey('rooms.id', ondelete='CASCADE'),
        nullable=False
    )
    name = Column(String, nullable=True)
    status = Column(String, default='started')
    player_ids = Column(String, nullable=True)
    results = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    games = has_many(
        "Game", back_populates="session", cascade="all, delete-orphan"
    )
    room = belongs_to("Room", back_populates="sessions")
