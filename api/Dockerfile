# syntax=docker/dockerfile:1.6
# ─────────────────────────────────────────────────────────────
# TechPulse API — image production gunicorn
# Multi-stage : builder install deps puis runtime minimal.
# ─────────────────────────────────────────────────────────────

# ─── Stage 1 : builder ──────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps en premier pour bénéficier du cache Docker
COPY scraper/pyproject.toml ./scraper/
COPY api/pyproject.toml ./api/
COPY scraper/src ./scraper/src
COPY api/src ./api/src

RUN pip install --prefix=/install ./scraper ./api

# ─── Stage 2 : runtime ──────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.11/site-packages" \
    PORT=5001

# Utilisateur non-root
RUN useradd -m -u 1000 techpulse

WORKDIR /app
COPY --from=builder /install /install
COPY --chown=techpulse:techpulse scraper ./scraper
COPY --chown=techpulse:techpulse api ./api

USER techpulse

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{__import__(\"os\").environ.get(\"PORT\", 5001)}/health').read()" || exit 1

# Gunicorn : PORT injecté par Railway, fallback 5001 local
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --access-logfile - --error-logfile - techpulse_api.wsgi:app"]
