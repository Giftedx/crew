#!/usr/bin/env python3
"""Diagnostic script for /autointel command failures.

Run this to test the workflow and capture detailed logs showing where failures occur.
"""

import asyncio
import logging
import sys
from pathlib import Path


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# CRITICAL: Load .env file so environment variables are available
try:
    from dotenv import load_dotenv

    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, trying without .env loading")
    print("   Install with: pip install python-dotenv")

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("autointel_diagnostic.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Run diagnostic test of the /autointel workflow."""
    logger.info("=" * 80)
    logger.info("AUTOINTEL DIAGNOSTIC TEST STARTED")
    logger.info("=" * 80)

    # Test URL from user's command
    test_url = "https://www.youtube.com/watch?v=xtFiJ8AVdW0"
    test_depth = "experimental"

    logger.info(f"Test URL: {test_url}")
    logger.info(f"Test Depth: {test_depth}")

    try:
        # Import orchestrator
        logger.info("\n[1/6] Importing AutonomousIntelligenceOrchestrator...")
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )

        # Create mock interaction
        logger.info("\n[2/6] Creating mock Discord interaction...")

        class MockInteraction:
            """Minimal interaction mock for testing."""

            user = type("User", (), {"id": "test_user", "name": "DiagnosticTest"})()
            guild = type("Guild", (), {"id": "test_guild", "name": "DiagnosticGuild"})()
            channel = type("Channel", (), {"id": "test_channel", "name": "diagnostic-channel"})()

            async def followup_send(self, content=None, embed=None):
                logger.info(f"[DISCORD FOLLOWUP] {content if content else 'embed'}")

            class _Response:
                async def defer(self, ephemeral=False):
                    logger.info("[DISCORD] Interaction deferred")

            response = _Response()

        interaction = MockInteraction()

        # Initialize orchestrator
        logger.info("\n[3/6] Initializing AutonomousIntelligenceOrchestrator...")
        orchestrator = AutonomousIntelligenceOrchestrator()

        # Validate prerequisites
        logger.info("\n[4/6] Validating system prerequisites...")
        health = orchestrator._validate_system_prerequisites()
        logger.info(f"System Health: {health}")

        if not health["healthy"]:
            logger.warning("⚠️  SYSTEM HEALTH CHECK FOUND ISSUES")
            logger.warning(f"Errors: {health['errors']}")
            logger.warning(f"Warnings: {health['warnings']}")
            logger.info(f"Available capabilities: {health['available_capabilities']}")
            logger.info(f"Degraded capabilities: {health['degraded_capabilities']}")

            # Check if we can still proceed (need at least yt-dlp and LLM API)
            has_ytdlp = "yt-dlp" not in [e.split(": ")[-1] for e in health["errors"]]
            has_llm = "llm_api" not in [e.split(": ")[-1] for e in health["errors"]]

            if not (has_ytdlp and has_llm):
                logger.error("❌ Cannot proceed - missing critical dependencies (yt-dlp or LLM API)")
                logger.error("")
                logger.error("To fix:")
                if not has_llm:
                    logger.error("  1. Set OPENAI_API_KEY or OPENROUTER_API_KEY in .env")
                if not has_ytdlp:
                    logger.error("  2. Install yt-dlp: pip install yt-dlp")
                logger.error("")
                return 1
            else:
                logger.info("✅ Minimum requirements met, proceeding with degraded capabilities...")

        # Execute workflow
        logger.info("\n[5/6] Executing autonomous intelligence workflow...")
        logger.info("This will take several minutes...")

        result = await orchestrator.execute_autonomous_intelligence_workflow(
            interaction=interaction, url=test_url, depth=test_depth
        )

        # Analyze results
        logger.info("\n[6/6] Analyzing results...")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result: {result}")

        # Check for failures
        if hasattr(result, "success") and not result.success:
            logger.error("WORKFLOW FAILED!")
            if hasattr(result, "error"):
                logger.error(f"Error: {result.error}")
            if hasattr(result, "data"):
                logger.error(f"Data: {result.data}")
            return 1

        logger.info("\n" + "=" * 80)
        logger.info("DIAGNOSTIC TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        return 0

    except Exception as e:
        logger.exception("DIAGNOSTIC TEST FAILED WITH EXCEPTION")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {e!s}")

        # Try to get detailed traceback
        import traceback

        logger.error("\n" + "=" * 80)
        logger.error("FULL TRACEBACK:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
