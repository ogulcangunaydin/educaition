import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import has_many, belongs_to

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