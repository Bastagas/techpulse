"""Configuration centralisée — chargée depuis `.env.local`.

Usage :
    from techpulse_scraper.config import settings
    print(settings.mysql_host)
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Settings typées chargées depuis l'environnement + `.env.local`."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── MySQL ──────────────────────────────────────
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "techpulse"
    mysql_password: str = "techpass"
    mysql_database: str = "techpulse"
    mysql_root_password: str = "rootpass"

    # ─── France Travail API ─────────────────────────
    france_travail_client_id: str = ""
    france_travail_client_secret: str = ""
    france_travail_token_url: str = (
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    )
    france_travail_api_base: str = "https://api.francetravail.io/partenaire/offresdemploi/v2"
    france_travail_scope: str = "api_offresdemploiv2 o2dsoffre"

    # ─── Adresse API (géocodage gratuit) ────────────
    adresse_api_url: str = "https://api-adresse.data.gouv.fr"

    # ─── Application ────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    log_format: str = "text"

    # ─── Scraping ───────────────────────────────────
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36 TechPulseBot/0.1"
    )
    rate_limit_per_domain: float = 2.0
    http_timeout: float = 15.0

    @property
    def mysql_dsn(self) -> str:
        """DSN SQLAlchemy MySQL (utilisateur applicatif, pas root)."""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def has_france_travail_credentials(self) -> bool:
        return bool(self.france_travail_client_id and self.france_travail_client_secret)


settings = Settings()
