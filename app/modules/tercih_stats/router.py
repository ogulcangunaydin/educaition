"""
API router for tercih statistics.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.tercih_stats.schemas import (
    ProgramPriceListResponse,
    ProgramPriceResponse,
    TercihIstatistikleriResponse,
    TercihPreferenceListResponse,
    TercihPreferenceResponse,
    TercihStatsListResponse,
    TercihStatsResponse,
)
from app.modules.tercih_stats.service import TercihStatsService

router = APIRouter(prefix="/tercih-stats", tags=["Tercih Statistics"])


def get_service(db: Session = Depends(get_db)) -> TercihStatsService:
    """Get tercih stats service instance."""
    return TercihStatsService(db)


# ===================== Program Prices =====================


@router.get("/prices", response_model=ProgramPriceListResponse)
def get_all_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    service: TercihStatsService = Depends(get_service),
):
    """Get all program prices with pagination."""
    items = service.get_all_prices(skip=skip, limit=limit)
    total = service.get_prices_count()
    return ProgramPriceListResponse(items=items, total=total)


@router.get("/prices/{yop_kodu}", response_model=List[ProgramPriceResponse])
def get_prices_by_yop_kodu(
    yop_kodu: str,
    service: TercihStatsService = Depends(get_service),
):
    """Get price records for a specific program by yop_kodu."""
    prices = service.get_prices_by_yop_kodu(yop_kodu)
    return prices


# ===================== Tercih Stats =====================


@router.get("/stats", response_model=TercihStatsListResponse)
def get_all_stats(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    service: TercihStatsService = Depends(get_service),
):
    """Get all tercih stats with pagination."""
    items = service.get_all_stats(skip=skip, limit=limit)
    total = service.get_stats_count()
    return TercihStatsListResponse(items=items, total=total)


@router.get("/stats/{yop_kodu}", response_model=List[TercihStatsResponse])
def get_stats_by_yop_kodu(
    yop_kodu: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    service: TercihStatsService = Depends(get_service),
):
    """Get tercih stats for a specific program by yop_kodu."""
    stats = service.get_stats_by_yop_kodu(yop_kodu, year)
    return stats


@router.get("/stats/year/{year}", response_model=List[TercihStatsResponse])
def get_stats_by_year(
    year: int,
    service: TercihStatsService = Depends(get_service),
):
    """Get all tercih stats for a specific year."""
    return service.get_stats_by_year(year)


# ===================== Tercih Istatistikleri =====================


@router.get("/istatistikleri", response_model=List[TercihIstatistikleriResponse])
def get_all_istatistikleri(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    service: TercihStatsService = Depends(get_service),
):
    """Get all detailed istatistikleri with pagination."""
    return service.get_all_istatistikleri(skip=skip, limit=limit)


@router.get("/istatistikleri/{yop_kodu}", response_model=TercihIstatistikleriResponse)
def get_istatistikleri_by_yop_kodu(
    yop_kodu: str,
    service: TercihStatsService = Depends(get_service),
):
    """Get detailed istatistikleri for a specific program by yop_kodu."""
    istat = service.get_istatistikleri_by_yop_kodu(yop_kodu)
    if not istat:
        raise HTTPException(status_code=404, detail="Istatistikleri not found")
    return istat


# ===================== Tercih Preferences =====================


@router.get("/preferences", response_model=TercihPreferenceListResponse)
def get_all_preferences(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    service: TercihStatsService = Depends(get_service),
):
    """Get all tercih preferences with pagination."""
    items = service.get_all_preferences(skip=skip, limit=limit)
    total = service.get_preferences_count()
    return TercihPreferenceListResponse(items=items, total=total)


@router.get("/preferences/{yop_kodu}", response_model=List[TercihPreferenceResponse])
def get_preferences_by_yop_kodu(
    yop_kodu: str,
    source_university: Optional[str] = Query(None, description="Filter by source university"),
    preference_type: Optional[str] = Query(None, description="Filter by type: city, university, program"),
    year: Optional[int] = Query(None, description="Filter by year"),
    service: TercihStatsService = Depends(get_service),
):
    """Get tercih preferences for a specific program by yop_kodu."""
    return service.get_preferences_by_yop_kodu(
        yop_kodu,
        source_university=source_university,
        preference_type=preference_type,
        year=year,
    )


@router.get("/preferences/source/{source_university}", response_model=List[TercihPreferenceResponse])
def get_preferences_by_source(
    source_university: str,
    preference_type: Optional[str] = Query(None, description="Filter by type: city, university, program"),
    year: Optional[int] = Query(None, description="Filter by year"),
    service: TercihStatsService = Depends(get_service),
):
    """Get all tercih preferences for a source university."""
    return service.get_preferences_by_source(
        source_university,
        preference_type=preference_type,
        year=year,
    )


# ===================== Metadata =====================


@router.get("/source-universities", response_model=List[str])
def get_source_universities(service: TercihStatsService = Depends(get_service)):
    """Get list of all source universities."""
    return service.get_source_universities()


@router.get("/years", response_model=List[int])
def get_available_years(service: TercihStatsService = Depends(get_service)):
    """Get list of available years for tercih stats."""
    return service.get_available_years()
