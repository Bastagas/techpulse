"""Routes /alerts — gestion des alertes email."""

from __future__ import annotations

import os
import secrets

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate
from sqlalchemy import select

from techpulse_scraper.db import get_session
from techpulse_scraper.models import Alert

blp = Blueprint("alerts", "alerts", url_prefix="/alerts", description="Alertes email")


class AlertCreateSchema(Schema):
    email = fields.Email(required=True)
    keyword = fields.Str(required=False, load_default=None)
    city = fields.Str(required=False, load_default=None)
    tech = fields.Str(required=False, load_default=None)
    contract = fields.Str(required=False, load_default=None)
    salary_min = fields.Int(required=False, load_default=None, validate=validate.Range(min=0))


class AlertResponseSchema(Schema):
    id = fields.Int()
    email = fields.Email()
    token = fields.Str()
    filter_keyword = fields.Str(allow_none=True)
    filter_city = fields.Str(allow_none=True)
    filter_tech = fields.Str(allow_none=True)
    filter_contract = fields.Str(allow_none=True)
    filter_salary_min = fields.Int(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime()
    last_notified_at = fields.DateTime(allow_none=True)
    notification_count = fields.Int()
    unsubscribe_url = fields.Str()


def _public_base_url() -> str:
    return os.environ.get("PUBLIC_FRONTEND_URL", "http://localhost:8000")


def _serialize(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "email": alert.email,
        "token": alert.token,
        "filter_keyword": alert.filter_keyword,
        "filter_city": alert.filter_city,
        "filter_tech": alert.filter_tech,
        "filter_contract": alert.filter_contract,
        "filter_salary_min": alert.filter_salary_min,
        "is_active": alert.is_active,
        "created_at": alert.created_at,
        "last_notified_at": alert.last_notified_at,
        "notification_count": alert.notification_count,
        "unsubscribe_url": f"{_public_base_url()}/unsubscribe.php?token={alert.token}",
    }


@blp.route("")
class AlertsList(MethodView):
    @blp.arguments(AlertCreateSchema)
    @blp.response(201, AlertResponseSchema)
    @blp.doc(tags=["alerts"])
    def post(self, data):
        """Crée une alerte email pour des critères donnés."""
        has_filter = any(
            data.get(k) for k in ("keyword", "city", "tech", "contract", "salary_min")
        )
        if not has_filter:
            abort(400, message="Au moins un filtre doit être fourni (keyword, city, tech, contract ou salary_min)")

        with get_session() as session:
            alert = Alert(
                email=data["email"],
                token=secrets.token_urlsafe(24)[:32],
                filter_keyword=data.get("keyword") or None,
                filter_city=data.get("city") or None,
                filter_tech=data.get("tech") or None,
                filter_contract=data.get("contract") or None,
                filter_salary_min=data.get("salary_min"),
                is_active=True,
            )
            session.add(alert)
            session.flush()
            session.refresh(alert)
            return _serialize(alert)


@blp.route("/<string:token>")
class AlertByToken(MethodView):
    @blp.response(200, AlertResponseSchema)
    @blp.doc(tags=["alerts"])
    def get(self, token: str):
        """Récupère une alerte via son token (pour page unsubscribe)."""
        with get_session() as session:
            alert = session.scalar(select(Alert).where(Alert.token == token))
            if alert is None:
                abort(404, message="Alerte introuvable")
            return _serialize(alert)

    @blp.doc(tags=["alerts"])
    def delete(self, token: str):
        """Désactive (soft-delete) une alerte via son token."""
        with get_session() as session:
            alert = session.scalar(select(Alert).where(Alert.token == token))
            if alert is None:
                abort(404, message="Alerte introuvable")
            alert.is_active = False
            return {"success": True, "message": "Alerte désactivée."}
