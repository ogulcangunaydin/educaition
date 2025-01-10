import uuid
from sqlalchemy import Column, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from ..database import Base
from .helpers.relationships import has_many, belongs_to

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
