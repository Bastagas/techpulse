"""Modèles SQLAlchemy reflétant le schéma MySQL de `db/migrations/001_init.sql`."""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


def _enum_values(cls: type[enum.Enum]) -> list[str]:
    """Mappe l'Enum sur ses valeurs (lowercase) et non ses noms (UPPERCASE),
    compatible avec les tables MySQL déjà créées en minuscules."""
    return [e.value for e in cls]


# ─── Enums ──────────────────────────────────────────
class Source(enum.StrEnum):
    FRANCE_TRAVAIL = "france_travail"
    HELLOWORK = "hellowork"
    APEC = "apec"
    WTTJ = "wttj"


class TechCategory(enum.StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    LIBRARY = "library"
    METHODOLOGY = "methodology"


class ScrapeStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ─── Company ────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lat: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 6), nullable=True)
    lng: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 6), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    offers: Mapped[list[Offer]] = relationship(back_populates="company")


# ─── Technology (référentiel canonique) ─────────────
class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[TechCategory] = mapped_column(Enum(TechCategory, values_callable=_enum_values))
    aliases: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    offer_links: Mapped[list[OfferTechnology]] = relationship(back_populates="technology")


# ─── Offer ──────────────────────────────────────────
class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"))
    source: Mapped[Source] = mapped_column(Enum(Source, values_callable=_enum_values))
    source_offer_id: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remote_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    lat: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 6), nullable=True)
    lng: Mapped[Decimal | None] = mapped_column(DECIMAL(9, 6), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    fingerprint: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[Company] = relationship(back_populates="offers")
    tech_links: Mapped[list[OfferTechnology]] = relationship(
        back_populates="offer", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("source", "source_offer_id", name="uq_offers_source"),)


# ─── OfferTechnology (jointure N:N) ─────────────────
class OfferTechnology(Base):
    __tablename__ = "offer_technologies"

    offer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("offers.id"), primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("technologies.id"), primary_key=True
    )
    confidence_score: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), default=Decimal("1.00"))
    extracted_by: Mapped[str] = mapped_column(String(20), default="regex")

    offer: Mapped[Offer] = relationship(back_populates="tech_links")
    technology: Mapped[Technology] = relationship(back_populates="offer_links")


# ─── ScrapeRun (traçabilité) ────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255))
    token: Mapped[str] = mapped_column(String(32), unique=True)
    filter_keyword: Mapped[str | None] = mapped_column(String(200), nullable=True)
    filter_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    filter_tech: Mapped[str | None] = mapped_column(String(100), nullable=True)
    filter_contract: Mapped[str | None] = mapped_column(String(50), nullable=True)
    filter_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notification_count: Mapped[int] = mapped_column(Integer, default=0)
    last_offers_count: Mapped[int] = mapped_column(Integer, default=0)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    spider: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ScrapeStatus] = mapped_column(
        Enum(ScrapeStatus, values_callable=_enum_values), default=ScrapeStatus.RUNNING
    )
    pages_fetched: Mapped[int] = mapped_column(Integer, default=0)
    offers_found: Mapped[int] = mapped_column(Integer, default=0)
    offers_new: Mapped[int] = mapped_column(Integer, default=0)
    offers_updated: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
