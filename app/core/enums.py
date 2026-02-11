"""
Centralized enums and controlled values for the application.

This module provides a single source of truth for all enumerated values
used across both backend and frontend. Values are exposed via API endpoint.
"""

from enum import Enum
from typing import Any


# =============================================================================
# USER ENUMS
# =============================================================================


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    VIEWER = "viewer"


class UniversityKey(str, Enum):
    """University identifiers for user affiliation."""

    HALIC = "halic"
    IBNHALDUN = "ibnhaldun"
    FSM = "fsm"
    IZU = "izu"
    MAYIS = "mayis"


class TestType(str, Enum):
    """Test types for unified room management."""

    PRISONERS_DILEMMA = "prisoners_dilemma"
    DISSONANCE_TEST = "dissonance_test"
    PROGRAM_SUGGESTION = "program_suggestion"
    PERSONALITY_TEST = "personality_test"


# =============================================================================
# PROGRAM SUGGESTION ENUMS
# =============================================================================


class Gender(str, Enum):
    """Gender options."""

    MALE = "erkek"
    FEMALE = "kadin"
    OTHER = "diger"


class ClassYear(str, Enum):
    """High school class years."""

    GRADE_11 = "11"
    GRADE_12 = "12"
    GRADUATE = "mezun"


class ScoreArea(str, Enum):
    """University exam score areas (puan türleri)."""

    SAY = "say"  # Sayısal
    EA = "ea"  # Eşit Ağırlık
    SOZ = "söz"  # Sözel
    DIL = "dil"  # Dil


class ScoreDistribution(str, Enum):
    """Expected score distribution confidence levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PreferredLanguage(str, Enum):
    """Preferred education language."""

    TURKISH = "türkçe"
    ENGLISH = "ingilizce"
    ANY = "farketmez"


class City(str, Enum):
    """Major cities for university preferences."""

    ISTANBUL = "istanbul"
    ANKARA = "ankara"
    IZMIR = "izmir"
    BURSA = "bursa"
    ANTALYA = "antalya"
    KONYA = "konya"
    ADANA = "adana"
    KAYSERI = "kayseri"
    OTHER = "other"


class StudentStatus(str, Enum):
    """Program suggestion student progress status."""

    STARTED = "started"
    STEP1_COMPLETED = "step1_completed"
    STEP2_COMPLETED = "step2_completed"
    STEP3_COMPLETED = "step3_completed"
    STEP4_COMPLETED = "step4_completed"
    RIASEC_COMPLETED = "riasec_completed"
    COMPLETED = "completed"


# =============================================================================
# DISSONANCE TEST ENUMS
# =============================================================================


class Education(str, Enum):
    """Education level options."""

    HIGH_SCHOOL_STUDENT = "lise öğrencisi"
    HIGH_SCHOOL_GRADUATE = "lise mezunu"
    UNIVERSITY_STUDENT = "üniversite öğrencisi"
    UNIVERSITY_GRADUATE = "üniversite mezunu"
    POSTGRADUATE = "y.lisans öğrencisi ve üzeri"


class StarSign(str, Enum):
    """Zodiac signs."""

    ARIES = "Koç"
    TAURUS = "Boğa"
    GEMINI = "İkizler"
    CANCER = "Yengeç"
    LEO = "Aslan"
    VIRGO = "Başak"
    LIBRA = "Terazi"
    SCORPIO = "Akrep"
    SAGITTARIUS = "Yay"
    CAPRICORN = "Oğlak"
    AQUARIUS = "Kova"
    PISCES = "Balık"


# =============================================================================
# GAME/SESSION ENUMS
# =============================================================================


class SessionStatus(str, Enum):
    """Game session status."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameChoice(str, Enum):
    """Prisoner's dilemma game choices."""

    COOPERATE = "cooperate"
    DEFECT = "defect"


# =============================================================================
# RIASEC ENUMS
# =============================================================================


class RiasecType(str, Enum):
    """Holland RIASEC personality types."""

    REALISTIC = "R"
    INVESTIGATIVE = "I"
    ARTISTIC = "A"
    SOCIAL = "S"
    ENTERPRISING = "E"
    CONVENTIONAL = "C"


class RiasecAnswer(str, Enum):
    """RIASEC question answer options."""

    STRONGLY_LIKE = "strongly_like"
    LIKE = "like"
    UNSURE = "unsure"
    DISLIKE = "dislike"
    STRONGLY_DISLIKE = "strongly_dislike"


