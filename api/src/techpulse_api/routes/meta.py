"""Routes /health, /version — métadonnées et santé."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import func, select
from techpulse_scraper import __version__ as scraper_version
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Offer

from techpulse_api import __version__
from techpulse_api.schemas import HealthSchema, VersionSchema

blp = Blueprint("meta", "meta", description="Métadonnées et santé de l'API")


@blp.route("/health")
class Health(MethodView):
    @blp.response(200, HealthSchema)
    @blp.doc(tags=["meta"])
    def get(self):
        """Santé de l'API + connexion BDD."""
        try:
            with get_session() as session:
                n = int(session.scalar(select(func.count()).select_from(Offer)) or 0)
            return {"status": "ok", "database": "connected", "offers_count": n}
        except Exception:
            return {"status": "degraded", "database": "unreachable", "offers_count": 0}


@blp.route("/version")
class Version(MethodView):
    @blp.response(200, VersionSchema)
    @blp.doc(tags=["meta"])
    def get(self):
        """Version de l'API et du scraper."""
        return {"version": __version__, "scraper_version": scraper_version}
