#!/usr/bin/env python3
"""
Thin launcher delegating to the modular runner with backward-compatible exports.

All primary functionality lives under the package
`ultimate_discord_intelligence_bot.discord_bot`. This file re-exports the
helpers used by tests (`_infer_platform`, `_evaluate_claim`, `_detect_fallacies`,
`_fallacy_database`, `assess_response_quality`) and the main bot entrypoints
(`create_full_bot`, `main`) plus `ToolContainer` and `LIGHTWEIGHT_IMPORT`.

By keeping this module import-light, we preserve CI safety even without
optional dependencies like discord.py (tests can set LIGHTWEIGHT_IMPORT=1).
"""

from __future__ import annotations


# LIGHTWEIGHT_IMPORT flag passthrough for tests (import-safe)
try:
    from ultimate_discord_intelligence_bot.discord_bot.discord_env import (
        LIGHTWEIGHT_IMPORT,
    )
except Exception:  # pragma: no cover - optional dep path
    LIGHTWEIGHT_IMPORT = False  # type: ignore[assignment]

# Back-compat: expose ToolContainer for downstream imports
try:
    from ultimate_discord_intelligence_bot.discord_bot.tools_bootstrap import (
        ToolContainer,
    )
except Exception:  # pragma: no cover - degraded mode

    class ToolContainer:  # type: ignore[no-redef]
        def get_all_tools(self):  # pragma: no cover - trivial shim
            return {}


# Delegation to modular runner (safe import; defer exceptions until called)
try:
    from ultimate_discord_intelligence_bot.discord_bot.runner import (
        create_full_bot,
        main,
    )
except Exception as e:  # pragma: no cover - keep import-safe in lightweight envs
    _import_err_msg = str(e)
    import traceback

    _import_traceback = traceback.format_exc()

    def create_full_bot():  # type: ignore[no-redef]
        print(f"❌ Runner import failed with: {_import_err_msg}")
        print(f"📋 Full traceback:\n{_import_traceback}")
        raise RuntimeError(f"runner not available: {_import_err_msg}")

    async def main():  # type: ignore[no-redef]
        print(f"❌ Runner import failed with: {_import_err_msg}")
        print(f"📋 Full traceback:\n{_import_traceback}")
        raise RuntimeError(f"runner not available: {_import_err_msg}")


# Lightweight helpers re-exported from helpers package (import-safe)
from ultimate_discord_intelligence_bot.discord_bot.helpers import (
    _detect_fallacies,
    _evaluate_claim,
    _fallacy_database,
    _infer_platform,
    assess_response_quality,
)


if __name__ == "__main__":  # pragma: no cover - manual execution path
    import asyncio

    asyncio.run(main())


__all__ = [
    "LIGHTWEIGHT_IMPORT",
    "ToolContainer",
    "_detect_fallacies",
    "_evaluate_claim",
    "_fallacy_database",
    "_infer_platform",
    "assess_response_quality",
    "create_full_bot",
    "main",
]
