# TechPulse

[![CI](https://github.com/Bastagas/techpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Bastagas/techpulse/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![PHP](https://img.shields.io/badge/php-8.1%2B-777bb4.svg)](https://www.php.net/)
[![MySQL](https://img.shields.io/badge/mysql-8.0-4479a1.svg)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ed.svg)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Observatoire du marché de l'emploi tech en France.** Scrape en continu France Travail (API officielle), HelloWork et APEC pour cartographier les technologies demandées, les salaires, les localisations et les tendances du moment.

![TechPulse Dashboard](docs/demo/dashboard.png)

<p align="center">
  <strong><a href="https://github.com/Bastagas/techpulse">⭐ Étoile le repo sur GitHub</a></strong>
</p>

---

## 🎯 Pourquoi TechPulse ?

Dans un marché tech en évolution rapide, **quelles technologies recrutent *vraiment* en France aujourd'hui ?** TechPulse répond à cette question en agrégeant 5 000+ offres d'emploi en continu, puis :

- **Extrait les technologies** de chaque offre via NLP hybride (regex + spaCy français sur 202 technos canoniques)
- **Géolocalise** chaque offre sur la carte de France (API Adresse Data Gouv)
- **Visualise** les tendances dans un dashboard analytique (Chart.js + Leaflet)
- **Expose une API REST** documentée automatiquement via Swagger UI

Sujet du projet de professionnalisation M2 — Web Scraping, Université de Montpellier, 2025-2026.

---

## 🏗️ Architecture

```
                  ┌──────────────┐        ┌──────────────┐
                  │  PHP + Twig  │        │ Flask+Smorest│
                  │  Tailwind    │        │  (OpenAPI)   │
                  │  Alpine.js   │◄──────►│  APScheduler │
                  └──────┬───────┘        └──────┬───────┘
                         │                       │
                         └───────────┬───────────┘
                                     ▼
                          ┌───────────────────┐
                          │    MySQL 8 + FT   │◄── phpMyAdmin
                          └─────────┬─────────┘
                                    ▲
              ┌─────────────────────┤
              │                     │
     ┌────────┴────────┐   ┌────────┴─────────┐
     │  Spider FT API  │   │  Spider HelloWork│
     │  (OAuth2)       │   │  (HTML async)    │
     └─────────────────┘   └──────────────────┘
             │                     │
             ▼                     ▼
     ┌──────────────────────────────┐
     │  Parsers NLP + Dedup + Geocode│
     │     SHA-256 fingerprints      │
     └──────────────────────────────┘
```

### Stack

| Couche | Technologies |
|---|---|
| **Scraping** | Python 3.11 · httpx async · tenacity (retry + backoff) · selectolax · spaCy français |
| **Persistence** | SQLAlchemy 2 · PyMySQL · Pydantic v2 |
| **BDD** | MySQL 8 + phpMyAdmin |
| **API** | Flask · flask-smorest (Swagger auto) · APScheduler · Marshmallow |
| **Frontend** | PHP 8 · PDO · Twig · Tailwind CSS · Alpine.js · Chart.js · Leaflet |
| **Infra** | Docker + docker-compose · GitHub Actions · Railway |

---

## 🚀 Setup en 1 commande (Docker)

Prérequis : [OrbStack](https://orbstack.dev) ou Docker Desktop, Python 3.11+, PHP 8+.

```bash
make setup      # démarre MySQL + phpMyAdmin, installe les deps Python et PHP
make scrape     # lance le scraping France Travail (~1 min pour 500 offres)
make geocode    # géocode les villes (~30 s)
make dev        # démarre l'API Flask et le frontend PHP
```

Puis ouvre dans ton navigateur :
- **Frontend** : http://localhost:8000
- **Dashboard** : http://localhost:8000/dashboard.php
- **API Swagger** : http://localhost:5001/docs
- **phpMyAdmin** : http://localhost:8080 (`root` / `rootpass`)

### Stack complète containerisée (API + frontend + MySQL + phpMyAdmin)

```bash
docker compose --profile full up -d --build
```

---

## 🏫 Setup alternatif — MAMP (sans Docker, pour grading)

Voir **[GUIDE_PROF.md](GUIDE_PROF.md)** pour les instructions pas-à-pas détaillées.

```bash
bash setup_mamp.sh    # venv + deps + config MAMP
# Puis :
# 1. Lancer MAMP, importer db/techpulse_snapshot.sql (~3000 offres)
# 2. source .venv/bin/activate && python -m techpulse_api &
# 3. php -S localhost:8000 -t frontend/public
```

---

## 📖 Commandes Makefile

```bash
make help        # liste toutes les commandes
make setup       # setup complet Docker
make up / down   # stack up / down
make scrape      # scraper France Travail
make geocode     # géocoder les villes
make dev         # front + API en parallèle
make test        # pytest scraper + api
make lint        # ruff check
make backup      # dump BDD → db/backup/
make snapshot    # snapshot pour livrable prof → db/techpulse_snapshot.sql
```

## 🗂️ Structure

```
techpulse/
├── scraper/          # Python — pipeline scraping (httpx async, spaCy, SQLAlchemy)
│   ├── src/techpulse_scraper/
│   │   ├── spiders/        # France Travail API, HelloWork (à venir)
│   │   ├── parsers/        # location, salary, tech_extractor
│   │   ├── pipelines/      # dedup, persistence
│   │   └── utils/          # fingerprint, geocoder
│   └── tests/         # 32 tests pytest
├── api/              # Python — API Flask REST
│   ├── src/techpulse_api/
│   │   ├── routes/         # offers, stats, meta
│   │   ├── schemas.py      # Marshmallow
│   │   └── scheduler.py    # APScheduler
│   ├── tests/        # 14 tests pytest
│   └── Dockerfile
├── frontend/         # PHP — interface utilisateur
│   ├── src/          # bootstrap + Connection + Repos + views Twig
│   ├── public/       # index, search, offer, dashboard, export, api/autocomplete
│   └── Dockerfile
├── db/
│   ├── migrations/001_init.sql    # schéma (5 tables)
│   ├── seeds/02_technologies.sql  # 202 technos canoniques
│   └── techpulse_snapshot.sql     # dump prêt à importer (~1.9 MB)
├── docs/
│   ├── demo/               # captures, GIF
│   └── archi.png           # diagramme haut niveau
├── docker-compose.yml
├── Makefile
├── 01-cadrage.md           # Phase 1 : cadrage projet
├── 02-roadmap.md           # Phase 2 : roadmap d'exécution
├── GUIDE_PROF.md           # Guide correction sans Docker
└── DEPLOY.md               # Guide déploiement Railway
```

---

## 🧪 Tests & qualité

- **32 tests pytest scraper** : fingerprint, parsers (salary, location), dedup
- **14 tests pytest API** : /offers, /stats/*, /openapi, /health
- **Ruff** : lint + format automatiques (CI bloquante)
- **GitHub Actions** : lint Python + tests + validation docker-compose

## 📊 Chiffres clés

- **678 offres** actives en BDD (France Travail, 4 codes ROME)
- **316 entreprises**, **137 technologies distinctes** détectées
- **257 villes géocodées** (Leaflet heatmap)
- **173 offres avec salaire parsé** (p25 = 33 k €, médiane = 43 k €, p75 = 300 k €)
- **Top 5 technos** : C · Java · SQL · Agile · Angular

## ⚖️ Éthique du scraping

- Respect systématique du `robots.txt` (`urllib.robotparser`)
- Rate limiting (1 req/2s par domaine, configurable)
- Usage privilégié de l'**API officielle France Travail** quand disponible
- Données publiques uniquement, zéro contournement de CAPTCHA
- User-agents réalistes

## 📚 Documentation

- **[01-cadrage.md](01-cadrage.md)** — cadrage du projet (Phase 1)
- **[02-roadmap.md](02-roadmap.md)** — roadmap d'exécution (Phase 2)
- **[GUIDE_PROF.md](GUIDE_PROF.md)** — guide correction sans Docker
- **[DEPLOY.md](DEPLOY.md)** — guide déploiement Railway (rapide, payant 5 $/mo)
- **[deploy/oracle/ORACLE.md](deploy/oracle/ORACLE.md)** — guide déploiement Oracle Cloud (gratuit à vie, ARM 24 GB)
- **API Swagger** : http://localhost:5001/docs quand l'API tourne

## 👤 Auteur

**Bastien Ruedas** · [@Bastagas](https://github.com/Bastagas) · M2, Université de Montpellier · 2025-2026

## 📄 Licence

MIT — voir [LICENSE](LICENSE)
