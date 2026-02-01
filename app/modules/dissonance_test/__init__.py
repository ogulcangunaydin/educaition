"""
Dissonance Test module - Cognitive dissonance test management.

This module handles:
- Dissonance test participant CRUD
- Personality trait calculations
- Job recommendations and compatibility analysis
"""

from .router import router as dissonance_test_router, dissonance_test_public_router
from .schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantBase,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateSecond,
)
from .service import DissonanceTestService

__all__ = [
    "dissonance_test_router",
    "dissonance_test_public_router",
    "DissonanceTestService",
    "DissonanceTestParticipant",
    "DissonanceTestParticipantBase",
    "DissonanceTestParticipantCreate",
    "DissonanceTestParticipantResult",
    "DissonanceTestParticipantUpdateSecond",
]
