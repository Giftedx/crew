"""Helper package with dynamic shims for legacy modules.

We pre-register a lightweight in-memory module for ``scripts.start_full_bot``
so imports remain fast and safe in environments without optional deps.
"""

from __future__ import annotations

import contextlib
import sys
import types


def _register_start_full_bot_shim() -> None:
    # Build a minimal, import-safe module that mirrors the expected API
    mod_name = __name__ + ".start_full_bot"
    if mod_name in sys.modules:
        return

    m = types.ModuleType(mod_name)

    # LIGHTWEIGHT_IMPORT flag passthrough for tests (import-safe)
    try:  # pragma: no cover - optional dep path
        from ultimate_discord_intelligence_bot.discord_bot.discord_env import (
            LIGHTWEIGHT_IMPORT as _LW,
        )
    except Exception:  # pragma: no cover
        _LW = False
    m.LIGHTWEIGHT_IMPORT = _LW

    # ToolContainer shim
    try:  # pragma: no cover - optional dep path
        from ultimate_discord_intelligence_bot.discord_bot.tools_bootstrap import (
            ToolContainer as _TC,
        )
    except Exception:  # pragma: no cover

        class _TC:  # type: ignore
            def get_all_tools(self):
                return {}

    m.ToolContainer = _TC

    # Runner delegation (defer heavy imports until called)
    try:  # pragma: no cover
        from ultimate_discord_intelligence_bot.discord_bot.runner import (
            create_full_bot as _cfb,
        )
        from ultimate_discord_intelligence_bot.discord_bot.runner import main as _main

        def create_full_bot():  # type: ignore
            return _cfb()

        async def main():  # type: ignore
            return await _main()

    except Exception as e:  # pragma: no cover
        _err_msg = str(e)

        def create_full_bot():  # type: ignore
            raise RuntimeError(f"runner not available: {_err_msg}")

        async def main():  # type: ignore
            raise RuntimeError(f"runner not available: {_err_msg}")

    m.create_full_bot = create_full_bot
    m.main = main

    # Lightweight helpers
    from ultimate_discord_intelligence_bot.discord_bot.helpers import (
        _detect_fallacies,
        _evaluate_claim,
        _fallacy_database,
        _infer_platform,
        assess_response_quality,
    )

    m._detect_fallacies = _detect_fallacies
    m._evaluate_claim = _evaluate_claim
    m._fallacy_database = _fallacy_database
    m._infer_platform = _infer_platform
    m.assess_response_quality = assess_response_quality

    m.__all__ = [
        "ToolContainer",
        "assess_response_quality",
        "main",
        "create_full_bot",
        "LIGHTWEIGHT_IMPORT",
        "_infer_platform",
        "_evaluate_claim",
        "_detect_fallacies",
        "_fallacy_database",
    ]

    sys.modules[mod_name] = m


# Register shim on package import
with contextlib.suppress(Exception):
    _register_start_full_bot_shim()
