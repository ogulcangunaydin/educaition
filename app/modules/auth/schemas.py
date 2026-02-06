from pydantic import BaseModel
from app.services.password_service import PasswordConfig

class Token(BaseModel):
    access_token: str
    refresh_token: str
    current_user_id: int
    token_type: str = "bearer"
    expires_in: int  # Access token expiry in seconds
    role: str
    university: str

class DeviceLoginRequest(BaseModel):
    device_id: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiry in seconds

class PasswordRequirements(BaseModel):
    min_length: int = PasswordConfig.MIN_LENGTH
    max_length: int = PasswordConfig.MAX_LENGTH
    require_uppercase: bool = PasswordConfig.REQUIRE_UPPERCASE
    require_lowercase: bool = PasswordConfig.REQUIRE_LOWERCASE
    require_digit: bool = PasswordConfig.REQUIRE_DIGIT
    require_special: bool = PasswordConfig.REQUIRE_SPECIAL
    special_characters: str = PasswordConfig.SPECIAL_CHARACTERS
    message: str = (
        f"Password must be {PasswordConfig.MIN_LENGTH}-{PasswordConfig.MAX_LENGTH} characters, "
        "with at least one uppercase letter, one lowercase letter, "
        "one digit, and one special character."
    )

class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"
