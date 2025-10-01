#!/usr/bin/env python3
"""Thin wrapper that delegates to the modular scoped bot runner.

This preserves the existing CLI entry point while moving implementation to
`src/ultimate_discord_intelligence_bot/discord_bot/scoped/`.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure src is importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ultimate_discord_intelligence_bot.discord_bot.scoped.runner import main
except Exception as e:  # pragma: no cover - keep import safe in CI
    _err = e

    async def main() -> None:  # type: ignore[no-redef]
        raise RuntimeError(f"scoped runner unavailable: {_err}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scoped bot stopped")
