"""Pipeline de persistence — transforme un RawOffer en Offer + Company + tech_links.

Flow :
    1. get_or_create Company (par nom normalisé)
    2. normalise salaire, lieu
    3. calcule fingerprint
    4. find_existing_offer → INSERT ou UPDATE
    5. extrait technos, crée OfferTechnology links
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from techpulse_scraper.logger import logger
from techpulse_scraper.models import (
    Company,
    Offer,
    OfferTechnology,
    ScrapeRun,
    ScrapeStatus,
    Source,
)
from techpulse_scraper.parsers import (
    TechExtractor,
    detect_remote_policy,
    parse_location,
    parse_salary,
)
from techpulse_scraper.pipelines.deduplication import find_existing_offer
from techpulse_scraper.spiders.base import RawOffer
from techpulse_scraper.utils.fingerprint import offer_fingerprint

PersistResult = Literal["new", "updated", "skipped"]


class PersistencePipeline:
    """Gère la persistence d'un flux de RawOffer vers la BDD."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.extractor = TechExtractor(session)

    # ─── Companies ──────────────────────────────────
    def _get_or_create_company(self, name: str | None, sector: str | None = None) -> Company:
        display_name = (name or "Entreprise anonyme").strip()[:255]
        stmt = select(Company).where(Company.name == display_name)
        company = self.session.scalars(stmt).first()
        if company:
            company.last_seen_at = datetime.utcnow()
            if sector and not company.sector:
                company.sector = sector[:100]
            return company

        company = Company(
            name=display_name,
            sector=sector[:100] if sector else None,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
        )
        self.session.add(company)
        self.session.flush()  # récupère l'id
        return company

    # ─── Offers ─────────────────────────────────────
    def persist(self, raw: RawOffer, source: Source) -> PersistResult:
        """Insère ou met à jour une offre. Retourne 'new', 'updated' ou 'skipped'."""
        if not raw.source_offer_id or not raw.title:
            return "skipped"

        # Entreprise
        company = self._get_or_create_company(raw.company_name, raw.company_sector)

        # Location + salary + remote parsing
        location = parse_location(raw.location_raw)
        salary = parse_salary(raw.salary_text)
        remote = raw.remote_policy or detect_remote_policy(raw.title, raw.description)

        # Fingerprint
        fingerprint = offer_fingerprint(
            raw.title,
            company.name,
            location.city,
        )

        # Lookup existant
        existing = find_existing_offer(self.session, source, raw.source_offer_id, fingerprint)

        if existing:
            # Update : last_seen + champs mutables
            existing.title = raw.title[:500]
            existing.description = raw.description
            existing.contract_type = (raw.contract_type or "")[:50] or None
            existing.experience_level = (raw.experience_level or "")[:50] or None
            existing.salary_min = salary.min if salary else None
            existing.salary_max = salary.max if salary else None
            existing.remote_policy = remote or existing.remote_policy
            existing.is_active = True
            self.session.flush()
            self._update_tech_links(existing)
            return "updated"

        # Insert
        offer = Offer(
            company_id=company.id,
            source=source,
            source_offer_id=raw.source_offer_id[:255],
            source_url=(raw.source_url or "")[:1000],
            title=raw.title[:500],
            description=raw.description,
            description_html=raw.description_html,
            contract_type=(raw.contract_type or "")[:50] or None,
            experience_level=(raw.experience_level or "")[:50] or None,
            remote_policy=remote,
            salary_min=salary.min if salary else None,
            salary_max=salary.max if salary else None,
            salary_currency="EUR",
            city=location.city,
            department_code=location.department_code,
            posted_at=raw.posted_at,
            fingerprint=fingerprint,
            is_active=True,
        )
        self.session.add(offer)
        self.session.flush()
        self._update_tech_links(offer)
        return "new"

    def _update_tech_links(self, offer: Offer) -> None:
        """Extrait les technos du titre + description et (re)crée les liens."""
        extracted = self.extractor.extract(offer.title, offer.description)
        if not extracted:
            return

        # Supprime les anciens liens
        existing_ids = {link.technology_id for link in offer.tech_links}
        new_ids = {t.technology_id for t in extracted}

        # Add les nouveaux
        for t in extracted:
            if t.technology_id not in existing_ids:
                link = OfferTechnology(
                    offer_id=offer.id,
                    technology_id=t.technology_id,
                    confidence_score=Decimal(str(round(t.confidence, 2))),
                    extracted_by="regex",
                )
                self.session.add(link)

        # Remove les technos qui ne sont plus détectées (pour un update)
        for link in list(offer.tech_links):
            if link.technology_id not in new_ids:
                self.session.delete(link)

    # ─── ScrapeRun ─────────────────────────────────
    def start_run(self, spider_name: str) -> ScrapeRun:
        run = ScrapeRun(
            spider=spider_name,
            started_at=datetime.utcnow(),
            status=ScrapeStatus.RUNNING,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def finish_run(
        self,
        run: ScrapeRun,
        status: ScrapeStatus,
        found: int,
        new: int,
        updated: int,
        errors: int = 0,
        error_log: str | None = None,
        pages_fetched: int = 0,
    ) -> None:
        run.finished_at = datetime.utcnow()
        run.status = status
        run.offers_found = found
        run.offers_new = new
        run.offers_updated = updated
        run.errors_count = errors
        run.error_log = error_log
        run.pages_fetched = pages_fetched
        self.session.flush()
        logger.info(
            "Run {} {} : {} offres trouvées ({} new, {} updated, {} erreurs)",
            run.spider,
            status.value,
            found,
            new,
            updated,
            errors,
        )
