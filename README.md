# TechPulse

> **Observatoire du marché de l'emploi tech en France** · Scrape en continu 3 sources d'offres d'emploi, extrait les technologies par NLP, visualise la demande française sur un dashboard analytique.

**Statut :** en développement — Sprint 0 terminé · deadline 1ᵉʳ juin 2026

---

## Pitch

TechPulse agrège en continu 5 000+ offres d'emploi tech publiées sur **France Travail**, **HelloWork** et **APEC**, puis :

- extrait les technologies par NLP (regex + spaCy français sur un référentiel de 180+ entrées canoniques)
- géolocalise chaque offre sur la carte de France (API Adresse Data Gouv)
- affiche un dashboard analytique (top technos, distribution salaires, heatmap, tendances)
- expose une **API REST Flask** documentée via Swagger UI

## Démo

*URL publique en ligne à la fin du Sprint 5 (28 mai 2026).*

## Stack

| Couche | Technos |
|---|---|
| **Scraping** | Python 3.11 · httpx async · tenacity · selectolax · spaCy fr |
| **Persistence** | SQLAlchemy 2 · PyMySQL · Pydantic v2 |
| **BDD** | MySQL 8 + phpMyAdmin |
| **API** | Flask + flask-smorest (Swagger auto) · APScheduler |
| **Frontend** | PHP 8 · PDO · Twig · Tailwind CSS · Alpine.js · Chart.js · Leaflet |
| **Infra** | Docker + docker-compose · GitHub Actions · Railway |

## Setup

Deux chemins supportés **dans le même projet** :

### Option A — Docker (recommandé, 1 commande)

Prérequis : [OrbStack](https://orbstack.dev) ou Docker Desktop, Python 3.11+, PHP 8+.

```bash
make setup      # démarre MySQL + phpMyAdmin, installe les deps Python/PHP
make scrape     # lance le scraping (arrive en Sprint 1)
make dev        # démarre le frontend et l'API en parallèle
```

Services exposés :
- **phpMyAdmin** : http://localhost:8080 (`root` / `rootpass`)
- **Frontend PHP** : http://localhost:8000 *(Sprint 2)*
- **API Flask** : http://localhost:5001/docs *(Sprint 3)*

### Option B — MAMP (sans Docker, pour grading)

Voir **[GUIDE_PROF.md](GUIDE_PROF.md)** pour le pas-à-pas détaillé avec captures.

Résumé rapide :
1. Lancer MAMP (MySQL + Apache)
2. Importer `db/techpulse_snapshot.sql` dans phpMyAdmin
3. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
4. `python -m techpulse_api` (API → port 5000)
5. `php -S localhost:8000 -t frontend/public` (frontend → port 8000)

## Commandes disponibles

```
make help        # liste toutes les commandes
make setup       # setup complet (Docker)
make up / down   # démarrer / arrêter la stack
make scrape      # lancer le scraping
make dev         # lancer frontend + API
make test        # lancer les tests pytest
make lint        # linter Ruff
make backup      # dump BDD → db/backup/
make snapshot    # dump BDD → db/techpulse_snapshot.sql (livrable prof)
```

## Structure du projet

```
techpulse/
├── scraper/       # Python — pipeline de scraping
├── api/           # Python — API Flask REST
├── frontend/      # PHP — interface utilisateur
├── db/            # migrations SQL + seeds + dumps
├── docs/          # diagrammes, captures, démo
├── docker-compose.yml
├── Makefile
├── requirements.txt     # deps consolidées (path MAMP)
├── 01-cadrage.md        # cadrage projet (Phase 1)
├── 02-roadmap.md        # roadmap d'exécution (Phase 2)
└── GUIDE_PROF.md        # guide correction sans Docker
```

## Documentation

- **[01-cadrage.md](01-cadrage.md)** — cadrage du projet (3 sujets, architecture, bonus)
- **[02-roadmap.md](02-roadmap.md)** — roadmap d'exécution (6 sprints, risques, checklist)
- **[GUIDE_PROF.md](GUIDE_PROF.md)** — guide détaillé pour la correction sans Docker

## Éthique du scraping

- Respect systématique du `robots.txt` de chaque source (`urllib.robotparser`).
- Rate limiting configurable (token bucket, 1 req / 2s par domaine par défaut).
- Usage privilégié de l'**API officielle France Travail** quand disponible.
- User-agents réalistes, jamais de contournement de CAPTCHA.
- Données publiques uniquement, pas de scraping authentifié.

## Auteur

**Bastien Ruedas** — M2, Université de Montpellier · 2025-2026
Projet de professionnalisation noté — cours Web Scraping.

## Licence

MIT
