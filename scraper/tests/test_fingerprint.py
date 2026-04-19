"""Tests du module fingerprint (normalisation + hashing)."""

from __future__ import annotations

from techpulse_scraper.utils.fingerprint import normalize, offer_fingerprint


class TestNormalize:
    def test_accents_folded(self) -> None:
        assert normalize("Développeur") == "developpeur"
        assert normalize("Saint-Étienne") == "saint etienne"

    def test_lowercase(self) -> None:
        assert normalize("PYTHON") == "python"
        assert normalize("FastAPI") == "fastapi"

    def test_punctuation_removed(self) -> None:
        assert normalize("C#") == "c"  # attention : peut être un problème pour C/C++
        assert normalize("Java (H/F)") == "java h f"

    def test_spaces_collapsed(self) -> None:
        assert normalize("   hello    world   ") == "hello world"

    def test_empty(self) -> None:
        assert normalize("") == ""
        assert normalize(None) == ""


class TestOfferFingerprint:
    def test_deterministic(self) -> None:
        f1 = offer_fingerprint("Dev Python", "Acme", "Paris")
        f2 = offer_fingerprint("Dev Python", "Acme", "Paris")
        assert f1 == f2

    def test_length_is_64(self) -> None:
        f = offer_fingerprint("Any", "Any", "Any")
        assert len(f) == 64
        assert all(c in "0123456789abcdef" for c in f)

    def test_normalization_matters(self) -> None:
        """Deux offres différant uniquement par la casse / accents → même fingerprint."""
        f1 = offer_fingerprint("Développeur Python", "ACME", "Saint-Étienne")
        f2 = offer_fingerprint("DEVELOPPEUR python", "acme", "SAINT-ETIENNE")
        assert f1 == f2

    def test_different_city_different_hash(self) -> None:
        f1 = offer_fingerprint("Dev Python", "Acme", "Paris")
        f2 = offer_fingerprint("Dev Python", "Acme", "Lyon")
        assert f1 != f2

    def test_city_optional(self) -> None:
        """Pas de ville → fingerprint quand même calculable (pour offres remote)."""
        f = offer_fingerprint("Dev Python", "Acme", None)
        assert len(f) == 64
