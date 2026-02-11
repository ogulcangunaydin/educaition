from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.mixins import SoftDeleteMixin


class ProgramSuggestionStudent(Base, SoftDeleteMixin):
    __tablename__ = "program_suggestion_students"

    id = Column(Integer, primary_key=True, index=True)
    
    # New unified test room reference
    test_room_id = Column(
        Integer, ForeignKey("test_rooms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Legacy field - kept for backward compatibility, will be removed later
    high_school_room_id = Column(
        Integer, ForeignKey("high_school_rooms.id"), nullable=True, index=True
    )

    # Device tracking for duplicate prevention
    device_fingerprint = Column(String(255), nullable=True, index=True)

    # Step 1.1 - Personal Info
    name = Column(String(100), nullable=True)
    birth_year = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)

    # Step 1.2 - Education Info
    class_year = Column(String(20), nullable=True)
    will_take_exam = Column(Boolean, default=True)
    average_grade = Column(Float, nullable=True)
    area = Column(String(50), nullable=True)
    wants_foreign_language = Column(Boolean, default=False)

    # Step 1.3 - Score Expectations
    expected_score_min = Column(Float, nullable=True)
    expected_score_max = Column(Float, nullable=True)
    expected_score_distribution = Column(String(20), nullable=True)
    alternative_area = Column(String(50), nullable=True)
    alternative_score_min = Column(Float, nullable=True)
    alternative_score_max = Column(Float, nullable=True)
    alternative_score_distribution = Column(String(20), nullable=True)

    # Step 1.4 - Preferences
    preferred_language = Column(String(50), nullable=True)
    desired_universities = Column(JSONB, nullable=True)
    desired_cities = Column(JSONB, nullable=True)

    # RIASEC Test Results
    riasec_answers = Column(JSONB, nullable=True)
    riasec_scores = Column(JSONB, nullable=True)
    suggested_jobs = Column(JSONB, nullable=True)

    # Final Results
    suggested_programs = Column(JSONB, nullable=True)  # flat list (backward compat)
    program_groups = Column(JSONB, nullable=True)  # NEW: grouped by program name
    alternative_jobs = Column(JSONB, nullable=True)  # NEW: alt area jobs
    alternative_program_groups = Column(JSONB, nullable=True)  # NEW: alt area groups

    # GPT Debug Info
    gpt_prompt = Column(Text, nullable=True)
    gpt_response = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="started")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    test_room = relationship("TestRoom", backref="program_suggestion_students")
    high_school_room = relationship("HighSchoolRoom", back_populates="students")
    interaction_logs = relationship(
        "ProgramInteractionLog", back_populates="student", cascade="all, delete-orphan"
    )


class ProgramInteractionLog(Base):
    """Tracks student interactions with suggested programs (google search, add to basket)."""

    __tablename__ = "program_interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("program_suggestion_students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(50), nullable=False)  # google_search, add_to_basket
    program_name = Column(String(255), nullable=False)
    university = Column(String(255), nullable=False)
    scholarship = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    student = relationship("ProgramSuggestionStudent", back_populates="interaction_logs")
