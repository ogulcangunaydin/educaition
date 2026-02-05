#!/usr/bin/env python3
"""Test script to verify input validation implementation."""

import sys
sys.path.insert(0, '/Users/ogulcangunaydin/Projects/educaition')

from pydantic import ValidationError

from app.modules.users.schemas import UserCreate, UserUpdate
from app.modules.rooms.schemas import RoomCreate
from app.modules.players.schemas import PlayerCreate
from app.modules.high_school_rooms.schemas import HighSchoolRoomCreate
from app.modules.dissonance_test.schemas import DissonanceTestParticipantCreate
from app.modules.program_suggestion.schemas import (
    ProgramSuggestionStudentUpdateStep1,
    ProgramSuggestionStudentUpdateRiasec,
)
from app.modules.games.schemas import GameBase

print("=" * 60)
print("INPUT VALIDATION TESTS")
print("=" * 60)

print("\n1. All schemas imported successfully!")

errors = []

# Test username too short
try:
    UserCreate(username='ab', password='TestPass123!', email='test@test.com')
    errors.append("Username too short should be rejected")
except ValidationError:
    print("✓ Username too short rejected")

# Test username starting with number
try:
    UserCreate(username='123user', password='TestPass123!', email='test@test.com')
    errors.append("Username starting with number should be rejected")
except ValidationError:
    print("✓ Username starting with number rejected")

# Test invalid email format
try:
    UserCreate(username='testuser', password='TestPass123!', email='invalid-email')
    errors.append("Invalid email should be rejected")
except ValidationError:
    print("✓ Invalid email format rejected")

# Test valid user creation
try:
    user = UserCreate(username='testuser', password='TestPass123!', email='test@example.com')
    print(f"✓ Valid user created: {user.username}")
except ValidationError as e:
    errors.append(f"Valid user creation failed: {e}")

# Test XSS sanitization in room name
room = RoomCreate(name='  <script>alert(1)</script>  ')
if '<script>' not in room.name:
    print(f"✓ XSS sanitized in room name: {room.name!r}")
else:
    errors.append("XSS not sanitized in room name")

# Test field length limits
try:
    RoomCreate(name='a' * 200)  # Exceeds NAME_MAX (100)
    errors.append("Room name too long should be rejected")
except ValidationError:
    print("✓ Room name too long rejected")

# Test age constraints in dissonance test
try:
    DissonanceTestParticipantCreate(user_id=1, age=200)
    errors.append("Age > 150 should be rejected")
except ValidationError:
    print("✓ Invalid age rejected")

# Test score constraints
try:
    ProgramSuggestionStudentUpdateStep1(name='Test', birth_year=1800, gender='M')
    errors.append("Birth year < 1950 should be rejected")
except ValidationError:
    print("✓ Invalid birth year rejected")

# Test RIASEC validation
try:
    ProgramSuggestionStudentUpdateRiasec(riasec_answers={'q1': 10})  # Score > 5
    errors.append("RIASEC score > 5 should be rejected")
except ValidationError:
    print("✓ Invalid RIASEC score rejected")

# Test valid RIASEC
riasec = ProgramSuggestionStudentUpdateRiasec(riasec_answers={'q1': 3, 'q2': 4})
print(f"✓ Valid RIASEC answers: {riasec.riasec_answers}")

# Test game score constraint
try:
    GameBase(home_player_id=1, away_player_id=2, home_player_score=-5, away_player_score=0, session_id=1)
    errors.append("Negative score should be rejected")
except ValidationError:
    print("✓ Negative game score rejected")

print("\n" + "=" * 60)
if errors:
    print("FAILURES:")
    for error in errors:
        print(f"  ✗ {error}")
else:
    print("All validation tests passed! ✓")
print("=" * 60)
