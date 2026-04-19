"""Registry des spiders disponibles."""

from techpulse_scraper.spiders.base import BaseSpider, RawOffer
from techpulse_scraper.spiders.francetravail_api import FranceTravailSpider

SPIDER_REGISTRY: dict[str, type[BaseSpider]] = {
    "france_travail": FranceTravailSpider,
}

__all__ = ["SPIDER_REGISTRY", "BaseSpider", "RawOffer"]
