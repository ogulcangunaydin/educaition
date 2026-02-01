from typing import Annotated
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from app.services.participant_token_service import (
    ParticipantTokenError,
    ParticipantTokenExpiredError,
    ParticipantTokenInvalidError,
    ParticipantTokenPayload,
    ParticipantType,
    verify_participant_token,
)

def _extract_participant_token(
    authorization: str | None = Header(None),
    participant_token: str | None = Cookie(None),
) -> str | None:
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    return participant_token


async def get_current_participant(
    request: Request,
    token: str | None = Depends(_extract_participant_token),
) -> ParticipantTokenPayload:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token required",
            headers={"X-Token-Required": "participant"},
        )

    try:
        payload = verify_participant_token(token)

        # Store in request state for downstream use
        request.state.participant_id = payload.participant_id
        request.state.participant_type = payload.participant_type
        request.state.room_id = payload.room_id

        return payload

    except ParticipantTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please rejoin.",
            headers={"X-Token-Expired": "true"},
        )
    except ParticipantTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except ParticipantTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )

async def get_player(
    request: Request,
    token: str | None = Depends(_extract_participant_token),
) -> ParticipantTokenPayload:

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player session token required",
        )

    try:
        payload = verify_participant_token(token, expected_type=ParticipantType.PLAYER)

        request.state.participant_id = payload.participant_id
        request.state.player_id = payload.participant_id
        request.state.room_id = payload.room_id

        return payload

    except ParticipantTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Game session has expired",
        )
    except ParticipantTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )

async def get_test_participant(
    request: Request,
    token: str | None = Depends(_extract_participant_token),
) -> ParticipantTokenPayload:

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Test session token required",
        )

    try:
        payload = verify_participant_token(
            token, expected_type=ParticipantType.DISSONANCE_TEST
        )

        request.state.participant_id = payload.participant_id
        request.state.room_id = payload.room_id

        return payload

    except ParticipantTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Test session has expired. Please start a new test.",
        )
    except ParticipantTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )

async def get_program_student(
    request: Request,
    token: str | None = Depends(_extract_participant_token),
) -> ParticipantTokenPayload:

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student session token required",
        )

    try:
        payload = verify_participant_token(
            token, expected_type=ParticipantType.PROGRAM_SUGGESTION
        )

        request.state.participant_id = payload.participant_id
        request.state.student_id = payload.participant_id
        request.state.high_school_room_id = payload.room_id

        return payload

    except ParticipantTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please rejoin from the room link.",
        )
    except ParticipantTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )

CurrentParticipant = Annotated[
    ParticipantTokenPayload, Depends(get_current_participant)
]
CurrentPlayer = Annotated[ParticipantTokenPayload, Depends(get_player)]
CurrentTestParticipant = Annotated[
    ParticipantTokenPayload, Depends(get_test_participant)
]
CurrentProgramStudent = Annotated[ParticipantTokenPayload, Depends(get_program_student)]

def verify_participant_ownership(
    token_participant_id: int,
    url_participant_id: int,
) -> None:

    if token_participant_id != url_participant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this participant's data",
        )

__all__ = [
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
