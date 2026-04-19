"""Scheduler APScheduler — scraping automatique périodique.

Activation via la variable d'env `APSCHEDULER_ENABLED=1`. Par défaut, OFF
(évite de scraper accidentellement en dev). En production on l'active et
le scheduler relance les spiders toutes les 24 h.

Le Makefile expose `make scheduler-enable` pour activer le job à la demande.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler: BackgroundScheduler | None = None


def _scraping_job() -> None:
    """Lance le scraping via la CLI. Exécuté dans un sous-processus pour isoler
    les erreurs et éviter de monopoliser le thread principal Flask."""
    start = datetime.utcnow()
    print(f"[scheduler] {start.isoformat()} lancement du scraping…", flush=True)
    try:
        result = subprocess.run(
            ["python", "-m", "techpulse_scraper", "run", "--spider=all", "--limit=1000"],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min max
        )
        print(f"[scheduler] terminé ({result.returncode}) : {result.stdout[-300:]}", flush=True)
        if result.returncode != 0:
            print(f"[scheduler] erreur stderr : {result.stderr[-300:]}", flush=True)
    except subprocess.TimeoutExpired:
        print("[scheduler] TIMEOUT après 30 min", flush=True)
    except Exception as exc:
        print(f"[scheduler] exception : {exc}", flush=True)


def init_scheduler() -> BackgroundScheduler | None:
    """Initialise le scheduler si `APSCHEDULER_ENABLED=1` dans l'env.

    Configuration par défaut : cron journalier à 03h00 UTC (ajustable via
    `APSCHEDULER_CRON_HOUR` et `APSCHEDULER_CRON_MINUTE`).
    """
    global scheduler
    if scheduler is not None:
        return scheduler
    if os.environ.get("APSCHEDULER_ENABLED") != "1":
        return None

    hour = int(os.environ.get("APSCHEDULER_CRON_HOUR", 3))
    minute = int(os.environ.get("APSCHEDULER_CRON_MINUTE", 0))

    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    scheduler.add_job(
        _scraping_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="scrape_all",
        name="Scrape tous les spiders",
        replace_existing=True,
    )
    scheduler.add_job(
        _alerts_check_job,
        trigger=CronTrigger(minute=15),  # Chaque heure à :15
        id="check_alerts",
        name="Vérifie les alertes email",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler


def _alerts_check_job() -> None:
    """Check alertes et envoie les emails. Import tardif pour éviter boucle."""
    from techpulse_api.alerts_job import check_alerts

    start = datetime.utcnow()
    print(f"[scheduler] {start.isoformat()} check des alertes…", flush=True)
    try:
        stats = check_alerts()
        print(
            f"[scheduler] alertes : {stats['alerts_checked']} vérifiées, "
            f"{stats['emails_sent']} emails envoyés, {stats['errors']} erreurs",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[scheduler] erreur alertes : {exc}", flush=True)


def get_next_run() -> datetime | None:
    """Renvoie la date de la prochaine exécution planifiée (si scheduler actif)."""
    if scheduler is None:
        return None
    job = scheduler.get_job("scrape_all")
    return job.next_run_time if job else None
