"""Recherche par similarité TF-IDF.

Approche : vectorisation des titres + descriptions via TF-IDF, puis cosine similarity.
Pour chaque offre, on précalcule le top N des offres les plus similaires et
on les stocke dans le modèle pickle.

Entraînement :
    python -m techpulse_api.ml.similarity train

Inference :
    from techpulse_api.ml.similarity import get_similar
    offers = get_similar(offer_id, top_n=5)
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Offer

MODEL_FILE = Path(__file__).parent / "similarity_model.pkl"

# Stopwords français classiques (courts)
FR_STOPWORDS = {
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "où", "à",
    "au", "aux", "en", "dans", "par", "pour", "sur", "avec", "sans", "ce",
    "cet", "cette", "ces", "que", "qui", "quoi", "dont", "son", "sa", "ses",
    "notre", "nos", "votre", "vos", "leur", "leurs", "est", "sont", "été",
    "être", "avoir", "fait", "faire", "plus", "moins", "tout", "tous", "toute",
    "toutes", "vous", "nous", "je", "tu", "il", "elle", "ils", "elles",
    "mais", "donc", "car", "ni", "si", "aussi", "très", "peut", "faut",
    "h/f", "f/h", "m/f",
}


def _prepare_corpus() -> tuple[list[int], list[str]]:
    """Charge tous les titres+descriptions."""
    with get_session() as session:
        offers = session.scalars(
            select(Offer).where(Offer.is_active.is_(True))
        ).all()
    ids = [o.id for o in offers]
    texts = [f"{o.title} {o.description or ''}"[:4000] for o in offers]
    return ids, texts


def train(top_n: int = 5) -> dict:
    """Entraîne le vectoriseur TF-IDF et précalcule le top N par offre."""
    ids, texts = _prepare_corpus()
    if len(ids) < 10:
        raise RuntimeError(f"Trop peu d'offres ({len(ids)}) pour entraîner.")

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words=list(FR_STOPWORDS),
        min_df=2,
        max_df=0.6,
        sublinear_tf=True,
    )
    tfidf = vectorizer.fit_transform(texts)

    # Similarité (matrice N × N)
    sim_matrix = cosine_similarity(tfidf)
    np.fill_diagonal(sim_matrix, 0)  # on ne matche pas une offre avec elle-même

    # Pour chaque offre, top N indices + scores
    top_similar: dict[int, list[tuple[int, float]]] = {}
    for i, offer_id in enumerate(ids):
        top_idx = np.argsort(-sim_matrix[i])[:top_n]
        top_similar[offer_id] = [
            (int(ids[j]), float(round(sim_matrix[i][j], 3)))
            for j in top_idx
            if sim_matrix[i][j] > 0.05
        ]

    metadata = {
        "n_offers": len(ids),
        "n_features": tfidf.shape[1],
        "top_n": top_n,
        "non_trivial_matches": sum(1 for v in top_similar.values() if len(v) > 0),
    }

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_FILE.open("wb") as f:
        pickle.dump({"top_similar": top_similar, "metadata": metadata}, f)
    return metadata


_cache: dict | None = None


def _load() -> dict | None:
    global _cache
    if _cache is not None:
        return _cache
    if not MODEL_FILE.exists():
        return None
    with MODEL_FILE.open("rb") as f:
        _cache = pickle.load(f)  # noqa: S301
    return _cache


def get_similar(offer_id: int) -> list[dict]:
    """Retourne les offres similaires à l'offre donnée, enrichies avec title/company/city."""
    data = _load()
    if data is None:
        return []
    similar = data["top_similar"].get(offer_id, [])
    if not similar:
        return []

    similar_ids = [s[0] for s in similar]

    from sqlalchemy.orm import selectinload

    with get_session() as session:
        offers = session.scalars(
            select(Offer)
            .options(selectinload(Offer.company))
            .where(Offer.id.in_(similar_ids))
        ).all()

        # Construction du résultat dans le scope de la session pour éviter DetachedInstanceError
        by_id = {o.id: o for o in offers}
        result = []
        for oid, score in similar:
            o = by_id.get(oid)
            if o is None:
                continue
            result.append({
                "id": o.id,
                "title": o.title,
                "company": o.company.name if o.company else None,
                "city": o.city,
                "score": score,
            })
    return result


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] != "train":
        print("Usage: python -m techpulse_api.ml.similarity train")
        return 1
    print("━━━ Entraînement TF-IDF similarité ━━━")
    metadata = train(top_n=5)
    print(f"✓ {metadata['n_offers']} offres vectorisées sur {metadata['n_features']} features")
    print(f"  {metadata['non_trivial_matches']} offres ont au moins 1 match similaire")
    print(f"\n  Modèle : {MODEL_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
