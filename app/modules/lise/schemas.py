"""Pydantic schemas for lise (high school) data."""

from typing import Dict, List, Optional

from pydantic import BaseModel


# ===================== Lise Mapping =====================


class LiseResponse(BaseModel):
    """Response schema for a single lise record."""

    lise_id: int
    lise_adi: str
    sehir: Optional[str] = None
    year_group: str

    class Config:
        from_attributes = True


class LiseMappingResponse(BaseModel):
    """Response schema for lise mapping (id -> info)."""

    mapping: Dict[str, Dict[str, str]]  # lise_id -> {lise_adi, sehir}


# ===================== Lise Placements =====================


class LisePlacementResponse(BaseModel):
    """Response schema for lise placement record."""

    yop_kodu: str
    year: int
    lise_id: int
    yerlesen_sayisi: int
    school_type: Optional[int] = None

    class Config:
        from_attributes = True


class LisePlacementWithInfoResponse(BaseModel):
    """Response schema for lise placement with lise info."""

    yop_kodu: str
    year: int
    lise_id: int
    lise_adi: str
    lise_sehir: Optional[str] = None
    yerlesen_sayisi: int
    school_type: Optional[int] = None

    class Config:
        from_attributes = True


class LisePlacementListResponse(BaseModel):
    """Response schema for list of lise placements."""

    items: List[LisePlacementWithInfoResponse]
    total: int


# ===================== University Mapping =====================


class UniversityMappingResponse(BaseModel):
    """Response schema for university slug mapping."""

    mapping: Dict[str, str]  # university_name -> sanitized_slug


class UniversityListResponse(BaseModel):
    """Response schema for list of universities with lise data."""

    universities: List[str]


# ===================== Score Ranking Distribution =====================


class ScoreRankingResponse(BaseModel):
    """Response schema for score ranking distribution."""

    puan_turu: str
    puan: float
    siralama: int

    class Config:
        from_attributes = True


class ScoreRankingDistributionItem(BaseModel):
    """Schema for a single puan_turu distribution."""

    minScore: float
    maxScore: float
    distribution: List[Dict[str, float]]


class ScoreRankingDistributionResponse(BaseModel):
    """Response schema for full score ranking distribution."""

    data: Dict[str, ScoreRankingDistributionItem]  # puan_turu -> {minScore, maxScore, distribution}
