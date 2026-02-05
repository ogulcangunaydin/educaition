"""
Pydantic schemas for University and Program API responses.
"""

from pydantic import BaseModel, computed_field


class UniversityBase(BaseModel):
    """Base university schema."""
    id: int
    name: str
    city: str
    university_type: str

    class Config:
        from_attributes = True


class UniversityListResponse(BaseModel):
    """Response for listing universities."""
    universities: list[UniversityBase]
    total: int


class ProgramYearlyStatsSchema(BaseModel):
    """Yearly statistics for a program."""
    year: int
    kontenjan: int | None = None
    yerlesen: int | None = None
    taban_puan: float | None = None
    tavan_puan: float | None = None
    tavan_basari_sirasi: int | None = None
    taban_basari_sirasi: int | None = None
    has_data: bool = True

    class Config:
        from_attributes = True


class ProgramBase(BaseModel):
    """Base program schema."""
    id: int
    yop_kodu: str
    faculty: str
    name: str
    detail: str | None = None
    scholarship: str | None = None
    puan_type: str

    class Config:
        from_attributes = True


class ProgramWithUniversity(ProgramBase):
    """Program with university info."""
    university_id: int
    university_name: str
    university_city: str
    university_type: str


class ProgramWithStats(ProgramWithUniversity):
    """Program with yearly stats - used for detailed views."""
    yearly_stats: list[ProgramYearlyStatsSchema] = []


class ProgramFlat(BaseModel):
    """
    Flattened program schema matching frontend CSV structure.
    This is the format the frontend currently expects.
    """
    yop_kodu: str
    university: str
    faculty: str
    program: str
    program_detail: str | None = None
    city: str
    university_type: str
    scholarship: str | None = None
    puan_type: str

    # Year-specific fields (dynamically added based on available data)
    # These will be populated from yearly_stats
    kontenjan_2022: int | None = None
    taban_2022: float | None = None
    tavan_2022: float | None = None
    tavan_bs_2022: int | None = None
    tbs_2022: int | None = None
    yerlesen_2022: int | None = None
    has_2022: bool = False

    kontenjan_2023: int | None = None
    taban_2023: float | None = None
    tavan_2023: float | None = None
    tavan_bs_2023: int | None = None
    tbs_2023: int | None = None
    yerlesen_2023: int | None = None
    has_2023: bool = False

    kontenjan_2024: int | None = None
    taban_2024: float | None = None
    tavan_2024: float | None = None
    tavan_bs_2024: int | None = None
    tbs_2024: int | None = None
    yerlesen_2024: int | None = None
    has_2024: bool = False

    kontenjan_2025: int | None = None
    taban_2025: float | None = None
    tavan_2025: float | None = None
    tavan_bs_2025: int | None = None
    tbs_2025: int | None = None
    yerlesen_2025: int | None = None
    has_2025: bool = False

    class Config:
        from_attributes = True


class ProgramListResponse(BaseModel):
    """Response for listing programs."""
    programs: list[ProgramFlat]
    total: int


class ProgramSearchParams(BaseModel):
    """Search parameters for programs."""
    university_id: int | None = None
    university_name: str | None = None
    puan_type: str | None = None
    year: int | None = None
    city: str | None = None
    program_name: str | None = None
    min_tbs: int | None = None
    max_tbs: int | None = None
    limit: int = 100
    offset: int = 0
