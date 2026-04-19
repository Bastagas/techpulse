"""Détection de la politique télétravail depuis le texte libre d'une offre.

Renvoie un label standardisé :
  - "full_remote"   : télétravail complet / 100 %
  - "hybrid"        : hybride / partiel / N jours
  - "on_site"       : pas de télétravail explicite / sur site
  - None            : rien d'exploitable dans le texte

L'approche est hybride : regex prioritaires pour le full_remote
(le moins ambigu), puis patterns hybrides, sinon on_site par défaut
si le texte est suffisamment long pour en décider.
"""

from __future__ import annotations

import re

# Ordre d'évaluation = priorité (plus spécifique d'abord)

# "Full remote", "Télétravail complet", "100% remote", "entièrement à distance"
_FULL_REMOTE = re.compile(
    r"(?:full|full\s*remote|100\s*%?\s*remote|100\s*%?\s*t[ée]l[ée]travail|"
    r"t[ée]l[ée]travail\s*(?:complet|total|int[ée]gral|100\s*%?)|"
    r"enti[èe]rement\s*(?:en\s*)?t[ée]l[ée]travail|"
    r"enti[èe]rement\s*[àa]\s*distance|"
    r"100\s*%?\s*(?:t[ée]l[ée]travail|[àa]\s*distance|remote)|"
    r"remote\s*(?:only|first|full-time)|"
    r"telework\s*full-time)",
    re.IGNORECASE,
)

# "Hybride", "2-3 jours de télétravail", "partiel"
_HYBRID = re.compile(
    r"(?:hybrid[ae]|"
    r"\d\s*(?:j|jour)s?\s*(?:de|/)?\s*(?:t[ée]l[ée]travail|remote|semaine)|"
    r"(?:t[ée]l[ée]travail|remote)\s*(?:hybrid[ae]|partiel|occasionnel|ponctuel)|"
    r"mix\s*(?:pr[ée]sentiel|t[ée]l[ée]travail|bureau)|"
    r"partiellement\s*(?:en\s*)?t[ée]l[ée]travail|"
    r"partiellement\s*[àa]\s*distance|"
    r"pr[ée]sentiel\s*(?:et|\+|/)?\s*t[ée]l[ée]travail|"
    r"t[ée]l[ée]travail\s*(?:et|\+|/)?\s*pr[ée]sentiel)",
    re.IGNORECASE,
)

# Marqueurs explicites d'on-site (sans télétravail)
_ON_SITE_EXPLICIT = re.compile(
    r"(?:pas\s*de\s*(?:t[ée]l[ée]travail|remote)|"
    r"aucun\s*(?:t[ée]l[ée]travail|remote)|"
    r"100\s*%?\s*(?:pr[ée]sentiel|bureau|sur\s*site)|"
    r"enti[èe]rement\s*(?:en\s*)?pr[ée]sentiel|"
    r"pr[ée]sence\s*(?:obligatoire|requise|physique)|"
    r"on-?site\s*only)",
    re.IGNORECASE,
)

# Mention de remote même si on n'a pas matché les patterns précédents
_REMOTE_KEYWORD = re.compile(
    r"\b(?:t[ée]l[ée]travail|remote|home.?office|[àa]\s*distance|homeoffice)\b",
    re.IGNORECASE,
)


def detect_remote_policy(*texts: str | None) -> str | None:
    """Détecte la politique télétravail depuis un ou plusieurs textes (title + description).

    Retourne "full_remote" | "hybrid" | "on_site" | None.
    """
    combined = " ".join(t for t in texts if t).lower()
    if not combined.strip():
        return None

    if _ON_SITE_EXPLICIT.search(combined):
        return "on_site"

    if _FULL_REMOTE.search(combined):
        return "full_remote"

    if _HYBRID.search(combined):
        return "hybrid"

    # Mention de remote sans pattern spécifique → probable hybride
    if _REMOTE_KEYWORD.search(combined):
        return "hybrid"

    # Rien trouvé → on assume on_site si le texte est long (fiche d'offre normale)
    if len(combined) > 500:
        return "on_site"

    return None
