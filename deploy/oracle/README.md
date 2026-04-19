# Déploiement Oracle Cloud — fichiers

Guide complet : **[ORACLE.md](ORACLE.md)**

## Fichiers

| Fichier | Rôle |
|---|---|
| `ORACLE.md` | Guide étape par étape du déploiement (création compte → URL live HTTPS) |
| `setup-server.sh` | Script à lancer sur l'instance Ubuntu fraîchement provisionnée (Docker + firewall + clone repo + .env.local) |
| `docker-compose.prod.yml` | Override compose pour la prod : ferme les ports applicatifs, ajoute Caddy en front |
| `Caddyfile` | Reverse proxy avec domaine + HTTPS auto Let's Encrypt |
| `Caddyfile.ip-only` | Alternative si pas de domaine (IP publique brute, pas de HTTPS) |

## Workflow rapide

```bash
# 1. Sur ton Mac, transfère le script sur l'instance Oracle
scp -i ~/.ssh/oracle_techpulse.key deploy/oracle/setup-server.sh ubuntu@<IP>:~/

# 2. SSH, lance le script
ssh -i ~/.ssh/oracle_techpulse.key ubuntu@<IP>
./setup-server.sh

# 3. Édite les secrets (France Travail)
nano ~/techpulse/.env.local

# 4. Démarre
cd ~/techpulse
newgrp docker
docker compose --profile full up -d --build

# 5. Importe les données
docker compose exec -T mysql mysql -uroot -p$(grep MYSQL_ROOT_PASSWORD .env.local | cut -d= -f2) techpulse < db/techpulse_snapshot.sql

# 6. Depuis ton Mac, teste l'URL
curl http://<IP>:8000/dashboard.php -o /dev/null -w "%{http_code}\n"
```
