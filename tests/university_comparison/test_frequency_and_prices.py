"""
Tests for frequency data and price data returned by compare().
"""

import pytest


class TestFrequencyData:
    """Frequency histograms for the four filter sliders."""

    def _wide_result(self, svc, make_request):
        return svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))

    def test_city_frequencies_sorted_descending(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        cities = res.frequency_data.cities
        assert len(cities) == 3  # İstanbul, Ankara, İzmir
        counts = [c[1] for c in cities]
        assert counts == sorted(counts, reverse=True)

    def test_city_frequency_values(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        city_dict = {c[0]: c[1] for c in res.frequency_data.cities}
        assert city_dict["İstanbul"] == 50
        assert city_dict["Ankara"] == 30
        assert city_dict["İzmir"] == 10

    def test_university_frequencies_exclude_own(self, svc, make_request):
        """Own university (HALİÇ) must NOT appear in university frequencies."""
        res = self._wide_result(svc, make_request)
        uni_names = {u[0] for u in res.frequency_data.universities}
        assert "HALİÇ ÜNİVERSİTESİ" not in uni_names
        assert "İSTANBUL ÜNİVERSİTESİ" in uni_names

    def test_university_frequency_values(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        uni_dict = {u[0]: u[1] for u in res.frequency_data.universities}
        assert uni_dict["İSTANBUL ÜNİVERSİTESİ"] == 40
        assert uni_dict["ANKARA ÜNİVERSİTESİ"] == 25
        assert uni_dict["BAŞKENT ÜNİVERSİTESİ"] == 15

    def test_program_frequencies_sorted_descending(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        programs = res.frequency_data.programs
        assert len(programs) == 2
        counts = [p[1] for p in programs]
        assert counts == sorted(counts, reverse=True)

    def test_program_frequency_values(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        prog_dict = {p[0]: p[1] for p in res.frequency_data.programs}
        assert prog_dict["Bilgisayar Mühendisliği"] == 60
        assert prog_dict["Elektrik-Elektronik Mühendisliği"] == 20

    def test_fulfillment_thresholds_are_standard(self, svc, make_request):
        res = self._wide_result(svc, make_request)
        thresholds = [f[0] for f in res.frequency_data.fulfillment]
        assert thresholds == [0, 20, 40, 60, 80, 100]

    def test_fulfillment_counts_are_non_increasing(self, svc, make_request):
        """At threshold 0 everyone passes; at 100 only perfectly filled programs do.
        The count should be non-increasing as the threshold rises."""
        res = self._wide_result(svc, make_request)
        counts = [f[1] for f in res.frequency_data.fulfillment]
        for i in range(len(counts) - 1):
            assert counts[i] >= counts[i + 1]

    def test_fulfillment_at_zero_equals_total_with_data(self, svc, make_request):
        """Threshold 0% should include every program that has kontenjan and yerlesen."""
        res = self._wide_result(svc, make_request)
        # All 6 programs have kontenjan and yerlesen → all should count at threshold 0
        assert res.frequency_data.fulfillment[0][1] == 6

    def test_no_preferences_returns_empty_frequencies(self, svc, make_request):
        """When source university has no preference data, frequencies should be empty."""
        res = svc.compare(make_request(
            source_university="nonexistent",
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        assert res.frequency_data.cities == []
        assert res.frequency_data.universities == []
        assert res.frequency_data.programs == []
        # Fulfillment still computed from program data (not preferences)
        assert len(res.frequency_data.fulfillment) == 6


class TestPriceData:
    """Price data collection for matching programs."""

    def test_returns_prices_for_matching_programs(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        price_yop_kodus = {p.yop_kodu for p in res.price_data}
        # We seeded prices for HALIC-CS and BASK-CS
        assert "HALIC-CS" in price_yop_kodus
        assert "BASK-CS" in price_yop_kodus

    def test_price_fields_populated(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        halic_prices = [p for p in res.price_data if p.yop_kodu == "HALIC-CS"]
        assert len(halic_prices) == 1
        hp = halic_prices[0]
        assert hp.scholarship_pct == 100
        assert hp.full_price_2024 == 150_000
        assert hp.discounted_price_2024 == 0

    def test_no_prices_for_programs_without_price_data(self, svc, make_request):
        """IST-CS has no price data → should not appear in price_data."""
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
        ))
        price_yop_kodus = {p.yop_kodu for p in res.price_data}
        assert "IST-CS" not in price_yop_kodus

    def test_empty_result_returns_empty_prices(self, svc, make_request):
        """If compare yields no programs, prices list is empty."""
        res = svc.compare(make_request(year="2023"))
        assert res.price_data == []


class TestSelectedProgramAlwaysFirst:
    """The selected program must ALWAYS be the first element in similar_programs."""

    def test_first_after_all_filters(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            top_cities_limit=40,
            min_university_count=30,
            min_program_count=50,
            min_fulfillment_rate=90,
        ))
        assert res.similar_programs[0].yop_kodu == "HALIC-CS"

    def test_first_even_with_heavy_exclusions(self, svc, make_request):
        res = svc.compare(make_request(
            university_type="all",
            custom_range_min=0,
            custom_range_max=200_000,
            excluded_cities=["İstanbul"],
        ))
        assert res.similar_programs[0].yop_kodu == "HALIC-CS"
