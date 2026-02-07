"""
University Comparison API endpoints.

Two endpoints replace five parallel bulk-data calls:
  GET  /programs  – lightweight dropdown data
  POST /compare   – all filtering, frequency data, prices in one shot
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.university_comparison.schemas import (
    CompareRequest,
    CompareResponse,
)
from app.modules.university_comparison.service import UniversityComparisonService

router = APIRouter(prefix="/university-comparison", tags=["university_comparison"])


@router.get("/programs")
def get_own_programs(
    university_name: str = Query(..., description="Full university name"),
    year: str = Query(..., description="Year, e.g. '2024'"),
    db: Session = Depends(get_db),
):
    """Return programs for a single university that have data for the given year.

    Used to populate the program selector dropdown – much lighter than
    loading every programme in the database.
    """
    svc = UniversityComparisonService(db)
    return svc.get_own_programs(university_name, year)


@router.post("/compare", response_model=CompareResponse)
def compare_programs(
    body: CompareRequest,
    db: Session = Depends(get_db),
):
    """The main comparison endpoint.

    Accepts all filter parameters in the request body and returns:
      • selected programme (ProgramFlat)
      • list of similar programmes (filtered, sorted)
      • price data for matched programmes
      • frequency histograms for the four filter sliders
      • scholarship breakdown
    """
    try:
        svc = UniversityComparisonService(db)
        return svc.compare(body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
