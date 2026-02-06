"""
TestRoom Model - Unified room management for all test types.

This model replaces the separate Room (prisoners_dilemma) and HighSchoolRoom
(program_suggestion) models with a unified structure that supports all test types.

Features:
- Single table for all test rooms
- Test-type specific settings via JSONB column
- Soft delete support
- Participant count tracking
- Legacy ID mapping for migration
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import TestType
from app.core.mixins import SoftDeleteMixin


class TestRoom(Base, SoftDeleteMixin):
    """
    Unified room model for all test types.
    
    Attributes:
        id: Primary key
        name: Display name for the room
        test_type: Type of test (prisoners_dilemma, dissonance_test, etc.)
        created_by: User ID who created the room
        is_active: Whether the room is currently accepting participants
        settings: Test-specific configuration (JSONB)
        legacy_room_id: Original room ID for migration tracking
        legacy_table: Original table name for migration tracking
    
    Settings examples by test type:
        prisoners_dilemma: {"rounds": 10, "max_players": 20}
        program_suggestion: {"high_school_code": "123456"}
        dissonance_test: {"include_personality_test": true}
        personality_test: {"test_version": "big5"}
    """
    __tablename__ = "test_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    test_type = Column(
        String(50),
        nullable=False,
        index=True,
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Test-specific settings stored as JSON
    settings = Column(JSONB, nullable=True, default=dict)
    
    # For data migration - track original room IDs
    legacy_room_id = Column(Integer, nullable=True, index=True)
    legacy_table = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="test_rooms")
    
    # Test-specific participant relationships
    personality_test_participants = relationship(
        "PersonalityTestParticipant", 
        back_populates="test_room",
        cascade="all, delete-orphan",
    )
    # Future: Add other participant relationships as modules are migrated
    # prisoners_dilemma_players = relationship(...)
    # dissonance_test_participants = relationship(...)
    # program_suggestion_students = relationship(...)

    def __repr__(self):
        return f"<TestRoom(id={self.id}, name='{self.name}', type='{self.test_type}')>"

    @property
    def is_prisoners_dilemma(self) -> bool:
        return self.test_type == TestType.PRISONERS_DILEMMA.value

    @property
    def is_dissonance_test(self) -> bool:
        return self.test_type == TestType.DISSONANCE_TEST.value

    @property
    def is_program_suggestion(self) -> bool:
        return self.test_type == TestType.PROGRAM_SUGGESTION.value

    @property
    def is_personality_test(self) -> bool:
        return self.test_type == TestType.PERSONALITY_TEST.value

    def get_setting(self, key: str, default=None):
        """Safely get a setting value."""
        if self.settings is None:
            return default
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        """Safely set a setting value."""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value
