#!/usr/bin/env python3
"""Verify the room migration to test_rooms table."""

from app.core.database import SessionLocal
from app.modules.test_rooms.models import TestRoom
from app.modules.rooms.models import Room
from app.modules.high_school_rooms.models import HighSchoolRoom
from sqlalchemy import func

db = SessionLocal()

# Count rooms
old_rooms = db.query(Room).count()
old_hs_rooms = db.query(HighSchoolRoom).count()
test_rooms = db.query(TestRoom).count()
migrated = db.query(TestRoom).filter(TestRoom.legacy_room_id.isnot(None)).count()

print(f"Old Rooms (prisoners_dilemma): {old_rooms}")
print(f"Old HighSchoolRooms (program_suggestion): {old_hs_rooms}")
print(f"Test Rooms total: {test_rooms}")
print(f"Migrated from legacy: {migrated}")

# Show test room types
by_type = db.query(TestRoom.test_type, func.count(TestRoom.id)).group_by(TestRoom.test_type).all()
print("\nBy test type:")
for t, c in by_type:
    print(f"  {t}: {c}")

db.close()
