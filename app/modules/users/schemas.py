from enum import Enum
from pydantic import BaseModel, field_validator
from app.services.password_service import validate_password_strength

def _validate_password_field(password: str) -> str:
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        raise ValueError("; ".join(errors))
    return password

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    VIEWER = "viewer"

class UniversityKeyEnum(str, Enum):
    HALIC = "halic"
    IBNHALDUN = "ibnhaldun"
    FSM = "fsm"
    IZU = "izu"
    MAYIS = "mayis"

class UserBase(BaseModel):
    username: str
    email: str | None = None

class UserCreate(UserBase):
    password: str
    role: UserRoleEnum = UserRoleEnum.STUDENT
    university: UniversityKeyEnum = UniversityKeyEnum.HALIC

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_field(v)

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    role: UserRoleEnum | None = None
    university: UniversityKeyEnum | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_password_field(v)
        return v

class User(UserBase):
    id: int
    is_active: bool
    role: str
    university: str

    class Config:
        from_attributes = True
