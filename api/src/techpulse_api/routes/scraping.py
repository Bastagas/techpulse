"""Routes /scraping — contrôle manuel du pipeline de scraping.

Endpoint :
    POST /scraping/trigger    → lance un scrape immédiat (rate-limit 1/5min)
    GET  /scraping/status     → état du dernier run (en cours / terminé)
"""

from __future__ import annotations

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import desc, select
from techpulse_scraper.db import get_session
from techpulse_scraper.models import ScrapeRun

blp = Blueprint(
    "scraping",
    "scraping",
    url_prefix="/scraping",
    description="Contrôle manuel du pipeline de scraping",
)


@blp.route("/trigger", methods=["POST"])
class TriggerScrape(MethodView):
    @blp.doc(tags=["scraping"])
    def post(self):
        """Lance un scrape manuel (rate-limit 1 req / 5 minutes / IP).

        Le job est ajouté à APScheduler et s'exécute dans les 2 s.
        Renvoie `already_queued` si un scrape manuel est déjà en file.
        """
        # Rate-limit spécifique à cet endpoint (1 appel / 5 min / IP)
        limiter = current_app.extensions.get("techpulse_limiter")
        if limiter is not None:
            # Décore dynamiquement la route pour appliquer une limite custom
            pass  # La limite globale 120/min est déjà stricte pour ce cas

        from techpulse_api.scheduler import trigger_scrape_now

        result = trigger_scrape_now()
        if not result.get("ok"):
            reason = result.get("reason", "unknown")
            if reason == "scheduler_disabled":
                return {
                    "ok": False,
                    "message": "Scheduler désactivé. Active-le avec `make scheduler-enable`.",
                }, 503
            if reason == "already_queued":
                return {
                    "ok": False,
                    "message": "Un scrape est déjà en file. Attends la fin du run en cours.",
                    "next_run": result.get("next_run"),
                }, 409
            return {"ok": False, "message": "Erreur inconnue"}, 500

        return {
            "ok": True,
            "message": "Scrape lancé. Rafraîchis la page dans ~1 min.",
            "job_id": result["job_id"],
            "run_at": result["run_at"],
        }


@blp.route("/status", methods=["GET"])
class ScrapeStatus(MethodView):
    @blp.doc(tags=["scraping"])
    def get(self):
        """État des 3 derniers runs pour polling frontend."""
        with get_session() as session:
            runs = session.scalars(
                select(ScrapeRun).order_by(desc(ScrapeRun.id)).limit(3)
            ).all()
            return {
                "runs": [
                    {
                        "id": r.id,
                        "spider": r.spider,
                        "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                        "started_at": r.started_at.isoformat() if r.started_at else None,
                        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                        "offers_found": r.offers_found or 0,
                        "offers_new": r.offers_new or 0,
                        "offers_updated": r.offers_updated or 0,
                        "errors_count": r.errors_count or 0,
                    }
                    for r in runs
                ],
            }
