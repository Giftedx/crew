"""System validation and health check utilities.

This module provides utilities for:
- Validating system prerequisites and dependencies
- Checking availability of critical services (yt-dlp, LLM APIs, Discord)
- Providing degraded mode detection
"""

import os
from typing import Any


def validate_system_prerequisites() -> dict[str, Any]:
    """Validate system dependencies and return health status.

    Checks critical dependencies (yt-dlp, LLM API) and optional services
    (Discord, Qdrant, Google Drive, Prometheus). Returns comprehensive
    health status with errors, warnings, and capability lists.

    Returns:
        Health status dictionary with:
        - healthy: bool - True if all critical dependencies available
        - warnings: list[str] - Non-critical issues
        - errors: list[str] - Critical dependency failures
        - available_capabilities: list[str] - Working features
        - degraded_capabilities: list[str] - Unavailable features

    Example:
        >>> health = validate_system_prerequisites()
        >>> if not health["healthy"]:
        ...     print(f"Errors: {health['errors']}")
    """
    health = {
        "healthy": True,
        "warnings": [],
        "errors": [],
        "available_capabilities": [],
        "degraded_capabilities": [],
    }

    # Check critical dependencies (only yt-dlp and LLM API are truly critical)
    critical_deps = {
        "yt-dlp": check_ytdlp_available(),
        "llm_api": check_llm_api_available(),
    }

    for dep, available in critical_deps.items():
        if not available:
            health["errors"].append(f"Critical dependency missing: {dep}")
            health["healthy"] = False

    # Discord is optional - check separately
    discord_available = check_discord_available()
    if not discord_available:
        health["degraded_capabilities"].append("discord_posting")
        health["warnings"].append("Discord integration disabled - posts will be skipped")
    else:
        health["available_capabilities"].append("discord_posting")

    # Check optional services
    optional_services = {
        "qdrant": os.getenv("QDRANT_URL") is not None,
        "vector_search": os.getenv("QDRANT_URL") is not None,
        "drive_upload": os.getenv("GOOGLE_DRIVE_CREDENTIALS") is not None,
        "advanced_analytics": os.getenv("PROMETHEUS_ENDPOINT_PATH") is not None,
    }

    for service, available in optional_services.items():
        if available:
            health["available_capabilities"].append(service)
        else:
            health["degraded_capabilities"].append(service)
            health["warnings"].append(f"Optional service unavailable: {service}")

    # Determine workflow capabilities based on available dependencies
    if critical_deps["yt-dlp"] and critical_deps["llm_api"]:
        health["available_capabilities"].extend(["content_acquisition", "transcription_processing", "content_analysis"])

    return health


def check_ytdlp_available() -> bool:
    """Check if yt-dlp is available without importing it directly (guard-safe).

    Uses PATH probing to detect yt-dlp availability without triggering
    guard script violations. Falls back to checking configured directory hint.

    Returns:
        True if yt-dlp is available, False otherwise

    Example:
        >>> if check_ytdlp_available():
        ...     print("✅ yt-dlp available")
    """
    try:
        # Use PATH probing to detect presence; avoid direct downloader-imports here
        import shutil

        if shutil.which("yt-dlp"):
            return True
        # Check configured directory hint
        try:
            from ..settings import YTDLP_DIR  # noqa: PLC0415

            return bool(YTDLP_DIR)
        except Exception:
            return False
    except Exception:
        return False


def check_llm_api_available() -> bool:
    """Check if LLM API keys are configured.

    Validates that either OpenAI or OpenRouter API keys are present and
    are not dummy/placeholder values.

    Returns:
        True if valid API key found, False otherwise

    Example:
        >>> if check_llm_api_available():
        ...     print("✅ LLM API available")
    """
    openai_key = os.getenv("OPENAI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    # Dummy keys don't count as available
    dummy_patterns = ["dummy_", "your-", "sk-your-"]

    valid_openai = openai_key and not any(pattern in openai_key for pattern in dummy_patterns)
    valid_openrouter = openrouter_key and not any(pattern in openrouter_key for pattern in dummy_patterns)

    return valid_openai or valid_openrouter


def check_discord_available() -> bool:
    """Check if Discord integration is properly configured.

    Validates that either Discord bot token or webhook URL is present and
    is not a dummy/placeholder value.

    Returns:
        True if Discord configured, False otherwise

    Example:
        >>> if check_discord_available():
        ...     print("✅ Discord available")
    """
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    webhook = os.getenv("DISCORD_WEBHOOK", "")

    # Dummy values don't count
    dummy_patterns = ["dummy_", "your-", "https://discord.com/api/webhooks/YOUR_"]

    valid_token = token and not any(pattern in token for pattern in dummy_patterns)
    valid_webhook = webhook and not any(pattern in webhook for pattern in dummy_patterns)

    return valid_token or valid_webhook
