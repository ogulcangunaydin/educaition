from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.services.password_service import (
    PasswordConfig,
    validate_password_strength,
)

# Re-export auth schemas for backward compatibility
from app.modules.auth.schemas import (
    PasswordRequirements,
    Token,
    TokenRefreshRequest,
    TokenRefreshResponse,
)

# Re-export user schemas for backward compatibility
from app.modules.users.schemas import (
    User,
    UserBase,
    UserCreate,
    UserRoleEnum,
    UserUpdate,
    UniversityKeyEnum,
)

# Re-export room schemas for backward compatibility
from app.modules.rooms.schemas import (
    Room,
    RoomBase,
    RoomCreate,
    SessionBase,
    SessionCreate,
)

# Re-export player schemas for backward compatibility
from app.modules.players.schemas import (
    Player,
    PlayerBase,
    PlayerCreate,
)

# Re-export game schemas for backward compatibility
from app.modules.games.schemas import (
    Game,
    GameBase,
    GameCreate,
    Round,
    RoundBase,
    RoundCreate,
)

# Re-export dissonance test schemas for backward compatibility
from app.modules.dissonance_test.schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantBase,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateSecond,
)


def _validate_password_field(password: str) -> str:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password


# UserRoleEnum, UniversityKeyEnum, UserBase, UserCreate, UserUpdate, User
# moved to app.modules.users.schemas (re-exported above for compatibility)

# Token, TokenRefreshRequest, TokenRefreshResponse, PasswordRequirements
# moved to app.modules.auth.schemas (re-exported above for compatibility)

# Room, RoomBase, RoomCreate, SessionBase, SessionCreate
# moved to app.modules.rooms.schemas (re-exported above for compatibility)

# Player, PlayerBase, PlayerCreate
# moved to app.modules.players.schemas (re-exported above for compatibility)

# Game, GameBase, GameCreate, Round, RoundBase, RoundCreate
# moved to app.modules.games.schemas (re-exported above for compatibility)

# DissonanceTestParticipant, DissonanceTestParticipantBase, DissonanceTestParticipantCreate,
# DissonanceTestParticipantResult, DissonanceTestParticipantUpdateSecond
# moved to app.modules.dissonance_test.schemas (re-exported above for compatibility)

# Re-export high school room schemas for backward compatibility
from app.modules.high_school_rooms.schemas import (
    HighSchoolRoom,
    HighSchoolRoomBase,
    HighSchoolRoomCreate,
)

# Re-export program suggestion schemas for backward compatibility
from app.modules.program_suggestion.schemas import (
    ProgramSuggestionStudent,
    ProgramSuggestionStudentBase,
    ProgramSuggestionStudentCreate,
    ProgramSuggestionStudentDebug,
    ProgramSuggestionStudentResult,
    ProgramSuggestionStudentUpdateRiasec,
    ProgramSuggestionStudentUpdateStep1,
    ProgramSuggestionStudentUpdateStep2,
    ProgramSuggestionStudentUpdateStep3,
    ProgramSuggestionStudentUpdateStep4,
)

# HighSchoolRoom, HighSchoolRoomBase, HighSchoolRoomCreate
# moved to app.modules.high_school_rooms.schemas (re-exported above for compatibility)

# ProgramSuggestionStudent, ProgramSuggestionStudentBase, ProgramSuggestionStudentCreate,
# ProgramSuggestionStudentDebug, ProgramSuggestionStudentResult, etc.
# moved to app.modules.program_suggestion.schemas (re-exported above for compatibility)


class ParticipantSessionResponse(BaseModel):
    participant_id: int
    session_token: str
    expires_in: int
