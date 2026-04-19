#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup-server.sh — provisionne une instance Oracle Ubuntu 22.04
# pour faire tourner TechPulse en production.
#
# Usage :
#   scp -i key.pem setup-server.sh ubuntu@<IP>:~/
#   ssh -i key.pem ubuntu@<IP>
#   chmod +x setup-server.sh
#   ./setup-server.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Bastagas/techpulse.git}"
PROJECT_DIR="${HOME}/techpulse"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

log()  { echo -e "${CYAN}→${RESET} $*"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}!${RESET} $*"; }
die()  { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${CYAN}  TechPulse — setup Oracle Cloud Ubuntu 22.04${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# ─── 0. Checks préliminaires ─────────────────────
if [ "$(id -u)" -eq 0 ]; then
    die "Ne pas exécuter en root. Connecte-toi en 'ubuntu' et le script utilisera sudo quand nécessaire."
fi

if ! grep -qi "ubuntu" /etc/os-release; then
    warn "Ce script cible Ubuntu. Détection : $(grep -i '^NAME=' /etc/os-release)"
fi

# ─── 1. Mise à jour système ──────────────────────
log "Mise à jour apt (peut prendre 2-3 min)..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
ok "Système à jour"

# ─── 2. Paquets de base ──────────────────────────
log "Installation des paquets essentiels..."
sudo apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release \
    git make unzip ufw htop tmux nano

ok "Paquets de base installés"

# ─── 3. Docker ───────────────────────────────────
if command -v docker >/dev/null 2>&1; then
    ok "Docker déjà installé ($(docker --version))"
else
    log "Installation de Docker..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin

    sudo usermod -aG docker "$USER"
    ok "Docker installé"
fi

# ─── 4. UFW firewall ─────────────────────────────
log "Configuration du firewall UFW (22, 80, 443)..."
sudo ufw allow 22/tcp >/dev/null
sudo ufw allow 80/tcp >/dev/null
sudo ufw allow 443/tcp >/dev/null
sudo ufw --force enable >/dev/null
ok "Firewall actif"

# ─── 5. Clone du repo ────────────────────────────
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Repo déjà cloné, git pull..."
    cd "$PROJECT_DIR"
    git pull --ff-only
else
    log "Clone de $REPO_URL..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi
ok "Code à jour dans $PROJECT_DIR"

# ─── 6. .env.local ───────────────────────────────
if [ ! -f "$PROJECT_DIR/.env.local" ]; then
    log "Création de .env.local depuis .env.example..."
    cp .env.example .env.local

    # Génère un mot de passe root MySQL aléatoire
    ROOT_PW=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    APP_PW=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)

    sed -i "s/MYSQL_ROOT_PASSWORD=rootpass/MYSQL_ROOT_PASSWORD=${ROOT_PW}/" .env.local
    sed -i "s/MYSQL_PASSWORD=techpass/MYSQL_PASSWORD=${APP_PW}/" .env.local
    sed -i "s/APP_ENV=development/APP_ENV=production/" .env.local

    ok ".env.local créé avec mots de passe aléatoires"
    warn "ÉDITE .env.local pour mettre tes FRANCE_TRAVAIL_CLIENT_ID et CLIENT_SECRET !"
else
    ok ".env.local existe déjà, laissé inchangé"
fi

# ─── 7. Récap ────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  ✓ Setup serveur terminé${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "Prochaines étapes sur ce serveur :"
echo ""
echo "  1. ${CYAN}nano $PROJECT_DIR/.env.local${RESET}"
echo "     → remplis FRANCE_TRAVAIL_CLIENT_ID et CLIENT_SECRET"
echo ""
echo "  2. ${CYAN}newgrp docker${RESET}     # recharge les groupes pour éviter 'sudo docker'"
echo ""
echo "  3. ${CYAN}cd $PROJECT_DIR && docker compose --profile full up -d --build${RESET}"
echo "     → démarre la stack (premier build : ~5 min)"
echo ""
echo "  4. ${CYAN}docker compose exec -T mysql mysql -uroot -p\$(grep MYSQL_ROOT_PASSWORD .env.local | cut -d= -f2) techpulse < db/techpulse_snapshot.sql${RESET}"
echo "     → importe les 678 offres pré-scrapées"
echo ""
echo "  5. Tester depuis ton Mac :"
echo "     ${CYAN}curl http://$(curl -s ifconfig.me):5001/health${RESET}"
echo "     ${CYAN}curl http://$(curl -s ifconfig.me):8000/dashboard.php -o /dev/null -w '%{http_code}\\n'${RESET}"
echo ""
echo "Bonus : active le scraping automatique en mettant APSCHEDULER_ENABLED=1 dans .env.local."
