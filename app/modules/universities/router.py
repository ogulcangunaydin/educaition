"""
API router for University and Program endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.universities.schemas import (
    ProgramFlat,
    ProgramListResponse,
    UniversityBase,
    UniversityListResponse,
)
from app.modules.universities.service import ProgramService, UniversityService

router = APIRouter(prefix="/universities", tags=["universities"])


# ============================================================================
# University Endpoints
# ============================================================================


@router.get("", response_model=UniversityListResponse)
def list_universities(db: Session = Depends(get_db)):
    """Get all universities ordered by name."""
    universities = UniversityService.get_all_universities(db)
    return UniversityListResponse(
        universities=[UniversityBase.model_validate(u) for u in universities],
        total=len(universities),
    )


@router.get("/cities", response_model=list[str])
def list_cities(db: Session = Depends(get_db)):
    """Get all unique cities with universities."""
    return UniversityService.get_cities(db)


@router.get("/{university_id}", response_model=UniversityBase)
def get_university(university_id: int, db: Session = Depends(get_db)):
    """Get a university by ID."""
    university = UniversityService.get_university_by_id(db, university_id)
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return UniversityBase.model_validate(university)


@router.get("/{university_id}/programs", response_model=list[ProgramFlat])
def get_university_programs(
    university_id: int,
    year: int | None = Query(None, description="Filter by year with data"),
    db: Session = Depends(get_db),
):
    """Get all programs for a specific university."""
    university = UniversityService.get_university_by_id(db, university_id)
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return ProgramService.get_programs_by_university(db, university_id, year)


# ============================================================================
# Program Endpoints
# ============================================================================


programs_router = APIRouter(prefix="/programs", tags=["programs"])


@programs_router.get("", response_model=ProgramListResponse)
def list_programs(
    university_id: int | None = Query(None, description="Filter by university ID"),
    university_name: str | None = Query(None, description="Filter by university name (partial match)"),
    puan_type: str | None = Query(None, description="Filter by score type (SAY, EA, SÖZ, DİL, TYT)"),
    year: int | None = Query(None, description="Filter by year with data"),
    city: str | None = Query(None, description="Filter by city"),
    program_name: str | None = Query(None, description="Filter by program name (partial match)"),
    min_tbs: int | None = Query(None, description="Minimum TBS (success ranking)"),
    max_tbs: int | None = Query(None, description="Maximum TBS (success ranking)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    List programs with optional filtering.
    Returns programs in flattened format with all yearly data.
    """
    programs, total = ProgramService.get_programs_flat(
        db,
        university_id=university_id,
        university_name=university_name,
        puan_type=puan_type,
        year=year,
        city=city,
        program_name=program_name,
        min_tbs=min_tbs,
        max_tbs=max_tbs,
        limit=limit,
        offset=offset,
    )
    return ProgramListResponse(
        programs=programs,
        total=total,
        limit=limit,
        offset=offset,
    )


@programs_router.get("/all", response_model=list[ProgramFlat])
def get_all_programs(
    year: int | None = Query(None, description="Filter by year with data"),
    db: Session = Depends(get_db),
):
    """
    Get ALL programs in flattened format.
    This endpoint is optimized for bulk loading by the frontend.
    Use with caution as it returns a large dataset.
    """
    return ProgramService.get_all_programs_flat(db, year)


@programs_router.get("/{yop_kodu}", response_model=ProgramFlat)
def get_program(yop_kodu: str, db: Session = Depends(get_db)):
    """Get a single program by YOP code."""
    program = ProgramService.get_program_by_yop_kodu(db, yop_kodu)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return ProgramService._to_flat(db, program)
