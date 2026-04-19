SHELL := /bin/bash
.DEFAULT_GOAL := help

# Couleurs
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

.PHONY: help setup up down restart logs ps scrape scrape-sample dev test lint format clean backup snapshot setup-mamp check-docker

help: ## Affiche cette aide
	@echo ""
	@echo "$(CYAN)TechPulse — commandes disponibles$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-16s$(RESET) %s\n", $$1, $$2}'
	@echo ""

check-docker: ## Vérifie que Docker est installé et actif
	@docker --version >/dev/null 2>&1 || (echo "❌ Docker n'est pas installé. Installe OrbStack ou Docker Desktop." && exit 1)
	@docker info >/dev/null 2>&1 || (echo "❌ Le daemon Docker n'est pas démarré. Lance OrbStack." && exit 1)
	@echo "✓ Docker OK"

setup: check-docker ## Setup complet (Docker) : stack + BDD + deps Python/PHP
	@test -f .env.local || (cp .env.example .env.local && echo "→ .env.local créé depuis .env.example")
	@echo "→ Démarrage stack Docker..."
	@docker compose up -d
	@echo "→ Attente MySQL prêt..."
	@until docker compose exec -T mysql mysqladmin ping -h localhost --silent 2>/dev/null; do sleep 1; done
	@echo "→ Install Python (scraper)..."
	@cd scraper && python3 -m venv .venv 2>/dev/null; true
	@cd scraper && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -e ".[dev]"
	@echo "→ Install Python (api)..."
	@cd api && python3 -m venv .venv 2>/dev/null; true
	@cd api && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -e ".[dev]"
	@echo "→ Install PHP..."
	@cd frontend && composer install -q 2>/dev/null || echo "  (composer.json vide pour l'instant)"
	@echo ""
	@echo "$(GREEN)✓ Setup terminé.$(RESET)"
	@echo "  • phpMyAdmin : http://localhost:8080  (root / rootpass)"
	@echo "  • MySQL      : localhost:3306         (root / rootpass)"

up: check-docker ## Démarre la stack Docker
	docker compose up -d

down: ## Arrête la stack Docker
	docker compose down

restart: down up ## Restart complet

logs: ## Affiche les logs Docker en direct
	docker compose logs -f

ps: ## Liste les conteneurs actifs
	docker compose ps

scrape: ## Lance le scraping (tous les spiders)
	@cd scraper && .venv/bin/python -m techpulse_scraper run --spider=all

scrape-sample: ## Scrape 50 offres par source (rapide, pour dev)
	@cd scraper && .venv/bin/python -m techpulse_scraper run --spider=all --limit=50

dev: ## Lance l'API Flask (5000) et le front PHP (8000) en parallèle
	@echo "→ API Flask en arrière-plan (localhost:5000)..."
	@cd api && .venv/bin/python -m techpulse_api &
	@echo "→ Front PHP (localhost:8000)..."
	@cd frontend && php -S localhost:8000 -t public

test: ## Lance tous les tests (pytest scraper + api)
	@cd scraper && .venv/bin/pytest tests/ -v
	@cd api && .venv/bin/pytest tests/ -v

lint: ## Vérifie le code (ruff)
	@cd scraper && .venv/bin/ruff check src/ tests/
	@cd api && .venv/bin/ruff check src/ tests/

format: ## Formate le code Python (ruff)
	@cd scraper && .venv/bin/ruff format src/ tests/
	@cd api && .venv/bin/ruff format src/ tests/

clean: ## Supprime caches, venvs, node_modules, vendor
	@find . -type d -name '__pycache__' -not -path '*/node_modules/*' -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name '.venv' -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name 'node_modules' -exec rm -rf {} + 2>/dev/null; true
	@find . -type d -name 'vendor' -exec rm -rf {} + 2>/dev/null; true
	@echo "✓ Caches supprimés"

backup: ## Dump BDD → db/backup/techpulse_YYYYMMDD_HHMMSS.sql
	@mkdir -p db/backup
	@docker compose exec -T mysql mysqldump -uroot -p$$(grep '^MYSQL_ROOT_PASSWORD=' .env.local | cut -d= -f2) techpulse > db/backup/techpulse_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ Backup créé dans db/backup/"

snapshot: ## Génère db/techpulse_snapshot.sql (livrable prof)
	@docker compose exec -T mysql mysqldump -uroot -p$$(grep '^MYSQL_ROOT_PASSWORD=' .env.local | cut -d= -f2) --single-transaction --routines --triggers techpulse > db/techpulse_snapshot.sql
	@echo "✓ Snapshot généré : db/techpulse_snapshot.sql"

setup-mamp: ## Setup pour path MAMP (sans Docker) — pour grading prof
	@bash setup_mamp.sh
