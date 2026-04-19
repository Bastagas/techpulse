#!/usr/bin/env bash
# TechPulse — setup pour path MAMP (sans Docker)
# Usage : bash setup_mamp.sh

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${CYAN}━━━ TechPulse — setup MAMP (sans Docker) ━━━${RESET}"
echo ""

# ─── 1. Vérifier Python ─────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}✗ Python 3 non trouvé. Installer Python 3.11+ depuis python.org${RESET}"
  exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓${RESET} Python $PYVER détecté"

# ─── 2. Vérifier PHP ────────────────────────────
if ! command -v php &>/dev/null; then
  echo -e "${RED}✗ PHP non trouvé. Installer PHP 8.1+ (inclus dans MAMP ou via brew install php)${RESET}"
  exit 1
fi
PHPVER=$(php -r 'echo PHP_VERSION;')
echo -e "${GREEN}✓${RESET} PHP $PHPVER détecté"

# ─── 3. Créer .env.local si absent ──────────────
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  # Adapter pour MAMP
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/MYSQL_PORT=3306/MYSQL_PORT=8889/' .env.local
    sed -i '' 's/MYSQL_PASSWORD=techpass/MYSQL_PASSWORD=root/' .env.local
    sed -i '' 's/MYSQL_USER=techpulse/MYSQL_USER=root/' .env.local
  else
    sed -i 's/MYSQL_PORT=3306/MYSQL_PORT=8889/' .env.local
    sed -i 's/MYSQL_PASSWORD=techpass/MYSQL_PASSWORD=root/' .env.local
    sed -i 's/MYSQL_USER=techpulse/MYSQL_USER=root/' .env.local
  fi
  echo -e "${GREEN}✓${RESET} .env.local créé et adapté pour MAMP (port 8889, root/root)"
else
  echo -e "${YELLOW}!${RESET} .env.local existe déjà — laissé inchangé"
fi

# ─── 4. Virtualenv Python ───────────────────────
if [ ! -d .venv ]; then
  python3 -m venv .venv
  echo -e "${GREEN}✓${RESET} Virtualenv créé dans .venv/"
else
  echo -e "${YELLOW}!${RESET} .venv existe déjà"
fi

# ─── 5. Installer les dépendances ───────────────
echo -e "${CYAN}→ Installation des dépendances Python (peut prendre 1-2 min)...${RESET}"
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

# ─── 6. Installer les packages locaux en mode dev ─
./.venv/bin/pip install -q -e ./scraper
./.venv/bin/pip install -q -e ./api
echo -e "${GREEN}✓${RESET} Dépendances Python installées"

# ─── 7. Composer pour le frontend ───────────────
if [ -f frontend/composer.json ]; then
  if command -v composer &>/dev/null; then
    (cd frontend && composer install -q)
    echo -e "${GREEN}✓${RESET} Dépendances PHP installées"
  else
    echo -e "${YELLOW}!${RESET} Composer non installé — optionnel pour Sprint 0, requis plus tard"
  fi
fi

# ─── 8. Rappel étapes manuelles ─────────────────
echo ""
echo -e "${CYAN}━━━ Étapes manuelles restantes ━━━${RESET}"
echo ""
echo "1. Lancer MAMP (MySQL + Apache)"
echo "2. Ouvrir phpMyAdmin : http://localhost:8888/phpMyAdmin"
echo "3. Créer la base : techpulse"
echo "4. Importer : db/techpulse_snapshot.sql"
echo "5. Activer le venv :     source .venv/bin/activate"
echo "6. Lancer l'API :        python -m techpulse_api"
echo "7. Lancer le frontend :  php -S localhost:8000 -t frontend/public"
echo ""
echo -e "${GREEN}✓ Setup MAMP terminé. Voir GUIDE_PROF.md pour les détails.${RESET}"
