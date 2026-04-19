"""Pipelines — dédup et persistence."""

from techpulse_scraper.pipelines.deduplication import find_existing_offer
from techpulse_scraper.pipelines.persistence import PersistencePipeline, PersistResult

__all__ = ["PersistencePipeline", "PersistResult", "find_existing_offer"]
