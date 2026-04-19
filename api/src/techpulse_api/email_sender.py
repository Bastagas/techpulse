"""Envoi d'emails via SMTP (ou log local si SMTP non configuré).

Variables d'env :
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM

Si SMTP_HOST vide → mode log seul (écriture dans /tmp/techpulse_emails.log).
Parfait pour dev sans compte mail, ou pour tester sans pollution.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

LOG_FILE = Path("/tmp/techpulse_emails.log")


def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    """Envoie un email. Retourne True si envoyé (ou loggué en dev)."""
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_from = os.environ.get("SMTP_FROM", smtp_user or "noreply@techpulse.local")

    if not smtp_host:
        # Mode dev : log seul
        _log_email(to, subject, html_body)
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls(context=context)
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        _log_email(to, subject, html_body, sent=True)
        return True
    except Exception as exc:  # noqa: BLE001
        _log_email(to, subject, html_body, sent=False, error=str(exc))
        return False


def _log_email(
    to: str, subject: str, html: str, *, sent: bool | None = None, error: str | None = None
) -> None:
    status = "SENT" if sent else ("FAILED" if sent is False else "LOGGED (no SMTP configured)")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(
            f"\n{'=' * 60}\n"
            f"[{datetime.now().isoformat()}] {status}\n"
            f"To: {to}\nSubject: {subject}\n"
        )
        if error:
            f.write(f"Error: {error}\n")
        f.write(f"\n--- HTML ---\n{html[:2000]}\n")
