"""
High School Rooms module - High school room management for program suggestions.

This module handles:
- High school room CRUD operations
- Room-student associations
"""

from .router import router as high_school_rooms_router
from .schemas import (
    HighSchoolRoom,
    HighSchoolRoomBase,
    HighSchoolRoomCreate,
)
from .service import HighSchoolRoomService

__all__ = [
    "high_school_rooms_router",
    "HighSchoolRoomService",
    "HighSchoolRoom",
    "HighSchoolRoomBase",
    "HighSchoolRoomCreate",
]
