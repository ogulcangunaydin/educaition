import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.mixins import SoftDeleteMixin
from .helpers.relationships import has_many, belongs_to

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
        "User", secondary="user_room_association", back_populates="participant_rooms"
    )
    sessions = has_many(
        "Session", back_populates="room", cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'room'
    }
