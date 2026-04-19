# Guide d'installation — correction sans Docker

> Ce document est dédié à **M. Gilles / Michel / Roger** pour faciliter la correction du projet TechPulse sans nécessiter l'installation de Docker.

**Temps estimé d'installation : 5 minutes.**

Le projet **fonctionne aussi avec Docker** (voir `README.md`) mais cette voie est optionnelle.

---

## Prérequis

| Outil | Version | Comment vérifier |
|---|---|---|
| **MAMP** (ou équivalent MySQL + phpMyAdmin) | 6+ | Ouvrir l'app, *Start* |
| **Python** | 3.11+ | `python3 --version` |
| **PHP** | 8.1+ | `php --version` |

MAMP est recommandé parce qu'il embarque MySQL + Apache + phpMyAdmin + PHP en une seule installation. Téléchargeable gratuitement sur **[mamp.info](https://www.mamp.info)**.

---

## Étape 1 — Démarrer MAMP

1. Lancer l'application **MAMP**.
2. Cliquer sur **"Start"** (MySQL + Apache démarrent, les voyants deviennent verts).
3. Noter les ports par défaut de MAMP :
   - MySQL : **8889** (pas 3306 !)
   - Apache : **8888**

## Étape 2 — Importer la base de données

1. Ouvrir **phpMyAdmin** : http://localhost:8888/phpMyAdmin (ou depuis l'onglet "Tools" de MAMP)
2. Identifiants MAMP par défaut : user `root` / password `root`.
3. Créer une base de données nommée **`techpulse`** (onglet *Bases de données* → *Créer*).
4. Sélectionner la base `techpulse` dans le menu de gauche.
5. Onglet **Importer** → choisir le fichier **`db/techpulse_snapshot.sql`** (livré dans le zip).
6. Cliquer sur **Exécuter**. ~30 secondes d'import.

La base contient alors **~3 000 offres d'emploi**, **~1 500 entreprises**, et **180+ technologies** canoniques. Le projet est immédiatement utilisable sans rescraper.

## Étape 3 — Installer les dépendances Python

Ouvrir un terminal à la racine du projet (le dossier extrait du `.zip`) :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Cela crée un environnement virtuel isolé et installe toutes les bibliothèques Python nécessaires (httpx, Flask, SQLAlchemy, spaCy, etc.).

## Étape 4 — Configurer les paramètres de connexion

Copier le fichier d'exemple :

```bash
cp .env.example .env.local
```

Ouvrir `.env.local` dans un éditeur de texte et **adapter les valeurs MAMP** :

```env
MYSQL_HOST=localhost
MYSQL_PORT=8889          # port MAMP (pas 3306)
MYSQL_USER=root
MYSQL_PASSWORD=root      # password MAMP par défaut
MYSQL_DATABASE=techpulse
```

## Étape 5 — Lancer l'API Flask

Dans le terminal (venv toujours activé) :

```bash
python -m techpulse_api
```

L'API est accessible sur **http://localhost:5001** avec la documentation Swagger sur **http://localhost:5001/docs**.

## Étape 6 — Lancer le frontend PHP

**Option A** : via le serveur intégré PHP (recommandé, zéro config) :

```bash
# dans un NOUVEAU terminal
php -S localhost:8000 -t frontend/public
```

Le frontend est accessible sur **http://localhost:8000**.

**Option B** : via Apache MAMP (si préféré) :

1. Copier le dossier `frontend/public/` dans `/Applications/MAMP/htdocs/techpulse/`
2. Accéder à http://localhost:8888/techpulse/

## Étape 7 — Tester le scraping (optionnel)

Si vous souhaitez vérifier que le scraping fonctionne (la base est déjà peuplée, ce n'est pas nécessaire) :

```bash
python -m techpulse_scraper run --spider=all --limit=20
```

Cela scrape 20 offres récentes depuis France Travail et HelloWork, les ajoute à la base.

---

## Points d'accès récapitulatifs

| Service | URL |
|---|---|
| **Frontend** (liste des offres, recherche, dashboard) | http://localhost:8000 |
| **API Swagger** (doc interactive) | http://localhost:5001/docs |
| **phpMyAdmin** (exploration BDD) | http://localhost:8888/phpMyAdmin |

---

## Dépannage rapide

| Problème | Solution |
|---|---|
| *"Access denied for user 'root'"* | Vérifier `MYSQL_PASSWORD=root` dans `.env.local` |
| *"Can't connect to MySQL"* | Vérifier `MYSQL_PORT=8889` et que MAMP est démarré |
| *"Module not found"* | Activer le venv : `source .venv/bin/activate` |
| Port 8000 déjà utilisé | Changer le port : `php -S localhost:9000 -t frontend/public` |
| Port 5000 déjà utilisé | Sur macOS, AirPlay occupe 5000 → désactiver dans *Réglages système → Général → AirDrop et Handoff → Récepteur AirPlay* |

---

## Contact

Pour toute question technique : **ruedasbastien@gmail.com**
