# Déploiement sur Oracle Cloud Always Free

> Guide complet : du compte Oracle jusqu'à `https://techpulse.xxx` avec HTTPS valide, gratuit à vie.

**Temps estimé : 2-3 heures en une fois. Ensuite chaque `git push` est auto-déployé par ton propre runner.**

---

## 📋 Ce que tu obtiens

- **Instance ARM Ampere** : 4 cores + 24 GB RAM + 200 GB disque — gratuit à vie
- **URL publique** : soit IP directe (gratuit), soit domaine `.xyz` (~1 €/an)
- **HTTPS valide** via Caddy + Let's Encrypt (auto-renouvelé)
- **24/7** : le site tourne même laptop fermé
- **Auto-redeploy** possible via webhook GitHub (optionnel, ajoutable plus tard)

---

## 🗂️ Plan des 5 étapes

1. [Créer le compte Oracle](#etape-1--creer-le-compte-oracle) (15 min)
2. [Provisionner une instance ARM](#etape-2--provisionner-une-instance-arm-ampere) (10-30 min)
3. [Se connecter en SSH](#etape-3--se-connecter-en-ssh) (5 min)
4. [Lancer le script `setup-server.sh`](#etape-4--provisionner-le-serveur) (15 min automatique)
5. [Démarrer TechPulse](#etape-5--demarrer-techpulse) (10 min)

**Bonus optionnels** :
- [Ajouter un domaine + HTTPS Caddy](#bonus-1--domaine--https)
- [Activer le scheduler auto (scraping hebdo)](#bonus-2--scheduler-automatique)

---

## Étape 1 · Créer le compte Oracle

1. Aller sur https://signup.cloud.oracle.com/
2. Remplir le formulaire :
   - Région : **Frankfurt (eu-frankfurt-1)** ou **Marseille (eu-marseille-1)** — le plus proche pour de meilleures perfs
   - Adresse + téléphone valides
   - **Carte bancaire** requise pour vérification identité — **aucun débit** réalisé (tu peux mettre une CB virtuelle Revolut si tu veux)
3. Validation de l'email + numéro (SMS)
4. Tu atterris sur le **Oracle Cloud Dashboard**

### ⚠️ Points d'attention

- Utilise ton **vrai nom** et **vraie adresse** — ils vérifient. Les comptes rejetés sont fréquents avec des infos bidons.
- Oracle détecte les VPN/proxys → désactive NordVPN / Cloudflare WARP pendant l'inscription.
- Si ton premier essai échoue ("We were unable to verify your account"), attends 24 h avant de réessayer avec une **autre CB** — c'est leur algo anti-abuse.

---

## Étape 2 · Provisionner une instance ARM Ampere

Depuis le dashboard Oracle :

1. Menu hamburger → **Compute** → **Instances** → **Create instance**
2. Remplir :
   - **Name** : `techpulse`
   - **Image** : cliquer **Change image** → Ubuntu → **Canonical Ubuntu 22.04**
   - **Shape** : cliquer **Change shape** → onglet **Ampere** → sélectionner **VM.Standard.A1.Flex**
     - **OCPUs** : `4` (max free)
     - **Memory** : `24 GB` (max free)
   - **Networking** : laisser par défaut (nouveau VCN + subnet public)
   - **SSH keys** :
     - Option simple : clique **Generate a key pair for me** → **Save private key** (fichier `ssh-key-XXXX.key` téléchargé)
     - Option pro : colle ta clé publique existante (`~/.ssh/id_rsa.pub`)
3. **Create**

### 🔄 Si "Out of capacity"

Oracle refuse parfois la création ARM parce que la région est saturée. Dans ce cas :

```
❌ Out of host capacity. Please try again later or choose a different shape.
```

**Solutions (dans l'ordre)** :
1. Réessayer toutes les 30 min — souvent ça passe
2. Changer de **availability domain** (AD-1, AD-2, AD-3 dans la liste)
3. Changer de région (Frankfurt ↔ Marseille) — attention, nécessite un "tenancy switch" qui prend quelques minutes
4. Réduire OCPU à 2 et RAM à 12 GB (toujours gratuit, plus dispo)
5. Script community qui retry toutes les 5 min : https://github.com/hitrov/oci-arm-host-capacity

**Scénario typique** : ça passe en 1-3 tentatives, max 2-3 h d'attente au pire.

---

## Étape 3 · Se connecter en SSH

Une fois l'instance créée (statut **Running**) :

1. Dans la fiche de l'instance → **Public IP address** → copier (ex. `152.67.12.34`)
2. Déplacer la clé SSH téléchargée dans `~/.ssh/` et sécuriser les droits :

```bash
mv ~/Downloads/ssh-key-XXXX.key ~/.ssh/oracle_techpulse.key
chmod 400 ~/.ssh/oracle_techpulse.key
```

3. Tester la connexion :

```bash
ssh -i ~/.ssh/oracle_techpulse.key ubuntu@152.67.12.34
```

Le premier prompt demande de confirmer le fingerprint → **yes**. Tu devrais voir :

```
Welcome to Ubuntu 22.04.4 LTS (GNU/Linux 6.5.0-1018-oracle aarch64)
ubuntu@techpulse:~$
```

### 🛡️ Ouvrir les ports dans Oracle Security Lists

Par défaut, Oracle **bloque tout sauf le port 22 (SSH)**. Il faut autoriser 80 et 443 :

1. Dashboard Oracle → **Networking** → **Virtual Cloud Networks** → ton VCN
2. **Security Lists** → **Default Security List for vcn-xxx** → **Add Ingress Rules**
3. Ajouter 2 règles :

| Source CIDR | Protocol | Destination Port |
|---|---|---|
| `0.0.0.0/0` | TCP | `80` |
| `0.0.0.0/0` | TCP | `443` |

Sauvegarder. Les ports sont maintenant ouverts vers l'Internet.

---

## Étape 4 · Provisionner le serveur

Sur ton Mac, envoie le script `setup-server.sh` sur l'instance :

```bash
scp -i ~/.ssh/oracle_techpulse.key deploy/oracle/setup-server.sh ubuntu@152.67.12.34:~/
```

Puis connecte-toi et lance-le :

```bash
ssh -i ~/.ssh/oracle_techpulse.key ubuntu@152.67.12.34
chmod +x setup-server.sh
./setup-server.sh
```

Le script installe automatiquement :
- Docker + docker-compose plugin
- Git, Make, curl, utilitaires
- Clone du repo GitHub
- Configuration firewall Ubuntu (UFW) : ports 22/80/443 ouverts
- Création du `.env.local` à remplir

**Durée : ~10 minutes.**

### Remplir les secrets

Le script te demandera à la fin d'éditer `.env.local` :

```bash
cd ~/techpulse
nano .env.local
```

Mets les **vraies valeurs** (reprends ton `.env.local` local) :

```env
MYSQL_ROOT_PASSWORD=change-moi-par-un-mot-de-passe-long
MYSQL_PASSWORD=change-moi-aussi
FRANCE_TRAVAIL_CLIENT_ID=PAR_techpulseobservatoire_4e4c47...
FRANCE_TRAVAIL_CLIENT_SECRET=b093c3cd92c41c117...
APSCHEDULER_ENABLED=1       # Active le scraping auto hebdo en prod
```

Sauvegarde (`Ctrl+X` → `Y` → `Entrée`).

---

## Étape 5 · Démarrer TechPulse

Toujours connecté à l'instance :

```bash
cd ~/techpulse
docker compose --profile full up -d --build
```

Première exécution : ~5 min de build.

Puis importer la BDD :

```bash
# Le snapshot SQL est déjà dans le repo
docker compose exec -T mysql mysql -uroot -p$(grep '^MYSQL_ROOT_PASSWORD=' .env.local | cut -d= -f2) techpulse < db/techpulse_snapshot.sql
```

### 🎉 Vérifier que tout tourne

Depuis ton Mac :

```bash
curl http://152.67.12.34:5001/health
curl http://152.67.12.34:8000/dashboard.php -o /dev/null -w "%{http_code}\n"
```

**Si tu vois HTTP 200, c'est en ligne !** Ouvre :

- **Frontend** : http://152.67.12.34:8000
- **Dashboard** : http://152.67.12.34:8000/dashboard.php
- **API Swagger** : http://152.67.12.34:5001/docs

*Remplace `152.67.12.34` par TA vraie IP publique.*

---

## Bonus 1 · Domaine + HTTPS

Pour avoir une URL propre type `https://techpulse.xyz` au lieu de `http://152.67.12.34:8000` :

### A. Acheter un domaine

- **Namecheap** `.xyz` à ~1 €/an : https://www.namecheap.com/domains/registration/results/?domain=techpulse
- Ou **Gandi**, **OVH**, **Porkbun** selon préférence

### B. Pointer le domaine sur l'IP Oracle

Chez ton registrar → DNS → ajouter 2 enregistrements A :

```
A     techpulse.xyz      152.67.12.34       600
A     www.techpulse.xyz  152.67.12.34       600
A     api.techpulse.xyz  152.67.12.34       600
```

Propagation DNS : 5-30 min.

### C. Activer Caddy (reverse proxy + SSL auto)

Sur l'instance :

```bash
cd ~/techpulse
cp deploy/oracle/docker-compose.prod.yml docker-compose.override.yml
cp deploy/oracle/Caddyfile .
# Éditer Caddyfile pour remplacer techpulse.xyz par ton domaine
nano Caddyfile
# Puis :
docker compose --profile full down
docker compose --profile full up -d
```

Caddy va automatiquement obtenir les certificats Let's Encrypt. Attends ~60 s puis :

```
🌐 https://techpulse.xyz                → frontend
🌐 https://techpulse.xyz/dashboard.php  → dashboard
🌐 https://api.techpulse.xyz/docs       → Swagger API
```

**HTTPS valide, renouvelé automatiquement tous les 60 jours.**

---

## Bonus 2 · Scheduler automatique

Si tu veux que TechPulse **scrape tout seul** chaque semaine :

1. Dans `.env.local` sur le serveur :
   ```
   APSCHEDULER_ENABLED=1
   APSCHEDULER_CRON_HOUR=3
   APSCHEDULER_CRON_MINUTE=0
   ```
2. Redémarrer le service API :
   ```bash
   docker compose restart api
   ```
3. Vérifier : `curl http://<IP>:5001/stats/runs` → `scheduler.enabled: true`

Le scraping se lancera tous les jours à 03:00 UTC.

---

## 🆘 Troubleshooting

| Problème | Solution |
|---|---|
| `ssh: connect to host ... port 22: Operation timed out` | Vérifier ingress rules Oracle (port 22 autorisé) et que tu utilises la bonne IP publique |
| `Permission denied (publickey)` | `chmod 400 ~/.ssh/oracle_techpulse.key` · user = `ubuntu` (pas `root`) |
| `docker compose` command not found | Relancer `setup-server.sh` ou exécuter manuellement les étapes qui ont échoué |
| Site inaccessible sur port 80 depuis l'extérieur | Vérifier (a) ingress Oracle + (b) UFW : `sudo ufw status` doit montrer 80 autorisé |
| Caddy ne récupère pas de certificats SSL | DNS pas encore propagé (attendre 30 min) ou port 443 bloqué par Oracle |
| Out of memory au build | Improbable avec 24 GB, sinon `docker builder prune` pour libérer |
| `No space left on device` | `docker system prune -a` pour virer images/containers inutiles |

---

## 🔄 Mise à jour du site après un `git push`

Connecté en SSH sur l'instance :

```bash
cd ~/techpulse
git pull
docker compose --profile full up -d --build
```

Environ 2-3 min pour rebuilder les images modifiées.

### 🤖 Auto-deploy (optionnel, plus avancé)

Pour que chaque `git push` redéploie automatiquement, tu peux utiliser :
- **Webhook GitHub → script sur le serveur** (simple mais demande un port ouvert)
- **GitHub Actions → SSH → git pull** (propre mais demande une clé SSH deploy)
- **Watchtower** (container Docker qui surveille les images)

Un guide séparé peut être ajouté à la demande.

---

## 💰 Coût réel

| Item | Coût |
|---|---|
| Instance ARM (4 cores + 24 GB RAM) | **0 €** à vie |
| 200 GB storage | 0 € |
| 10 TB traffic sortant / mois | 0 € |
| IP publique fixe | 0 € |
| Domaine `.xyz` (optionnel) | ~1 €/an |
| Certificats SSL Let's Encrypt | 0 € |
| **Total** | **0 à 1 €/an** |

Compare à Railway : 60 $/an minimum. Oracle gagne largement pour un projet étudiant.

---

## 🆚 Quand basculer sur Railway ?

- Tu veux auto-deploy à chaque git push **sans effort**
- Tu n'as pas envie de gérer Linux / Docker / SSL
- Tu veux un support en cas de pépin
- Ton budget accepte 5 $/mois

Sinon, Oracle reste imbattable pour un projet perso tant que la stack reste simple.
