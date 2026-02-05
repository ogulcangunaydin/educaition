"""Service layer for lise (high school) data."""

from typing import Dict, List, Optional

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.modules.lise.models import (
    Lise,
    LisePlacement,
    LisePlacement2025,
    ScoreRankingDistribution,
)


class LiseService:
    """Service for lise data operations."""

    def __init__(self, db: Session):
        self.db = db

    # ===================== Lise Mapping =====================

    def get_lise_mapping(self, year_group: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Get lise mapping as dict: lise_id -> {lise_adi, sehir}.
        Optionally filter by year_group.
        """
        query = self.db.query(Lise)
        if year_group:
            query = query.filter(Lise.year_group == year_group)

        mapping = {}
        for lise in query.all():
            mapping[str(lise.lise_id)] = {
                "lise_adi": lise.lise_adi,
                "sehir": lise.sehir or "",
            }
        return mapping

    def get_all_lises(
        self, year_group: Optional[str] = None, skip: int = 0, limit: int = 1000
    ) -> List[Lise]:
        """Get all lise records with pagination."""
        query = self.db.query(Lise)
        if year_group:
            query = query.filter(Lise.year_group == year_group)
        return query.offset(skip).limit(limit).all()

    # ===================== University Mapping =====================

    def get_university_slugs(self, year_group: Optional[str] = None) -> Dict[str, str]:
        """
        Get mapping of university names to slugs.
        Returns dict: university_name -> sanitized_slug
        """
        query = self.db.query(distinct(LisePlacement.university_slug))

        slugs = [row[0] for row in query.all()]

        # Convert slug back to display name and create mapping
        # The slug is already in the format we need (e.g., "istanbul_universitesi")
        mapping = {}
        for slug in slugs:
            # Convert slug to display name (reverse of sanitization)
            display_name = slug.replace("_", " ").upper()
            mapping[display_name] = slug

        return mapping

    def get_university_list(self) -> List[str]:
        """Get list of unique university slugs with lise data."""
        query = self.db.query(distinct(LisePlacement.university_slug))
        return [row[0] for row in query.all()]

    # ===================== Lise Placements =====================

    def get_placements_by_programs(
        self,
        yop_kodlari: List[str],
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 10000,
    ) -> List[dict]:
        """
        Get lise placements for given programs with lise info joined.
        Returns list of dicts with placement + lise info.
        """
        # Determine year_group for lise mapping
        year_group = "2025" if year == 2025 else "2022-2024"

        # Get placements
        query = self.db.query(LisePlacement).filter(
            LisePlacement.yop_kodu.in_(yop_kodlari)
        )
        if year:
            query = query.filter(LisePlacement.year == year)

        placements = query.offset(skip).limit(limit).all()

        # Get lise mapping for lookup
        lise_mapping = self.get_lise_mapping(year_group)

        # Join with lise info
        results = []
        for p in placements:
            lise_info = lise_mapping.get(str(p.lise_id), {})
            results.append({
                "yop_kodu": p.yop_kodu,
                "year": p.year,
                "lise_id": p.lise_id,
                "lise_adi": lise_info.get("lise_adi", f"Lise ID: {p.lise_id}"),
                "lise_sehir": lise_info.get("sehir", ""),
                "yerlesen_sayisi": p.yerlesen_sayisi,
                "school_type": p.school_type,
            })

        return results

    def get_placements_by_university(
        self,
        university_slug: str,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 50000,
    ) -> List[dict]:
        """
        Get lise placements for a specific university.
        Returns list of dicts with placement + lise info.
        """
        # Determine year_group for lise mapping
        year_group = "2025" if year == 2025 else "2022-2024"

        query = self.db.query(LisePlacement).filter(
            LisePlacement.university_slug == university_slug
        )
        if year:
            query = query.filter(LisePlacement.year == year)

        placements = query.offset(skip).limit(limit).all()

        # Get lise mapping for lookup
        lise_mapping = self.get_lise_mapping(year_group)

        results = []
        for p in placements:
            lise_info = lise_mapping.get(str(p.lise_id), {})
            results.append({
                "yop_kodu": p.yop_kodu,
                "year": p.year,
                "lise_id": p.lise_id,
                "lise_adi": lise_info.get("lise_adi", f"Lise ID: {p.lise_id}"),
                "lise_sehir": lise_info.get("sehir", ""),
                "yerlesen_sayisi": p.yerlesen_sayisi,
                "school_type": p.school_type,
            })

        return results

    def get_placements_count(
        self,
        yop_kodlari: Optional[List[str]] = None,
        university_slug: Optional[str] = None,
        year: Optional[int] = None,
    ) -> int:
        """Get count of placements matching filters."""
        query = self.db.query(func.count(LisePlacement.id))

        if yop_kodlari:
            query = query.filter(LisePlacement.yop_kodu.in_(yop_kodlari))
        if university_slug:
            query = query.filter(LisePlacement.university_slug == university_slug)
        if year:
            query = query.filter(LisePlacement.year == year)

        return query.scalar()

    # ===================== Score Ranking Distribution =====================

    def get_score_ranking_distribution(self) -> Dict[str, List[Dict[str, float]]]:
        """
        Get score ranking distribution grouped by puan_turu.
        Returns dict matching frontend JSON structure.
        """
        records = self.db.query(ScoreRankingDistribution).all()

        result = {}
        for r in records:
            if r.puan_turu not in result:
                result[r.puan_turu] = {
                    "minScore": r.puan,
                    "maxScore": r.puan,
                    "distribution": [],
                }
            result[r.puan_turu]["distribution"].append({
                "score": r.puan,
                "avgRanking": r.siralama,
            })
            # Update min/max
            if r.puan < result[r.puan_turu]["minScore"]:
                result[r.puan_turu]["minScore"] = r.puan
            if r.puan > result[r.puan_turu]["maxScore"]:
                result[r.puan_turu]["maxScore"] = r.puan

        return result
