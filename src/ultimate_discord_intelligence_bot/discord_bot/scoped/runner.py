from __future__ import annotations

import asyncio
import os
import sys
from typing import NoReturn

from .bot import ScopedCommandBot
from .env import DEFAULT_FEATURE_FLAGS


def _check_environment() -> bool:
    required_vars = ["DISCORD_BOT_TOKEN"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    return True


async def main() -> None:
    print("🚀 Starting Scoped Discord Intelligence Bot...")
    if not _check_environment():
        sys.exit(1)
    print("✅ Environment validated")
    for flag, value in DEFAULT_FEATURE_FLAGS.items():
        if not os.getenv(flag):
            os.environ[flag] = value
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    bot = ScopedCommandBot()
    await bot.start(token)


def run() -> NoReturn:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scoped bot stopped")
        raise SystemExit(0)


__all__ = ["main", "run"]
