import uuid
from sqlalchemy import Column, ForeignKey, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_mixins import AllFeaturesMixin
from .database import Base
from .helpers.relationships import belongs_to

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
    
    comfort_question_displayed_average = Column(Float, nullable=True)
    fare_question_displayed_average = Column(Float, nullable=True)

    personality_test_answers = Column(JSONB, nullable=True)
    
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
