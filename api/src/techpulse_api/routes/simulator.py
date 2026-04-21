"""Route simulateur salaire — prédit depuis un profil décrit par l'utilisateur.

Endpoint : POST /simulator/salary
Payload JSON : {
    "city": "Paris",
    "department": "75",
    "experience": "5 An(s)",
    "contract": "CDI",
    "technologies": ["python", "django", "postgresql"]
}
"""

from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

blp = Blueprint(
    "simulator",
    "simulator",
    url_prefix="/simulator",
    description="Simulateur salaire — prédit une fourchette depuis un profil décrit",
)


class SimulateSalaryRequest(Schema):
    city = fields.String(load_default=None, validate=validate.Length(max=80))
    department = fields.String(load_default=None, validate=validate.Length(max=10))
    experience = fields.String(load_default=None, validate=validate.Length(max=50))
    contract = fields.String(load_default=None, validate=validate.Length(max=50))
    technologies = fields.List(
        fields.String(validate=validate.Length(max=50)),
        load_default=list,
        validate=validate.Length(max=25),
    )


class SimulateSalaryResponse(Schema):
    available = fields.Boolean()
    reason = fields.String(required=False)
    prediction = fields.Dict(required=False)
    model = fields.Dict(required=False)


@blp.route("/salary")
class SimulateSalary(MethodView):
    @blp.arguments(SimulateSalaryRequest)
    @blp.response(200, SimulateSalaryResponse)
    @blp.doc(tags=["simulator"])
    def post(self, data: dict):
        """Prédit une fourchette de salaire pour un profil hypothétique.

        Utilise le même modèle RandomForest que `/offers/<id>/salary-prediction`,
        mais accepte des features brutes (technos, ville, expérience, contrat).
        """
        from techpulse_api.ml.salary import predict_from_features

        prediction = predict_from_features(
            city=data.get("city"),
            department=data.get("department"),
            experience=data.get("experience"),
            contract=data.get("contract"),
            technologies=data.get("technologies") or [],
        )

        if prediction is None:
            return {
                "available": False,
                "reason": "Modèle non entraîné. Lance `make retrain`.",
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
        }
