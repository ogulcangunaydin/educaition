"""
Tests for POST /api/tercih-stats/batch endpoint.
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


class TestBatchEndpoint:
    """POST /api/tercih-stats/batch"""

    # ── Stats only ──────────────────────────────────────────────

    def test_stats_only_returns_matching_programs(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001", "100002"],
            "include_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        yop_codes = {s["yop_kodu"] for s in data["stats"]}
        assert yop_codes == {"100001", "100002"}
        # 100001 has 2 years, 100002 has 1 year → 3 total
        assert len(data["stats"]) == 3
        # prices and detailed_stats should be empty
        assert data["prices"] == []
        assert data["detailed_stats"] == []

    def test_stats_filtered_by_year(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001", "100002"],
            "year": 2024,
            "include_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Only 2024 data: 100001 + 100002 = 2
        assert len(data["stats"]) == 2
        for stat in data["stats"]:
            assert stat["year"] == 2024

    def test_stats_empty_for_unknown_yop_kodu(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["999999"],
            "include_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []

    def test_stats_correct_values(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001"],
            "year": 2024,
            "include_stats": True,
        })
        data = resp.json()
        assert len(data["stats"]) == 1
        stat = data["stats"][0]
        assert stat["yop_kodu"] == "100001"
        assert stat["ortalama_tercih_edilme_sirasi"] == 5.0
        assert stat["ortalama_yerlesen_tercih_sirasi"] == 3.0
        assert stat["marka_etkinlik_degeri"] == 1.67

    # ── Prices ──────────────────────────────────────────────────

    def test_prices_only(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001", "100002"],
            "include_stats": False,
            "include_prices": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []
        assert len(data["prices"]) == 2
        yop_codes = {p["yop_kodu"] for p in data["prices"]}
        assert yop_codes == {"100001", "100002"}

    def test_prices_no_match(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100003"],  # no prices seeded for 100003
            "include_stats": False,
            "include_prices": True,
        })
        assert resp.status_code == 200
        assert resp.json()["prices"] == []

    # ── Detailed Stats ──────────────────────────────────────────

    def test_detailed_stats_only(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001", "100002"],
            "include_stats": False,
            "include_detailed_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []
        assert len(data["detailed_stats"]) == 2

    def test_detailed_stats_correct_values(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001"],
            "include_stats": False,
            "include_detailed_stats": True,
        })
        data = resp.json()
        assert len(data["detailed_stats"]) == 1
        istat = data["detailed_stats"][0]
        assert istat["yop_kodu"] == "100001"
        assert istat["bir_kontenjana_talip_olan_aday_sayisi_2024"] == 12.5
        assert istat["ilk_uc_sirada_tercih_eden_orani_2024"] == 40.0
        assert istat["ilk_uc_tercih_olarak_yerlesen_orani_2024"] == 60.0

    # ── Combined request ────────────────────────────────────────

    def test_all_three_together(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001", "100002", "100003"],
            "year": 2024,
            "include_stats": True,
            "include_prices": True,
            "include_detailed_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Stats: 100001(2024) + 100002(2024) + 100003(2024) = 3
        assert len(data["stats"]) == 3
        # Prices: 100001 + 100002 = 2 (no price for 100003)
        assert len(data["prices"]) == 2
        # Detailed stats: 100001 + 100002 = 2 (no istat for 100003)
        assert len(data["detailed_stats"]) == 2

    # ── Edge cases ──────────────────────────────────────────────

    def test_empty_yop_kodlari(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": [],
            "include_stats": True,
            "include_prices": True,
            "include_detailed_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []
        assert data["prices"] == []
        assert data["detailed_stats"] == []

    def test_nothing_requested(self, client):
        """All include flags false → empty response."""
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001"],
            "include_stats": False,
            "include_prices": False,
            "include_detailed_stats": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []
        assert data["prices"] == []
        assert data["detailed_stats"] == []

    def test_422_missing_yop_kodlari(self, client):
        resp = client.post("/api/tercih-stats/batch", json={})
        assert resp.status_code == 422

    def test_single_yop_kodu(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100003"],
            "year": 2024,
            "include_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["stats"]) == 1
        assert data["stats"][0]["yop_kodu"] == "100003"
        assert data["stats"][0]["ortalama_tercih_edilme_sirasi"] == 3.0

    def test_year_with_no_data_returns_empty(self, client):
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001"],
            "year": 2020,
            "include_stats": True,
        })
        assert resp.status_code == 200
        assert resp.json()["stats"] == []

    def test_year_filter_does_not_affect_prices_or_detailed_stats(self, client):
        """year filter only affects stats, not prices/detailed_stats."""
        resp = client.post("/api/tercih-stats/batch", json={
            "yop_kodlari": ["100001"],
            "year": 2020,  # no stats for this year
            "include_stats": True,
            "include_prices": True,
            "include_detailed_stats": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"] == []
        # prices and detailed_stats are not filtered by year
        assert len(data["prices"]) == 1
        assert len(data["detailed_stats"]) == 1
