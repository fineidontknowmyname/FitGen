"""
workers/celery_app.py
----------------------
Celery application instance for Koda background workers.

Broker / backend
─────────────────
Both default to Redis on localhost.  Override via environment variables:

    CELERY_BROKER_URL    redis://localhost:6379/0   (default)
    CELERY_RESULT_BACKEND redis://localhost:6379/1  (default, separate DB)

The backend uses a different Redis database index (1) so result keys don't
collide with broker queues (0).

Worker startup
───────────────
    # Requires `pip install -e .` once (see pyproject.toml) — after that,
    # bare imports resolve from any directory, no PYTHONPATH needed:
    celery -A workers.celery_app worker --loglevel=info --pool=solo

    # With flower dashboard:
    celery -A workers.celery_app flower

Task routing
─────────────
All tasks currently land on the default queue.  Add routing_key /
queue config here when you need priority or dedicated queues.

Serialisation
─────────────
JSON throughout — avoids pickle security issues and keeps task payloads
human-readable in the broker.
"""

from __future__ import annotations

import logging
import os

from celery import Celery

log = logging.getLogger(__name__)


def _broker_url() -> str:
    """Read broker URL from settings or env, falling back to local Redis."""
    try:
        from config.settings import settings
        return getattr(settings, "CELERY_BROKER_URL", None) or os.getenv(
            "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )
    except Exception:
        return os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")


def _backend_url() -> str:
    """Read result backend URL, defaulting to Redis DB 1 (separate from broker)."""
    try:
        from config.settings import settings
        return getattr(settings, "CELERY_RESULT_BACKEND", None) or os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
        )
    except Exception:
        return os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")


celery_app = Celery(
    "koda_workers",
    broker=_broker_url(),
    backend=_backend_url(),
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    result_expires=60 * 60 * 24,

    timezone="UTC",
    enable_utc=True,
)

log.info(
    "Celery app created  broker=%s  backend=%s",
    _broker_url().split("@")[-1],
    _backend_url().split("@")[-1],
)
