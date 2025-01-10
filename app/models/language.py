import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import has_many

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
