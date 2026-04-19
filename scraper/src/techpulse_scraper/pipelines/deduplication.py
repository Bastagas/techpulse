"""Vérifie l'existence d'une offre en BDD avant insertion (via fingerprint)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from techpulse_scraper.models import Offer, Source


def find_existing_offer(
    session: Session,
    source: Source,
    source_offer_id: str,
    fingerprint: str,
) -> Offer | None:
    """Cherche une offre par (source, source_offer_id) puis par fingerprint.

    - Match exact `(source, source_offer_id)` → c'est la même offre, on update.
    - Sinon match par fingerprint → déduplication cross-source (ex. la même offre
      trouvée sur FT et HelloWork).
    """
    stmt = select(Offer).where(Offer.source == source, Offer.source_offer_id == source_offer_id)
    existing = session.scalars(stmt).first()
    if existing:
        return existing

    stmt = select(Offer).where(Offer.fingerprint == fingerprint)
    return session.scalars(stmt).first()
