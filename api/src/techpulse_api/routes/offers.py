"""Routes /offers — liste paginée avec filtres + fiche détail."""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Offer, OfferTechnology, Technology

from techpulse_api.schemas import OfferSchema, OffersQueryArgs, PaginatedOffersSchema

blp = Blueprint(
    "offers",
    "offers",
    url_prefix="/offers",
    description="Offres d'emploi scrapées",
)


def _serialize_offer(offer: Offer) -> dict:
    """Transforme un Offer ORM en dict sérialisable (avec technos enrichies)."""
    return {
        "id": offer.id,
        "title": offer.title,
        "description": offer.description,
        "company_name": offer.company.name if offer.company else None,
        "company_sector": offer.company.sector if offer.company else None,
        "source": offer.source.value,
        "source_url": offer.source_url,
        "city": offer.city,
        "department_code": offer.department_code,
        "contract_type": offer.contract_type,
        "experience_level": offer.experience_level,
        "salary_min": offer.salary_min,
        "salary_max": offer.salary_max,
        "salary_currency": offer.salary_currency,
        "posted_at": offer.posted_at,
        "scraped_at": offer.scraped_at,
        "technologies": [
            {
                "canonical_name": link.technology.canonical_name,
                "display_name": link.technology.display_name,
                "category": link.technology.category.value,
            }
            for link in offer.tech_links
        ],
    }


@blp.route("")
class OffersList(MethodView):
    @blp.arguments(OffersQueryArgs, location="query")
    @blp.response(200, PaginatedOffersSchema)
    @blp.doc(tags=["offers"])
    def get(self, args):
        """Liste paginée des offres avec filtres optionnels."""
        page = max(1, int(args.get("page", 1)))
        per_page = min(100, max(1, int(args.get("per_page", 20))))

        with get_session() as session:
            stmt = (
                select(Offer)
                .where(Offer.is_active.is_(True))
                .options(
                    selectinload(Offer.company),
                    selectinload(Offer.tech_links).selectinload(OfferTechnology.technology),
                )
            )

            if args.get("keyword"):
                kw = f"%{args['keyword']}%"
                stmt = stmt.where((Offer.title.like(kw)) | (Offer.description.like(kw)))
            if args.get("city"):
                stmt = stmt.where(Offer.city == args["city"])
            if args.get("contract"):
                stmt = stmt.where(Offer.contract_type == args["contract"])
            if args.get("tech"):
                tech_cn = args["tech"]
                sub = (
                    select(Offer.id)
                    .join(Offer.tech_links)
                    .join(Technology)
                    .where(Technology.canonical_name == tech_cn)
                )
                stmt = stmt.where(Offer.id.in_(sub))

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = int(session.scalar(count_stmt) or 0)

            stmt = (
                stmt.order_by(Offer.posted_at.desc(), Offer.id.desc())
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            offers = session.scalars(stmt).unique().all()

            # Force load des relations avant fermeture de session
            items = [_serialize_offer(o) for o in offers]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": max(1, (total + per_page - 1) // per_page),
            }


@blp.route("/<int:offer_id>")
class OfferDetail(MethodView):
    @blp.response(200, OfferSchema)
    @blp.doc(tags=["offers"])
    def get(self, offer_id: int):
        """Fiche détail d'une offre."""
        with get_session() as session:
            offer = session.get(Offer, offer_id)
            if offer is None or not offer.is_active:
                abort(404, message=f"Offre {offer_id} introuvable")
            return _serialize_offer(offer)


@blp.route("/<int:offer_id>/similar")
class OfferSimilar(MethodView):
    @blp.doc(tags=["offers"])
    def get(self, offer_id: int):
        """Retourne les 5 offres les plus similaires (TF-IDF cosine).

        Le modèle doit être entraîné au préalable :
            python -m techpulse_api.ml.similarity train
        """
        from techpulse_api.ml.similarity import get_similar

        with get_session() as session:
            offer = session.get(Offer, offer_id)
            if offer is None:
                abort(404, message=f"Offre {offer_id} introuvable")

        similar = get_similar(offer_id)
        return {"available": len(similar) > 0, "items": similar}


@blp.route("/<int:offer_id>/salary-prediction")
class OfferSalaryPrediction(MethodView):
    @blp.doc(tags=["offers"])
    def get(self, offer_id: int):
        """Prédit une fourchette de salaire pour l'offre via scikit-learn.

        Le modèle RandomForest est entraîné sur les offres ayant un salaire
        renseigné (~127 offres). Renvoie un point estimé + fourchette P25-P75
        basée sur la dispersion des prédictions des arbres individuels.
        """
        from techpulse_api.ml.salary import predict_for_offer

        with get_session() as session:
            offer = session.get(Offer, offer_id)
            if offer is None:
                abort(404, message=f"Offre {offer_id} introuvable")

            prediction = predict_for_offer(session, offer_id)
            if prediction is None:
                return {
                    "available": False,
                    "reason": "Modèle non entraîné. Lance `python -m techpulse_api.ml.salary train`.",
                }

            return {
                "available": True,
                "prediction": {
                    "point": prediction.point,
                    "low": prediction.low,
                    "high": prediction.high,
                    "confidence": prediction.confidence,
                },
                "model": {
                    "training_size": prediction.training_size,
                    "feature_count": prediction.feature_count,
                },
                "actual": {
                    "salary_min": offer.salary_min,
                    "salary_max": offer.salary_max,
                },
            }
