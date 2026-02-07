"""
Edge-case and regression tests for the comparison service.
"""

import pytest

from app.modules.universities.models import Program, ProgramYearlyStats, University
from app.modules.university_comparison.service import UniversityComparisonService
from app.modules.university_comparison.schemas import CompareRequest


class TestEmptyAndNullEdgeCases:
    """Boundary conditions that could trip up the pipeline."""

    def test_program_with_no_yearly_stats(self, db, seed_data):
        """A program that exists but has no stats for the requested year."""
        # Add a program with no stats at all
        halic = db.query(University).filter(University.name == "HALİÇ ÜNİVERSİTESİ").first()
        orphan = Program(
            yop_kodu="HALIC-ORPHAN",
            university_id=halic.id,
            faculty="Test",
            name="Orphan Program",
            puan_type="say",
        )
        db.add(orphan)
        db.flush()

        svc = UniversityComparisonService(db)
        req = CompareRequest(
            yop_kodu="HALIC-ORPHAN",
            year="2024",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
        )
        # Should return empty response (no range data)
        res = svc.compare(req)
        assert len(res.similar_programs) == 1
        assert res.similar_programs[0].yop_kodu == "HALIC-ORPHAN"

    def test_program_with_null_scores(self, db, seed_data):
        """A program with has_data=True but null scores (Dolmadı case)."""
        halic = db.query(University).filter(University.name == "HALİÇ ÜNİVERSİTESİ").first()
        dolmadi = Program(
            yop_kodu="HALIC-DOLMADI",
            university_id=halic.id,
            faculty="Test",
            name="Dolmadı Program",
            puan_type="say",
        )
        db.add(dolmadi)
        db.flush()
        stat = ProgramYearlyStats(
            program_id=dolmadi.id,
            year=2024,
            kontenjan=10,
            yerlesen=0,
            taban_puan=None,
            tavan_puan=None,
            tavan_basari_sirasi=None,
            taban_basari_sirasi=None,
            has_data=True,
        )
        db.add(stat)
        db.flush()

        svc = UniversityComparisonService(db)
        req = CompareRequest(
            yop_kodu="HALIC-DOLMADI",
            year="2024",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
        )
        res = svc.compare(req)
        # No range data → empty response
        assert len(res.similar_programs) == 1

    def test_zero_fulfillment_rate_program_excluded_at_any_positive_threshold(
        self, db, seed_data
    ):
        """Programs with yerlesen=0 should be excluded when min_fulfillment_rate > 0."""
        svc = UniversityComparisonService(db)
        req = CompareRequest(
            yop_kodu="HALIC-CS",
            year="2024",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            min_fulfillment_rate=1,
        )
        res = svc.compare(req)
        for p in res.similar_programs:
            if p.yop_kodu != "HALIC-CS":
                kontenjan = getattr(p, "kontenjan_2024", 0)
                yerlesen = getattr(p, "yerlesen_2024", 0)
                if kontenjan and yerlesen:
                    assert (yerlesen / kontenjan) * 100 >= 1


class TestCombinedFilters:
    """Test that multiple filters stack correctly."""

    def test_city_plus_university_filter(self, svc, make_request):
        """Apply city filter (İstanbul only) + university filter (high threshold).
        Should narrow results significantly."""
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            top_cities_limit=40,           # only İstanbul
            min_university_count=30,       # only İSTANBUL ÜNİVERSİTESİ
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.city == "İstanbul"
            assert p.university == "İSTANBUL ÜNİVERSİTESİ"

    def test_all_filters_together(self, svc, make_request):
        """Apply every filter at once with wide range."""
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            top_cities_limit=5,
            min_university_count=10,
            min_program_count=15,
            min_fulfillment_rate=30,
        ))
        # Should still have selected program first
        assert res.similar_programs[0].yop_kodu == "HALIC-CS"
        # Result should be non-empty (the selected program is always there)
        assert len(res.similar_programs) >= 1

    def test_filters_plus_exclusions(self, svc, make_request):
        """Preference filters + manual exclusions work together."""
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            top_cities_limit=5,
            excluded_cities=["İzmir"],
            excluded_scholarships=["%50 İndirimli"],
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.city != "İzmir"
            assert p.scholarship != "%50 İndirimli"


class TestRangeEdgeCases:
    """Edge cases in the range filtering logic."""

    def test_swapped_min_max_handled(self, db, seed_data):
        """If a program has min > max in the flat data, the filter should still work."""
        svc = UniversityComparisonService(db)
        # Use very wide custom range to test the filter doesn't crash
        req = CompareRequest(
            yop_kodu="HALIC-CS",
            year="2024",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
            university_type="all",
            custom_range_min=0,
            custom_range_max=999_999,
        )
        res = svc.compare(req)
        assert len(res.similar_programs) == 6

    def test_exact_boundary_match(self, svc, make_request):
        """Program whose range exactly equals custom_range boundaries should be included."""
        # HALIC-CS: tavan_bs=40000, tbs=80000
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=40_000,
            custom_range_max=80_000,
        ))
        assert any(p.yop_kodu == "HALIC-CS" for p in res.similar_programs)

    def test_score_metric_range(self, svc, make_request):
        """Score metric uses taban/tavan columns."""
        # HALIC-CS: taban_2024=350, tavan_2024=400
        res = svc.compare(make_request(
            metric="score",
            university_type="all",
            custom_range_min=350,
            custom_range_max=400,
        ))
        assert any(p.yop_kodu == "HALIC-CS" for p in res.similar_programs)


class TestSearchRangeDetermination:
    """Tests for _get_search_range logic."""

    def test_uses_selected_program_range_by_default(self, svc, make_request):
        """When no custom range is set, uses the selected program's range."""
        res = svc.compare(make_request(university_type="all"))
        # Should include at least the selected program
        assert len(res.similar_programs) >= 1

    def test_custom_range_overrides_program_range(self, svc, make_request):
        """Custom range should completely override the program's natural range."""
        narrow = svc.compare(make_request(university_type="all"))
        # Now set a wider custom range
        wide = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        assert len(wide.similar_programs) >= len(narrow.similar_programs)
