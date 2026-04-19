# Projet M2 Web Scraping — Phase 1 : Cadrage

**Auteur :** Bastien Ruedas
**Date :** 19 avril 2026
**Deadline soutenance :** 1er juin 2026 (~6 semaines · ~60 h disponibles à 10 h/semaine)
**Méthodologie :** 3 phases bloquantes — Cadrage → Roadmap → Implémentation

---

## Sommaire

- [A. Propositions de sujets](#a-propositions-de-sujets)
- [B. Architecture technique cible](#b-architecture-technique-cible)
- [C. Roadmap des fonctionnalités bonus](#c-roadmap-des-fonctionnalités-bonus)
- [D. Critères d'excellence](#d-critères-dexcellence)
- [Prochaines étapes](#prochaines-étapes)

---

## A. Propositions de sujets

### Critères de sélection appliqués

J'ai écarté les sujets surreprésentés dans les rendus étudiants (Marmiton, Amazon, comparateurs de vols, Allociné) pour ne te proposer que des sujets qui cochent ces cases :

| Critère | Pourquoi ça compte |
|---|---|
| **Sources stables** | Le HTML ne doit pas casser toutes les 2 semaines. |
| **Éthique ok** | `robots.txt` tolérant, API officielle si dispo, rate-limit raisonnable. |
| **Matière riche** | Assez de champs pour alimenter NLP, géospatial, time series ou clustering. |
| **Storytelling** | Pitchable en 30 secondes, instantanément compris par un recruteur. |
| **Différenciant** | Un jury qui enchaîne 20 rendus doit se souvenir de toi. |

---

### Sujet 1 (recommandé) — **TechPulse** · Observatoire du marché de l'emploi tech en France

**Angle :** Scraper en continu les offres d'emploi tech/data/dev publiées en France pour cartographier ce qui recrute vraiment — technologies, salaires, localisations, politiques de télétravail, exigences par séniorité.

**Pitch 30 secondes :**
> *« J'ai scrapé 5 000+ offres sur 4 sources pour mesurer en temps réel la demande réelle du marché tech français. Le dashboard révèle quelles technos dominent, où elles se concentrent géographiquement, et comment évoluent les exigences selon le niveau d'expérience. »*

**Sources envisagées :**

| Source | Mode d'accès | Faisabilité | Volume estimé |
|---|---|---|---|
| **France Travail** | API officielle gratuite (clé) | Excellent — éthique parfaite | 10 k+ offres tech actives |
| **HelloWork** | Scraping HTML | HTML stable, `robots.txt` ok | 3 k+ offres |
| **APEC** | Scraping HTML | HTML stable | 5 k+ offres cadres |
| **Welcome to the Jungle** | Scraping HTML | Faisable, ToS floue | 2 k+ offres |
| ~~LinkedIn~~ | — | Interdit par ToS | skip |
| ~~Indeed~~ | — | Anti-bot fort | skip |

**Données extractibles :**

- Intitulé, entreprise, description, type de contrat, niveau d'expérience
- Technologies mentionnées *(extraction NLP depuis la description)*
- Compétences soft/hard *(NLP)*
- Ville + géocodage *(API Adresse Data Gouv)*
- Politique télétravail *(classifier léger)*
- Salaire min/max *(regex + extraction)*
- Date de publication, âge de l'offre, URL source (traçabilité)

**Analyses possibles :**

- Top 20 technos les plus demandées — overall et par métier (dev front, data eng, ML, DevOps…)
- Heatmap géographique des offres (densité par département)
- Distribution des salaires par techno / expérience
- Évolution hebdomadaire si scraping périodique activé
- Clustering KMeans des offres → archétypes de postes
- Wordcloud des compétences soft par niveau (junior vs senior)
- Prédiction de salaire simple (régression linéaire scikit-learn)

**Difficulté :** Moyenne

- Scraping HTML stable sur HelloWork/APEC
- L'API France Travail réduit la complexité et donne un gage d'éthique à afficher en soutenance
- NLP d'extraction des technos = exercice technique intéressant (regex + liste contrôlée + `spaCy fr`)

**Pertinence portfolio :** Maximale

- Tu scrapes *exactement le marché auquel tu postules* — narratif imbattable en entretien
- Démo visuelle spectaculaire (dashboard chargé de vraies offres du moment)
- Sujet instantanément compris par un recruteur tech
- Extensible à l'infini après la note (v2, v3, blog post, side-project…)

---

### Sujet 2 — **MeepleLab** · Exploration intelligente des jeux de société modernes

**Angle :** Combiner l'API officielle BoardGameGeek (référentiel mondial) avec le scraping de sites francophones (Philibert, Trictrac) pour bâtir un moteur d'exploration + recommandation par mécaniques, complexité et avis utilisateurs.

**Pitch 30 secondes :**
> *« Un comparateur intelligent de jeux de société qui agrège notes internationales, prix français en temps réel et analyse sémantique d'avis francophones pour te recommander ton prochain jeu. »*

**Sources :**

| Source | Mode | Faisabilité |
|---|---|---|
| **BoardGameGeek** | API XML officielle | Éthique impeccable |
| **Philibert.net** | Scraping HTML (prix + stock FR) | Stable |
| **Trictrac.net** | Scraping HTML (reviews FR) | Stable |

**Données :** nom, année, mécaniques, complexité (poids BGG), durée, nombre de joueurs, notes, prix Philibert, stock, reviews FR, éditeurs, illustrateurs.

**Analyses :**

- Corrélation complexité ↔ note
- Clustering par mécaniques similaires → *"si tu aimes X, tu aimeras Y"*
- Analyse sentiment des reviews FR (`TextBlob fr` ou transformers léger)
- Détection des bons plans (prix Philibert vs note BGG)
- Top éditeurs par rating moyen

**Difficulté :** Facile à moyenne

- API officielle = éthique parfaite
- Données très structurées (XML)
- Volumes gérables (~5 k jeux pertinents)

**Pertinence portfolio :** Forte mais niche

- Excellent pour montrer la posture *"API quand elle existe, scraping quand il le faut"*
- Niche attachante, raconte bien en entretien
- Moins tech-cliché que TechPulse mais aussi moins générique

---

### Sujet 3 — **StartupsFR** · Cartographie dynamique de l'écosystème startup français

**Angle :** Agréger les annonces de levées de fonds, créations et actualités startups publiées par la presse spécialisée française pour construire une cartographie vivante de l'écosystème.

**Sources :**

| Source | Mode | Faisabilité |
|---|---|---|
| **Maddyness** | Scraping HTML (articles levées) | Stable |
| **FrenchWeb** | Scraping HTML | Stable |
| **EU-Startups** | Scraping HTML | Stable |
| **France Digitale** | Scraping HTML (annuaire) | Stable |
| ~~Crunchbase~~ | — | Paywall strict |

**Données :** startup, secteur, montant levé, date, série (Seed / A / B…), investisseurs lead, ville, effectifs approx., description.

**Analyses :**

- Timeline des levées (€ cumulés par mois)
- Top secteurs qui lèvent
- Graphe investisseurs ↔ startups (NetworkX)
- Carte Folium des sièges sociaux
- Détection d'anomalies (levées inhabituelles)

**Difficulté :** Moyenne à difficile

- Scraping d'articles de presse → extraction NLP pour structurer du texte libre = riche techniquement
- Qualité des données hétérogène (c'est justement le défi)

**Pertinence portfolio :** Bonne pour profil business/data

- Narratif business intéressant
- Plus risqué : qualité variable des sources, plus de parsing NLP à faire proprement

---

### Recommandation finale

| Critère | TechPulse | MeepleLab | StartupsFR |
|---|---|---|---|
| Portfolio recruteur tech | ++++ | +++ | +++ |
| Technicité scraping | +++ | +++ | ++++ |
| Richesse analytique | ++++ | +++ | +++ |
| Éthique / stabilité des sources | ++++ (API FT) | ++++ (API BGG) | +++ |
| Effort réaliste en 60 h | +++ | ++++ | +++ |
| **Total** | **18 / 20** | **17 / 20** | **15 / 20** |

**Je recommande TechPulse** parce que :

1. Il combine les trois axes qui impressionnent un jury de M2 en 2026 : **data + NLP + déploiement live**.
2. Tu pourras le réutiliser tel quel dans ton portfolio GitHub et le présenter en entretien comme une vitrine de tes compétences full-stack.
3. Le mix API France Travail + scraping complémentaire = preuve de maturité technique (*"je respecte les APIs quand elles existent, je scrape le reste proprement"*).
4. La démo live est spectaculaire : 5 000 vraies offres du moment, un dashboard qui bouge → personne ne peut dire *"c'est un projet d'école"*.
5. Le sujet t'est personnellement utile (veille marché, découverte de technos qui recrutent dans ta région) → motivation intrinsèque = projet mieux fini.

> **La suite du document (sections B, C, D) est rédigée pour TechPulse.** Si tu choisis MeepleLab ou StartupsFR, ~80 % de l'architecture reste valide — seuls les spiders et le schéma BDD changent.

---

## B. Architecture technique cible

### B.1 — Arborescence du projet

```
techpulse/
├── docker-compose.yml          # Stack complète : MySQL + phpMyAdmin + API + front
├── Makefile                    # make setup / make scrape / make dev / make test
├── .env.example                # Template variables env
├── .gitignore
├── README.md                   # Pitch, setup 1-commande, captures, archi
├── 01-cadrage.md               # ← ce document
├── 02-roadmap.md               # À venir (Phase 2)
│
├── docs/
│   ├── archi.png               # Diagramme haut niveau
│   ├── bdd-schema.png          # ERD
│   └── demo/                   # Captures d'écran pour soutenance
│
├── scraper/                    # Python — scraping + persistence
│   ├── pyproject.toml
│   ├── src/techpulse_scraper/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic settings
│   │   ├── db.py               # SQLAlchemy engine + session
│   │   ├── models.py           # Déclarations tables (ORM)
│   │   ├── http_client.py      # httpx async + retry + rate limit
│   │   ├── spiders/
│   │   │   ├── base.py         # Spider ABC
│   │   │   ├── francetravail_api.py
│   │   │   ├── hellowork.py
│   │   │   └── apec.py
│   │   ├── parsers/
│   │   │   ├── offer_parser.py
│   │   │   ├── tech_extractor.py   # NLP extraction technos
│   │   │   └── salary_parser.py    # Regex salaires
│   │   ├── pipelines/
│   │   │   ├── deduplication.py
│   │   │   └── persistence.py
│   │   ├── utils/
│   │   │   ├── logger.py       # loguru
│   │   │   └── geocoder.py     # API Adresse Data Gouv
│   │   └── cli.py              # python -m techpulse_scraper run --spider=all
│   └── tests/
│       ├── test_parsers.py
│       ├── test_deduplication.py
│       └── fixtures/
│
├── api/                        # Python — API Flask REST
│   ├── pyproject.toml
│   ├── src/techpulse_api/
│   │   ├── __init__.py
│   │   ├── app.py              # Factory Flask
│   │   ├── config.py
│   │   ├── db.py               # Même SQLAlchemy
│   │   ├── routes/
│   │   │   ├── offers.py       # GET /offers, /offers/:id
│   │   │   ├── stats.py        # GET /stats/top-techs, /stats/salaries
│   │   │   └── meta.py         # GET /health, /version
│   │   ├── schemas/            # Marshmallow (flask-smorest)
│   │   └── services/
│   └── tests/
│
├── frontend/                   # PHP — interface utilisateur
│   ├── public/
│   │   ├── index.php           # Accueil / liste offres (niveau 1)
│   │   ├── offer.php           # Fiche détail
│   │   ├── search.php          # Recherche avancée (niveau 2)
│   │   ├── dashboard.php       # Dashboard analytique (bonus)
│   │   └── assets/
│   │       ├── css/app.css     # Tailwind compilé
│   │       └── js/app.js       # Alpine.js
│   ├── src/
│   │   ├── db/Connection.php   # PDO wrapper
│   │   ├── repos/              # OfferRepository, TechRepository
│   │   ├── controllers/
│   │   └── views/
│   │       ├── layout.php
│   │       └── partials/
│   ├── composer.json
│   └── tailwind.config.js
│
├── db/
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   └── 002_add_fulltext.sql
│   ├── seeds/
│   │   └── technologies.sql    # Référentiel canonique (200+ technos)
│   └── backup/                 # Dumps réguliers
│
└── .github/
    └── workflows/
        └── ci.yml              # Lint + tests + build Docker
```

### B.2 — Séparation des responsabilités

```
┌──────────────────────────────────────────────────────────────────┐
│                       UTILISATEUR FINAL                          │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
      ┌─────────────────────┐   ┌──────────────────────┐
      │    Frontend PHP     │   │    API Flask REST    │
      │   (lecture BDD)     │   │   (JSON pour devs /  │
      │                     │   │    intégrations)     │
      └──────────┬──────────┘   └──────────┬───────────┘
                 │                         │
                 └───────────┬─────────────┘
                             ▼
                   ┌─────────────────────┐
                   │    MySQL 8 + FT     │◄── phpMyAdmin (admin manuel)
                   └──────────┬──────────┘
                              ▲
                              │
                  ┌───────────┴──────────────┐
                  │  Pipeline Python         │
                  │  Spider → Parser →       │
                  │  Dedup → Persistence     │
                  └───────────┬──────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
   France Travail       HelloWork            APEC / WTTJ
    (API JSON)          (scraping)           (scraping)
```

| Couche | Rôle | Qui fait quoi |
|---|---|---|
| **Spider** | Récupère le HTML / JSON brut | Un fichier par source, interface `BaseSpider` commune |
| **Parser** | Transforme brut → objet structuré | Stateless, testable en isolation |
| **Pipeline** | Dédup, enrichissement, validation | Entre parser et BDD |
| **Persistence** | Écriture BDD via ORM | Seul composant qui touche MySQL en écriture |
| **API** | Lecture BDD + sérialisation JSON | Jamais d'écriture |
| **Frontend PHP** | Lecture BDD via PDO (niveau 1-2) ou via API (niveau 3) | Aucune business logic lourde |

### B.3 — Choix technologiques justifiés

| Composant | Choix | Pourquoi, vs alternatives |
|---|---|---|
| **HTTP client** | `httpx` (async) + `tenacity` | vs `requests` : async = gain vitesse × 5-10 sur multi-pages. `tenacity` gère retry + backoff exponentiel en 3 lignes. |
| **Parsing HTML** | `selectolax` + `beautifulsoup4` en fallback | `selectolax` (bindings C lexbor) ≈ 10× plus rapide que BS4 ; BS4 gardé pour HTML cassé. |
| **JS rendering** | `playwright` (optionnel) | Seulement si une source nécessite JS. Prévu en backup, pas obligatoire. |
| **ORM** | `SQLAlchemy 2.x` (sync) | vs `PyMySQL` brut : type-safe, migrations claires, relations explicites. Sync car MySQL reste simple ici. |
| **Validation** | `pydantic v2` | Schémas stricts entre couches, settings env typées, validations avant BDD. |
| **Cache HTTP dev** | `hishel` | Évite de re-fetcher en développement, rend le code idempotent. |
| **Logs** | `loguru` | API plus simple que `logging`, couleurs, rotation, mode JSON structuré. |
| **Scheduler** | `APScheduler` | Embarqué dans l'API Flask, pas besoin de cron externe. |
| **Tests** | `pytest` + `pytest-asyncio` + `respx` (mock HTTPX) | Standard Python. |
| **Lint / Format** | `ruff` | Successeur de black + isort + flake8 en un seul outil rapide. |
| **API Python** | `Flask` + `flask-smorest` (OpenAPI auto) | Flask est imposé par le cahier des charges. `flask-smorest` génère un Swagger automatique = gros plus en soutenance. |
| **PHP** | PHP 8.x + PDO + Twig (templating) | Pas de framework lourd (Laravel/Symfony sont overkill). Twig rend les vues plus propres que du PHP mélangé HTML. |
| **CSS** | Tailwind CSS | vs Bootstrap : rendu custom, pas cliché "projet étudiant", moderne et dashboard-friendly. |
| **JS léger** | Alpine.js | vs jQuery / Vue : ≈ 15 Ko, parfait pour autocomplete + modales + toggles, sans build step. |
| **Charts** | Chart.js | vs Plotly : plus léger, suffisant pour toutes nos visualisations prévues. |
| **Container** | Docker + docker-compose | Permet `make setup` qui démarre tout en 1 commande → énorme effet wahou jury. |
| **CI** | GitHub Actions | Gratuit, intégré, workflows YAML simples. |
| **Déploiement** | Railway (recommandé) ou Fly.io | Railway supporte MySQL + Python + PHP + Docker → tout-in-one + URL publique = preuve de maturité. |

### B.4 — Schéma conceptuel de la BDD

**Tables principales :**

```sql
-- Entreprises qui publient les offres
CREATE TABLE companies (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) UNIQUE,
    website         VARCHAR(500),
    sector          VARCHAR(100),
    size_range      VARCHAR(50),    -- '1-10', '11-50', ...
    city            VARCHAR(100),
    lat             DECIMAL(9,6),
    lng             DECIMAL(9,6),
    logo_url        VARCHAR(500),
    first_seen_at   DATETIME,
    last_seen_at    DATETIME,
    INDEX idx_name (name),
    INDEX idx_city (city)
);

-- Offres d'emploi
CREATE TABLE offers (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    company_id          BIGINT NOT NULL,
    source              ENUM('france_travail','hellowork','apec','wttj') NOT NULL,
    source_offer_id     VARCHAR(255) NOT NULL,
    source_url          VARCHAR(1000) NOT NULL,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    description_html    MEDIUMTEXT,
    contract_type       VARCHAR(50),         -- CDI / CDD / Freelance / Stage / Alternance
    experience_level    VARCHAR(50),         -- Junior / Confirmé / Senior / Lead
    remote_policy       VARCHAR(50),         -- Sur site / Hybride / Full remote
    salary_min          INT,
    salary_max          INT,
    salary_currency     CHAR(3) DEFAULT 'EUR',
    city                VARCHAR(100),
    department_code     VARCHAR(5),
    lat                 DECIMAL(9,6),
    lng                 DECIMAL(9,6),
    posted_at           DATETIME,
    scraped_at          DATETIME,
    fingerprint         CHAR(64) NOT NULL,   -- sha256(title+company+city) pour dédup cross-source
    is_active           BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE KEY uq_source (source, source_offer_id),
    INDEX idx_fingerprint (fingerprint),
    INDEX idx_posted (posted_at),
    INDEX idx_city (city),
    FULLTEXT KEY ft_title_desc (title, description)
);

-- Référentiel technos (canonique)
CREATE TABLE technologies (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    canonical_name  VARCHAR(100) UNIQUE NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    category        ENUM('language','framework','database','cloud','tool','methodology','library'),
    aliases         JSON             -- ["JS", "Javascript", "ECMAScript"]
);

-- N↔N avec score de confiance NLP
CREATE TABLE offer_technologies (
    offer_id            BIGINT,
    technology_id       INT,
    confidence_score    DECIMAL(3,2),  -- 0.00 à 1.00
    extracted_by        VARCHAR(20),   -- 'regex' / 'nlp' / 'manual'
    PRIMARY KEY (offer_id, technology_id),
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE,
    FOREIGN KEY (technology_id) REFERENCES technologies(id)
);

-- Traçabilité des runs de scraping
CREATE TABLE scrape_runs (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    spider          VARCHAR(50) NOT NULL,
    started_at      DATETIME NOT NULL,
    finished_at     DATETIME,
    status          ENUM('running','success','partial','failed') NOT NULL,
    pages_fetched   INT DEFAULT 0,
    offers_found    INT DEFAULT 0,
    offers_new      INT DEFAULT 0,
    offers_updated  INT DEFAULT 0,
    errors_count    INT DEFAULT 0,
    error_log       TEXT,
    INDEX idx_spider_date (spider, started_at)
);
```

**Justification de la normalisation :**

- 3ᵉ forme normale respectée (pas de redondance `company_name` dans `offers`).
- Le référentiel `technologies` évite la cacophonie "JS" / "javascript" / "Javascript" grâce au champ `canonical_name` unique + liste `aliases` JSON.
- L'index `FULLTEXT` sur `offers(title, description)` rend la recherche PHP native (`MATCH AGAINST`) performante sans ElasticSearch.
- `fingerprint` + `UNIQUE(source, source_offer_id)` permettent la déduplication intra- et cross-source.
- `scrape_runs` donne un historique auditable et nourrit un tableau de bord admin (bonus).

**Adaptation pour MeepleLab / StartupsFR :** on remplace `companies/offers/technologies` par `games/reviews/mechanics` ou `startups/funding_rounds/investors`. La structure générique (référentiel + N:N + table de runs) reste identique → ~30 % du schéma à réécrire seulement.

---

## C. Roadmap des fonctionnalités bonus

### Vue d'ensemble — répartition des 60 h

| Bloc | Heures | % | Note |
|---|---|---|---|
| Socle obligatoire (BDD + scraping + persistence + front niveau 1) | 15 h | 25 % | Minimum cahier des charges |
| Niveau 2 (recherche / filtres PHP) | 4 h | 7 % | Demandé explicitement |
| Niveau 3 (API Flask) | 6 h | 10 % | Demandé explicitement |
| **Bonus sélectionnés** | **30 h** | **50 %** | **Différenciation** |
| Polish, README, déploiement, préparation soutenance | 5 h | 8 % | Non négligeable |

---

### Axe 1 — Data / Analytics

| # | Bonus | Effort | Valeur jury | Dépendances |
|---|---|---|---|---|
| D1 | **Dashboard analytique** (Chart.js embarqué dans PHP) : top technos, distribution des salaires, offres par ville | M | ★★★★★ | Front niveau 1 terminé |
| D2 | **Extraction NLP des technos** depuis descriptions (regex + référentiel canonique + `spaCy fr_core_news_sm`) | M | ★★★★★ | Scraping fonctionnel |
| D3 | **Heatmap géographique** (Leaflet.js + géocodage via API Adresse Data Gouv) | M | ★★★★ | Géocodage du champ `city` |
| D4 | **Export CSV / JSON / Excel** des résultats filtrés | S | ★★★ | Front recherche terminé |
| D5 | **Scraping récurrent + tracking historique** (APScheduler hebdo) → permet des tendances sur N semaines | M | ★★★★ | Pipeline stable |
| D6 | **Clustering KMeans** des offres (scikit-learn) → archétypes de postes + viz t-SNE | L | ★★★★ | D2 terminé |
| D7 | **Prédiction salaire** (régression linéaire simple sur offres avec salaire renseigné) | M | ★★★ | D2 + données suffisantes |
| D8 | **Wordcloud** des mots-clés par métier (lib `wordcloud` → PNG dans front) | S | ★★ | D2 terminé |

**Recommandation Axe 1 :** D1 + D2 + D3 + D5 obligatoires · D4 et D6 si temps restant · D7 / D8 optionnels.

---

### Axe 2 — UX / UI

| # | Bonus | Effort | Valeur jury | Dépendances |
|---|---|---|---|---|
| U1 | **Design moderne Tailwind** style dashboard pro (plutôt que Bootstrap cliché) | M | ★★★★★ | — |
| U2 | **Mode sombre / clair** toggle avec mémoire localStorage | S | ★★★ | U1 |
| U3 | **Recherche instantanée avec autocomplete** (Alpine.js + API) | M | ★★★★★ | API Flask prête |
| U4 | **Filtres combinables** (ville, techno, télétravail, salaire min, séniorité) avec URL-state | M | ★★★★ | Front + API |
| U5 | **Pagination élégante + tri colonnes** cliquable | S | ★★★ | — |
| U6 | **Fiche détail offre** (description formatée, technos en badges, lien vers source) | S | ★★★ | — |
| U7 | **Micro-animations** (skeletons loading, transitions douces) | S | ★★ | U1 |
| U8 | **Page "À propos"** avec narratif + stats projet (nb offres, nb sources, dernier scrape) | S | ★★★ | — |

**Recommandation Axe 2 :** U1 + U3 + U4 + U5 + U6 + U8 (pilier de la démo) · U2 / U7 finitions.

---

### Axe 3 — DevOps

| # | Bonus | Effort | Valeur jury | Dépendances |
|---|---|---|---|---|
| O1 | **docker-compose complet** (MySQL + phpMyAdmin + API Python + app PHP + reverse proxy Caddy) + setup 1 commande | L | ★★★★★ | — |
| O2 | **Makefile** : `make setup / scrape / test / dev / lint / deploy` | S | ★★★★ | — |
| O3 | **Variables .env + .env.example** (`python-dotenv` côté Python, `vlucas/phpdotenv` côté PHP) | S | ★★★ | — |
| O4 | **GitHub Actions CI** : lint Ruff + tests pytest + build image Docker | M | ★★★★ | Tests écrits |
| O5 | **Pre-commit hooks** (ruff, yamllint, markdownlint) | S | ★★ | — |
| O6 | **Tests unitaires + intégration** (pytest pour scraper et API, PHPUnit léger côté PHP) | M | ★★★★ | Code stabilisé |
| O7 | **README pro** avec badges, capture animée GIF, diagramme d'archi, setup en 1 commande | M | ★★★★★ | Projet complet |
| O8 | **Swagger / OpenAPI auto** sur l'API Flask via `flask-smorest` + UI sur `/docs` | S | ★★★★ | API en place |
| O9 | **Déploiement public Railway** (URL partagée avec le jury dans le README) | M | ★★★★★ | Docker fonctionnel |
| O10 | **Monitoring dashboard interne** (`/admin/runs`) montrant la table `scrape_runs` | M | ★★★ | Table `scrape_runs` |

**Recommandation Axe 3 :** O1 + O2 + O3 + O7 + O8 + O9 prioritaires · O4 / O6 si temps · O5 / O10 finitions.

---

### Axe 4 — Robustesse scraping

| # | Bonus | Effort | Valeur jury | Dépendances |
|---|---|---|---|---|
| R1 | **Scraping async httpx** (vs requests séquentiel) → gain × 5-10 | M | ★★★★ | — |
| R2 | **Retry exponentiel tenacity** sur 429 / 500 / timeout | S | ★★★ | — |
| R3 | **Rate-limiter respectueux** (token bucket, 1 req / 2s par domaine, configurable) | S | ★★★★ | — |
| R4 | **Rotation user-agents** (liste réaliste, pas uniquement "bot") | S | ★★ | — |
| R5 | **Respect robots.txt** programmatique (`urllib.robotparser`) | S | ★★★★ | — |
| R6 | **Cache HTTP en dev** (`hishel`) pour éviter de re-fetcher pendant le développement | S | ★★★ | — |
| R7 | **Scheduler APScheduler** dans l'API → scraping auto hebdo | S | ★★★★ | R1-R5 |
| R8 | **Logs structurés loguru** + rotation fichiers + mode JSON pour grep | S | ★★★ | — |
| R9 | **Détection HTML cassé** : si parse échoue sur >10 % des pages, alerte + dump HTML | M | ★★★★ | Spider générique |
| R10 | **Validation pydantic** des objets avant insertion BDD | S | ★★★ | Parser prêt |
| R11 | **Déduplication cross-source** (fingerprint sha256 sur title+company+city normalisés) | S | ★★★★★ | Modèle offer |

**Recommandation Axe 4 :** R1 + R2 + R3 + R5 + R6 + R8 + R10 + R11 (fondamentaux, dès Sprint 1) · R4 / R7 mid-project · R9 polish.

---

### Synthèse — bonus pré-sélectionnés pour le planning

Si je devais geler maintenant la liste de bonus à livrer (assignation sprint par sprint en Phase 2) :

**MUST-HAVE** — impact majeur sur la note (22 items, ≈ 25 h) :
> D1, D2, D3 · U1, U3, U4, U6, U8 · O1, O2, O3, O7, O8, O9 · R1, R2, R3, R5, R6, R8, R10, R11

**NICE-TO-HAVE** — si temps en fin de Sprint 4 (10 items, ≈ 10 h) :
> D4, D5 · U2, U5, U7 · O4, O5, O6 · R4, R7

**STRETCH** — uniquement si tout est bouclé (5 items, ≈ 6 h) :
> D6, D7, D8 · O10 · R9

> Total MUST-HAVE ≈ 25 h → cadre avec le budget des 30 h alloués aux bonus. Marge prévue pour les imprévus.

---

## D. Critères d'excellence

Les éléments qui feront la différence **devant un jury** (ordre d'impact décroissant) :

### 1. Démo live avec vraies données *(critère n°1 en soutenance)*

Tu arrives avec une URL publique : `https://techpulse.up.railway.app`. Le jury voit **immédiatement** 3 000+ vraies offres d'emploi, un dashboard qui bouge, une carte de France qui s'affiche. Fini le discours : on te regarde *utiliser* ton projet. 90 % des rendus étudiants montrent du `localhost` → tu seras dans les 10 %.

### 2. Storytelling clair

Tu sais pitcher ton projet en 30 secondes (*« Observatoire du marché de l'emploi tech qui scrape 4 sources, extrait les technos par NLP et cartographie la demande française »*) et répondre en 2 phrases à *"pourquoi ce sujet ?"* et *"c'était quoi le plus dur ?"*. C'est ce qui reste en mémoire.

### 3. Qualité du code & ingénierie

Type hints Python systématiques, docstrings, fonctions courtes, tests qui tournent en CI, commits atomiques avec messages conventionnels, linter propre. Le jury regarde ton repo GitHub pendant que tu parles — la première impression compte énormément.

### 4. Ampleur de la stack maîtrisée

Python + MySQL + PHP + Docker + CI + déploiement + API + front. Tu prouves que tu peux **livrer** une vraie app bout en bout. C'est ce que tu vendras en entretien.

### 5. Documentation premium

README avec : badges CI, capture animée GIF, diagramme d'archi, pitch clair, setup en 1 commande, section "choix techniques", lien démo, captures. C'est souvent ce que le jury lit AVANT de t'écouter.

### 6. Éthique du scraping documentée

Section dédiée dans le README : respect `robots.txt`, rate limiting, usage d'API officielle quand disponible, anonymisation si pertinent. Beaucoup d'étudiants l'ignorent → tu le mentionnes et tu gagnes un point maturité.

### 7. Touche analytique / intelligence

Le projet n'est pas juste *"je scrape, je stocke, j'affiche un tableau"*. Il y a de l'**analyse** : NLP pour extraire les technos, corrélations, tendances, prédictions légères. C'est ce qui transforme un projet *"techniquement correct"* en projet *"techniquement correct ET intelligent"*.

---

## Prochaines étapes

**Ta validation attendue sur :**

1. Le **sujet choisi** — je recommande TechPulse ; MeepleLab et StartupsFR sont prêts en plan B / C.
2. La **stack technique** — `httpx` async, SQLAlchemy, Flask + flask-smorest, Tailwind, Docker, Railway, etc.
3. La **liste de bonus MUST-HAVE** — 22 items listés ci-dessus.

**Dès validation je rédige la Phase 2** (`02-roadmap.md`) :

- Découpage en 6 sprints avec livrables et critères de validation
- Planning semaine par semaine jusqu'au 1er juin
- Risques identifiés + plans de mitigation
- Checklist finale pré-soutenance

---

*Document rédigé le 19 avril 2026 — Version 1.0*
