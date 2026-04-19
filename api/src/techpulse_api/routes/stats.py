"""Routes /stats — agrégations pour dashboard analytique."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import func, select
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Offer, OfferTechnology, Technology

from techpulse_api.schemas import (
    CityCountSchema,
    SalaryDistributionSchema,
    SourceStatSchema,
    TimelinePointSchema,
    TopTechItemSchema,
)

blp = Blueprint(
    "stats",
    "stats",
    url_prefix="/stats",
    description="Statistiques agrégées",
)


@blp.route("/top-techs")
class TopTechs(MethodView):
    @blp.response(200, TopTechItemSchema(many=True))
    @blp.doc(tags=["stats"])
    def get(self):
        """Top technologies par nombre d'offres actives."""
        limit = 20
        with get_session() as session:
            rows = session.execute(
                select(
                    Technology.canonical_name,
                    Technology.display_name,
                    Technology.category,
                    func.count(func.distinct(OfferTechnology.offer_id)).label("count"),
                )
                .join(OfferTechnology, OfferTechnology.technology_id == Technology.id)
                .join(Offer, Offer.id == OfferTechnology.offer_id)
                .where(Offer.is_active.is_(True))
                .group_by(Technology.id)
                .order_by(func.count(func.distinct(OfferTechnology.offer_id)).desc())
                .limit(limit)
            ).all()
        return [
            {
                "name": r.canonical_name,
                "display_name": r.display_name,
                "category": r.category.value if hasattr(r.category, "value") else str(r.category),
                "count": int(r.count),
            }
            for r in rows
        ]


@blp.route("/salaries")
class SalaryStats(MethodView):
    @blp.response(200, SalaryDistributionSchema)
    @blp.doc(tags=["stats"])
    def get(self):
        """Distribution des salaires (offres ayant au moins salary_min)."""
        with get_session() as session:
            values = [
                row[0]
                for row in session.execute(
                    select(Offer.salary_min).where(
                        Offer.salary_min.is_not(None), Offer.is_active.is_(True)
                    )
                ).all()
            ]
        if not values:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "p25": None,
                "p75": None,
                "min": None,
                "max": None,
            }
        values.sort()
        n = len(values)

        def pct(p: float) -> int:
            idx = min(n - 1, int(p * (n - 1)))
            return int(values[idx])

        return {
            "count": n,
            "mean": round(sum(values) / n, 2),
            "median": pct(0.5),
            "p25": pct(0.25),
            "p75": pct(0.75),
            "min": values[0],
            "max": values[-1],
        }


@blp.route("/cities")
class CitiesStats(MethodView):
    @blp.response(200, CityCountSchema(many=True))
    @blp.doc(tags=["stats"])
    def get(self):
        """Top villes par nombre d'offres."""
        with get_session() as session:
            rows = session.execute(
                select(
                    Offer.city,
                    Offer.department_code,
                    func.count().label("count"),
                )
                .where(Offer.city.is_not(None), Offer.is_active.is_(True))
                .group_by(Offer.city, Offer.department_code)
                .order_by(func.count().desc())
                .limit(30)
            ).all()
        return [
            {"city": r.city, "department_code": r.department_code, "count": int(r.count)}
            for r in rows
        ]


@blp.route("/timeline")
class TimelineStats(MethodView):
    @blp.response(200, TimelinePointSchema(many=True))
    @blp.doc(tags=["stats"])
    def get(self):
        """Timeline des offres publiées par jour (30 derniers jours)."""
        with get_session() as session:
            rows = session.execute(
                select(
                    func.date(Offer.posted_at).label("d"),
                    func.count().label("c"),
                )
                .where(Offer.posted_at.is_not(None), Offer.is_active.is_(True))
                .group_by(func.date(Offer.posted_at))
                .order_by(func.date(Offer.posted_at).desc())
                .limit(30)
            ).all()
        return [{"date": r.d, "count": int(r.c)} for r in reversed(rows)]


