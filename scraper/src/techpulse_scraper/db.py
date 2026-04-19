"""Engine SQLAlchemy + factory de sessions.

Usage :
    from techpulse_scraper.db import get_session

    with get_session() as session:
        offers = session.scalars(select(Offer)).all()
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from techpulse_scraper.config import settings

engine = create_engine(
    settings.mysql_dsn,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.app_env == "development" and settings.log_level == "DEBUG",
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager autour d'une session SQLAlchemy avec commit/rollback auto."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
