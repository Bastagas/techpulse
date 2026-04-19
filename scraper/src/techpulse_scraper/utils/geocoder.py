"""Géocodage des villes via l'API Adresse Data Gouv.

API gratuite sans clé : https://adresse.data.gouv.fr/api-doc/adresse
Rate limit : 50 req/s → confortable.

Usage batch (CLI) :
    python -m techpulse_scraper geocode
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import cast

import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from techpulse_scraper.config import settings
from techpulse_scraper.logger import logger
from techpulse_scraper.models import Offer


@dataclass
class GeoPoint:
    lat: float
    lng: float
    department: str | None = None


async def _geocode_one(
    client: httpx.AsyncClient, city: str, dept: str | None = None
) -> GeoPoint | None:
    """Géocode une ville via l'API Adresse Data Gouv."""
    params = {"q": city, "type": "municipality", "limit": 1}
    if dept:
        params["postcode"] = dept.ljust(5, "0")

    try:
        response = await client.get(f"{settings.adresse_api_url}/search/", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.warning("Géocodage échoué pour '{}' : {}", city, exc)
        return None

    features = data.get("features", [])
    if not features:
        return None

    props = features[0].get("properties", {})
    geometry = features[0].get("geometry", {})
    coords = geometry.get("coordinates", [])
    if len(coords) < 2:
        return None

    return GeoPoint(
        lat=float(coords[1]),
        lng=float(coords[0]),
        department=props.get("citycode", "")[:3] if props.get("citycode") else None,
    )


async def geocode_cities(session: Session, *, limit: int | None = None) -> tuple[int, int]:
    """Géocode toutes les villes distinctes des offres non encore géocodées.

    Retourne (resolved, skipped).
    """
    # Liste des couples (ville, dept) avec lat/lng null
    stmt = (
        select(Offer.city, Offer.department_code)
        .where(Offer.city.is_not(None), Offer.lat.is_(None))
        .distinct()
    )
    if limit is not None:
        stmt = stmt.limit(limit)

    couples: list[tuple[str, str | None]] = [
        (row[0], row[1]) for row in session.execute(stmt).all()
    ]
    logger.info("{} couples (ville, dept) à géocoder", len(couples))

    resolved = 0
    skipped = 0
    cache: dict[tuple[str, str | None], GeoPoint] = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for city, dept in couples:
            key = (city, dept)
            if key in cache:
                geo = cache[key]
            else:
                geo = await _geocode_one(client, city, dept)
                if geo:
                    cache[key] = geo
                await asyncio.sleep(0.05)  # 20 req/s, large marge sous la limite

            if not geo:
                skipped += 1
                continue

            # Update des offres avec cette ville+dept
            update_stmt = update(Offer).where(
                Offer.city == city,
                Offer.lat.is_(None),
            )
            if dept:
                update_stmt = update_stmt.where(Offer.department_code == dept)
            update_stmt = update_stmt.values(lat=geo.lat, lng=geo.lng)
            result = session.execute(update_stmt)
            resolved += cast(int, result.rowcount)

        session.commit()

    logger.info("Géocodage terminé : {} offres résolues, {} villes non trouvées", resolved, skipped)
    return resolved, skipped


def geocode_cities_sync(session: Session, *, limit: int | None = None) -> tuple[int, int]:
    """Wrapper synchrone pour intégration CLI."""
    return asyncio.run(geocode_cities(session, limit=limit))
