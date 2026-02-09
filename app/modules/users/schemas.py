from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.enums import UniversityKey, UserRole
from app.core.validators import (
    EmailStrOptional,
    FieldLimits,
    UsernameStr,
    sanitize_string,
)
from app.services.password_service import validate_password_strength


def _validate_password_field(password: str) -> str:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password


class UserBase(BaseModel):
    username: UsernameStr = Field(
        min_length=FieldLimits.USERNAME_MIN,
        max_length=FieldLimits.USERNAME_MAX,
        description="Username must start with a letter and contain only letters, numbers, underscores, and dots",
    )
    email: EmailStrOptional = Field(default=None, max_length=FieldLimits.EMAIL_MAX)


class UserCreate(UserBase):
    password: str = Field(
        min_length=FieldLimits.PASSWORD_MIN,
        max_length=FieldLimits.PASSWORD_MAX,
    )
    role: UserRole = UserRole.STUDENT
    university: UniversityKey = UniversityKey.HALIC

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_field(v)


class UserUpdate(BaseModel):
    username: UsernameStr | None = Field(
        default=None,
        min_length=FieldLimits.USERNAME_MIN,
        max_length=FieldLimits.USERNAME_MAX,
    )
    email: EmailStrOptional = Field(default=None, max_length=FieldLimits.EMAIL_MAX)
    password: str | None = Field(
        default=None,
        min_length=FieldLimits.PASSWORD_MIN,
        max_length=FieldLimits.PASSWORD_MAX,
    )
    role: UserRole | None = None
    university: UniversityKey | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_password_field(v)
        return v

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, v: str | None) -> str | None:
        return sanitize_string(v) if v else v


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    role: str
    university: str
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime | None, _info) -> str | None:
        if value is None:
            return None
        return value.strftime("%d/%m/%Y %H:%M:%S")
