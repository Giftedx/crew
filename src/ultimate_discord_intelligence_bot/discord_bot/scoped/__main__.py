"""Main entry point for scoped Discord bot."""

from __future__ import annotations

# CRITICAL: Add src/ to path BEFORE any imports to avoid platform module conflicts
# Python's built-in 'platform' module conflicts with our 'src/platform/' package
import sys
from pathlib import Path


src_dir = Path(__file__).resolve().parents[4]  # Go up to /home/crew/src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Note: Imports after sys.path manipulation are intentional (noqa: E402)
import logging  # noqa: E402
import os  # noqa: E402

from .bot import ScopedCommandBot  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the scoped Discord bot."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN environment variable not set")
        sys.exit(1)

    logger.info("🚀 Starting scoped Discord bot...")
    bot_instance = ScopedCommandBot()

    try:
        # Use run() instead of start() for simpler execution
        bot_instance.bot.run(token, log_handler=None)  # We handle logging ourselves
    except KeyboardInterrupt:
        logger.info("⏸️  Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
