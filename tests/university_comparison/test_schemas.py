"""
Tests for Pydantic schemas used by university comparison.
"""

import pytest
from pydantic import ValidationError

from app.modules.university_comparison.schemas import (
    CompareRequest,
    CompareResponse,
    FrequencyData,
    PriceItem,
)
from app.modules.universities.schemas import ProgramFlat


class TestCompareRequest:
    """CompareRequest validation."""

    def test_minimal_valid_request(self):
        req = CompareRequest(
            yop_kodu="TEST-001",
            year="2024",
            own_university_name="TEST UNI",
        )
        assert req.metric == "ranking"  # default
        assert req.university_type == "Vakıf"
        assert req.record_limit == 10
        assert req.sort_by == "spread"
        assert req.top_cities_limit == 0
        assert req.excluded_cities == []

    def test_all_fields(self):
        req = CompareRequest(
            yop_kodu="TEST-001",
            year="2024",
            metric="score",
            university_type="Devlet",
            source_university="fsm",
            own_university_name="TEST UNI",
            record_limit=50,
            sort_by="price",
            custom_range_min=100.5,
            custom_range_max=500.0,
            top_cities_limit=10,
            top_cities_reversed=True,
            min_university_count=5,
            university_count_reversed=True,
            min_program_count=3,
            program_count_reversed=False,
            min_fulfillment_rate=80,
            fulfillment_rate_reversed=False,
            excluded_cities=["İstanbul"],
            excluded_universities=["UNI A"],
            excluded_programs=["Prog A"],
            excluded_scholarships=["Burslu"],
        )
        assert req.metric == "score"
        assert req.excluded_cities == ["İstanbul"]

    def test_missing_yop_kodu_raises(self):
        with pytest.raises(ValidationError):
            CompareRequest(year="2024", own_university_name="TEST")

    def test_missing_year_raises(self):
        with pytest.raises(ValidationError):
            CompareRequest(yop_kodu="TEST-001", own_university_name="TEST")

    def test_missing_own_university_name_raises(self):
        with pytest.raises(ValidationError):
            CompareRequest(yop_kodu="TEST-001", year="2024")

    def test_record_limit_minimum(self):
        with pytest.raises(ValidationError):
            CompareRequest(
                yop_kodu="TEST-001",
                year="2024",
                own_university_name="TEST",
                record_limit=0,
            )


class TestCompareResponse:
    """CompareResponse structure."""

    def _dummy_flat(self, **overrides):
        defaults = dict(
            yop_kodu="TEST-001",
            university="TEST UNI",
            faculty="Test Faculty",
            program="Test Program",
            city="İstanbul",
            university_type="Vakıf",
            puan_type="say",
        )
        defaults.update(overrides)
        return ProgramFlat(**defaults)

    def test_valid_response(self):
        sp = self._dummy_flat()
        resp = CompareResponse(
            selected_program=sp,
            similar_programs=[sp],
            total_before_limit=1,
            price_data=[],
            frequency_data=FrequencyData(),
            scholarship_counts={},
        )
        assert resp.selected_program.yop_kodu == "TEST-001"
        assert resp.total_before_limit == 1

    def test_frequency_data_defaults(self):
        fd = FrequencyData()
        assert fd.cities == []
        assert fd.universities == []
        assert fd.programs == []
        assert fd.fulfillment == []

    def test_price_item_defaults(self):
        pi = PriceItem(yop_kodu="TEST-001")
        assert pi.scholarship_pct is None
        assert pi.is_english is False
        assert pi.full_price_2024 is None


class TestProgramFlat:
    """ProgramFlat schema – the denormalized program view."""

    def test_minimal_valid(self):
        flat = ProgramFlat(
            yop_kodu="TEST-001",
            university="TEST UNI",
            faculty="Test Faculty",
            program="Test Program",
            city="İstanbul",
            university_type="Vakıf",
            puan_type="say",
        )
        assert flat.has_2024 is False
        assert flat.kontenjan_2024 is None
        assert flat.taban_2024 is None

    def test_with_yearly_data(self):
        flat = ProgramFlat(
            yop_kodu="TEST-001",
            university="TEST UNI",
            faculty="Test Faculty",
            program="Test Program",
            city="İstanbul",
            university_type="Vakıf",
            puan_type="say",
            has_2024=True,
            kontenjan_2024=50,
            taban_2024=350.0,
            tavan_2024=400.0,
            tavan_bs_2024=40000,
            tbs_2024=80000,
            yerlesen_2024=50,
        )
        assert flat.has_2024 is True
        assert flat.taban_2024 == 350.0
        assert flat.tbs_2024 == 80000
