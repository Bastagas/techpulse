"""Tests du parser de localisation."""

from __future__ import annotations

import pytest

from techpulse_scraper.parsers import parse_location


class TestParseLocation:
    @pytest.mark.parametrize(
        ("raw", "expected_city", "expected_dept"),
        [
            ("38 - Grenoble", "Grenoble", "38"),
            ("75 - PARIS 08", "Paris", "75"),
            ("44 - Saint-Nazaire", "Saint-Nazaire", "44"),
            ("69 - LYON 03", "Lyon", "69"),
            ("971 - Pointe-à-Pitre", "Pointe-À-Pitre", "971"),
        ],
    )
    def test_standard_format(self, raw: str, expected_city: str, expected_dept: str) -> None:
        r = parse_location(raw)
        assert r.city == expected_city
        assert r.department_code == expected_dept

    @pytest.mark.parametrize(
        "raw",
        ["Télétravail", "télétravail total", "Remote", "Home office"],
    )
    def test_remote_returns_none(self, raw: str) -> None:
        r = parse_location(raw)
        assert r.city is None
        assert r.department_code is None

    def test_empty_input(self) -> None:
        r = parse_location("")
        assert r.city is None
        assert r.department_code is None
        r = parse_location(None)
        assert r.city is None

    def test_unknown_format_kept_as_city(self) -> None:
        """Fallback : si format non reconnu, on garde le texte comme ville."""
        r = parse_location("Montpellier")
        assert r.city == "Montpellier"
        assert r.department_code is None
