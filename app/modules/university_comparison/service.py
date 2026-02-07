"""
Service layer for University Comparison.

Moves ALL heavy filtering from the browser to the server:
  1. Find similar programs by score/ranking range
  2. Apply preference-based filters (city, university, program)
  3. Apply fulfillment-rate and exclusion filters
  4. Compute slider frequency data
  5. Collect prices for matching programs
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session, joinedload

from app.modules.tercih_stats.models import ProgramPrice, TercihPreference
from app.modules.universities.models import Program, ProgramYearlyStats, University
from app.modules.universities.service import ProgramService
from app.modules.university_comparison.schemas import (
    CompareRequest,
    CompareResponse,
    FrequencyData,
    PriceItem,
)

logger = logging.getLogger(__name__)


class UniversityComparisonService:
    """All comparison logic lives here – no heavy work in the browser."""

    def __init__(self, db: Session):
        self.db = db

    # ── public entry points ──────────────────────────────────────

    def get_own_programs(self, university_name: str, year: str) -> list[dict]:
        """Return programs for the user's university that have data for *year*."""
        year_int = int(year)
        programs = (
            self.db.query(Program)
            .join(University)
            .join(ProgramYearlyStats)
            .options(joinedload(Program.university))
            .filter(sa_func.upper(University.name) == university_name.upper())
            .filter(ProgramYearlyStats.year == year_int)
            .filter(ProgramYearlyStats.has_data.is_(True))
            .order_by(Program.name)
            .all()
        )

        # Batch-load yearly stats for these programs
        program_ids = [p.id for p in programs]
        all_stats = (
            self.db.query(ProgramYearlyStats)
            .filter(ProgramYearlyStats.program_id.in_(program_ids))
            .all()
        )
        stats_map: dict[int, list[ProgramYearlyStats]] = defaultdict(list)
        for s in all_stats:
            stats_map[s.program_id].append(s)

        return [
            ProgramService._program_to_flat(p, stats_map.get(p.id, [])).model_dump()
            for p in programs
        ]

    def compare(self, req: CompareRequest) -> CompareResponse:
        """The main comparison endpoint – replaces the entire frontend filter chain."""
        year_int = int(req.year)

        # 1. Resolve the selected program
        selected_program_obj = self._get_program(req.yop_kodu)
        if selected_program_obj is None:
            raise ValueError(f"Program {req.yop_kodu} not found")
        selected_flat = ProgramService._to_flat(self.db, selected_program_obj)

        # 2. Determine search range
        range_min, range_max = self._get_search_range(selected_flat, req)
        if range_min is None or range_max is None:
            return self._empty_response(selected_flat)

        # 3. Find candidate programs (SQL: year + puan_type + has_data + university_type)
        candidates = self._find_candidates(
            year_int, selected_flat.puan_type, req.university_type
        )

        # 4. Range filter (Python – handles string-parsed columns)
        in_range = self._filter_by_range(
            candidates, req.year, req.metric, range_min, range_max
        )

        # 5. Preference-based filters
        prefs = self._load_preferences(req.yop_kodu, req.source_university, year_int)

        # Compute frequency data BEFORE applying pref filters (for slider histograms)
        freq = self._compute_frequency_data(
            prefs, in_range, req, selected_flat, year_int
        )

        filtered = in_range

        # City preference filter
        if req.top_cities_limit > 0:
            filtered = self._filter_by_preference(
                filtered, prefs.get("city", {}), "city",
                req.top_cities_limit, req.top_cities_reversed,
                selected_flat, req.own_university_name,
            )

        # Manual city exclusions
        if req.excluded_cities:
            excluded_set = set(req.excluded_cities)
            filtered = [
                p for p in filtered
                if p.yop_kodu == selected_flat.yop_kodu or p.city not in excluded_set
            ]

        # University preference filter
        if req.min_university_count > 0:
            filtered = self._filter_by_preference(
                filtered, prefs.get("university", {}), "university",
                req.min_university_count, req.university_count_reversed,
                selected_flat, req.own_university_name,
            )

        # Manual university exclusions
        if req.excluded_universities:
            excluded_set = set(req.excluded_universities)
            filtered = [
                p for p in filtered
                if p.yop_kodu == selected_flat.yop_kodu or p.university not in excluded_set
            ]

        # Program preference filter
        if req.min_program_count > 0:
            filtered = self._filter_by_program_preference(
                filtered, prefs.get("program", {}),
                req.min_program_count, req.program_count_reversed,
                selected_flat,
            )

        # Manual program exclusions
        if req.excluded_programs:
            excluded_lower = {s.lower() for s in req.excluded_programs}
            filtered = [
                p for p in filtered
                if p.yop_kodu == selected_flat.yop_kodu
                or (p.program or "").lower() not in excluded_lower
            ]

        # Fulfillment rate filter
        if req.min_fulfillment_rate > 0:
            filtered = self._filter_by_fulfillment(
                filtered, req.year, req.min_fulfillment_rate,
                req.fulfillment_rate_reversed, selected_flat,
            )

        # Compute scholarship counts BEFORE scholarship exclusion
        scholarship_counts = self._count_scholarships(filtered, selected_flat)

        # Scholarship exclusions
        if req.excluded_scholarships:
            excluded_set = set(req.excluded_scholarships)
            filtered = [
                p for p in filtered
                if p.yop_kodu == selected_flat.yop_kodu
                or (p.scholarship or "Ücretli") not in excluded_set
            ]

        # Ensure selected program is first
        filtered = self._ensure_selected_first(filtered, selected_flat)
        total_before_limit = len(filtered)

        # 6. Collect prices for ALL matching programs (before limit)
        all_yop_kodus = [p.yop_kodu for p in filtered]
        price_data = self._get_prices(all_yop_kodus)

        return CompareResponse(
            selected_program=selected_flat,
            similar_programs=filtered,
            total_before_limit=total_before_limit,
            price_data=price_data,
            frequency_data=freq,
            scholarship_counts=scholarship_counts,
        )

    # ── internal helpers ─────────────────────────────────────────

    def _get_program(self, yop_kodu: str) -> Optional[Program]:
        return (
            self.db.query(Program)
            .options(joinedload(Program.university))
            .filter(Program.yop_kodu == yop_kodu)
            .first()
        )

    def _get_search_range(self, selected, req):
        """Determine min/max search boundaries from selected program or custom range."""
        year = req.year
        if req.metric == "ranking":
            sel_min = getattr(selected, f"tavan_bs_{year}", None)
            sel_max = getattr(selected, f"tbs_{year}", None)
        else:
            sel_min = getattr(selected, f"taban_{year}", None)
            sel_max = getattr(selected, f"tavan_{year}", None)

        range_min = req.custom_range_min if req.custom_range_min is not None else sel_min
        range_max = req.custom_range_max if req.custom_range_max is not None else sel_max
        return range_min, range_max

    def _find_candidates(self, year_int, puan_type, university_type):
        """SQL query: broad filter by year, puan_type, university_type."""
        query = (
            self.db.query(Program)
            .join(University)
            .join(ProgramYearlyStats)
            .options(joinedload(Program.university))
            .filter(ProgramYearlyStats.year == year_int)
            .filter(ProgramYearlyStats.has_data.is_(True))
            .filter(sa_func.lower(Program.puan_type) == puan_type.lower())
        )
        if university_type != "all":
            query = query.filter(University.university_type == university_type)

        programs = query.all()

        # Batch-load all yearly stats for these programs
        program_ids = [p.id for p in programs]
        if not program_ids:
            return []

        all_stats = (
            self.db.query(ProgramYearlyStats)
            .filter(ProgramYearlyStats.program_id.in_(program_ids))
            .all()
        )
        stats_map: dict[int, list[ProgramYearlyStats]] = defaultdict(list)
        for s in all_stats:
            stats_map[s.program_id].append(s)

        return [
            ProgramService._program_to_flat(p, stats_map.get(p.id, []))
            for p in programs
        ]

    def _filter_by_range(self, candidates, year, metric, range_min, range_max):
        """Python-side range overlap check (handles parsed String columns)."""
        if metric == "ranking":
            min_col = f"tavan_bs_{year}"
            max_col = f"tbs_{year}"
        else:
            min_col = f"taban_{year}"
            max_col = f"tavan_{year}"

        result = []
        for p in candidates:
            p_min = getattr(p, min_col, None)
            p_max = getattr(p, max_col, None)

            # Handle "Dolmadı" – if min is null but max exists, use max for both
            if p_min is None and p_max is not None:
                p_min = p_max
            if p_min is None or p_max is None:
                continue

            # Ensure correct ordering
            if p_min > p_max:
                p_min, p_max = p_max, p_min

            if p_min >= range_min and p_max <= range_max:
                result.append(p)

        return result

    def _load_preferences(self, yop_kodu, source_university, year_int):
        """Load all three preference types for the selected program in one query."""
        rows = (
            self.db.query(TercihPreference)
            .filter(
                TercihPreference.yop_kodu == yop_kodu,
                TercihPreference.source_university == source_university,
                TercihPreference.year == year_int,
            )
            .all()
        )

        prefs: dict[str, dict[str, int]] = {"city": {}, "university": {}, "program": {}}
        for r in rows:
            bucket = prefs.get(r.preference_type, {})
            bucket[r.preferred_item] = bucket.get(r.preferred_item, 0) + r.tercih_sayisi
            prefs[r.preference_type] = bucket

        return prefs

    def _filter_by_preference(
        self, programs, totals, attr, threshold, reversed_, selected, own_uni_name
    ):
        """Generic preference filter: keep programs whose attr is in the allowed set."""
        # For university preferences, exclude own university from the totals
        if attr == "university":
            totals = {k: v for k, v in totals.items() if k != own_uni_name}

        allowed = {
            item
            for item, count in totals.items()
            if (count <= threshold if reversed_ else count >= threshold)
        }

        return [
            p
            for p in programs
            if p.yop_kodu == selected.yop_kodu
            or getattr(p, attr, None) in allowed
        ]

    def _filter_by_program_preference(
        self, programs, totals, threshold, reversed_, selected
    ):
        """Program preference filter — case-insensitive Turkish matching."""
        allowed_lower = {
            prog.lower()
            for prog, count in totals.items()
            if (count <= threshold if reversed_ else count >= threshold)
        }

        return [
            p
            for p in programs
            if p.yop_kodu == selected.yop_kodu
            or (p.program or "").lower() in allowed_lower
        ]

    def _filter_by_fulfillment(self, programs, year, threshold, reversed_, selected):
        result = []
        for p in programs:
            if p.yop_kodu == selected.yop_kodu:
                result.append(p)
                continue
            kontenjan = getattr(p, f"kontenjan_{year}", None)
            yerlesen = getattr(p, f"yerlesen_{year}", None)
            if not kontenjan or not yerlesen:
                continue
            rate = (yerlesen / kontenjan) * 100
            if reversed_:
                if rate <= threshold:
                    result.append(p)
            else:
                if rate >= threshold:
                    result.append(p)
        return result

    def _count_scholarships(self, programs, selected):
        counts: dict[str, int] = {}
        for p in programs:
            if p.yop_kodu == selected.yop_kodu:
                continue
            sch = p.scholarship or "Ücretli"
            counts[sch] = counts.get(sch, 0) + 1
        return counts

    def _ensure_selected_first(self, programs, selected):
        others = [p for p in programs if p.yop_kodu != selected.yop_kodu]
        return [selected, *others]

    def _compute_frequency_data(self, prefs, in_range, req, selected, year_int):
        """Compute all four frequency datasets for the filter sliders."""
        # City frequency
        city_totals = prefs.get("city", {})
        cities = sorted(city_totals.items(), key=lambda x: x[1], reverse=True)

        # University frequency (excluding own)
        uni_totals = {
            k: v
            for k, v in prefs.get("university", {}).items()
            if k != req.own_university_name
        }
        universities = sorted(uni_totals.items(), key=lambda x: x[1], reverse=True)

        # Program frequency
        prog_totals = prefs.get("program", {})
        programs = sorted(prog_totals.items(), key=lambda x: x[1], reverse=True)

        # Fulfillment frequency — computed from the in-range programs (before pref filters)
        filtered_by_type = in_range  # already filtered by university_type in SQL
        fulfillment_rates = []
        for p in filtered_by_type:
            kontenjan = getattr(p, f"kontenjan_{req.year}", None)
            yerlesen = getattr(p, f"yerlesen_{req.year}", None)
            if kontenjan and yerlesen:
                fulfillment_rates.append((yerlesen / kontenjan) * 100)

        thresholds = [0, 20, 40, 60, 80, 100]
        fulfillment = [
            [t, sum(1 for r in fulfillment_rates if r >= t)] for t in thresholds
        ]

        return FrequencyData(
            cities=cities,
            universities=universities,
            programs=programs,
            fulfillment=fulfillment,
        )

    def _get_prices(self, yop_kodus: list[str]) -> list[PriceItem]:
        if not yop_kodus:
            return []
        rows = (
            self.db.query(ProgramPrice)
            .filter(ProgramPrice.yop_kodu.in_(yop_kodus))
            .all()
        )
        return [
            PriceItem(
                yop_kodu=r.yop_kodu,
                scholarship_pct=r.scholarship_pct,
                is_english=r.is_english,
                full_price_2024=r.full_price_2024,
                full_price_2025=r.full_price_2025,
                discounted_price_2024=r.discounted_price_2024,
                discounted_price_2025=r.discounted_price_2025,
            )
            for r in rows
        ]

    def _empty_response(self, selected):
        return CompareResponse(
            selected_program=selected,
            similar_programs=[selected],
            total_before_limit=1,
            price_data=[],
            frequency_data=FrequencyData(),
            scholarship_counts={},
        )
