from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import DeviceTestCompletion


class DeviceTrackingService:
    """Service for tracking device test completions"""

    @staticmethod
    def has_completed_test(
        db: Session,
        device_id: str,
        test_type: str,
        room_id: int | None = None
    ) -> DeviceTestCompletion | None:
        """
        Check if a device has completed a specific test.
        
        Args:
            db: Database session
            device_id: UUID of the device
            test_type: Type of test (e.g., 'dissonance_test', 'program_suggestion')
            room_id: Optional room/session ID for context
            
        Returns:
            DeviceTestCompletion record if found, None otherwise
        """
        query = db.query(DeviceTestCompletion).filter(
            DeviceTestCompletion.device_id == device_id,
            DeviceTestCompletion.test_type == test_type,
        )
        
        if room_id is not None:
            query = query.filter(DeviceTestCompletion.room_id == room_id)
        else:
            query = query.filter(DeviceTestCompletion.room_id.is_(None))
            
        return query.first()

    @staticmethod
    def mark_test_completed(
        db: Session,
        device_id: str,
        test_type: str,
        room_id: int | None = None
    ) -> DeviceTestCompletion:
        """
        Mark a device as having completed a test.
        
        If the device has already completed this test, returns the existing record.
        
        Args:
            db: Database session
            device_id: UUID of the device
            test_type: Type of test
            room_id: Optional room/session ID
            
        Returns:
            DeviceTestCompletion record (existing or newly created)
        """
        # Check if already exists
        existing = DeviceTrackingService.has_completed_test(
            db, device_id, test_type, room_id
        )
        if existing:
            return existing
        
        # Create new record
        completion = DeviceTestCompletion(
            device_id=device_id,
            test_type=test_type,
            room_id=room_id,
        )
        
        try:
            db.add(completion)
            db.commit()
            db.refresh(completion)
            return completion
        except IntegrityError:
            # Race condition - record was created by another request
            db.rollback()
            return DeviceTrackingService.has_completed_test(
                db, device_id, test_type, room_id
            )

    @staticmethod
    def get_device_completions(
        db: Session,
        device_id: str
    ) -> list[DeviceTestCompletion]:
        """
        Get all test completions for a device.
        
        Args:
            db: Database session
            device_id: UUID of the device
            
        Returns:
            List of DeviceTestCompletion records
        """
        return db.query(DeviceTestCompletion).filter(
            DeviceTestCompletion.device_id == device_id
        ).all()