@blp.route("/sources")
class SourcesStats(MethodView):
    @blp.response(200, SourceStatSchema(many=True))
    @blp.doc(tags=["stats"])
    def get(self):
        """Répartition des offres par source (France Travail, HelloWork…)."""
        with get_session() as session:
            rows = session.execute(
                select(Offer.source, func.count().label("count"))
                .where(Offer.is_active.is_(True))
                .group_by(Offer.source)
                .order_by(func.count().desc())
            ).all()
        return [
            {
                "source": r.source.value if hasattr(r.source, "value") else str(r.source),
                "count": int(r.count),
            }
            for r in rows
        ]


@blp.route("/tech-correlations")
class TechCorrelations(MethodView):
    @blp.doc(tags=["stats"])
    def get(self):
        """Matrice de corrélation P(B|A) entre les top N technologies.

        Retourne la liste des technos (top_n=12) et toutes les paires (a, b) avec :
          - count : nombre d'offres actives mentionnant les deux
          - conf  : P(b | a) = count / offres_avec_a
        """
        top_n = 12
        with get_session() as session:
            top_rows = session.execute(
                select(
                    Technology.id,
                    Technology.display_name,
                    func.count(func.distinct(OfferTechnology.offer_id)).label("count"),
                )
                .join(OfferTechnology, OfferTechnology.technology_id == Technology.id)
                .join(Offer, Offer.id == OfferTechnology.offer_id)
                .where(Offer.is_active.is_(True))
                .group_by(Technology.id)
                .order_by(func.count(func.distinct(OfferTechnology.offer_id)).desc())
                .limit(top_n)
            ).all()

            techs = [
                {"id": r.id, "name": r.display_name, "count": int(r.count)} for r in top_rows
            ]
            if len(techs) < 2:
                return {"techs": techs, "pairs": []}

            top_ids = [t["id"] for t in techs]
            count_by_id = {t["id"]: t["count"] for t in techs}

            ot_a = OfferTechnology.__table__.alias("ota")
            ot_b = OfferTechnology.__table__.alias("otb")
            pair_rows = session.execute(
                select(
                    ot_a.c.technology_id.label("a_id"),
                    ot_b.c.technology_id.label("b_id"),
                    func.count(func.distinct(ot_a.c.offer_id)).label("count"),
                )
                .join(ot_b, (ot_a.c.offer_id == ot_b.c.offer_id) & (ot_a.c.technology_id != ot_b.c.technology_id))
                .join(Offer, Offer.id == ot_a.c.offer_id)
                .where(
                    Offer.is_active.is_(True),
                    ot_a.c.technology_id.in_(top_ids),
                    ot_b.c.technology_id.in_(top_ids),
                )
                .group_by(ot_a.c.technology_id, ot_b.c.technology_id)
            ).all()

            name_by_id = {t["id"]: t["name"] for t in techs}
            pairs = [
                {
                    "a": name_by_id[r.a_id],
                    "b": name_by_id[r.b_id],
                    "count": int(r.count),
                    "conf": round(r.count / count_by_id[r.a_id], 3) if count_by_id[r.a_id] else 0.0,
                }
                for r in pair_rows
                if r.a_id in name_by_id and r.b_id in name_by_id
            ]

        return {
            "techs": [{"name": t["name"], "count": t["count"]} for t in techs],
            "pairs": pairs,
        }


@blp.route("/runs")
class Runs(MethodView):
    @blp.doc(tags=["stats"])
    def get(self):
        """Historique des derniers runs de scraping (monitoring)."""
        from techpulse_scraper.models import ScrapeRun

        from techpulse_api.scheduler import get_next_run

        with get_session() as session:
            rows = (
                session.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(20))
                .scalars()
                .all()
            )

        next_run = get_next_run()
        return {
            "scheduler": {
                "enabled": next_run is not None,
                "next_run_at": next_run.isoformat() if next_run else None,
            },
            "recent_runs": [
                {
                    "id": r.id,
                    "spider": r.spider,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "offers_found": r.offers_found,
                    "offers_new": r.offers_new,
                    "offers_updated": r.offers_updated,
                    "errors_count": r.errors_count,
                }
                for r in rows
            ],
        }
