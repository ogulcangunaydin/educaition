"""
Pydantic schemas for tercih stats API.
"""

from typing import List, Optional

from pydantic import BaseModel


# Program Price schemas
class ProgramPriceBase(BaseModel):
    yop_kodu: str
    is_english: bool = False
    scholarship_pct: Optional[float] = None
    full_price_2024: Optional[float] = None
    full_price_2025: Optional[float] = None
    discounted_price_2024: Optional[float] = None
    discounted_price_2025: Optional[float] = None


class ProgramPriceResponse(ProgramPriceBase):
    id: int

    class Config:
        from_attributes = True


# Tercih Stats schemas
class TercihStatsBase(BaseModel):
    yop_kodu: str
    year: int
    ortalama_tercih_edilme_sirasi: Optional[float] = None
    ortalama_yerlesen_tercih_sirasi: Optional[float] = None
    marka_etkinlik_degeri: Optional[float] = None


class TercihStatsResponse(TercihStatsBase):
    id: int

    class Config:
        from_attributes = True


# Tercih Detailed Stats schemas
class TercihDetailedStatsBase(BaseModel):
    yop_kodu: str
    bir_kontenjana_talip_olan_aday_sayisi_2022: Optional[float] = None
    bir_kontenjana_talip_olan_aday_sayisi_2023: Optional[float] = None
    bir_kontenjana_talip_olan_aday_sayisi_2024: Optional[float] = None
    bir_kontenjana_talip_olan_aday_sayisi_2025: Optional[float] = None
    ilk_uc_sirada_tercih_eden_sayisi_2022: Optional[float] = None
    ilk_uc_sirada_tercih_eden_sayisi_2023: Optional[float] = None
    ilk_uc_sirada_tercih_eden_sayisi_2024: Optional[float] = None
    ilk_uc_sirada_tercih_eden_sayisi_2025: Optional[float] = None
    ilk_uc_sirada_tercih_eden_orani_2022: Optional[float] = None
    ilk_uc_sirada_tercih_eden_orani_2023: Optional[float] = None
    ilk_uc_sirada_tercih_eden_orani_2024: Optional[float] = None
    ilk_uc_sirada_tercih_eden_orani_2025: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_sayisi_2022: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_sayisi_2023: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_sayisi_2024: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_sayisi_2025: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_orani_2022: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_orani_2023: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_orani_2024: Optional[float] = None
    ilk_uc_tercih_olarak_yerlesen_orani_2025: Optional[float] = None


class TercihDetailedStatsResponse(TercihDetailedStatsBase):
    id: int

    class Config:
        from_attributes = True


# Tercih Preference schemas
class TercihPreferenceBase(BaseModel):
    source_university: str
    yop_kodu: str
    year: int
    preference_type: str
    preferred_item: str
    tercih_sayisi: int
    university_type: Optional[str] = None


class TercihPreferenceResponse(TercihPreferenceBase):
    id: int

    class Config:
        from_attributes = True


# List response schemas
class ProgramPriceListResponse(BaseModel):
    items: List[ProgramPriceResponse]
    total: int


class TercihStatsListResponse(BaseModel):
    items: List[TercihStatsResponse]
    total: int


class TercihPreferenceListResponse(BaseModel):
    items: List[TercihPreferenceResponse]
    total: int


# Batch request / response schemas
class BatchStatsRequest(BaseModel):
    """Request body for fetching stats/prices/detailed_stats for multiple programs at once."""
    yop_kodlari: List[str]
    year: Optional[int] = None
    include_stats: bool = True
    include_prices: bool = False
    include_detailed_stats: bool = False


class BatchStatsResponse(BaseModel):
    """Combined batch response containing stats, prices, and detailed_stats."""
    stats: List[TercihStatsResponse] = []
    prices: List[ProgramPriceResponse] = []
    detailed_stats: List[TercihDetailedStatsResponse] = []
