"""
TestRoom Router - API endpoints for unified room management.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.enums import TestType
from app.dependencies.auth import (
    TeacherOrAdmin,
    get_current_active_user,
    get_db,
)
from app.modules.users.models import User

from .schemas import (
    TestRoomCreate,
    TestRoomList,
    TestRoomPublicInfo,
    TestRoomResponse,
    TestRoomUpdate,
)
from .service import TestRoomService


# =============================================================================
# PUBLIC ROUTER (No authentication required)
# =============================================================================

public_router = APIRouter(
    prefix="/test-rooms",
    tags=["test_rooms"],
)


@public_router.get(
    "/{room_id}/public",
    response_model=TestRoomPublicInfo,
)
def get_room_public_info(
    room_id: int,
    db: Session = Depends(get_db),
):
    """
    Get public information about a test room.
    Used by anonymous users accessing tests via QR code.
    Only returns active rooms.
    """
    return TestRoomService.get_room_public(db, room_id)


# =============================================================================
# PROTECTED ROUTER (Authentication required)
# =============================================================================

router = APIRouter(
    prefix="/test-rooms",
    tags=["test_rooms"],
    dependencies=[Depends(get_current_active_user)],
)


@router.post(
    "/",
    response_model=TestRoomResponse,
    status_code=201,
)
def create_room(
    room_data: TestRoomCreate,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """
    Create a new test room.
    Only teachers and admins can create rooms.
    """
    return TestRoomService.create_room(db, room_data, current_user.id)


@router.get(
    "/",
    response_model=TestRoomList,
)
def list_my_rooms(
    current_user: TeacherOrAdmin,
    test_type: TestType | None = Query(default=None, description="Filter by test type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all test rooms created by the current user.
    Optionally filter by test type.
    """
    rooms, total = TestRoomService.get_rooms_by_user(
        db,
        current_user.id,
        test_type=test_type,
        skip=skip,
        limit=limit,
    )
    return TestRoomList(
        items=rooms,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/by-type/{test_type}",
    response_model=TestRoomList,
)
def list_rooms_by_type(
    test_type: TestType,
    current_user: TeacherOrAdmin,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all rooms of a specific test type owned by current user.
    """
    rooms, total = TestRoomService.get_rooms_by_user(
        db,
        current_user.id,
        test_type=test_type,
        skip=skip,
        limit=limit,
    )
    return TestRoomList(
        items=rooms,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{room_id}",
    response_model=TestRoomResponse,
)
def get_room(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """
    Get details of a specific test room.
    User must own the room.
    """
    return TestRoomService.verify_room_ownership(db, room_id, current_user.id)


@router.put(
    "/{room_id}",
    response_model=TestRoomResponse,
)
def update_room(
    room_id: int,
    room_data: TestRoomUpdate,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """
    Update a test room.
    User must own the room.
    """
    return TestRoomService.update_room(db, room_id, room_data, current_user.id)


@router.delete(
    "/{room_id}",
    response_model=TestRoomResponse,
)
def delete_room(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """
    Soft delete a test room.
    User must own the room.
    """
    return TestRoomService.delete_room(db, room_id, current_user.id)


@router.post(
    "/{room_id}/toggle-active",
    response_model=TestRoomResponse,
)
def toggle_room_active(
    room_id: int,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
):
    """
    Toggle the active status of a test room.
    When inactive, the room won't accept new participants.
    """
    return TestRoomService.toggle_active(db, room_id, current_user.id)
