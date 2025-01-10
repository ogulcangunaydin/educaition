import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .schemas import Theme, Role
from .helpers.mixins import SoftDeleteMixin
from .helpers.relationships import has_many, has_one

class User(Base, AllFeaturesMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    token = Column(String, nullable=True)
    username = Column(String, unique=False, index=True)
    language_id = Column(
        UUID(as_uuid=True), ForeignKey('languages.id', ondelete='SET NULL'),
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
        "Room", secondary="user_room_association", back_populates="participants"
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
