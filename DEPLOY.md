# Guide de déploiement — Railway

> Ce guide te permet de déployer TechPulse en production sur [Railway](https://railway.app) pour obtenir une URL publique partageable (portfolio, CV, soutenance).

**Durée estimée : 20-30 minutes.** Gratuit avec le tier de base Railway (5 $ de crédits offerts).

---

## Pourquoi Railway ?

- Supporte MySQL + Docker + PHP + Python en un seul projet
- Déploiement automatique à chaque push GitHub
- URL publique HTTPS par service
- Logs en temps réel, metrics, rollback
- 5 $ offerts mensuels (suffisant pour ce projet)

Alternative : Fly.io (gratuit mais setup plus technique), Render (gratuit avec cold start).

---

## 1. Compte Railway

1. Créer un compte sur https://railway.app (login via GitHub recommandé).
2. Autoriser l'accès au repo `Bastagas/techpulse` quand demandé.

## 2. Créer le projet Railway

Depuis le dashboard Railway :

1. **New Project** → **Deploy from GitHub repo** → sélectionner `Bastagas/techpulse`.
2. Railway va scanner le repo et détecter les services possibles.
3. Par défaut il créera un service depuis le root. **Supprime ce service** — on en créera 3 manuellement.

## 3. Ajouter le service MySQL

1. Dans le projet : **+ New** → **Database** → **MySQL**.
2. Railway provisionne MySQL 8 en ~30 s.
3. Onglet **Variables** du service MySQL — noter les valeurs générées :
   - `MYSQL_URL`, `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`

### Initialiser le schéma

1. Dans le service MySQL, cliquer **Data** → **New** → Collerle contenu de `db/migrations/001_init.sql`.
2. Idem pour `db/seeds/02_technologies.sql`.
3. Idem pour `db/techpulse_snapshot.sql` (import des offres existantes).

*Alternative : connecter MySQL Workbench à `MYSQL_PUBLIC_URL` et exécuter les 3 SQL.*

## 4. Déployer l'API Flask

1. **+ New** → **GitHub Repo** → `Bastagas/techpulse`.
2. Settings → **Root Directory** : laisser vide.
3. Settings → **Build** → Builder : **Dockerfile**.
4. Settings → **Build** → Dockerfile Path : `api/Dockerfile`.
5. Settings → **Variables** : ajouter (référence vers le service MySQL) :
   ```
   MYSQL_HOST=${{MySQL.MYSQLHOST}}
   MYSQL_PORT=${{MySQL.MYSQLPORT}}
   MYSQL_USER=${{MySQL.MYSQLUSER}}
   MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}
   MYSQL_DATABASE=${{MySQL.MYSQLDATABASE}}
   FRANCE_TRAVAIL_CLIENT_ID=<ta clé>
   FRANCE_TRAVAIL_CLIENT_SECRET=<ta clé secrète>
   APSCHEDULER_ENABLED=1
   APSCHEDULER_CRON_HOUR=3
   ```
6. Settings → **Networking** → **Generate Domain** → Railway génère `techpulse-api-production.up.railway.app`.
7. Déploiement automatique, ~3-5 min.
8. Test : ouvrir `https://<ton-domaine>/docs` → Swagger UI doit s'afficher.

## 5. Déployer le frontend PHP

1. **+ New** → **GitHub Repo** → `Bastagas/techpulse`.
2. Settings → **Root Directory** : `frontend`.
3. Settings → **Build** → Builder : **Dockerfile**.
4. Variables : idem que l'API + pointer vers MySQL.
5. Generate Domain → `techpulse-frontend-production.up.railway.app`.
6. ~3 min de build. Ouvrir l'URL → dashboard live.

## 6. Configurer le domaine

Pour un nom plus propre qu'`up.railway.app` :
1. Settings → **Networking** → **Custom Domain**.
2. Railway donne un CNAME. Le mettre chez ton registrar (Gandi, OVH, Cloudflare).
3. SSL automatique via Let's Encrypt.

## 7. Vérification post-déploiement

- [ ] `https://api.../health` retourne `{"status":"ok","offers_count": ...}`
- [ ] `https://api.../docs` affiche Swagger UI
- [ ] `https://api.../stats/top-techs` retourne un JSON non vide
- [ ] `https://frontend.../` affiche la page d'accueil avec les offres
- [ ] `https://frontend.../dashboard.php` affiche les 4 charts + heatmap
- [ ] Modifier un fichier sur `main` → auto-deploy en < 2 min

## 8. Mettre à jour le README et le GUIDE_PROF

Remplacer les URLs `localhost` par les URLs de production Railway :

```markdown
## Démo en live
🌐 https://techpulse-frontend-production.up.railway.app
📊 https://techpulse-api-production.up.railway.app/docs
```

---

## Coût estimé

| Service | RAM | Prix / mois |
|---|---|---|
| MySQL | 512 Mo | ~$3 |
| API Flask | 256 Mo | ~$1 |
| Frontend PHP | 256 Mo | ~$1 |
| **Total** | | **~$5** |

Le tier gratuit Railway (5 $ offerts) couvre **1 mois de démo**. Largement suffisant pour la soutenance + démo à des recruteurs.

Pour plus long terme : passer au Hobby Plan (5 $/mois) ou basculer sur Fly.io.

---

## Alternatives si Railway ne convient pas

- **Fly.io** : gratuit jusqu'à 3 VMs de 256 Mo. Plus technique (CLI flyctl) mais très léger.
- **Render** : gratuit avec cold start (service s'endort après 15 min d'inactivité).
- **VPS (OVH, DigitalOcean)** : 5 $/mois, full control, setup manuel avec docker compose.

---

## Troubleshooting

| Problème | Solution |
|---|---|
| 502 Bad Gateway | Service encore en train de build. Vérifier les logs. |
| Can't connect to MySQL | Variables mal pointées. Utiliser `${{MySQL.MYSQLHOST}}`. |
| Port binding | Railway injecte `$PORT`. Les Dockerfiles l'utilisent déjà. |
| Scheduler ne tourne pas | Vérifier `APSCHEDULER_ENABLED=1` dans les variables. |
| Out of memory | Passer au Hobby Plan (plus de RAM) ou réduire workers gunicorn. |
