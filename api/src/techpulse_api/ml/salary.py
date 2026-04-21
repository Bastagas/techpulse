"""Prédiction de salaire via RandomForest.

Entraînement :
    python -m techpulse_api.ml.salary train

Inference via le singleton :
    from techpulse_api.ml.salary import predict_for_offer
    result = predict_for_offer(session, offer_id)

Modèle : `RandomForestRegressor(n_estimators=100)`
Features : technos (one-hot), ville, département, experience_level, contract_type
Target : salary_min (filtré aux valeurs plausibles)
"""

from __future__ import annotations

import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline
from sqlalchemy import select
from sqlalchemy.orm import Session
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Offer

MODEL_FILE = Path(__file__).parent / "salary_model.pkl"

# Bornes plausibles pour le salaire annuel en €
SALARY_MIN_CLIP = 20_000
SALARY_MAX_CLIP = 200_000


@dataclass
class SalaryPrediction:
    point: int
    low: int
    high: int
    confidence: float  # 0..1 basé sur la dispersion des arbres
    training_size: int
    feature_count: int


_cached_pipeline: Pipeline | None = None
_cached_metadata: dict[str, Any] | None = None


def _build_feature_dict(offer: Offer) -> dict[str, Any]:
    """Transforme une offre en dict de features pour DictVectorizer."""
    features: dict[str, Any] = {
        "city": offer.city or "unknown",
        "department": offer.department_code or "unknown",
        "experience": (offer.experience_level or "unknown")[:50],
        "contract": (offer.contract_type or "unknown")[:50],
    }
    # Technos → features binaires
    for link in offer.tech_links:
        if link.technology is not None:
            features[f"tech_{link.technology.canonical_name}"] = 1
    return features


def _load_training_data(session: Session) -> tuple[list[dict], list[int]]:
    """Charge les offres avec salaire plausible + leurs features."""
    offers = session.execute(
        select(Offer)
        .where(
            Offer.salary_min.is_not(None),
            Offer.salary_min >= SALARY_MIN_CLIP,
            Offer.salary_min <= SALARY_MAX_CLIP,
            Offer.is_active.is_(True),
        )
    ).scalars().all()

    features_list: list[dict] = []
    targets: list[int] = []
    for offer in offers:
        # Charge explicitement la relation tech_links pour éviter les N+1 lazy loads
        _ = list(offer.tech_links)
        features_list.append(_build_feature_dict(offer))
        targets.append(int(offer.salary_min))
    return features_list, targets


