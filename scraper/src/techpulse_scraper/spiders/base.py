"""Classe abstraite commune à tous les spiders.

Les spiders produisent des `RawOffer` (dataclass neutre) que la pipeline
de persistence consomme — découplage propre entre récupération et persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from techpulse_scraper.models import Source


@dataclass
class RawOffer:
    """Format intermédiaire entre le spider et la pipeline de persistence."""

    source_offer_id: str
    source_url: str
    title: str
    description: str | None = None
    description_html: str | None = None
    contract_type: str | None = None
    experience_level: str | None = None
    remote_policy: str | None = None
    salary_text: str | None = None
    location_raw: str | None = None
    posted_at: datetime | None = None
    company_name: str | None = None
    company_sector: str | None = None
    company_size: str | None = None
    raw: dict = field(default_factory=dict)


class BaseSpider(ABC):
    name: str = ""
    source: Source = Source.FRANCE_TRAVAIL  # override in subclass

    @abstractmethod
    async def scrape(self, limit: int | None = None) -> AsyncIterator[RawOffer]:
        """Yield raw offers. `limit=None` → pas de limite, tout récupérer."""
        raise NotImplementedError
        yield  # pour que mypy comprenne que c'est un async generator
