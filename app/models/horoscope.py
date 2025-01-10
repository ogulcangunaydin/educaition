import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import belongs_to

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
