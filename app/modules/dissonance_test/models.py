from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.mixins import SoftDeleteMixin


class DissonanceTestParticipant(Base, SoftDeleteMixin):
    __tablename__ = "dissonance_test_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=True)
    student_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    education = Column(String(255), nullable=True)
    income = Column(Integer, nullable=True)
    sentiment = Column(Integer, nullable=True)
    comfort_question_first_answer = Column(Integer, nullable=True)
    fare_question_first_answer = Column(Integer, nullable=True)
    comfort_question_second_answer = Column(Integer, nullable=True)
    fare_question_second_answer = Column(Integer, nullable=True)
    extroversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    negative_emotionality = Column(Float, nullable=True)
    open_mindedness = Column(Float, nullable=True)
    job_recommendation = Column(String, nullable=True)
    compatibility_analysis = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    test_room_id = Column(
        Integer,
        ForeignKey("test_rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # The student (anonymous or real) who took the test
    student_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workload = Column(Integer, nullable=True)
    career_start = Column(Integer, nullable=True)
    flexibility = Column(Integer, nullable=True)
    star_sign = Column(String(50), nullable=True)
    rising_sign = Column(String(50), nullable=True)
    personality_test_answers = Column(JSONB, nullable=True)
    comfort_question_displayed_average = Column(Float, nullable=True)
    fare_question_displayed_average = Column(Float, nullable=True)
    device_fingerprint = Column(String(255), nullable=True, index=True)
    has_completed = Column(Integer, nullable=True, default=0)

    user = relationship("User", back_populates="dissonance_test_participants", foreign_keys=[user_id])
    student_user = relationship("User", foreign_keys=[student_user_id])
