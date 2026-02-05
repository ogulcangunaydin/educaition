from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.enums import UniversityKey, UserRole
from app.core.mixins import SoftDeleteMixin


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(
        String(20),
        default=UserRole.STUDENT.value,
        nullable=False,
    )
    university = Column(
        String(20),
        default=UniversityKey.HALIC.value,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    rooms = relationship("Room", back_populates="user")
    dissonance_test_participants = relationship(
        "DissonanceTestParticipant", back_populates="user"
    )
    high_school_rooms = relationship("HighSchoolRoom", back_populates="user")
