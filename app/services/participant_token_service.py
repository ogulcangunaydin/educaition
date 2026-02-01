from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings

class ParticipantType(str, Enum):
    PLAYER = "player"  # Game room players
    DISSONANCE_TEST = "dissonance_test"  # Dissonance test participants
    PROGRAM_SUGGESTION = "program_suggestion"  # Program suggestion students


class ParticipantTokenConfig:
    EXPIRATION_HOURS = {
        ParticipantType.PLAYER: 4,  # 4 hours for game players
        ParticipantType.DISSONANCE_TEST: 24,  # 24 hours for test
        ParticipantType.PROGRAM_SUGGESTION: 72,  # 3 days for program suggestion
    }
    ALGORITHM: str = settings.ALGORITHM
    SECRET_KEY: str = settings.SECRET_KEY


class ParticipantTokenPayload(BaseModel):
    participant_id: int
    participant_type: ParticipantType
    room_id: int  # Room or high school room ID
    exp: datetime
    iat: datetime
    jti: str  # Unique token ID


class ParticipantTokenError(Exception):
    def __init__(self, message: str, error_code: str = "participant_token_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ParticipantTokenExpiredError(ParticipantTokenError):
    def __init__(self, message: str = "Session has expired. Please rejoin."):
        super().__init__(message, "participant_token_expired")


class ParticipantTokenInvalidError(ParticipantTokenError):
    def __init__(self, message: str = "Invalid session token"):
        super().__init__(message, "participant_token_invalid")


def create_participant_token(
    participant_id: int,
    participant_type: ParticipantType,
    room_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        hours = ParticipantTokenConfig.EXPIRATION_HOURS.get(participant_type, 24)
        expire = now + timedelta(hours=hours)

    payload = {
        "participant_id": participant_id,
        "participant_type": participant_type.value,
        "room_id": room_id,
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
    }

    return jwt.encode(
        payload,
        ParticipantTokenConfig.SECRET_KEY,
        algorithm=ParticipantTokenConfig.ALGORITHM,
    )


def decode_participant_token(token: str) -> ParticipantTokenPayload:
    try:
        payload = jwt.decode(
            token,
            ParticipantTokenConfig.SECRET_KEY,
            algorithms=[ParticipantTokenConfig.ALGORITHM],
        )

        return ParticipantTokenPayload(
            participant_id=payload["participant_id"],
            participant_type=ParticipantType(payload["participant_type"]),
            room_id=payload["room_id"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload["jti"],
        )

    except jwt.ExpiredSignatureError:
        raise ParticipantTokenExpiredError()
    except JWTError as e:
        raise ParticipantTokenInvalidError(f"Token validation failed: {e!s}")


def verify_participant_token(
    token: str,
    expected_type: ParticipantType | None = None,
    expected_participant_id: int | None = None,
) -> ParticipantTokenPayload:
    payload = decode_participant_token(token)

    if expected_type and payload.participant_type != expected_type:
        raise ParticipantTokenInvalidError(
            f"Expected {expected_type.value} token, got {payload.participant_type.value}"
        )

    if expected_participant_id and payload.participant_id != expected_participant_id:
        raise ParticipantTokenInvalidError("Token does not match participant")

    return payload


def get_token_expiry_seconds(participant_type: ParticipantType) -> int:
    hours = ParticipantTokenConfig.EXPIRATION_HOURS.get(participant_type, 24)
    return hours * 60 * 60


__all__ = [
    "ParticipantType",
    "ParticipantTokenConfig",
    "ParticipantTokenPayload",
    "ParticipantTokenError",
    "ParticipantTokenExpiredError",
    "ParticipantTokenInvalidError",
    "create_participant_token",
    "decode_participant_token",
    "verify_participant_token",
    "get_token_expiry_seconds",
]
