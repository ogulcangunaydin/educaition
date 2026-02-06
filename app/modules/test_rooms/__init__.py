"""
Test Rooms Module

Unified room management for all test types.
"""

from .models import TestRoom
from .service import TestRoomService

__all__ = ["TestRoom", "TestRoomService"]
