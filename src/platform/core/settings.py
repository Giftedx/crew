"""Compatibility shim for platform.core.settings

This module re-exports the configuration API from ``platform.config.settings``
to preserve the historical import path expected by tests and modules.

Public surface:
- Settings (type alias to SecureConfig)
- SecureConfig
- get_settings()
- reload_settings()
- attribute passthrough via __getattr__ to the singleton settings object
"""

from __future__ import annotations

import os
from platform.config.settings import (
    SecureConfig,
)
from platform.config.settings import (
    get_settings as _get_secure_settings,
)
from platform.config.settings import (
    reload_settings as _reload_secure_settings,
)
from typing import Any


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


class CompatSettings:
    """Legacy-compatible settings wrapper.

    Exposes historical attributes expected by tests and legacy modules while
    delegating unknown lookups to the underlying SecureConfig instance.
    """

    def __init__(self) -> None:
        self._secure: SecureConfig = _get_secure_settings()

    # ---- Legacy attributes with sensible defaults/env overrides ----
    @property
    def cache_compression_enabled(self) -> bool:  # default True
        return _env_bool("CACHE_COMPRESSION_ENABLED", True)

    @property
    def cache_promotion_enabled(self) -> bool:  # default True
        return _env_bool("CACHE_PROMOTION_ENABLED", True)

    @property
    def enable_reranker(self) -> bool:  # default False
        return _env_bool("ENABLE_RERANKER", False)

    @property
    def enable_faster_whisper(self) -> bool:  # default False
        return _env_bool("ENABLE_FASTER_WHISPER", False)

    @property
    def enable_local_llm(self) -> bool:  # default False
        return _env_bool("ENABLE_LOCAL_LLM", False)

    @property
    def enable_prompt_compression(self) -> bool:  # default True
        return _env_bool("ENABLE_PROMPT_COMPRESSION", True)

    @property
    def enable_token_aware_chunker(self) -> bool:  # default True
        return _env_bool("ENABLE_TOKEN_AWARE_CHUNKER", True)

    @property
    def enable_semantic_cache(self) -> bool:  # conservative default False
        return _env_bool("ENABLE_SEMANTIC_CACHE", False)

    @property
    def rerank_provider(self) -> str | None:
        return os.getenv("RERANK_PROVIDER")

    @property
    def local_llm_url(self) -> str | None:
        val = os.getenv("LOCAL_LLM_URL")
        if val:
            return val
        # Fallback to any similarly named field in secure config
        return getattr(self._secure, "local_llm_url", None) or None

    @property
    def openrouter_referer(self) -> str | None:
        return os.getenv("OPENROUTER_REFERER")

    @property
    def openrouter_title(self) -> str | None:
        return os.getenv("OPENROUTER_TITLE")

    @property
    def reward_cost_weight(self) -> float:
        return float(os.getenv("REWARD_COST_WEIGHT", "0.5"))

    @property
    def reward_latency_weight(self) -> float:
        return float(os.getenv("REWARD_LATENCY_WEIGHT", "0.5"))

    @property
    def reward_latency_ms_window(self) -> int:
        return int(os.getenv("REWARD_LATENCY_MS_WINDOW", "2000"))

    @property
    def rl_policy_model_selection(self) -> str:
        return os.getenv("RL_POLICY_MODEL_SELECTION", "epsilon_greedy")

    @property
    def token_chunk_target_tokens(self) -> int:
        return int(os.getenv("TOKEN_CHUNK_TARGET_TOKENS", "2048"))

    @property
    def prompt_compression_max_repeated_blank_lines(self) -> int:
        return int(os.getenv("PROMPT_COMPRESSION_MAX_REPEATED_BLANK_LINES", "2"))

    @property
    def semantic_cache_threshold(self) -> float:
        return float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))

    @property
    def semantic_cache_ttl_seconds(self) -> int:
        return int(os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "86400"))

    @property
    def download_quality_default(self) -> str:
        return os.getenv("DOWNLOAD_QUALITY_DEFAULT", "1080p")

    @property
    def archive_api_token(self) -> str | None:
        return os.getenv("ARCHIVE_API_TOKEN")

    @property
    def discord_bot_token(self) -> str | None:
        val = getattr(self._secure, "discord_bot_token", None) or os.getenv("DISCORD_BOT_TOKEN")
        if not val:
            return None
        # Treat common placeholders as unset
        if str(val).strip().lower() in {"your_discord_bot_token_here", "changeme", "placeholder"}:
            return None
        return val

    # ---- Transparent delegation for all other attributes ----
    def __getattr__(self, name: str) -> Any:  # pragma: no cover - passthrough
        return getattr(self._secure, name)


_compat_singleton: CompatSettings | None = None


def get_settings() -> CompatSettings:
    global _compat_singleton
    if _compat_singleton is None:
        _compat_singleton = CompatSettings()
    return _compat_singleton


def reload_settings() -> CompatSettings:
    global _compat_singleton
    _reload_secure_settings()
    _compat_singleton = CompatSettings()
    return _compat_singleton


def __getattr__(name: str) -> Any:
    # Delegate module-level attribute access to the live wrapper instance
    return getattr(get_settings(), name)


# Exported names for type-checkers and from-imports
Settings = CompatSettings

__all__ = ["SecureConfig", "Settings", "get_settings", "reload_settings"]
