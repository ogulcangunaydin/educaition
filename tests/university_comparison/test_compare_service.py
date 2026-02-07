"""
Tests for the core compare() pipeline – the heart of the module.

Seed data reminder (all SAY, year=2024):
  HALIC-CS : Vakıf  İstanbul  tavan_bs=40k tbs=80k  Burslu        100% fulfillment
  HALIC-EE : Vakıf  İstanbul  tavan_bs=60k tbs=120k               50%  fulfillment
  IST-CS   : Devlet İstanbul  tavan_bs=30k tbs=70k                 100% fulfillment
  ANK-CS   : Devlet Ankara    tavan_bs=35k tbs=75k                 ~92% fulfillment
  BASK-CS  : Vakıf  Ankara    tavan_bs=45k tbs=90k  %50 İndirimli 100% fulfillment
  BASK-EE  : Vakıf  Ankara    tavan_bs=55k tbs=110k               ~33% fulfillment
"""

import pytest


class TestCompareBasic:
    """Basic compare behaviour – no extra filters applied."""

    def test_selected_program_is_first(self, svc, make_request):
        res = svc.compare(make_request())
        assert res.similar_programs[0].yop_kodu == "HALIC-CS"

    def test_selected_program_returned_separately(self, svc, make_request):
        res = svc.compare(make_request())
        assert res.selected_program.yop_kodu == "HALIC-CS"
        assert res.selected_program.university == "HALİÇ ÜNİVERSİTESİ"

    def test_total_before_limit_matches_list_length(self, svc, make_request):
        res = svc.compare(make_request())
        assert res.total_before_limit == len(res.similar_programs)

    def test_nonexistent_program_raises(self, svc, make_request):
        with pytest.raises(ValueError, match="not found"):
            svc.compare(make_request(yop_kodu="DOESNOTEXIST"))

    def test_year_without_data_returns_empty_response(self, svc, make_request):
        """No stats for 2023 → empty similar list (only selected program)."""
        res = svc.compare(make_request(year="2023"))
        # Selected program itself has no range for 2023 → empty response
        assert len(res.similar_programs) == 1
        assert res.similar_programs[0].yop_kodu == "HALIC-CS"


class TestCompareRangeFilter:
    """Range-based filtering: ranking vs score metric."""

    def test_ranking_metric_finds_programs_in_range(self, svc, make_request):
        """With university_type=all and ranking metric, HALIC-CS range is
        tavan_bs=40000..tbs=80000. Programs whose ranking fully falls
        within must be included."""
        res = svc.compare(make_request(university_type="all"))
        yop_kodus = {p.yop_kodu for p in res.similar_programs}
        # IST-CS (30k–70k) – 30k < 40k → outside range
        # ANK-CS (35k–75k) – 35k < 40k → outside range
        # HALIC-CS (40k–80k) – in range (selected)
        # BASK-CS (45k–90k) – 90k > 80k → outside range
        assert "HALIC-CS" in yop_kodus

    def test_custom_range_expands_results(self, svc, make_request):
        """Expanding the custom range should include more programs."""
        # Narrow: default range from HALIC-CS
        narrow = svc.compare(make_request(university_type="all"))

        # Wide: custom range covering all programs (30k–120k)
        wide = svc.compare(make_request(
            university_type="all",
            custom_range_min=25_000,
            custom_range_max=125_000,
        ))
        assert len(wide.similar_programs) >= len(narrow.similar_programs)

    def test_custom_range_includes_all_six(self, svc, make_request):
        """A very wide custom range should capture all 6 programs."""
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        assert len(res.similar_programs) == 6

    def test_score_metric_uses_taban_tavan(self, svc, make_request):
        """When metric='score', range is taban..tavan instead of ranking cols."""
        res = svc.compare(make_request(
            metric="score",
            university_type="all",
            custom_range_min=0,
            custom_range_max=500,
        ))
        # All programs have taban 280–420, tavan 330–420 → all within 0–500
        assert len(res.similar_programs) == 6


