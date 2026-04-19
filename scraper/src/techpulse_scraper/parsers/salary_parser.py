"""Parser de salaires à partir de texte libre français.

Gère :
  - « 45 000 € / an » → (45000, 45000)
  - « 40k à 55k € brut / an » → (40000, 55000)
  - « entre 3000 et 3500 € par mois » → (36000, 42000) (*12)
  - « 500€/jour » → (110000, 110000) (*220 jours ouvrables)

Retourne None si aucun montant plausible trouvé.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUM = r"(\d{1,3}(?:[\s\u202f\u00a0.,]\d{3})*|\d+)(?:[.,]\d{1,3})?"
_K = r"[kK]"
_EURO = r"(?:€|EUR|euros?)"
_SEP = r"\s*(?:-|à|a|et|jusqu[''`]?à|to)\s*"

_PER_YEAR = re.compile(r"(?:par\s+)?an(?:n[eé]e)?|annu?el|/\s*an|/y|yearly", re.I)
_PER_MONTH = re.compile(r"(?:par\s+)?mois|mensuel|/\s*mois|/m|monthly", re.I)
_PER_DAY = re.compile(r"(?:par\s+)?jour|quotidien|/\s*j|/d|daily|TJM", re.I)

WORKING_DAYS_PER_YEAR = 220


@dataclass
class ParsedSalary:
    min: int
    max: int
    currency: str = "EUR"


def _to_int(num_str: str) -> float:
    """'45 000' → 45000, '3,500' → 3500, '3.5' → 3.5, '40k' → 40000."""
    s = num_str.lower().strip().replace("\u202f", "").replace("\u00a0", "")
    if s.endswith("k"):
        base = s[:-1].replace(" ", "").replace(",", ".")
        return float(base) * 1000
    # Remove thousands separators (space or comma when followed by 3 digits)
    s = re.sub(r"[\s,](\d{3})\b", r"\1", s)
    # Replace remaining comma with dot (decimal)
    s = s.replace(",", ".")
    return float(s)


def _annualize(amount: float, text: str, match_start: int, match_end: int) -> float:
    """Multiplie selon la périodicité détectée à proximité du montant."""
    context = text[max(0, match_start - 20) : min(len(text), match_end + 40)]
    if _PER_DAY.search(context):
        return amount * WORKING_DAYS_PER_YEAR
    if _PER_MONTH.search(context):
        return amount * 12
    return amount  # default: annuel


def parse_salary(text: str | None) -> ParsedSalary | None:
    """Extrait un (min, max) annuel en euros depuis du texte libre.

    Retourne None si aucun montant raisonnable n'est trouvé ou si les montants
    normalisés tombent hors de la plage plausible (12 000 € – 500 000 €).
    """
    if not text:
        return None

    # Patterns : range ou single
    range_pattern = re.compile(rf"{_NUM}\s*{_K}?\s*{_EURO}?{_SEP}{_NUM}\s*{_K}?\s*{_EURO}?", re.I)
    single_pattern = re.compile(rf"{_NUM}\s*{_K}?\s*{_EURO}", re.I)

    m = range_pattern.search(text)
    if m:
        low = _to_int(
            m.group(1) + ("k" if "k" in m.group(0).lower().split(m.group(1))[1][:3] else "")
        )
        high = _to_int(
            m.group(2) + ("k" if "k" in m.group(0).lower().rsplit(m.group(2), 1)[1][:3] else "")
        )
        low_annual = _annualize(low, text, m.start(), m.end())
        high_annual = _annualize(high, text, m.start(), m.end())
        lo_i, hi_i = int(round(low_annual)), int(round(high_annual))
        if _plausible(lo_i) and _plausible(hi_i) and lo_i <= hi_i:
            return ParsedSalary(min=lo_i, max=hi_i)

    m = single_pattern.search(text)
    if m:
        amount = _to_int(m.group(1) + ("k" if "k" in m.group(0).lower() else ""))
        annual = int(round(_annualize(amount, text, m.start(), m.end())))
        if _plausible(annual):
            return ParsedSalary(min=annual, max=annual)

    return None


def _plausible(amount: int) -> bool:
    """Filtre les montants absurdes (ex. : 5 € interprété comme 5 €/an)."""
    return 12_000 <= amount <= 500_000
