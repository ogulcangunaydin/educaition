import re
from typing import Tuple, List
from passlib.context import CryptContext
from enum import Enum


class PasswordStrength(str, Enum):
    WEAK = "weak"
    FAIR = "fair"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class PasswordValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Password validation failed: {', '.join(errors)}")


class PasswordConfig:
    MIN_LENGTH: int = 8
    MAX_LENGTH: int = 128
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGIT: bool = True
    REQUIRE_SPECIAL: bool = True
    SPECIAL_CHARACTERS: str = r"!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
    
    # 12 rounds = ~250ms hashing time
    BCRYPT_ROUNDS: int = 12
    BCRYPT_DEPRECATED: str = "auto"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated=PasswordConfig.BCRYPT_DEPRECATED,
    bcrypt__rounds=PasswordConfig.BCRYPT_ROUNDS
)


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    
    if len(password) < PasswordConfig.MIN_LENGTH:
        errors.append(f"Password must be at least {PasswordConfig.MIN_LENGTH} characters long")
    
    if len(password) > PasswordConfig.MAX_LENGTH:
        errors.append(f"Password must not exceed {PasswordConfig.MAX_LENGTH} characters")
    
    if PasswordConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if PasswordConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if PasswordConfig.REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if PasswordConfig.REQUIRE_SPECIAL:
        special_pattern = f'[{re.escape(PasswordConfig.SPECIAL_CHARACTERS)}]'
        if not re.search(special_pattern, password):
            errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:',.<>?/`~)")
    
    return len(errors) == 0, errors


def check_password_strength(password: str) -> PasswordStrength:
    score = 0
    
    # Length scoring
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(f'[{re.escape(PasswordConfig.SPECIAL_CHARACTERS)}]', password):
        score += 1
    if re.search(r'[a-zA-Z].*\d.*[^a-zA-Z0-9]', password):
        score += 1
    
    if score <= 3:
        return PasswordStrength.WEAK
    elif score <= 5:
        return PasswordStrength.FAIR
    elif score <= 7:
        return PasswordStrength.STRONG
    else:
        return PasswordStrength.VERY_STRONG


def hash_password(password: str, validate: bool = True) -> str:
    if validate:
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            raise PasswordValidationError(errors)
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
