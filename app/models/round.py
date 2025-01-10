import uuid
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import belongs_to

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
