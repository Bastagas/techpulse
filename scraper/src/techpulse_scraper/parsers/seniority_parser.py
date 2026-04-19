"""Classification du niveau de séniorité depuis `experience_level` et `title`.

Retourne une classe standardisée :
  - "junior"    : 0-2 ans / débutant accepté / stage / alternance
  - "mid"       : 2-5 ans / confirmé
  - "senior"    : 5+ ans / senior / expert
  - "lead"      : lead / principal / staff / head / cto / chef de projet

Approche hybride : regex prioritaires sur les labels d'expérience (France Travail)
+ keywords dans le titre. Plus simple qu'un vrai ML mais très précis sur les data FR.
"""

from __future__ import annotations

import re

# Titres typiques
_LEAD_TITLE = re.compile(
    r"\b(lead|principal|staff|head\s*of|cto|cio|vp|directeur|chief|architect(?:e)?(?:\s|$))",
    re.IGNORECASE,
)
_SENIOR_TITLE = re.compile(r"\b(senior|sr\.|expert|confirm[ée]|exp[ée]riment[ée])", re.IGNORECASE)
_JUNIOR_TITLE = re.compile(
    r"\b(junior|jr\.|stage|stagiaire|alternance|alternant|apprenti|apprentie|d[ée]butant|graduate)",
    re.IGNORECASE,
)

# Extraction d'un nombre d'années du champ experience
_YEARS = re.compile(r"(\d+)\s*(?:an[s]?|ann[ée]es?|year[s]?)", re.IGNORECASE)


def detect_seniority(title: str | None, experience_level: str | None = None) -> str | None:
    """Renvoie 'junior' | 'mid' | 'senior' | 'lead' ou None."""
    title = (title or "").strip()
    experience_level = (experience_level or "").strip()

    # 1. Patterns forts dans le titre
    if title and _LEAD_TITLE.search(title):
        return "lead"
    if title and _SENIOR_TITLE.search(title):
        return "senior"
    if title and _JUNIOR_TITLE.search(title):
        return "junior"

    # 2. Keywords dans experience_level
    if experience_level:
        if re.search(r"\b(d[ée]butant|stage|alternance|apprenti)\b", experience_level, re.IGNORECASE):
            return "junior"
        if re.search(r"\bconfirm[ée]\b", experience_level, re.IGNORECASE):
            return "mid"

        # 3. Extraction d'années
        years_match = _YEARS.search(experience_level)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return "junior"
            if years <= 5:
                return "mid"
            return "senior"

    return None


def seniority_label(seniority: str | None) -> str:
    """Libellé d'affichage en français."""
    return {
        "junior": "Junior",
        "mid": "Confirmé",
        "senior": "Senior",
        "lead": "Lead",
    }.get(seniority or "", "—")
