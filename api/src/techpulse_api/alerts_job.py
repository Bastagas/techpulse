"""Job périodique : vérifie les alertes et envoie les emails.

Appelé par APScheduler toutes les heures (via init_scheduler).
Peut aussi être lancé manuellement :
    python -m techpulse_api.alerts_job
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from techpulse_scraper.db import get_session
from techpulse_scraper.models import Alert, Offer, OfferTechnology, Technology

from techpulse_api.email_sender import send_email


def _build_email_html(alert: Alert, offers: list[Offer]) -> str:
    """Construit le HTML de l'email de notification."""
    base_url = os.environ.get("PUBLIC_FRONTEND_URL", "http://localhost:8000")
    rows = []
    for o in offers:
        techs = ", ".join(link.technology.display_name for link in o.tech_links[:5])
        salary = f"{o.salary_min:,} – {o.salary_max:,} €".replace(",", " ") if o.salary_min else "Salaire non précisé"
        rows.append(
            f'<tr><td style="padding:10px;border-bottom:1px solid #eee;">'
            f'<a href="{base_url}/offer.php?id={o.id}" style="color:#2563eb;text-decoration:none;font-weight:600;">{o.title}</a><br>'
            f'<span style="color:#666;font-size:13px;">{o.company.name if o.company else ""} · {o.city or ""}</span><br>'
            f'<span style="color:#888;font-size:12px;">{salary} · {techs}</span>'
            f'</td></tr>'
        )
    filter_desc = []
    if alert.filter_keyword:
        filter_desc.append(f"mot-clé « {alert.filter_keyword} »")
    if alert.filter_city:
        filter_desc.append(f"ville : {alert.filter_city}")
    if alert.filter_tech:
        filter_desc.append(f"techno : {alert.filter_tech}")
    if alert.filter_contract:
        filter_desc.append(f"contrat : {alert.filter_contract}")
    if alert.filter_salary_min:
        filter_desc.append(f"salaire ≥ {alert.filter_salary_min} €")
    filter_str = " · ".join(filter_desc) or "tous les critères"

    return f"""<!DOCTYPE html>
<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<h2 style="color: #1e3a8a;">🎯 TechPulse — {len(offers)} nouvelle{'s' if len(offers) > 1 else ''} offre{'s' if len(offers) > 1 else ''} pour ton alerte</h2>
<p style="color: #555;">Filtres : <strong>{filter_str}</strong></p>
<table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
{"".join(rows)}
</table>
<p style="margin-top: 30px; font-size: 12px; color: #888;">
Tu as {alert.notification_count + 1} notification{"s" if alert.notification_count >= 1 else ""} pour cette alerte.
<br><a href="{base_url}/unsubscribe.php?token={alert.token}" style="color:#dc2626;">Me désabonner</a>
</p>
</body></html>"""


def check_alerts() -> dict:
    """Vérifie toutes les alertes actives, envoie les mails, met à jour last_notified_at."""
    stats = {"alerts_checked": 0, "emails_sent": 0, "errors": 0}
    now = datetime.utcnow()

    with get_session() as session:
        alerts = session.scalars(
            select(Alert).where(Alert.is_active.is_(True))
        ).all()
        stats["alerts_checked"] = len(alerts)

        for alert in alerts:
            # Période de check : depuis le dernier envoi, ou 7 jours en arrière pour les nouvelles alertes
            since = alert.last_notified_at or (now - timedelta(days=7))

            query = (
                select(Offer)
                .options(
                    selectinload(Offer.company),
                    selectinload(Offer.tech_links).selectinload(OfferTechnology.technology),
                )
                .where(
                    Offer.is_active.is_(True),
                    Offer.posted_at >= since,
                )
                .order_by(Offer.posted_at.desc())
                .limit(20)
            )
            if alert.filter_keyword:
                kw = f"%{alert.filter_keyword}%"
                query = query.where((Offer.title.like(kw)) | (Offer.description.like(kw)))
            if alert.filter_city:
                query = query.where(Offer.city == alert.filter_city)
            if alert.filter_contract:
                query = query.where(Offer.contract_type == alert.filter_contract)
            if alert.filter_salary_min:
                query = query.where(Offer.salary_min >= alert.filter_salary_min)
            if alert.filter_tech:
                sub = (
                    select(Offer.id)
                    .join(Offer.tech_links)
                    .join(Technology)
                    .where(Technology.canonical_name == alert.filter_tech)
                )
                query = query.where(Offer.id.in_(sub))

            matching_offers = list(session.scalars(query).unique())

            if not matching_offers:
                continue

            success = send_email(
                to=alert.email,
                subject=f"TechPulse — {len(matching_offers)} nouvelle(s) offre(s) pour toi",
                html_body=_build_email_html(alert, matching_offers),
            )
            if success:
                alert.last_notified_at = now
                alert.notification_count += 1
                alert.last_offers_count = len(matching_offers)
                stats["emails_sent"] += 1
            else:
                stats["errors"] += 1

    return stats


def main() -> int:
    print(f"━━━ Check alertes · {datetime.now().isoformat()} ━━━")
    stats = check_alerts()
    print(f"  {stats['alerts_checked']} alertes vérifiées")
    print(f"  {stats['emails_sent']} emails envoyés")
    print(f"  {stats['errors']} erreurs")
    print("\n  Log : /tmp/techpulse_emails.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
