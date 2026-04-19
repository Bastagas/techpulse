"""Parser de localisation — extrait ville + code département.

France Travail renvoie par exemple :
    "38 - Grenoble"  → (Grenoble, 38)
    "75 - PARIS 08"  → (Paris, 75)
    "Télétravail"    → (None, None)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedLocation:
    city: str | None
    department_code: str | None


_DEPT_CITY = re.compile(r"^\s*(\d{2,3})\s*[-–]\s*(.+?)\s*$")
_CITY_ARRONDISSEMENT = re.compile(r"^(.+?)\s+\d{1,3}$")  # "PARIS 08" → "PARIS"


def parse_location(text: str | None) -> ParsedLocation:
    if not text:
        return ParsedLocation(None, None)

    text = text.strip()

    # Télétravail, remote, home
    if re.search(r"t[ée]l[ée]travail|remote|home.?office", text, re.I):
        return ParsedLocation(None, None)

    m = _DEPT_CITY.match(text)
    if m:
        dept = m.group(1).zfill(2) if len(m.group(1)) == 1 else m.group(1)
        city = m.group(2).strip()
        # Normalise les arrondissements : "PARIS 08" → "Paris"
        arr_m = _CITY_ARRONDISSEMENT.match(city)
        if arr_m:
            city = arr_m.group(1).strip()
        return ParsedLocation(city=_titlecase(city), department_code=dept[:3])

    # Pas de format reconnu → on garde le texte comme ville
    return ParsedLocation(city=_titlecase(text), department_code=None)


def _titlecase(s: str) -> str:
    """'PARIS' → 'Paris' · 'saint-étienne' → 'Saint-Étienne'."""
    return "-".join(part.capitalize() for part in s.split("-"))
