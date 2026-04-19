"""Extraction de technologies depuis du texte libre (title + description).

Approche hybride :
  1. Chargement du référentiel canonique depuis la table `technologies` (+ aliases).
  2. Construction d'un regex `\\b(python|py|javascript|js|...)\\b` insensible à la casse.
  3. Matching, agrégation par canonical_name, score de confiance basique.

On pourra enrichir par spaCy en v2 (morphologie, contexte, compound words).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from techpulse_scraper.models import Technology


@dataclass
class ExtractedTech:
    technology_id: int
    canonical_name: str
    confidence: float  # 0.0 à 1.0
    matches: int  # nombre d'occurrences


class TechExtractor:
    """Construit un matcher à partir du référentiel BDD, puis extrait les technos.

    Le matcher est construit **une seule fois** à l'instanciation puis réutilisé
    pour toutes les offres → très rapide en batch.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._terms: list[tuple[re.Pattern[str], int, str]] = []
        self._build_matcher()

    def _build_matcher(self) -> None:
        """Charge toutes les technos + aliases et construit les regex.

        Un regex par techno (plus simple à debug que un méga-regex alterné).
        """
        techs = self.session.scalars(select(Technology)).all()
        for tech in techs:
            terms: set[str] = {tech.canonical_name, tech.display_name}
            if tech.aliases:
                terms.update(tech.aliases)
            # Normalisation des termes : retirer les caractères spéciaux inutiles
            # puis construire un OR de regex sûrs (escape).
            escaped = sorted(
                {re.escape(t.strip()) for t in terms if t and t.strip()},
                key=len,
                reverse=True,
            )
            if not escaped:
                continue
            pattern = re.compile(
                r"(?:(?<=\W)|(?<=^))(" + "|".join(escaped) + r")(?=\W|$)",
                re.IGNORECASE,
            )
            self._terms.append((pattern, tech.id, tech.canonical_name))

    def extract(self, *texts: str | None) -> list[ExtractedTech]:
        """Extrait les technos depuis un ou plusieurs textes (title + description)."""
        combined = " ".join(t for t in texts if t)
        if not combined:
            return []

        results: dict[int, ExtractedTech] = {}
        for pattern, tech_id, canonical in self._terms:
            matches = pattern.findall(combined)
            if matches:
                count = len(matches)
                # Confiance simple : plafonnée à 1.0, grimpe vite avec nb occurrences
                confidence = min(1.0, 0.6 + 0.1 * count)
                results[tech_id] = ExtractedTech(
                    technology_id=tech_id,
                    canonical_name=canonical,
                    confidence=confidence,
                    matches=count,
                )

        return sorted(results.values(), key=lambda x: (-x.confidence, x.canonical_name))