# Map RIASEC answers to scores
RIASEC_SCORE_MAP = {
    RiasecAnswer.STRONGLY_LIKE: 2,
    RiasecAnswer.LIKE: 1,
    RiasecAnswer.UNSURE: 0,
    RiasecAnswer.DISLIKE: -1,
    RiasecAnswer.STRONGLY_DISLIKE: -2,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def enum_to_options(enum_class: type[Enum], labels: dict[str, str] | None = None) -> list[dict[str, str]]:
    """
    Convert an enum to a list of {value, label} options for frontend dropdowns.

    Args:
        enum_class: The enum class to convert
        labels: Optional dict mapping enum values to display labels

    Returns:
        List of dicts with 'value' and 'label' keys
    """
    options = []
    for member in enum_class:
        label = labels.get(member.value, member.value) if labels else member.value
        options.append({"value": member.value, "label": label})
    return options


def get_all_enums() -> dict[str, Any]:
    """
    Get all enums as a dictionary for API response.

    Returns:
        Dict with enum names as keys and lists of options as values
    """
    return {
        # User enums
        "userRoles": enum_to_options(
            UserRole,
            {
                "admin": "Yönetici",
                "teacher": "Öğretmen",
                "student": "Öğrenci",
                "viewer": "İzleyici",
            },
        ),
        "universityKeys": enum_to_options(
            UniversityKey,
            {
                "halic": "Haliç Üniversitesi",
                "ibnhaldun": "İbn Haldun Üniversitesi",
                "fsm": "Fatih Sultan Mehmet Vakıf Üniversitesi",
                "izu": "İstanbul Sabahattin Zaim Üniversitesi",
                "mayis": "19 Mayıs Üniversitesi",
            },
        ),
        # Program suggestion enums
        "genders": enum_to_options(
            Gender,
            {"erkek": "Erkek", "kadin": "Kadın", "diger": "Diğer"},
        ),
        "classYears": enum_to_options(
            ClassYear,
            {
                "11": "11. Sınıf",
                "12": "12. Sınıf",
                "mezun": "Mezun",
            },
        ),
        "scoreAreas": enum_to_options(
            ScoreArea,
            {
                "say": "Sayısal (SAY)",
                "ea": "Eşit Ağırlık (EA)",
                "söz": "Sözel (SÖZ)",
                "dil": "Dil",
            },
        ),
        "scoreDistributions": enum_to_options(
            ScoreDistribution,
            {"low": "Düşük", "medium": "Orta", "high": "Yüksek"},
        ),
        "preferredLanguages": enum_to_options(
            PreferredLanguage,
            {"türkçe": "Türkçe", "ingilizce": "İngilizce", "farketmez": "Farketmez"},
        ),
        "cities": enum_to_options(
            City,
            {
                "istanbul": "İstanbul",
                "ankara": "Ankara",
                "izmir": "İzmir",
                "bursa": "Bursa",
                "antalya": "Antalya",
                "konya": "Konya",
                "adana": "Adana",
                "kayseri": "Kayseri",
                "other": "Diğer Şehirler",
            },
        ),
        "studentStatuses": enum_to_options(
            StudentStatus,
            {
                "started": "Başladı",
                "step1_completed": "Adım 1 Tamamlandı",
                "step2_completed": "Adım 2 Tamamlandı",
                "step3_completed": "Adım 3 Tamamlandı",
                "step4_completed": "Adım 4 Tamamlandı",
                "riasec_completed": "RIASEC Tamamlandı",
                "completed": "Tamamlandı",
            },
        ),
        # Dissonance test enums
        "educationLevels": enum_to_options(Education),
        "starSigns": enum_to_options(StarSign),
        # Game enums
        "sessionStatuses": enum_to_options(
            SessionStatus,
            {
                "pending": "Bekliyor",
                "active": "Aktif",
                "completed": "Tamamlandı",
                "cancelled": "İptal Edildi",
            },
        ),
        "gameChoices": enum_to_options(
            GameChoice, {"cooperate": "İşbirliği", "defect": "İhanet"}
        ),
        # RIASEC enums
        "riasecTypes": enum_to_options(
            RiasecType,
            {
                "R": "Realistic (Gerçekçi)",
                "I": "Investigative (Araştırmacı)",
                "A": "Artistic (Sanatsal)",
                "S": "Social (Sosyal)",
                "E": "Enterprising (Girişimci)",
                "C": "Conventional (Geleneksel)",
            },
        ),
        "riasecAnswers": enum_to_options(
            RiasecAnswer,
            {
                "strongly_like": "Kesinlikle Severim",
                "like": "Severim",
                "unsure": "Kararsızım",
                "dislike": "Sevmem",
                "strongly_dislike": "Kesinlikle Sevmem",
            },
        ),
        "riasecScoreMap": {k.value: v for k, v in RIASEC_SCORE_MAP.items()},
    }
