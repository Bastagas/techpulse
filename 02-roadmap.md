# Projet M2 Web Scraping — Phase 2 : Roadmap d'exécution

**Projet :** TechPulse · Observatoire du marché de l'emploi tech en France
**Auteur :** Bastien Ruedas
**Date de rédaction :** 19 avril 2026
**Deadline soutenance :** 1er juin 2026
**Budget temps :** 60 h (10 h/semaine × 6 semaines)
**Stack validée :** httpx async · SQLAlchemy · Flask + flask-smorest · PHP 8 + Twig · Tailwind · Alpine.js · Chart.js · Docker · Railway

---

## Sommaire

- [Vue d'ensemble](#vue-densemble)
- [Sprint 0 — Infrastructure](#sprint-0--infrastructure-5-h--20-22-avril)
- [Sprint 1 — MVP scraping & persistence](#sprint-1--mvp-scraping--persistence-15-h--23-avril--3-mai)
- [Sprint 2 — Frontend PHP niveaux 1 & 2](#sprint-2--frontend-php-niveaux-1--2-10-h--4--10-mai)
- [Sprint 3 — API Flask REST](#sprint-3--api-flask-rest-6-h--11--13-mai)
- [Sprint 4 — Bonus MUST-HAVE](#sprint-4--bonus-must-have-14-h--14--24-mai)
- [Sprint 5 — Déploiement & soutenance](#sprint-5--déploiement--soutenance-10-h--25-mai--1er-juin)
- [Risques & plans de mitigation](#risques--plans-de-mitigation)
- [Checklist finale pré-soutenance](#checklist-finale-pré-soutenance-j-1)

---

## Vue d'ensemble

### Gantt simplifié

```
Semaine         W1         W2         W3         W4         W5         W6
Dates        20-26/04   27/04-3/5   4-10/5    11-17/5    18-24/5    25/5-1/6

Sprint 0     ▓▓
Sprint 1       ▓▓▓     ▓▓▓▓▓▓▓▓▓▓
Sprint 2                           ▓▓▓▓▓▓▓▓▓▓
Sprint 3                                      ▓▓▓
Sprint 4                                         ▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓
Sprint 5                                                            ▓▓▓▓▓▓▓▓▓▓
```

### Jalons clés

| Date | Fin de | Conformité cahier des charges |
|---|---|---|
| 22 avril | Sprint 0 — infra docker prête | — |
| 3 mai | Sprint 1 — BDD peuplée par scraping | ✓ Étapes 1, 2, 3 |
| 10 mai | Sprint 2 — frontend PHP complet | ✓ Étape 4 niveaux 1 et 2 |
| 13 mai | Sprint 3 — API Flask livrée | ✓ Étape 5 (niveau 3) |
| 24 mai | Sprint 4 — bonus MUST-HAVE intégrés | — (différenciation) |
| 1er juin | Sprint 5 — déploiement + soutenance | ✓ Livraison |

> **Point clé :** Le cahier des charges **intégral** (5 étapes + les 3 niveaux de difficulté) est couvert dès le **13 mai** (fin Sprint 3). Les Sprints 4 et 5 sont **entièrement** dédiés à la différenciation jury. Tu as donc 19 jours de marge sécurisée avant la deadline.

### Budget heures par sprint

| Sprint | Durée | % du budget | Cumul |
|---|---|---|---|
| Sprint 0 | 5 h | 8 % | 5 h |
| Sprint 1 | 15 h | 25 % | 20 h |
| Sprint 2 | 10 h | 17 % | 30 h |
| Sprint 3 | 6 h | 10 % | 36 h |
| Sprint 4 | 14 h | 23 % | 50 h |
| Sprint 5 | 10 h | 17 % | 60 h |
| **Total** | **60 h** | **100 %** | — |

---

## Sprint 0 — Infrastructure (5 h · 20-22 avril)

### Objectif
Poser les fondations techniques avant d'écrire la moindre ligne de logique métier. À la fin du Sprint 0, `make setup` sur une machine vierge doit démarrer toute la stack en une commande.

### Tâches détaillées

| # | Tâche | Durée | Livrable |
|---|---|---|---|
| 0.1 | `git init` + arborescence projet + `.gitignore` soigné | 30 min | Repo local structuré |
| 0.2 | `docker-compose.yml` : MySQL 8 + phpMyAdmin + volume persistant | 1 h | `make up` démarre la stack |
| 0.3 | Migration `001_init.sql` (5 tables du schéma B.4) | 1 h | BDD initialisée |
| 0.4 | Seed `technologies.sql` (200 technos canoniques avec aliases) | 45 min | Référentiel en BDD |
| 0.5 | `Makefile` : `setup / up / down / scrape / test / dev / lint / clean / backup` | 30 min | Commandes unifiées |
| 0.6 | `.env.example` + `.env.local` (credentials MySQL, clé API France Travail) | 30 min | Config centralisée |
| 0.7 | `pyproject.toml` (scraper + api) avec ruff + pytest configurés | 30 min | Environnements Python prêts |
| 0.8 | `composer.json` frontend + Tailwind init (`tailwind.config.js`) | 30 min | Environnement PHP prêt |
| 0.9 | Demande clé API France Travail (pole-emploi.io) | 15 min | Clé en attente / reçue |
| 0.10 | Premier commit structurant + push GitHub | 15 min | Repo distant publié |

### Critères de validation

- [ ] `make setup` sur une machine vierge initialise tout (containers + BDD + seeds).
- [ ] phpMyAdmin accessible sur `http://localhost:8080`, login OK.
- [ ] BDD contient les 5 tables + 200 technos seedées.
- [ ] Repo GitHub public avec `01-cadrage.md` et `02-roadmap.md` commités.
- [ ] Aucun secret commité (vérifié avec `git log -p | grep -i password`).

### Livrables
Arborescence complète conforme à la section B.1 du cadrage · `docker-compose.yml` · `Makefile` · BDD initialisée · repo GitHub public.

---

## Sprint 1 — MVP scraping & persistence (15 h · 23 avril - 3 mai)

### Objectif
Scraper les 2 sources prioritaires (France Travail API + HelloWork), extraire proprement les champs, associer les technos par NLP et insérer en BDD avec déduplication robuste. **Ce sprint couvre à lui seul les étapes 1, 2 et 3 du cahier des charges.**

### Tâches détaillées

| # | Tâche | Durée | Livrable |
|---|---|---|---|
| 1.1 | `config.py` Pydantic settings (env → classes typées) | 30 min | Config typée |
| 1.2 | `db.py` SQLAlchemy engine + `models.py` (5 modèles ORM) | 1 h 30 | ORM fonctionnel |
| 1.3 | `http_client.py` : httpx async + tenacity + rate-limiter token bucket | 1 h 30 | Client HTTP robuste réutilisé partout |
| 1.4 | `logger.py` loguru (console coloré + fichier rotatif + JSON mode) | 30 min | Logs structurés |
| 1.5 | `spiders/base.py` ABC avec interface commune (`fetch`, `parse`, `yield_offers`) | 45 min | Socle réutilisable |
| 1.6 | `spiders/francetravail_api.py` (pagination + auth token) | 2 h | 1000+ offres récupérées |
| 1.7 | `spiders/hellowork.py` (scraping HTML, listing + fiche détail) | 2 h 30 | 500+ offres récupérées |
| 1.8 | `parsers/offer_parser.py` + `salary_parser.py` (regex robustes) | 1 h | Normalisation champs |
| 1.9 | `parsers/tech_extractor.py` (regex sur référentiel + fallback spaCy `fr_core_news_sm`) | 2 h | Technos associées aux offres |
| 1.10 | `pipelines/deduplication.py` (fingerprint sha256 sur title+company+city normalisés) | 45 min | Zéro doublon cross-source |
| 1.11 | `pipelines/persistence.py` + upsert idempotent (insert or update `last_seen_at`) | 1 h | Pipeline complet |
| 1.12 | `cli.py` (argparse : `--spider=all / francetravail / hellowork`, `--limit`, `--dry-run`) | 30 min | Point d'entrée CLI |
| 1.13 | Tests pytest sur parsers + dedup + tech_extractor | 30 min | ≥ 80 % coverage sur ces modules |

### Critères de validation

- [ ] `make scrape` exécute les 2 spiders et insère ≥ 1500 offres distinctes en BDD.
- [ ] Tests pytest passent (≥ 80 % de couverture sur parsers, dedup, tech_extractor).
- [ ] Re-run du scraping : aucun doublon créé, mais `last_seen_at` mis à jour sur les offres déjà vues.
- [ ] Vérification manuelle : 10 offres tirées au hasard ont des technos cohérentes associées.
- [ ] Logs propres, pas d'exception non rattrapée, pas de warning spammé.
- [ ] **Cahier des charges : étapes 1, 2, 3 validées.**

### Livrables
Pipeline scraping complet · 1500+ offres en BDD · 2 spiders · tests pytest.

---

## Sprint 2 — Frontend PHP niveaux 1 & 2 (10 h · 4 - 10 mai)

### Objectif
Livrer l'étape 4 du cahier des charges (niveaux 1 et 2) avec un design moderne Tailwind et une recherche filtrable. Visuellement professionnel, loin du rendu "TP étudiant".

### Tâches détaillées

| # | Tâche | Durée | Livrable |
|---|---|---|---|
| 2.1 | `src/db/Connection.php` PDO singleton + gestion erreurs | 30 min | Connexion BDD fiable |
| 2.2 | `src/repos/OfferRepository.php` (`listAll`, `findById`, `search`, `count`) | 1 h | Data layer testable |
| 2.3 | `src/repos/TechRepository.php` + `CompanyRepository.php` | 30 min | Data layer complet |
| 2.4 | Setup Twig + `views/layout.php` + composants réutilisables (navbar, footer, card) | 1 h | Charte graphique homogène |
| 2.5 | Config Tailwind + palette de couleurs + typographie + mode sombre | 45 min | Design system |
| 2.6 | `public/index.php` liste offres paginée (niveau 1 cahier des charges) | 1 h 30 | Tableau des offres avec tri |
| 2.7 | `public/offer.php` fiche détail (description, badges technos, infos entreprise) | 1 h | Vue détaillée |
| 2.8 | `public/search.php` formulaire `<select>` ville + `<select>` techno + input texte + filtre télétravail (niveau 2) | 1 h 30 | Recherche combinée |
| 2.9 | Autocomplete Alpine.js sur le champ techno (appel AJAX léger) | 1 h | UX fluide |
| 2.10 | Mode sombre toggle avec mémoire localStorage | 30 min | Toggle dans header |
| 2.11 | Responsive mobile-first + tests iOS/Android | 45 min | UI qui tient sur iPad + iPhone |

### Critères de validation

- [ ] Accueil affiche 20 offres par page, pagination fonctionnelle, tri par colonnes cliquable.
- [ ] Fiche détail affiche description propre, technos en badges cliquables, lien source.
- [ ] Recherche : texte + `<select>` ville + `<select>` techno + télétravail tous combinables, résultats cohérents.
- [ ] Autocomplete techno responsive sous 300 ms.
- [ ] Responsive testé sur iPhone et iPad (Safari dev tools).
- [ ] Mode sombre fonctionne, préférence sauvegardée.
- [ ] **Cahier des charges : étape 4 niveaux 1 et 2 validés.**

### Livrables
Frontend PHP complet, design Tailwind, recherche avancée, responsive.

---

## Sprint 3 — API Flask REST (6 h · 11 - 13 mai)

### Objectif
Livrer l'étape 5 du cahier des charges (3ᵉ niveau de difficulté) avec en bonus un Swagger UI auto-généré qui fait toujours son effet en soutenance.

### Tâches détaillées

| # | Tâche | Durée | Livrable |
|---|---|---|---|
| 3.1 | `api/app.py` factory Flask + flask-smorest + config + CORS | 45 min | Serveur Flask configuré |
| 3.2 | Schemas Marshmallow (`OfferSchema`, `TechSchema`, `StatsSchema`, `CompanySchema`) | 45 min | Sérialisation propre typée |
| 3.3 | `routes/offers.py` : `GET /offers` (pagination + filtres : tech, city, remote, salary_min) + `GET /offers/:id` | 1 h 30 | 2 endpoints documentés |
| 3.4 | `routes/stats.py` : `GET /stats/top-techs`, `/stats/salaries`, `/stats/cities`, `/stats/timeline` | 1 h 30 | 4 endpoints analytics |
| 3.5 | `routes/meta.py` : `/health`, `/version`, `/sources` | 15 min | Endpoints infra |
| 3.6 | Tests pytest API (client de test Flask, fixtures BDD) | 1 h | ≥ 80 % coverage API |
| 3.7 | Vérification Swagger UI sur `/docs` + schema OpenAPI exportable | 15 min | Doc interactive en ligne |

### Critères de validation

- [ ] `http://localhost:5000/docs` affiche Swagger UI avec tous les endpoints documentés.
- [ ] Appel `GET /offers?tech=python&city=montpellier&remote=true&per_page=20` retourne JSON cohérent et paginé.
- [ ] Tests pytest API passent.
- [ ] Temps de réponse < 200 ms sur requêtes simples.
- [ ] **Cahier des charges : étape 5 (niveau 3 de difficulté) validée.**

### Livrables
API Flask complète · Swagger UI · tests pytest.

### Point de vérification majeur
À la fin du Sprint 3 (~13 mai), **l'intégralité du cahier des charges est livrée**. Il reste 19 jours et 24 h de budget pour différencier le projet.

---

## Sprint 4 — Bonus MUST-HAVE (14 h · 14 - 24 mai)

### Objectif
Livrer les 22 bonus MUST-HAVE identifiés en Phase 1 qui feront basculer la note de *correct* à *excellent*. Priorité à l'impact jury.

### Tâches détaillées

| # | Tâche | Axe | Durée | Livrable |
|---|---|---|---|---|
| 4.1 | Spider APEC (3ᵉ source) + intégration dans le pipeline | R | 2 h | 1500+ offres supp., BDD ~3000+ |
| 4.2 | `public/dashboard.php` + Chart.js : top 20 technos, distribution salaires, offres par type de contrat | D1 | 2 h 30 | Dashboard visuel spectaculaire |
| 4.3 | Géocodage batch des villes via API Adresse Data Gouv + update BDD | D3 | 1 h | Lat/lng peuplés |
| 4.4 | Heatmap Leaflet intégrée dans dashboard (densité par département) | D3 | 2 h | Carte de France interactive |
| 4.5 | Scheduler APScheduler intégré à l'API Flask (scraping auto hebdo) | R7 | 1 h 30 | Scraping planifié visible dans `/admin` |
| 4.6 | Validation pydantic stricte avant insertion BDD + tests | R10 | 45 min | Garde-fou qualité |
| 4.7 | Cross-source deduplication finalisée + consolidation par fingerprint | R11 | 1 h | Unicité cross-source garantie |
| 4.8 | `public/about.php` : narratif projet + stats live (nb offres, nb sources, dernier scrape, top techno du moment) | U8 | 1 h | Page storytelling |
| 4.9 | Polish UI final : micro-animations, skeletons loading, hover states | U7 | 1 h 15 | Design poli |
| 4.10 | *Nice-to-have* : export CSV / JSON depuis page recherche | D4 | 1 h | Boutons d'export fonctionnels |

### Critères de validation

- [ ] BDD contient 3 000+ offres sur 3 sources distinctes (France Travail, HelloWork, APEC).
- [ ] Dashboard affiche au moins 3 visualisations animées (top techs, salaires, contrats).
- [ ] Heatmap Leaflet montre la densité géographique des offres.
- [ ] Scheduler programmé, logs montrent `next_run_at` et historique des runs.
- [ ] Page About affiche stats live (requête agrégée au chargement).
- [ ] Démo bout en bout : de l'arrivée sur le site jusqu'à la fiche détail → impeccable.

### Livrables
Bonus MUST-HAVE livrés · 3 000+ offres en BDD · dashboard · heatmap · scheduler.

---

## Sprint 5 — Déploiement & soutenance (10 h · 25 mai - 1er juin)

### Objectif
Rendre le projet public avec une URL que tu partages au jury, produire un README magnifique, préparer une soutenance maîtrisée.

### Tâches détaillées

| # | Tâche | Durée | Livrable |
|---|---|---|---|
| 5.1 | `Dockerfile` production optimisés (multi-stage pour scraper, api, frontend) | 1 h 30 | Images légères (< 200 Mo chacune) |
| 5.2 | Compte Railway + déploiement de la stack complète + seed BDD prod | 1 h 30 | **URL publique live** |
| 5.3 | GitHub Actions CI : lint Ruff + tests pytest + build Docker | 1 h | Badge CI vert sur README |
| 5.4 | README pro : badges · pitch · GIF démo · diagramme archi · setup 1-commande · stack · démo URL · licence MIT | 2 h | Vitrine GitHub |
| 5.5 | Diagramme d'archi (Excalidraw) + ERD exporté (dbdiagram.io) | 45 min | PNG dans `docs/` |
| 5.6 | Captures d'écran HD + GIF animé (Kap ou LICEcap) de la démo | 45 min | Assets visuels |
| 5.7 | Slides soutenance (Keynote, 10 slides max : pitch, problème, archi, démo, challenges, résultats, suites, Q&A) | 1 h 30 | Support visuel |
| 5.8 | Script démo de 5 min chrono, répété 2-3 fois | 45 min | Démo fluide |
| 5.9 | FAQ questions jury préparées (scraping éthique, justifications techniques, difficultés) | 30 min | Réponses prêtes |
| 5.10 | Tests end-to-end manuels + fix bugs visuels + dump BDD de backup | 45 min | Zéro bug visible |

### Critères de validation

- [ ] `https://techpulse.up.railway.app` (ou URL équivalente) accessible publiquement, BDD peuplée.
- [ ] README GitHub affiche badge CI vert, GIF animé, diagramme d'archi, lien démo.
- [ ] Slides finalisés, exportés en PDF de secours.
- [ ] Démo live testée sur connexion 4G mobile (scenario hors wifi fac).
- [ ] Script démo tenu en 5 minutes chrono au deuxième essai.
- [ ] Backup vidéo mp4 de la démo sur laptop (au cas où Railway tombe le jour J).

### Livrables
Projet déployé publiquement · README pro · slides · démo prête.

---

## Risques & plans de mitigation

| # | Risque | Probabilité | Impact | Plan de mitigation |
|---|---|---|---|---|
| 1 | Anti-bot sur HelloWork / WTTJ | Moyenne | Moyen | Fallback sur API France Travail (illimitée et officielle) + APEC. Le projet reste viable avec 1 seule source si nécessaire. |
| 2 | Changement HTML d'une source en cours de projet | Moyenne | Élevé | Tests d'intégration par spider + alerte si taux de parse < 90 % (R9 si temps). Structure spider isolée = fix rapide. |
| 3 | Extraction NLP des technos imprécise | Moyenne | Moyen | Approche hybride : regex sur référentiel canonique en priorité (déterministe), spaCy en complément. Évaluation manuelle sur 50 offres pour valider. |
| 4 | Railway : coût imprévu ou limites MySQL | Faible | Moyen | Plan B : Fly.io (crédit gratuit) ou VPS OVH 5 €/mois. Stack docker-compose = portable partout. |
| 5 | Dépassement de la charge horaire (60 h) | Élevée | Faible | La liste STRETCH est optionnelle par construction. Les MUST-HAVE suffisent pour une excellente note. Priorisation stricte + timeboxing. |
| 6 | Bugs de dernière minute avant soutenance | Moyenne | Élevé | **Code freeze J-3 (29 mai)**. Après cette date, uniquement slides + docs + répétitions démo. Aucune fonctionnalité ajoutée. |
| 7 | Performance dégradée sur grosse BDD | Faible | Moyen | Index SQL pré-calculés (cf. B.4) + pagination systématique + cache PHP (APCu) si besoin. Benchmark dès Sprint 2. |
| 8 | Clé API France Travail non délivrée à temps | Faible | Élevé | Demande dès Sprint 0. Sinon, fallback sur HelloWork + APEC suffit (volume toujours suffisant). |
| 9 | Perte de données BDD (volume Docker corrompu) | Faible | Élevé | `make backup` automatique + commit versionné hebdo du dump SQL. Dump prod téléchargé sur Google Drive chaque sprint. |
| 10 | Frustration ou perte de motivation | Moyenne | Élevé | Commits atomiques fréquents = chaque commit est une petite victoire. Mini-rapport de fin de sprint = vue claire du chemin parcouru. |
| 11 | Conflit de ports locaux (Docker MAMP/XAMPP déjà utilisé) | Faible | Faible | Ports configurables via `.env` (MYSQL_PORT=3307, PHP_PORT=8000, API_PORT=5000, PHPMYADMIN_PORT=8080). |
| 12 | Oubli d'un requis caché dans le brief prof | Faible | Élevé | Relecture croisée du sujet en Sprint 0 + Sprint 4. Liste explicite cochée du cahier des charges. |

---

## Checklist finale pré-soutenance (J-1)

### Technique
- [ ] `make setup` fonctionne sur machine vierge sans erreur (test sur VM propre ou container)
- [ ] BDD de production contient 3 000+ offres récentes (< 30 jours)
- [ ] Front PHP accessible en local ET en prod
- [ ] API Flask + Swagger UI accessibles en local ET en prod
- [ ] Dashboard charge en moins de 3 secondes
- [ ] Responsive mobile testé (iPhone + iPad)
- [ ] Aucune erreur dans la console navigateur
- [ ] Aucune exception non gérée dans les logs du dernier scrape

### Code & Documentation
- [ ] CI GitHub Actions verte sur la branche `main`
- [ ] README pro : badges · pitch · GIF · archi · setup · stack · démo URL · licence
- [ ] `01-cadrage.md` et `02-roadmap.md` présents et à jour
- [ ] Commits atomiques avec messages conventionnels (`feat:`, `fix:`, `docs:`, `refactor:`…)
- [ ] Aucun secret en dur dans le code (vérification `grep -r password\|API_KEY src/`)
- [ ] `.env.example` à jour avec toutes les variables nécessaires
- [ ] Diagramme d'archi et ERD dans `docs/`

### Démo & Soutenance
- [ ] URL publique fonctionnelle et testée depuis un autre réseau
- [ ] Slides (10 max) : pitch · problème · archi · démo · challenges · résultats · suites
- [ ] Script démo répété 2 fois en 5 minutes chrono
- [ ] FAQ questions-réponses préparée (scraping éthique, choix technos, difficultés rencontrées)
- [ ] Backup offline si internet fail : vidéo MP4 de la démo sur le laptop
- [ ] Dump SQL local + assets en cas de panne Railway
- [ ] Laptop chargé + chargeur + adaptateur HDMI/USB-C dans le sac

### Logistique jury
- [ ] Lien GitHub partagé au jury avant la soutenance (si demandé)
- [ ] Lien démo partagé au jury
- [ ] Contact du jury vérifié (salle, horaire, matériel dispo)
- [ ] Arrivée prévue 20 min en avance pour tester vidéo-projecteur

---

## Rituel de fin de sprint

À la fin de chaque sprint, je te livre :

1. **Mini-rapport** de 10-15 lignes : ce qui a été fait · ce qui a été reporté · surprises rencontrées · métriques (nb commits, tests, lignes ajoutées/supprimées, offres en BDD)
2. **Captures d'écran** de l'état du projet (front / phpMyAdmin / dashboard) pour que tu puisses valider visuellement
3. **Questions en suspens** si j'ai rencontré un choix technique qui nécessite ton arbitrage
4. **Validation explicite demandée** avant de passer au sprint suivant

Ce rituel te permet de garder la main sans être sollicité en continu.

---

*Document rédigé le 19 avril 2026 — Version 1.0*
