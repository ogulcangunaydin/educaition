"""
Pydantic schemas for University Comparison API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.universities.schemas import ProgramFlat


# ─── Request ────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    """All parameters the comparison page needs in a single request."""

    yop_kodu: str = Field(..., description="YOP code of the selected program")
    year: str = Field(..., description="Year as string, e.g. '2024'")
    metric: str = Field("ranking", description="'ranking' or 'score'")
    university_type: str = Field("Vakıf", description="'all', 'Devlet', 'Vakıf', 'KKTC'")
    source_university: str = Field("halic", description="Data prefix for preference lookups")
    own_university_name: str = Field(..., description="Full name, e.g. 'HALİÇ ÜNİVERSİTESİ'")
    record_limit: int = Field(10, ge=1)
    sort_by: str = Field("spread")
    custom_range_min: float | None = None
    custom_range_max: float | None = None

    # Preference-based filters
    top_cities_limit: int = 0
    top_cities_reversed: bool = False
    min_university_count: int = 0
    university_count_reversed: bool = False
    min_program_count: int = 0
    program_count_reversed: bool = False
    min_fulfillment_rate: int = 0
    fulfillment_rate_reversed: bool = False

    # Manual exclusions
    excluded_cities: list[str] = Field(default_factory=list)
    excluded_universities: list[str] = Field(default_factory=list)
    excluded_programs: list[str] = Field(default_factory=list)
    excluded_scholarships: list[str] = Field(default_factory=list)


# ─── Response sub-models ────────────────────────────────────────────

class PriceItem(BaseModel):
    yop_kodu: str
    scholarship_pct: float | None = None
    is_english: bool = False
    full_price_2024: float | None = None
    full_price_2025: float | None = None
    discounted_price_2024: float | None = None
    discounted_price_2025: float | None = None


class FrequencyData(BaseModel):
    cities: list[list] = Field(default_factory=list)
    universities: list[list] = Field(default_factory=list)
    programs: list[list] = Field(default_factory=list)
    fulfillment: list[list] = Field(default_factory=list)


# ─── Response ───────────────────────────────────────────────────────

class CompareResponse(BaseModel):
    selected_program: ProgramFlat
    similar_programs: list[ProgramFlat]
    total_before_limit: int
    price_data: list[PriceItem]
    frequency_data: FrequencyData
    scholarship_counts: dict[str, int] = Field(default_factory=dict)
