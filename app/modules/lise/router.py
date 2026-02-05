"""API router for lise (high school) data."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.lise.schemas import (
    LiseMappingResponse,
    LisePlacementListResponse,
    LisePlacementWithInfoResponse,
    ScoreRankingDistributionResponse,
    UniversityListResponse,
    UniversityMappingResponse,
)
from app.modules.lise.service import LiseService

router = APIRouter(prefix="/lise", tags=["Lise (High School)"])


def get_service(db: Session = Depends(get_db)) -> LiseService:
    """Get lise service instance."""
    return LiseService(db)


# ===================== Lise Mapping =====================


@router.get("/mapping", response_model=LiseMappingResponse)
def get_lise_mapping(
    year_group: Optional[str] = Query(
        None, description="Filter by year group: '2022-2024' or '2025'"
    ),
    service: LiseService = Depends(get_service),
):
    """
    Get lise ID to info mapping.
    Returns dict: lise_id -> {lise_adi, sehir}
    """
    mapping = service.get_lise_mapping(year_group)
    return LiseMappingResponse(mapping=mapping)


# ===================== University Mapping =====================


@router.get("/universities", response_model=UniversityListResponse)
def get_universities_with_lise_data(
    service: LiseService = Depends(get_service),
):
    """Get list of universities that have lise placement data."""
    universities = service.get_university_list()
    return UniversityListResponse(universities=universities)


@router.get("/university-mapping", response_model=UniversityMappingResponse)
def get_university_mapping(
    service: LiseService = Depends(get_service),
):
    """
    Get university name to slug mapping.
    Returns dict: display_name -> slug
    """
    mapping = service.get_university_slugs()
    return UniversityMappingResponse(mapping=mapping)


# ===================== Lise Placements =====================


@router.get("/placements", response_model=LisePlacementListResponse)
def get_placements_by_programs(
    yop_kodlari: str = Query(
        ..., description="Comma-separated list of YOP codes"
    ),
    year: Optional[int] = Query(None, description="Filter by year"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=100000),
    service: LiseService = Depends(get_service),
):
    """
    Get lise placements for given program YOP codes.
    Returns placements with joined lise info.
    """
    yop_list = [y.strip() for y in yop_kodlari.split(",") if y.strip()]
    items = service.get_placements_by_programs(yop_list, year, skip, limit)
    total = service.get_placements_count(yop_kodlari=yop_list, year=year)
    return LisePlacementListResponse(
        items=[LisePlacementWithInfoResponse(**item) for item in items],
        total=total,
    )


@router.get("/placements/university/{university_slug}", response_model=LisePlacementListResponse)
def get_placements_by_university(
    university_slug: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50000, ge=1, le=100000),
    service: LiseService = Depends(get_service),
):
    """
    Get lise placements for a specific university.
    Returns placements with joined lise info.
    """
    items = service.get_placements_by_university(university_slug, year, skip, limit)
    total = service.get_placements_count(university_slug=university_slug, year=year)
    return LisePlacementListResponse(
        items=[LisePlacementWithInfoResponse(**item) for item in items],
        total=total,
    )


# ===================== Score Ranking Distribution =====================


@router.get("/score-ranking-distribution", response_model=ScoreRankingDistributionResponse)
def get_score_ranking_distribution(
    service: LiseService = Depends(get_service),
):
    """
    Get score to ranking distribution by puan type.
    Returns same structure as frontend JSON file.
    """
    data = service.get_score_ranking_distribution()
    return ScoreRankingDistributionResponse(data=data)
