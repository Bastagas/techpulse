"""CLI TechPulse scraper.

Usage :
    python -m techpulse_scraper run --spider=all --limit=100
    python -m techpulse_scraper run --spider=france_travail --limit=50
    python -m techpulse_scraper stats
"""

from __future__ import annotations

import asyncio
import sys
from collections import Counter

import click
from sqlalchemy import func, select

from techpulse_scraper.db import get_session
from techpulse_scraper.logger import logger
from techpulse_scraper.models import (
    Offer,
    OfferTechnology,
    ScrapeStatus,
    Technology,
)
from techpulse_scraper.pipelines import PersistencePipeline
from techpulse_scraper.spiders import SPIDER_REGISTRY


@click.group()
def cli() -> None:
    """TechPulse scraper."""


@cli.command()
@click.option(
    "--spider",
    type=click.Choice(["all", *SPIDER_REGISTRY.keys()]),
    default="all",
    help="Spider(s) à exécuter.",
)
@click.option("--limit", type=int, default=None, help="Max offres par spider (défaut : illimité).")
def run(spider: str, limit: int | None) -> None:
    """Lance le scraping (un ou tous les spiders)."""
    targets = SPIDER_REGISTRY if spider == "all" else {spider: SPIDER_REGISTRY[spider]}
    logger.info("Démarrage : {} spider(s), limit={}", len(targets), limit or "∞")
    asyncio.run(_run(targets, limit))


async def _run(targets: dict, limit: int | None) -> None:
    for name, spider_cls in targets.items():
        await _run_spider(name, spider_cls(), limit)


async def _run_spider(name: str, spider, limit: int | None) -> None:  # noqa: ANN001
    stats = Counter()
    error_log: list[str] = []

    with get_session() as session:
        pipeline = PersistencePipeline(session)
        run_row = pipeline.start_run(name)

        try:
            async for raw_offer in spider.scrape(limit=limit):
                try:
                    result = pipeline.persist(raw_offer, spider.source)
                    stats[result] += 1
                    if stats["new"] + stats["updated"] + stats["skipped"]:
                        total = stats["new"] + stats["updated"] + stats["skipped"]
                        if total % 50 == 0:
                            logger.info(
                                "  … {} offres traitées ({}n / {}u / {}s)",
                                total,
                                stats["new"],
                                stats["updated"],
                                stats["skipped"],
                            )
                except Exception as exc:
                    stats["error"] += 1
                    error_log.append(f"{raw_offer.source_offer_id}: {exc}")
                    logger.exception("Erreur sur l'offre {}", raw_offer.source_offer_id)

            status = ScrapeStatus.SUCCESS if stats["error"] == 0 else ScrapeStatus.PARTIAL
            pipeline.finish_run(
                run_row,
                status=status,
                found=stats["new"] + stats["updated"] + stats["skipped"],
                new=stats["new"],
                updated=stats["updated"],
                errors=stats["error"],
                error_log="\n".join(error_log[:50]) if error_log else None,
            )
        except Exception as exc:
            logger.exception("Spider {} failed", name)
            pipeline.finish_run(
                run_row,
                status=ScrapeStatus.FAILED,
                found=stats["new"] + stats["updated"] + stats["skipped"],
                new=stats["new"],
                updated=stats["updated"],
                errors=stats["error"] + 1,
                error_log=str(exc),
            )


@cli.command()
@click.option("--limit", type=int, default=None, help="Max villes à géocoder (défaut : toutes).")
def geocode(limit: int | None) -> None:
    """Géocode les villes des offres via l'API Adresse Data Gouv."""
    from techpulse_scraper.utils.geocoder import geocode_cities_sync

    with get_session() as session:
        resolved, skipped = geocode_cities_sync(session, limit=limit)
    click.echo(
        f"\n✓ Géocodage terminé : {resolved} offres mises à jour, {skipped} villes non trouvées"
    )


@cli.command()
def stats() -> None:
    """Affiche quelques stats rapides sur le contenu de la BDD."""
    with get_session() as session:
        total_offers = session.scalar(select(func.count()).select_from(Offer)) or 0
        active = session.scalar(select(func.count()).select_from(Offer).where(Offer.is_active)) or 0
        with_salary = (
            session.scalar(
                select(func.count()).select_from(Offer).where(Offer.salary_min.is_not(None))
            )
            or 0
        )

        click.echo("\n━━━ Stats TechPulse ━━━")
        click.echo(f"Offres totales        : {total_offers}")
        click.echo(f"  dont actives        : {active}")
        click.echo(f"  avec salaire        : {with_salary}")

        click.echo("\nTop 10 technologies :")
        top_techs = session.execute(
            select(Technology.display_name, func.count(OfferTechnology.offer_id).label("n"))
            .join(OfferTechnology, OfferTechnology.technology_id == Technology.id)
            .group_by(Technology.id)
            .order_by(func.count(OfferTechnology.offer_id).desc())
            .limit(10)
        ).all()
        for name, n in top_techs:
            click.echo(f"  {name:25s} {n}")
        click.echo("")


def main() -> int:
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
