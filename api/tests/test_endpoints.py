"""Tests d'intégration de l'API Flask — utilise la BDD réelle (nécessite docker compose up)."""

from __future__ import annotations

import pytest

from techpulse_api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


class TestMeta:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert isinstance(data["offers_count"], int)

    def test_version(self, client):
        r = client.get("/version")
        assert r.status_code == 200
        data = r.get_json()
        assert "version" in data
        assert "scraper_version" in data


class TestOffers:
    def test_list_returns_paginated(self, client):
        r = client.get("/offers?per_page=5")
        assert r.status_code == 200
        data = r.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["items"]) <= 5

    def test_filter_by_tech(self, client):
        r = client.get("/offers?tech=python&per_page=3")
        assert r.status_code == 200
        data = r.get_json()
        for offer in data["items"]:
            tech_names = [t["canonical_name"] for t in offer["technologies"]]
            assert "python" in tech_names, f"Offre {offer['id']} n'a pas python : {tech_names}"

    def test_filter_by_keyword(self, client):
        r = client.get("/offers?keyword=développeur&per_page=5")
        assert r.status_code == 200

    def test_detail_404_on_missing(self, client):
        r = client.get("/offers/99999999")
        assert r.status_code == 404

    def test_detail_returns_full_offer(self, client):
        # Récupère le 1er id via le listing
        listing = client.get("/offers?per_page=1").get_json()
        if not listing["items"]:
            pytest.skip("Pas d'offres en BDD")
        offer_id = listing["items"][0]["id"]
        r = client.get(f"/offers/{offer_id}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["id"] == offer_id
        assert "title" in data
        assert "technologies" in data


class TestStats:
    def test_top_techs(self, client):
        r = client.get("/stats/top-techs")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        if data:
            assert "name" in data[0]
            assert "count" in data[0]
            assert "category" in data[0]

    def test_salaries_shape(self, client):
        r = client.get("/stats/salaries")
        assert r.status_code == 200
        data = r.get_json()
        assert "count" in data
        assert "mean" in data
        assert "median" in data

    def test_cities(self, client):
        r = client.get("/stats/cities")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)

    def test_sources(self, client):
        r = client.get("/stats/sources")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)

    def test_timeline(self, client):
        r = client.get("/stats/timeline")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)

    def test_runs(self, client):
        r = client.get("/stats/runs")
        assert r.status_code == 200
        data = r.get_json()
        assert "scheduler" in data
        assert "recent_runs" in data
        assert isinstance(data["recent_runs"], list)


class TestOpenAPI:
    def test_spec_is_accessible(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.get_json()
        assert spec["info"]["title"] == "TechPulse API"
        assert "/offers" in spec["paths"]
        assert "/stats/top-techs" in spec["paths"]
