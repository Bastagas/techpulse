"""Configuration du logger via loguru.

Usage :
    from techpulse_scraper.logger import logger
    logger.info("Démarrage du spider {}", spider_name)
"""

from __future__ import annotations

import sys

from loguru import logger

from techpulse_scraper.config import settings

logger.remove()

if settings.log_format == "json":
    logger.add(
        sys.stderr,
        level=settings.log_level,
        serialize=True,
    )
else:
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "<level>{level: <7}</level> "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

__all__ = ["logger"]
