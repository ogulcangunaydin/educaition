import uuid
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import belongs_to

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
