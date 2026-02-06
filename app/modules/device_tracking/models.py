from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class DeviceTestCompletion(Base):
    """
    Tracks which devices have completed which tests to prevent anonymous users
    from retaking tests by clearing their browser localStorage.
    
    Device ID is a UUID generated on the client side and stored in localStorage.
    This provides server-side validation for test completion status.
    """
    __tablename__ = "device_test_completions"

    id = Column(Integer, primary_key=True, index=True)
    
    # SHA-256 fingerprint hash generated from browser/device signals
    device_id = Column(String(64), nullable=False, index=True)
    
    # Type of test completed (e.g., 'dissonance_test', 'program_suggestion', 'prisoners_dilemma')
    test_type = Column(String(50), nullable=False, index=True)
    
    # Optional reference to the room/session ID for additional context
    room_id = Column(Integer, nullable=True, index=True)
    
    # Timestamp when the test was completed
    completed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint('device_id', 'test_type', 'room_id', name='uq_device_test_room'),
    )
