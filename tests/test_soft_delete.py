#!/usr/bin/env python3
"""Test script to verify soft delete implementation."""

import sys
sys.path.insert(0, '/Users/ogulcangunaydin/Projects/educaition')

from app.core.mixins import SoftDeleteMixin, SOFT_DELETE_CASCADE_RELATIONSHIPS
from app.modules.rooms.models import Room
from app.modules.users.models import User
from app.modules.players.models import Player
from app.modules.games.models import Session
from app.modules.dissonance_test.models import DissonanceTestParticipant
from app.modules.high_school_rooms.models import HighSchoolRoom
from app.modules.program_suggestion.models import ProgramSuggestionStudent

# Verify mixin is applied to all 7 models
models_with_soft_delete = [
    ("User", User),
    ("Room", Room),
    ("Player", Player),
    ("Session", Session),
    ("DissonanceTestParticipant", DissonanceTestParticipant),
    ("HighSchoolRoom", HighSchoolRoom),
    ("ProgramSuggestionStudent", ProgramSuggestionStudent),
]

print("=" * 60)
print("SOFT DELETE VERIFICATION")
print("=" * 60)

print("\n1. SoftDeleteMixin applied to models:")
all_ok = True
for name, model in models_with_soft_delete:
    has_mixin = hasattr(model, "soft_delete") and hasattr(model, "deleted_at")
    status = "✓" if has_mixin else "✗"
    print(f"   {status} {name}")
    if not has_mixin:
        all_ok = False

print("\n2. Cascade relationships configured:")
for table, rels in SOFT_DELETE_CASCADE_RELATIONSHIPS.items():
    rel_names = [r[0] for r in rels]
    print(f"   {table} -> {', '.join(rel_names)}")

print("\n3. Relationship chain:")
print("   User")
print("   ├── rooms -> players, sessions")
print("   ├── dissonance_test_participants")
print("   └── high_school_rooms -> students")

print("\n" + "=" * 60)
if all_ok:
    print("All checks passed! ✓")
else:
    print("Some checks failed! ✗")
print("=" * 60)
