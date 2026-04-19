"""CLI entry point for TechPulse scraper.

Usage :
    python -m techpulse_scraper run --spider=all
    python -m techpulse_scraper run --spider=hellowork --limit=50

Sprint 0 : stub minimal. L'implémentation réelle arrive en Sprint 1.
"""

from __future__ import annotations

import sys


def main() -> int:
    """Point d'entrée CLI. Stub du Sprint 0, à remplacer en Sprint 1."""
    print("TechPulse scraper — Sprint 0 stub. L'implémentation réelle arrive en Sprint 1.")
    print("Usage (à venir) : python -m techpulse_scraper run --spider=all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
