"""
Integration tests for the /api/university-comparison HTTP endpoints.

Uses FastAPI's TestClient with a dependency-overridden get_db.
"""

import pytest
from starlette.testclient import TestClient

from app.core.database import get_db
from app.main import app


@pytest.fixture()
def client(db, seed_data):
    """FastAPI TestClient with the test DB session injected."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        c = TestClient(app)
        yield c
    finally:
        app.dependency_overrides.clear()


# ─── GET /api/university-comparison/programs ───────────────────────


class TestProgramsEndpoint:
    """GET /programs – dropdown data."""

    def test_200_with_valid_params(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"university_name": "HALİÇ ÜNİVERSİTESİ", "year": "2024"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2  # HALIC-CS and HALIC-EE

    def test_returns_correct_fields(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"university_name": "HALİÇ ÜNİVERSİTESİ", "year": "2024"},
        )
        item = resp.json()[0]
        assert "yop_kodu" in item
        assert "university" in item
        assert "kontenjan_2024" in item

    def test_422_missing_university_name(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"year": "2024"},
        )
        assert resp.status_code == 422

    def test_422_missing_year(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"university_name": "HALİÇ ÜNİVERSİTESİ"},
        )
        assert resp.status_code == 422

    def test_empty_for_unknown_university(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"university_name": "UNKNOWN", "year": "2024"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_empty_for_year_without_data(self, client):
        resp = client.get(
            "/api/university-comparison/programs",
            params={"university_name": "HALİÇ ÜNİVERSİTESİ", "year": "2019"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


# ─── POST /api/university-comparison/compare ──────────────────────


class TestCompareEndpoint:
    """POST /compare – the main comparison endpoint."""

    def _body(self, **overrides):
        defaults = dict(
            yop_kodu="HALIC-CS",
            year="2024",
            metric="ranking",
            university_type="all",
            source_university="halic",
            own_university_name="HALİÇ ÜNİVERSİTESİ",
            record_limit=200,
            sort_by="spread",
        )
        defaults.update(overrides)
        return defaults

    def test_200_basic_compare(self, client):
        resp = client.post("/api/university-comparison/compare", json=self._body())
        assert resp.status_code == 200
        data = resp.json()
        assert "selected_program" in data
        assert "similar_programs" in data
        assert "total_before_limit" in data
        assert "price_data" in data
        assert "frequency_data" in data
        assert "scholarship_counts" in data

    def test_selected_program_fields(self, client):
        resp = client.post("/api/university-comparison/compare", json=self._body())
        sp = resp.json()["selected_program"]
        assert sp["yop_kodu"] == "HALIC-CS"
        assert sp["university"] == "HALİÇ ÜNİVERSİTESİ"
        assert sp["puan_type"] == "say"

    def test_similar_programs_first_is_selected(self, client):
        resp = client.post("/api/university-comparison/compare", json=self._body())
        data = resp.json()
        assert data["similar_programs"][0]["yop_kodu"] == "HALIC-CS"

    def test_404_for_nonexistent_program(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(yop_kodu="DOESNOTEXIST"),
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_422_missing_required_field(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json={"year": "2024"},  # missing yop_kodu and own_university_name
        )
        assert resp.status_code == 422

    def test_wide_range_returns_all_programs(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(custom_range_min=0, custom_range_max=200_000),
        )
        data = resp.json()
        assert data["total_before_limit"] == 6
        assert len(data["similar_programs"]) == 6

    def test_vakif_filter_applied(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(
                university_type="Vakıf",
                custom_range_min=0,
                custom_range_max=200_000,
            ),
        )
        data = resp.json()
        non_selected = [
            p for p in data["similar_programs"]
            if p["yop_kodu"] != "HALIC-CS"
        ]
        for p in non_selected:
            assert p["university_type"] == "Vakıf"

    def test_exclusion_applied_via_api(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(
                custom_range_min=0,
                custom_range_max=200_000,
                excluded_cities=["Ankara"],
            ),
        )
        data = resp.json()
        non_selected = [
            p for p in data["similar_programs"]
            if p["yop_kodu"] != "HALIC-CS"
        ]
        for p in non_selected:
            assert p["city"] != "Ankara"

    def test_frequency_data_structure(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(custom_range_min=0, custom_range_max=200_000),
        )
        fd = resp.json()["frequency_data"]
        assert isinstance(fd["cities"], list)
        assert isinstance(fd["universities"], list)
        assert isinstance(fd["programs"], list)
        assert isinstance(fd["fulfillment"], list)
        # Each entry is [name, count]
        if fd["cities"]:
            assert len(fd["cities"][0]) == 2

    def test_price_data_structure(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(custom_range_min=0, custom_range_max=200_000),
        )
        prices = resp.json()["price_data"]
        assert isinstance(prices, list)
        if prices:
            p = prices[0]
            assert "yop_kodu" in p
            assert "scholarship_pct" in p
            assert "full_price_2024" in p

    def test_scholarship_counts_structure(self, client):
        resp = client.post(
            "/api/university-comparison/compare",
            json=self._body(custom_range_min=0, custom_range_max=200_000),
        )
        sc = resp.json()["scholarship_counts"]
        assert isinstance(sc, dict)
        for key, val in sc.items():
            assert isinstance(key, str)
            assert isinstance(val, int)

    def test_defaults_work_without_optional_fields(self, client):
        """Sending only the required fields should work with sensible defaults."""
        resp = client.post(
            "/api/university-comparison/compare",
            json={
                "yop_kodu": "HALIC-CS",
                "year": "2024",
                "own_university_name": "HALİÇ ÜNİVERSİTESİ",
            },
        )
        assert resp.status_code == 200