def train() -> dict[str, Any]:
    """Entraîne le modèle, le pickle sur disque et renvoie les métadonnées."""
    with get_session() as session:
        features_list, targets = _load_training_data(session)

    n = len(features_list)
    if n < 20:
        raise RuntimeError(
            f"Pas assez d'offres avec salaire pour entraîner ({n} < 20). "
            "Lance plus de scraping d'abord."
        )

    pipeline = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("model", RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(features_list, targets)

    # Score R² sur le training set (pas sur un vrai test set par simplicité avec n petit)
    r2 = pipeline.score(features_list, targets)

    feature_names = pipeline.named_steps["vectorizer"].get_feature_names_out()

    metadata = {
        "training_size": n,
        "feature_count": len(feature_names),
        "r2_train": float(r2),
        "salary_median": float(np.median(targets)),
        "salary_mean": float(np.mean(targets)),
    }

    # Importance des features
    importances = pipeline.named_steps["model"].feature_importances_
    top_importances = sorted(
        zip(feature_names, importances, strict=False),
        key=lambda x: -x[1]
    )[:15]
    metadata["top_features"] = [
        {"name": str(name), "importance": round(float(imp), 4)}
        for name, imp in top_importances
    ]

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_FILE.open("wb") as f:
        pickle.dump({"pipeline": pipeline, "metadata": metadata}, f)

    global _cached_pipeline, _cached_metadata
    _cached_pipeline = pipeline
    _cached_metadata = metadata
    return metadata


def _load_model() -> tuple[Pipeline | None, dict[str, Any] | None]:
    """Charge le modèle depuis disque (avec cache mémoire)."""
    global _cached_pipeline, _cached_metadata
    if _cached_pipeline is not None:
        return _cached_pipeline, _cached_metadata
    if not MODEL_FILE.exists():
        return None, None
    with MODEL_FILE.open("rb") as f:
        data = pickle.load(f)  # noqa: S301 (modèle local, pas d'input externe)
    _cached_pipeline = data["pipeline"]
    _cached_metadata = data["metadata"]
    return _cached_pipeline, _cached_metadata


def predict_for_offer(session: Session, offer_id: int) -> SalaryPrediction | None:
    """Prédit le salaire pour une offre donnée.

    Retourne None si le modèle n'est pas entraîné.
    """
    pipeline, metadata = _load_model()
    if pipeline is None:
        return None

    offer = session.get(Offer, offer_id)
    if offer is None:
        return None
    _ = list(offer.tech_links)  # force load

    features = _build_feature_dict(offer)

    # Prédictions individuelles de chaque arbre → dispersion pour fourchette
    rf = pipeline.named_steps["model"]
    vectorizer = pipeline.named_steps["vectorizer"]
    X = vectorizer.transform([features])  # noqa: N806 (convention scikit-learn)
    tree_predictions = np.array([tree.predict(X)[0] for tree in rf.estimators_])

    point = float(np.mean(tree_predictions))
    low = float(np.percentile(tree_predictions, 25))
    high = float(np.percentile(tree_predictions, 75))
    std = float(np.std(tree_predictions))

    # Confidence : plus la dispersion est faible, plus on est confiant
    # std de 0 € = confidence 1, std de 15k € = confidence 0
    confidence = max(0.0, min(1.0, 1.0 - std / 15_000.0))

    return SalaryPrediction(
        point=int(round(point)),
        low=int(round(low)),
        high=int(round(high)),
        confidence=round(confidence, 2),
        training_size=metadata["training_size"],
        feature_count=metadata["feature_count"],
    )


def get_metadata() -> dict[str, Any] | None:
    """Renvoie les métadonnées du modèle entraîné (pour /stats/model)."""
    _, metadata = _load_model()
    return metadata


def predict_from_features(
    city: str | None,
    department: str | None,
    experience: str | None,
    contract: str | None,
    technologies: list[str],
) -> SalaryPrediction | None:
    """Prédit un salaire depuis des features brutes (sans offer_id existante).

    Utilisé par le simulateur salaire : l'utilisateur décrit un profil,
    on renvoie une fourchette estimée.
    """
    pipeline, metadata = _load_model()
    if pipeline is None:
        return None

    features: dict[str, Any] = {
        "city": (city or "unknown")[:50],
        "department": (department or "unknown")[:10],
        "experience": (experience or "unknown")[:50],
        "contract": (contract or "unknown")[:50],
    }
    for tech in technologies:
        if tech:
            features[f"tech_{tech.strip().lower()}"] = 1

    rf = pipeline.named_steps["model"]
    vectorizer = pipeline.named_steps["vectorizer"]
    X = vectorizer.transform([features])  # noqa: N806 (convention scikit-learn)
    tree_predictions = np.array([tree.predict(X)[0] for tree in rf.estimators_])

    point = float(np.mean(tree_predictions))
    low = float(np.percentile(tree_predictions, 25))
    high = float(np.percentile(tree_predictions, 75))
    std = float(np.std(tree_predictions))
    confidence = max(0.0, min(1.0, 1.0 - std / 15_000.0))

    return SalaryPrediction(
        point=int(round(point)),
        low=int(round(low)),
        high=int(round(high)),
        confidence=round(confidence, 2),
        training_size=metadata["training_size"],
        feature_count=metadata["feature_count"],
    )


def main() -> int:
    """CLI : python -m techpulse_api.ml.salary train"""
    if len(sys.argv) < 2 or sys.argv[1] != "train":
        print("Usage: python -m techpulse_api.ml.salary train")
        return 1
    print("━━━ Entraînement du modèle salaire ━━━")
    metadata = train()
    print(f"✓ Modèle entraîné sur {metadata['training_size']} offres")
    print(f"  Features           : {metadata['feature_count']}")
    print(f"  R² training        : {metadata['r2_train']:.3f}")
    print(f"  Salaire médian     : {metadata['salary_median']:.0f} €")
    print(f"  Salaire moyen      : {metadata['salary_mean']:.0f} €")
    print("\n  Top 10 features les plus importantes :")
    for f in metadata["top_features"][:10]:
        print(f"    {f['name']:40s} {f['importance']:.4f}")
    print(f"\n  Modèle sauvegardé dans : {MODEL_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
