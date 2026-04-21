"""Flask application factory — API REST TechPulse.

Endpoints exposés :
  GET  /offers                   (pagination + filtres)
  GET  /offers/<id>
  GET  /stats/top-techs
  GET  /stats/salaries
  GET  /stats/cities
  GET  /stats/timeline
  GET  /stats/sources
  GET  /health
  GET  /version

Documentation Swagger UI :
  http://localhost:5000/docs
"""

from __future__ import annotations

import hashlib

from flask import Flask, Response, make_response, redirect, request, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_smorest import Api


def create_app() -> Flask:
    app = Flask(__name__)

    # ─── Rate limiter (anti-abus) ───────────────────
    # 120 req/min par IP par défaut ; endpoints lourds peuvent override.
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["120 per minute", "2000 per hour"],
        storage_uri="memory://",
        headers_enabled=True,
    )
    app.extensions["techpulse_limiter"] = limiter

    # ─── Cache ETag + Cache-Control sur GET ─────────
    @app.after_request
    def add_cache_headers(response: Response) -> Response:
        if request.method != "GET" or response.status_code != 200:
            return response
        path = request.path
        # Routes lourdes (analytics) → cache 60s
        if path.startswith("/stats/") or path == "/offers":
            response.headers.setdefault("Cache-Control", "public, max-age=60")
        # Endpoints quasi-statiques
        elif path in ("/health", "/version"):
            response.headers.setdefault("Cache-Control", "public, max-age=10")
        # ETag pour JSON responses
        ctype = response.headers.get("Content-Type", "")
        if "application/json" in ctype and response.data:
            etag = hashlib.md5(response.data).hexdigest()
            response.headers["ETag"] = f'W/"{etag}"'
            if request.headers.get("If-None-Match") == f'W/"{etag}"':
                return make_response("", 304)
        return response

    # ─── Config flask-smorest / OpenAPI ─────────────
    app.config["API_TITLE"] = "TechPulse API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["OPENAPI_REDOC_PATH"] = "redoc"
    app.config["OPENAPI_REDOC_URL"] = (
        "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )
    app.config["API_SPEC_OPTIONS"] = {
        "info": {
            "description": (
                "API REST de l'observatoire TechPulse — expose les offres d'emploi tech "
                "scrapées depuis France Travail, HelloWork et APEC, ainsi que des "
                "statistiques agrégées (top technos, distributions de salaires, géographie)."
            ),
            "contact": {"name": "Bastien Ruedas", "url": "https://github.com/Bastagas/techpulse"},
            "license": {"name": "MIT"},
        },
        "servers": [
            {"url": "http://localhost:5001", "description": "Dev local"},
        ],
        "tags": [
            {"name": "offers", "description": "Offres d'emploi"},
            {"name": "stats", "description": "Statistiques agrégées"},
            {"name": "meta", "description": "Santé et métadonnées"},
        ],
    }

    CORS(app, resources={r"/*": {"origins": "*"}})
    api = Api(app)

    # ─── Scheduler (APScheduler, OFF par défaut) ───
    from techpulse_api.scheduler import init_scheduler

    init_scheduler()

    # ─── Blueprints ────────────────────────────────
    from techpulse_api.routes import alerts, meta, offers, simulator, stats

    api.register_blueprint(meta.blp)
    api.register_blueprint(offers.blp)
    api.register_blueprint(stats.blp)
    api.register_blueprint(alerts.blp)
    api.register_blueprint(simulator.blp)

    # Root → redirige vers Swagger UI
    @app.route("/")
    def index():
        return redirect(url_for("api-docs.openapi_swagger_ui"))

    return app


def run() -> None:
    """Lance le serveur de dev.

    Port par défaut : 5001 (port 5000 occupé par AirPlay Receiver sur macOS).
    Override possible via la variable d'env API_PORT.
    """
    import os

    port = int(os.environ.get("API_PORT", 5001))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    run()
