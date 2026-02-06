"""
PersonalityTest Database Models

This module defines the data models for the personality test system.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.mixins import SoftDeleteMixin


class PersonalityTestParticipant(Base, SoftDeleteMixin):
    """
    Stores personality test participant data and results.
    
    This is a standalone model that can be used independently or
    referenced by other test participants (like DissonanceTest).
    
    Attributes:
        id: Primary key
        test_room_id: Reference to unified TestRoom (nullable for legacy data)
        user_id: Owner of this participant data (teacher/admin who created the room)
        
        # Demographics
        email: Participant email (optional)
        age: Participant age
        gender: Participant gender
        education: Education level
        income: Income level (optional)
        
        # Astrological info (used for compatibility analysis)
        star_sign: Zodiac sign
        rising_sign: Rising sign
        
        # Career preferences
        workload: Preferred workload level (1-10)
        career_start: Career start preference (1-10)
        flexibility: Work flexibility preference (1-10)
        
        # Personality Test Results
        personality_test_answers: Raw answers as JSONB
        extroversion: Big Five trait score (0-1)
        agreeableness: Big Five trait score (0-1)
        conscientiousness: Big Five trait score (0-1)
        negative_emotionality: Big Five trait score (0-1)
        open_mindedness: Big Five trait score (0-1)
        
        # Analysis Results
        job_recommendation: AI-generated job recommendation
        compatibility_analysis: Astrological compatibility analysis
        
        # Device tracking
        device_fingerprint: Browser fingerprint for tracking
        device_info: Additional device information
    """
    
    __tablename__ = "personality_test_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Room and owner references
    test_room_id = Column(
        Integer, 
        ForeignKey("test_rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, 
        index=True,
    )
    # The student (anonymous or real) who took the test
    student_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Demographics
    full_name = Column(String(255), nullable=True)
    student_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    education = Column(String(255), nullable=True)
    income = Column(Integer, nullable=True)
    
    # Astrological
    star_sign = Column(String(50), nullable=True)
    rising_sign = Column(String(50), nullable=True)
    
    # Career preferences
    workload = Column(Integer, nullable=True)
    career_start = Column(Integer, nullable=True)
    flexibility = Column(Integer, nullable=True)
    
    # Personality test raw answers
    personality_test_answers = Column(JSONB, nullable=True)
    
    # Personality trait scores (Big Five / OCEAN)
    extroversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    negative_emotionality = Column(Float, nullable=True)
    open_mindedness = Column(Float, nullable=True)
    
    # Analysis results
    job_recommendation = Column(String, nullable=True)
    compatibility_analysis = Column(String, nullable=True)
    
    # Device tracking
    device_fingerprint = Column(String(255), nullable=True, index=True)
    device_info = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="personality_test_participants", foreign_keys=[user_id])
    student_user = relationship("User", foreign_keys=[student_user_id])
    test_room = relationship("TestRoom", back_populates="personality_test_participants")

    def has_completed_test(self) -> bool:
        """Check if participant has completed the personality test."""
        return self.personality_test_answers is not None and self.extroversion is not None

    def get_personality_summary(self) -> dict:
        """Get a summary of personality traits."""
        return {
            "extroversion": self.extroversion,
            "agreeableness": self.agreeableness,
            "conscientiousness": self.conscientiousness,
            "negative_emotionality": self.negative_emotionality,
            "open_mindedness": self.open_mindedness,
        }
