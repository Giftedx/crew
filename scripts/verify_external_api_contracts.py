#!/usr/bin/env python3
"""Best-effort verification of external API docs and expected patterns.

This script fetches reference pages (if network is available) and checks for
presence of expected terms (endpoints, headers). It is non-fatal and intended
for manual use. CI should not rely on it unless network is permitted.
"""

from __future__ import annotations

import sys as _sys
from collections.abc import Callable
from pathlib import Path

# Ensure src/ is on path so we can use core HTTP wrappers everywhere
_sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

# isort: off - local path mutation requires nearby import for stability
try:
    # Prefer centralized HTTP wrappers per repository policy
    from core.http_utils import REQUEST_TIMEOUT_SECONDS, cached_get
except Exception:  # pragma: no cover - fallback in environments without src path
    cached_get = None  # type: ignore
    REQUEST_TIMEOUT_SECONDS = 15  # sensible default
# isort: on

# Lint-friendly named constant for readability
HTTP_ERROR_THRESHOLD = 400


def _fetch(url: str, timeout: int = 10) -> str:
    """Fetch a URL using project HTTP helpers with caching when available.

    Returns empty string on any failure; intended for best-effort diagnostics only.
    """
    try:
        if cached_get is None:
            return ""  # wrappers unavailable in this environment
        resp = cached_get(url, timeout_seconds=timeout or REQUEST_TIMEOUT_SECONDS)
        if getattr(resp, "status_code", 500) >= HTTP_ERROR_THRESHOLD:
            return ""
        return getattr(resp, "text", "") or ""
    except Exception:
        return ""


def check_openrouter() -> bool:
    html = _fetch("https://openrouter.ai/docs")
    return "OpenRouter" in html or "chat/completions" in html


def check_exa() -> bool:
    html = _fetch("https://docs.exa.ai/reference/search")
    return "Search - Exa" in html or "search" in html.lower()


def check_perplexity() -> bool:
    html = _fetch("https://docs.perplexity.ai/reference/post_chat_completions")
    return "completions" in html.lower()


def check_wolfram() -> bool:
    html = _fetch("https://products.wolframalpha.com/simple-api/documentation/")
    return "v1/result" in html or "Simple API" in html


def check_discord_webhook() -> bool:
    # Developer portal is JS-heavy behind Cloudflare; allow minimal pass if any HTML returns
    html = _fetch("https://discord.com/developers/docs/resources/webhook")
    return bool(html)


def main() -> int:
    checks: list[tuple[str, Callable[[], bool]]] = [
        ("OpenRouter docs", check_openrouter),
        ("Exa docs", check_exa),
        ("Perplexity docs", check_perplexity),
        ("WolframAlpha Simple API docs", check_wolfram),
        ("Discord webhook docs", check_discord_webhook),
    ]
    failures = 0
    for name, fn in checks:
        ok = fn()
        print(f"{name:32} : {'OK' if ok else 'UNAVAILABLE'}")
        if not ok:
            failures += 1
    if failures:
        print("\nSome docs endpoints were unavailable. This tool is best-effort; verify manually if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
