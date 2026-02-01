"""
Schema re-exports for backward compatibility.
New code should import directly from app.modules.<module>.schemas
"""

from pydantic import BaseModel

from app.modules.auth.schemas import (
    PasswordRequirements,
    Token,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from app.modules.users.schemas import (
    UniversityKeyEnum,
    User,
    UserBase,
    UserCreate,
    UserRoleEnum,
    UserUpdate,
)
from app.modules.rooms.schemas import (
    Room,
    RoomBase,
    RoomCreate,
    SessionBase,
    SessionCreate,
)
from app.modules.players.schemas import (
    Player,
    PlayerBase,
    PlayerCreate,
)
from app.modules.games.schemas import (
    Game,
    GameBase,
    GameCreate,
    Round,
    RoundBase,
    RoundCreate,
)
from app.modules.dissonance_test.schemas import (
    DissonanceTestParticipant,
    DissonanceTestParticipantBase,
    DissonanceTestParticipantCreate,
    DissonanceTestParticipantResult,
    DissonanceTestParticipantUpdateSecond,
)
from app.modules.high_school_rooms.schemas import (
    HighSchoolRoom,
    HighSchoolRoomBase,
    HighSchoolRoomCreate,
)
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


class ParticipantSessionResponse(BaseModel):
    participant_id: int
    session_token: str
    expires_in: int
