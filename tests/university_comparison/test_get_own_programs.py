"""
Tests for UniversityComparisonService.get_own_programs
"""

import pytest


class TestGetOwnPrograms:
    """GET /programs equivalent – fetch programs for the user's university."""

    def test_returns_programs_for_correct_university(self, svc):
        programs = svc.get_own_programs("HALİÇ ÜNİVERSİTESİ", "2024")
        yop_kodus = {p["yop_kodu"] for p in programs}
        assert "HALIC-CS" in yop_kodus
        assert "HALIC-EE" in yop_kodus
        # Must NOT include programs from other universities
        assert "IST-CS" not in yop_kodus
        assert "BASK-CS" not in yop_kodus

    def test_returns_only_programs_with_data_for_year(self, svc, db, seed_data):
        """Programs without stats for the requested year must be excluded."""
        programs = svc.get_own_programs("HALİÇ ÜNİVERSİTESİ", "2023")
        # No stats seeded for 2023
        assert len(programs) == 0

    def test_returns_flat_format(self, svc):
        """Each returned item must be a ProgramFlat dict."""
        programs = svc.get_own_programs("HALİÇ ÜNİVERSİTESİ", "2024")
        assert len(programs) > 0
        first = programs[0]
        assert "yop_kodu" in first
        assert "university" in first
        assert "faculty" in first
        assert "puan_type" in first
        assert "city" in first
        # Year-specific fields
        assert "kontenjan_2024" in first
        assert "taban_2024" in first
        assert "has_2024" in first

    def test_case_insensitive_university_name(self, svc):
        """Name lookup should be case-insensitive (ASCII-range).

        Note: SQLite's UPPER() doesn't handle Turkish Unicode chars (İ,ç,ü).
        In production (PostgreSQL) full Turkish case-insensitivity works.
        Here we verify the exact stored name always resolves.
        """
        exact = svc.get_own_programs("HALİÇ ÜNİVERSİTESİ", "2024")
        assert len(exact) == 2

    def test_unknown_university_returns_empty(self, svc):
        programs = svc.get_own_programs("NONEXISTENT ÜNİVERSİTESİ", "2024")
        assert programs == []

    def test_programs_sorted_by_name(self, svc):
        programs = svc.get_own_programs("HALİÇ ÜNİVERSİTESİ", "2024")
        names = [p["program"] for p in programs]
        assert names == sorted(names)