class TestCompareUniversityType:
    """University type filter: Vakıf, Devlet, all."""

    def test_vakif_only(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="Vakıf",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        types = {p.university_type for p in res.similar_programs}
        assert types == {"Vakıf"}

    def test_devlet_only(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="Devlet",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        types = {p.university_type for p in res.similar_programs}
        # Selected program (Vakıf) is always included
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.university_type == "Devlet"

    def test_all_types(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        assert len(res.similar_programs) == 6


class TestCompareCityPreferenceFilter:
    """City preference filter: top_cities_limit + reversed."""

    def _wide_request(self, make_request, **overrides):
        """Helper: wide range so all 6 programs are candidates."""
        defaults = dict(university_type="all", custom_range_min=0, custom_range_max=200_000)
        defaults.update(overrides)
        return make_request(**defaults)

    def test_no_filter_when_zero(self, svc, make_request):
        res = svc.compare(self._wide_request(make_request, top_cities_limit=0))
        assert len(res.similar_programs) == 6

    def test_high_threshold_filters_small_cities(self, svc, make_request):
        """İstanbul=50, Ankara=30, İzmir=10.
        top_cities_limit=40 → only İstanbul passes → Ankara programs excluded."""
        res = svc.compare(self._wide_request(make_request, top_cities_limit=40))
        cities = {p.city for p in res.similar_programs if p.yop_kodu != "HALIC-CS"}
        assert "Ankara" not in cities
        assert "İstanbul" in cities

    def test_low_threshold_keeps_all(self, svc, make_request):
        """top_cities_limit=5 → İstanbul(50), Ankara(30), İzmir(10) all pass."""
        res = svc.compare(self._wide_request(make_request, top_cities_limit=5))
        assert len(res.similar_programs) == 6

    def test_reversed_keeps_small_cities(self, svc, make_request):
        """reversed + top_cities_limit=40 → keep cities with count ≤ 40.
        İzmir(10) and Ankara(30) pass; İstanbul(50) excluded."""
        res = svc.compare(self._wide_request(
            make_request, top_cities_limit=40, top_cities_reversed=True
        ))
        cities = {p.city for p in res.similar_programs if p.yop_kodu != "HALIC-CS"}
        assert "İstanbul" not in cities
        assert "Ankara" in cities


class TestCompareUniversityPreferenceFilter:
    """University preference filter."""

    def _wide_request(self, make_request, **overrides):
        defaults = dict(university_type="all", custom_range_min=0, custom_range_max=200_000)
        defaults.update(overrides)
        return make_request(**defaults)

    def test_excludes_own_university_from_totals(self, svc, make_request):
        """HALİÇ ÜNİVERSİTESİ=35 in prefs but must be excluded from threshold.
        min_university_count=30 → İSTANBUL(40) passes, ANKARA(25) doesn't,
        BAŞKENT(15) doesn't. HALİÇ always stays as selected."""
        res = svc.compare(self._wide_request(make_request, min_university_count=30))
        unis = {p.university for p in res.similar_programs}
        assert "HALİÇ ÜNİVERSİTESİ" in unis  # selected
        assert "İSTANBUL ÜNİVERSİTESİ" in unis
        assert "ANKARA ÜNİVERSİTESİ" not in unis
        assert "BAŞKENT ÜNİVERSİTESİ" not in unis

    def test_reversed_keeps_low_count_universities(self, svc, make_request):
        """reversed + min_university_count=30 → keep unis with count ≤ 30.
        ANKARA(25), BAŞKENT(15) pass; İSTANBUL(40) excluded."""
        res = svc.compare(self._wide_request(
            make_request, min_university_count=30, university_count_reversed=True
        ))
        unis = {p.university for p in res.similar_programs if p.yop_kodu != "HALIC-CS"}
        assert "İSTANBUL ÜNİVERSİTESİ" not in unis
        assert "ANKARA ÜNİVERSİTESİ" in unis
        assert "BAŞKENT ÜNİVERSİTESİ" in unis


class TestCompareProgramPreferenceFilter:
    """Program name preference filter."""

    def _wide_request(self, make_request, **overrides):
        defaults = dict(university_type="all", custom_range_min=0, custom_range_max=200_000)
        defaults.update(overrides)
        return make_request(**defaults)

    def test_high_threshold_keeps_popular_programs(self, svc, make_request):
        """Bilgisayar Mühendisliği=60, Elektrik-Elektronik=20.
        min_program_count=50 → only Bilgisayar passes."""
        res = svc.compare(self._wide_request(make_request, min_program_count=50))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert "bilgisayar" in p.program.lower()

    def test_reversed_keeps_unpopular_programs(self, svc, make_request):
        """reversed + min_program_count=50 → keep programs with count ≤ 50.
        Elektrik-Elektronik(20) passes; Bilgisayar(60) excluded."""
        res = svc.compare(self._wide_request(
            make_request, min_program_count=50, program_count_reversed=True
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert "elektrik" in p.program.lower()


class TestCompareFulfillmentFilter:
    """Fulfillment rate (yerlesen/kontenjan) filter."""

    def _wide_request(self, make_request, **overrides):
        defaults = dict(university_type="all", custom_range_min=0, custom_range_max=200_000)
        defaults.update(overrides)
        return make_request(**defaults)

    def test_high_threshold_excludes_low_fulfillment(self, svc, make_request):
        """min_fulfillment_rate=90 → only programs with ≥90% fulfillment.
        HALIC-EE (50%), BASK-EE (33%) excluded."""
        res = svc.compare(self._wide_request(make_request, min_fulfillment_rate=90))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            kontenjan = getattr(p, "kontenjan_2024", 0) or 1
            yerlesen = getattr(p, "yerlesen_2024", 0) or 0
            assert (yerlesen / kontenjan) * 100 >= 90

    def test_reversed_keeps_low_fulfillment(self, svc, make_request):
        """reversed + min_fulfillment_rate=60 → keep programs with ≤60%.
        HALIC-EE (50%) and BASK-EE (33%) pass."""
        res = svc.compare(self._wide_request(
            make_request, min_fulfillment_rate=60, fulfillment_rate_reversed=True
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            kontenjan = getattr(p, "kontenjan_2024", 0) or 1
            yerlesen = getattr(p, "yerlesen_2024", 0) or 0
            assert (yerlesen / kontenjan) * 100 <= 60


class TestCompareManualExclusions:
    """Manual exclusion lists: cities, universities, programs, scholarships."""

    def _wide_request(self, make_request, **overrides):
        defaults = dict(university_type="all", custom_range_min=0, custom_range_max=200_000)
        defaults.update(overrides)
        return make_request(**defaults)

    def test_exclude_city(self, svc, make_request):
        res = svc.compare(self._wide_request(make_request, excluded_cities=["Ankara"]))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.city != "Ankara"

    def test_exclude_university(self, svc, make_request):
        res = svc.compare(self._wide_request(
            make_request, excluded_universities=["İSTANBUL ÜNİVERSİTESİ"]
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.university != "İSTANBUL ÜNİVERSİTESİ"

    def test_exclude_program_name(self, svc, make_request):
        res = svc.compare(self._wide_request(
            make_request, excluded_programs=["Elektrik-Elektronik Mühendisliği"]
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert "elektrik" not in p.program.lower()

    def test_exclude_scholarship(self, svc, make_request):
        """Exclude '%50 İndirimli' → BASK-CS excluded."""
        res = svc.compare(self._wide_request(
            make_request, excluded_scholarships=["%50 İndirimli"]
        ))
        yop_kodus = {p.yop_kodu for p in res.similar_programs}
        assert "BASK-CS" not in yop_kodus

    def test_selected_program_never_excluded(self, svc, make_request):
        """Even when everything is excluded, the selected program stays."""
        res = svc.compare(self._wide_request(
            make_request,
            excluded_cities=["İstanbul", "Ankara"],
            excluded_universities=["HALİÇ ÜNİVERSİTESİ"],
        ))
        assert any(p.yop_kodu == "HALIC-CS" for p in res.similar_programs)

    def test_multiple_exclusions_stack(self, svc, make_request):
        """Exclude Ankara + İSTANBUL ÜNİVERSİTESİ → only Haliç programs remain."""
        res = svc.compare(self._wide_request(
            make_request,
            excluded_cities=["Ankara"],
            excluded_universities=["İSTANBUL ÜNİVERSİTESİ"],
        ))
        non_selected = [p for p in res.similar_programs if p.yop_kodu != "HALIC-CS"]
        for p in non_selected:
            assert p.city != "Ankara"
            assert p.university != "İSTANBUL ÜNİVERSİTESİ"


class TestCompareScholarshipCounts:
    """Scholarship count computation."""

    def test_counts_exclude_selected_program(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        # HALIC-CS is Burslu (selected → not counted)
        # The counts should only include other programs' scholarships
        for sch, count in res.scholarship_counts.items():
            assert count > 0

    def test_counts_computed_before_scholarship_exclusion(self, svc, make_request):
        """Scholarship counts must reflect programs BEFORE any scholarship
        exclusion is applied, so users can see all options in the UI."""
        without_excl = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        with_excl = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            excluded_scholarships=["%50 İndirimli"],
        ))
        # Counts should be identical because they're computed before exclusion
        assert without_excl.scholarship_counts == with_excl.scholarship_counts
