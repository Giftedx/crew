"""Arq task queue configuration."""

from __future__ import annotations

import os
from typing import Any

from arq import cron


# Arq worker settings
ARQ_SETTINGS = {
    "redis_settings": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD"),
        "database": int(os.getenv("REDIS_DB", "0")),
    },
    "max_jobs": int(os.getenv("ARQ_MAX_JOBS", "10")),
    "timeout": int(os.getenv("ARQ_TIMEOUT", "300")),  # 5 minutes default
    "retry_policy": {
        "max_retries": int(os.getenv("ARQ_MAX_RETRIES", "3")),
        "retry_delay": int(os.getenv("ARQ_RETRY_DELAY", "60")),  # 1 minute
    },
    "cron_jobs": [
        # Add scheduled jobs here
        # cron(trigger="*/5 * * * *", function="tasks.jobs:monitor_system"),
    ],
}


def get_arq_settings() -> dict[str, Any]:
    """Get Arq configuration settings."""
    return ARQ_SETTINGS
