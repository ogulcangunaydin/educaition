"""
Personality Test Module

This module provides a standalone personality test (Big Five / OCEAN) that can be:
1. Used independently for personality assessment
2. Referenced by DissonanceTest participants
3. Shared via QR code through TestRoom

The test measures five personality traits:
- Extroversion
- Agreeableness
- Conscientiousness
- Negative Emotionality (Neuroticism)
- Open Mindedness
"""

from .models import PersonalityTestParticipant
from .service import PersonalityTestService

__all__ = [
    "PersonalityTestParticipant",
    "PersonalityTestService",
]
