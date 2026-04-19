"""Tests du parser de salaires français."""

from __future__ import annotations

import pytest

from techpulse_scraper.parsers import parse_salary


class TestParseSalary:
    def test_single_annual(self) -> None:
        r = parse_salary("45 000 € / an")
        assert r is not None
        assert r.min == 45000
        assert r.max == 45000

    def test_range_annual_k_notation(self) -> None:
        r = parse_salary("entre 40k et 55k € annuel")
        assert r is not None
        assert r.min == 40000
        assert r.max == 55000

    def test_monthly_multiplied_by_12(self) -> None:
        r = parse_salary("3000 € par mois")
        assert r is not None
        assert r.min == 36000
        assert r.max == 36000

    def test_daily_multiplied_by_220(self) -> None:
        r = parse_salary("500€/jour")
        assert r is not None
        assert r.min == 110000
        assert r.max == 110000

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "pas de salaire",
            "Selon profil",
            "à négocier",
            "€€€",
        ],
    )
    def test_returns_none_on_unparseable(self, text: str) -> None:
        assert parse_salary(text) is None

    def test_implausibly_low_discarded(self) -> None:
        """5 € / an n'a pas de sens → rejeté."""
        r = parse_salary("5 € / an")
        assert r is None

    def test_implausibly_high_discarded(self) -> None:
        """10 000 000 € / an n'a pas de sens → rejeté."""
        r = parse_salary("10000000 € par an")
        assert r is None
