"""
TestRoom Service - Business logic for unified room management.
"""

import bleach
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import TestType
from .models import TestRoom
from .schemas import TestRoomCreate, TestRoomUpdate


class TestRoomService:
    """Service class for TestRoom operations."""

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    @staticmethod
    def create_room(
        db: Session,
        room_data: TestRoomCreate,
        user_id: int,
    ) -> TestRoom:
        """
        Create a new test room.
        
        Args:
            db: Database session
            room_data: Room creation data
            user_id: ID of the user creating the room
            
        Returns:
            Created TestRoom instance
        """
        # Sanitize the name
        clean_name = bleach.clean(room_data.name.strip(), strip=True)
        
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room name cannot be empty",
            )

        room = TestRoom(
            name=clean_name,
            test_type=room_data.test_type.value,
            created_by=user_id,
            settings=room_data.settings or {},
        )
        
        db.add(room)
        db.commit()
        db.refresh(room)
        
        return room

    @staticmethod
    def get_room(db: Session, room_id: int) -> TestRoom:
        """
        Get a single test room by ID.
        
        Args:
            db: Database session
            room_id: Room ID to fetch
            
        Returns:
            TestRoom instance
            
        Raises:
            HTTPException: If room not found
        """
        room = db.query(TestRoom).filter(TestRoom.id == room_id).first()
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test room not found",
            )
            
        return room

    @staticmethod
    def get_room_public(db: Session, room_id: int) -> TestRoom:
        """
        Get public room info (for anonymous access via QR).
        Only returns active rooms.
        
        Args:
            db: Database session
            room_id: Room ID to fetch
            
        Returns:
            TestRoom instance
            
        Raises:
            HTTPException: If room not found or inactive
        """
        room = db.query(TestRoom).filter(
            TestRoom.id == room_id,
            TestRoom.is_active == True,
        ).first()
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test room not found or inactive",
            )
            
        return room

    @staticmethod
    def get_rooms_by_user(
        db: Session,
        user_id: int,
        test_type: TestType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TestRoom], int]:
        """
        Get all rooms created by a user, optionally filtered by test type.
        
        Args:
            db: Database session
            user_id: User ID to filter by
            test_type: Optional test type filter
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (list of TestRoom instances, total count)
        """
        query = db.query(TestRoom).filter(TestRoom.created_by == user_id)
        
        if test_type:
            query = query.filter(TestRoom.test_type == test_type.value)
        
        total = query.count()
        rooms = query.order_by(TestRoom.created_at.desc()).offset(skip).limit(limit).all()
        
        return rooms, total

    @staticmethod
    def get_rooms_by_type(
        db: Session,
        test_type: TestType,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TestRoom], int]:
        """
        Get all rooms of a specific test type (admin use).
        
        Args:
            db: Database session
            test_type: Test type to filter by
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (list of TestRoom instances, total count)
        """
        query = db.query(TestRoom).filter(TestRoom.test_type == test_type.value)
        
        total = query.count()
        rooms = query.order_by(TestRoom.created_at.desc()).offset(skip).limit(limit).all()
        
        return rooms, total

    @staticmethod
    def update_room(
        db: Session,
        room_id: int,
        room_data: TestRoomUpdate,
        user_id: int,
    ) -> TestRoom:
        """
        Update a test room.
        
        Args:
            db: Database session
            room_id: Room ID to update
            room_data: Update data
            user_id: ID of user making the update (for authorization)
            
        Returns:
            Updated TestRoom instance
            
        Raises:
            HTTPException: If room not found or user not authorized
        """
        room = TestRoomService.get_room(db, room_id)
        
        # Check authorization
        if room.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this room",
            )
        
        # Update fields
        if room_data.name is not None:
            clean_name = bleach.clean(room_data.name.strip(), strip=True)
            if clean_name:
                room.name = clean_name
                
        if room_data.is_active is not None:
            room.is_active = room_data.is_active
            
        if room_data.settings is not None:
            # Merge settings instead of replacing
            current_settings = room.settings or {}
            current_settings.update(room_data.settings)
            room.settings = current_settings
        
        db.commit()
        db.refresh(room)
        
        return room

    @staticmethod
    def delete_room(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> TestRoom:
        """
        Soft delete a test room.
        
        Args:
            db: Database session
            room_id: Room ID to delete
            user_id: ID of user making the deletion (for authorization)
            
        Returns:
            Deleted TestRoom instance
            
        Raises:
            HTTPException: If room not found or user not authorized
        """
        room = TestRoomService.get_room(db, room_id)
        
        # Check authorization
        if room.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this room",
            )
        
        room.soft_delete()
        db.commit()
        
        return room

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    @staticmethod
    def toggle_active(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> TestRoom:
        """Toggle the active status of a room."""
        room = TestRoomService.get_room(db, room_id)
        
        if room.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this room",
            )
        
        room.is_active = not room.is_active
        db.commit()
        db.refresh(room)
        
        return room

    @staticmethod
    def verify_room_ownership(
        db: Session,
        room_id: int,
        user_id: int,
    ) -> TestRoom:
        """
        Verify that a user owns a room.
        
        Args:
            db: Database session
            room_id: Room ID to verify
            user_id: User ID to check ownership against
            
        Returns:
            TestRoom instance if user owns the room
            
        Raises:
            HTTPException: If room not found or user doesn't own it
        """
        room = TestRoomService.get_room(db, room_id)
        
        if room.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this room",
            )
            
        return room

    @staticmethod
    def get_room_by_legacy_id(
        db: Session,
        legacy_room_id: int,
        legacy_table: str,
    ) -> TestRoom | None:
        """
        Find a room by its legacy ID (for migration support).
        
        Args:
            db: Database session
            legacy_room_id: Original room ID
            legacy_table: Original table name ('rooms' or 'high_school_rooms')
            
        Returns:
            TestRoom instance or None if not found
        """
        return db.query(TestRoom).filter(
            TestRoom.legacy_room_id == legacy_room_id,
            TestRoom.legacy_table == legacy_table,
        ).first()
