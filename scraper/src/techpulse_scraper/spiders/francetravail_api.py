"""Spider France Travail — API officielle (pole-emploi.io).

- OAuth2 client_credentials : token mis en cache jusqu'à expiration
- Recherche par codes ROME tech (M1805 dev, M1802 support, M1810 prod, M1811 chef projet)
- Pagination par ranges 0-149, 150-299, ... (max 2999 par la doc)
- Rate limit géré côté HttpClient
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime

from techpulse_scraper.config import settings
from techpulse_scraper.http_client import HttpClient
from techpulse_scraper.logger import logger
from techpulse_scraper.models import Source
from techpulse_scraper.spiders.base import BaseSpider, RawOffer

ROME_CODES = [
    "M1805",  # Études et développement informatique
    "M1802",  # Expertise et support en systèmes d'information
    "M1810",  # Production et exploitation de systèmes d'information
    "M1811",  # Chef de projet informatique
    "M1803",  # Direction des systèmes d'information
    "M1806",  # Conseil et maîtrise d'ouvrage en SI
    "M1801",  # Administration de systèmes d'information
    "H1206",  # Management et ingénierie études, R&D industriel (data science / embedded)
]

PAGE_SIZE = 150
MAX_RANGE = 2999  # limite API FT


class FranceTravailSpider(BaseSpider):
    name = "france_travail"
    source = Source.FRANCE_TRAVAIL

    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expiry: float = 0.0

    async def _get_token(self, client: HttpClient) -> str:
        """Obtient (ou rafraîchit) un token OAuth2 client_credentials."""
        loop = asyncio.get_event_loop()
        now = loop.time()
        if self._token and self._token_expiry > now + 60:
            return self._token

        if not settings.has_france_travail_credentials:
            raise RuntimeError(
                "FRANCE_TRAVAIL_CLIENT_ID / FRANCE_TRAVAIL_CLIENT_SECRET manquants dans .env.local"
            )

        logger.info("Obtention d'un nouveau token France Travail…")
        response = await client.post(
            settings.france_travail_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.france_travail_client_id,
                "client_secret": settings.france_travail_client_secret,
                "scope": settings.france_travail_scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._token_expiry = now + float(data.get("expires_in", 1500))
        logger.info("Token obtenu (expire dans {}s)", int(data.get("expires_in", 1500)))
        return self._token

    async def scrape(self, limit: int | None = None) -> AsyncIterator[RawOffer]:
        """Scrape toutes les offres tech (ROME_CODES) par pages de 150."""
        total_yielded = 0

        # Rate limit à 0.2s (5 req/s, bien sous la limite de 10/s de l'API)
        async with HttpClient(rate_limit_interval=0.2) as client:
            token = await self._get_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            for rome_code in ROME_CODES:
                logger.info("Scraping ROME {} …", rome_code)
                start = 0

                while start <= MAX_RANGE:
                    if limit is not None and total_yielded >= limit:
                        logger.info("Limite atteinte ({} offres)", limit)
                        return

                    end = min(start + PAGE_SIZE - 1, MAX_RANGE)
                    url = (
                        f"{settings.france_travail_api_base}/offres/search"
                        f"?codeROME={rome_code}&range={start}-{end}"
                    )

                    try:
                        response = await client.get(url, headers=headers)
                    except Exception as exc:
                        logger.error("Erreur sur {} : {}", url, exc)
                        break

                    if response.status_code == 204:
                        logger.info("ROME {} : pas d'offres.", rome_code)
                        break

                    if response.status_code not in (200, 206):
                        logger.warning(
                            "ROME {} range {}-{} : HTTP {}",
                            rome_code,
                            start,
                            end,
                            response.status_code,
                        )
                        break

                    data = response.json()
                    offres = data.get("resultats", [])
                    if not offres:
                        break

                    for o in offres:
                        if limit is not None and total_yielded >= limit:
                            return
                        yield self._parse(o)
                        total_yielded += 1

                    # Si on a reçu moins que demandé → dernier batch
                    if len(offres) < PAGE_SIZE:
                        break

                    start += PAGE_SIZE

                logger.info(
                    "ROME {} terminé ({} offres yieldées au total pour ce spider)",
                    rome_code,
                    total_yielded,
                )

    def _parse(self, raw: dict) -> RawOffer:
        """Transforme la réponse JSON FT en RawOffer."""
        lieu = raw.get("lieuTravail") or {}
        entreprise = raw.get("entreprise") or {}
        origine = raw.get("origineOffre") or {}
        salaire = raw.get("salaire") or {}

        posted_at: datetime | None = None
        date_str = raw.get("dateCreation")
        if date_str:
            try:
                posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                posted_at = posted_at.replace(tzinfo=None)
            except (ValueError, TypeError):
                posted_at = None

        return RawOffer(
            source_offer_id=str(raw.get("id", "")),
            source_url=origine.get("urlOrigine") or "",
            title=raw.get("intitule") or "",
            description=raw.get("description"),
            contract_type=raw.get("typeContrat"),
            experience_level=raw.get("experienceLibelle"),
            remote_policy=None,
            salary_text=salaire.get("libelle"),
            location_raw=lieu.get("libelle"),
            posted_at=posted_at,
            company_name=entreprise.get("nom"),
            company_sector=raw.get("secteurActiviteLibelle"),
            company_size=None,
            raw=raw,
        )
