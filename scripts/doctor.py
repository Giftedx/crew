#!/usr/bin/env python3
"""Environment doctor: checks Python, venv, critical packages, and tools.

Exits non-zero on hard failures; prints actionable tips.
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str = ""


def check_python() -> CheckResult:
    ok = (3, 10) <= sys.version_info < (3, 14)
    return CheckResult(
        "Python version",
        ok,
        f"found {sys.version.split()[0]} (require >=3.10,<3.14)",
    )


def check_venv() -> CheckResult:
    ok = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    return CheckResult(
        "Virtualenv active",
        ok,
        "run `python scripts/bootstrap_env.py` and activate .venv",
    )


def check_import(pkg: str) -> CheckResult:
    try:
        mod = importlib.import_module(pkg)
        ver = getattr(mod, "__version__", "(unknown)")
        return CheckResult(f"import {pkg}", True, f"version {ver}")
    except Exception as exc:
        return CheckResult(f"import {pkg}", False, str(exc))


def check_cmd(cmd: str) -> CheckResult:
    path = shutil.which(cmd)
    return CheckResult(f"which {cmd}", path is not None, path or "not found in PATH")


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    results.append(check_python())
    results.append(check_venv())
    for pkg in (
        "pydantic",
        "pydantic_settings",
        "fastapi",
        "qdrant_client",
        "discord",
        "yt_dlp",
        "pytest",
        "ruff",
        "mypy",
        "pre_commit",
    ):
        results.append(check_import(pkg))
    for cmd in ("ffmpeg", "yt-dlp"):
        results.append(check_cmd(cmd))
    # Optional: validators for retry flag migration
    if os.getenv("ENABLE_HTTP_RETRY"):
        results.append(CheckResult("retry flags", False, "set ENABLE_HTTP_RETRY or migrate legacy flag"))
    else:
        results.append(CheckResult("retry flags", True, "ok"))
    # HTTP timeout sanity
    ht = os.getenv("HTTP_TIMEOUT")
    if ht:
        try:
            ok = int(ht) > 0
        except ValueError:
            ok = False
        results.append(CheckResult("http timeout", ok, ht if ok else "invalid integer"))
    # Validate Discord webhook URL format if present
    hook = os.getenv("DISCORD_WEBHOOK") or os.getenv("DISCORD_PRIVATE_WEBHOOK")
    if hook:
        ok = bool(re.match(r"^https://discord\.com/api/webhooks/\d+/[\w-]+", hook))
        results.append(CheckResult("discord webhook", ok, "format looks valid" if ok else "invalid format"))
    # Validate OpenRouter recommended headers usage if key present
    if os.getenv("OPENROUTER_API_KEY"):
        ref = os.getenv("OPENROUTER_REFERER")
        ttl = os.getenv("OPENROUTER_TITLE")
        results.append(
            CheckResult(
                "openrouter referer",
                bool(ref),
                ref if ref else "set OPENROUTER_REFERER for best practice",
            )
        )
        results.append(
            CheckResult(
                "openrouter title",
                bool(ttl),
                ttl if ttl else "set OPENROUTER_TITLE for best practice",
            )
        )
    # Tenants baseline files
    tenants_dir = Path("tenants/default")
    for f in ("tenant.yaml", "routing.yaml", "budgets.yaml"):
        exists = (tenants_dir / f).exists()
        results.append(
            CheckResult(
                f"tenants/default/{f}",
                exists,
                "present" if exists else "missing",
            )
        )
    return results


def summarize(results: Iterable[CheckResult]) -> int:
    failures = 0
    print("Environment Doctor Report:\n---------------------------")
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"- {r.name:24} [{status}] {r.details}")
        if not r.ok:
            failures += 1
    if failures:
        print(f"\n{failures} issue(s) detected. See messages above for remediation.")
    else:
        print("\nAll checks passed.")
    return failures


def main() -> int:
    return summarize(run_checks())


if __name__ == "__main__":
    raise SystemExit(main())
