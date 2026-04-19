"""Génération de fingerprints SHA-256 pour déduplication cross-source.

Deux offres différentes sur 2 sources (France Travail + HelloWork) peuvent concerner
le même poste → on normalise titre + entreprise + ville puis on hash, ce qui permet
de détecter les doublons avant insertion.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize(text: str | None) -> str:
    """Lowercase, ASCII fold, collapse spaces, strip punctuation."""
    if not text:
        return ""
    # ASCII fold (é → e, ç → c, etc.)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase + remove non-alphanumeric
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def offer_fingerprint(title: str, company: str, city: str | None = None) -> str:
    """Fingerprint SHA-256 (64 chars) basé sur (title, company, city) normalisés."""
    key = "|".join([normalize(title), normalize(company), normalize(city or "")])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
