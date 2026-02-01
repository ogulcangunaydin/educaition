"""
Rooms module - Game room management.

This module handles:
- Room CRUD operations
- Session management
- Game results
"""

from .router import router as rooms_router
from .schemas import Room, RoomBase, RoomCreate, SessionBase, SessionCreate
from .service import RoomService

__all__ = [
    "rooms_router",
    "RoomService",
    "Room",
    "RoomBase",
    "RoomCreate",
    "SessionBase",
    "SessionCreate",
]
