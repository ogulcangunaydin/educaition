from app.dependencies.auth import (
    CurrentActiveUser,
    CurrentUser,
    DbSession,
    OptionalUser,
    get_current_active_user,
    get_current_user,
    get_current_user_optional,
    get_db,
    oauth2_scheme,
    require_user_ownership,
)
from app.dependencies.participant import (
    CurrentParticipant,
    CurrentPlayer,
    CurrentProgramStudent,
    CurrentTestParticipant,
    get_current_participant,
    get_player,
    get_program_student,
    get_test_participant,
    verify_participant_ownership,
)

__all__ = [
    # Auth dependencies
    "get_db",
    "DbSession",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
    "CurrentUser",
    "CurrentActiveUser",
    "OptionalUser",
    "require_user_ownership",
    "oauth2_scheme",
    # Participant dependencies
    "get_current_participant",
    "get_player",
    "get_test_participant",
    "get_program_student",
    "CurrentParticipant",
    "CurrentPlayer",
    "CurrentTestParticipant",
    "CurrentProgramStudent",
    "verify_participant_ownership",
]
