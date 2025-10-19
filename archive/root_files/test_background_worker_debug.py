#!/usr/bin/env python3
"""Debug script to find why background worker fails."""

import asyncio
import logging
import sys

# Set up logging to see ALL errors
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("/tmp/background_worker_debug.log")],
)

logger = logging.getLogger(__name__)


async def test_background_worker():
    """Test the background worker with full error visibility."""
    try:
        logger.info("🔍 Starting background worker debug test...")

        # Import the components
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator
        from ultimate_discord_intelligence_bot.background_intelligence_worker import BackgroundIntelligenceWorker

        logger.info("✅ Imports successful")

        # Create orchestrator
        orchestrator = AutonomousIntelligenceOrchestrator()
        logger.info("✅ Orchestrator created")

        # Create worker
        worker = BackgroundIntelligenceWorker(orchestrator=orchestrator, storage_dir="/tmp/test_workflows")
        logger.info("✅ Worker created")

        # Start a test workflow
        workflow_id = await worker.start_background_workflow(
            url="https://youtu.be/dQw4w9WgXcQ",  # Short test video
            depth="quick",
            webhook_url="https://httpbin.org/post",  # Test webhook
            user_id="test_user",
            channel_id="test_channel",
        )

        logger.info(f"✅ Workflow started: {workflow_id}")

        # Wait a bit to see if task crashes
        await asyncio.sleep(5)

        # Check status
        status = worker.get_workflow_status(workflow_id)
        logger.info(f"📊 Workflow status: {status}")

        # Wait for completion or failure
        for i in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            status = worker.get_workflow_status(workflow_id)
            if status and status.get("status") in ["completed", "failed"]:
                logger.info(f"🏁 Workflow finished: {status['status']}")
                if status.get("error"):
                    logger.error(f"❌ Error: {status['error']}")
                break
            logger.info(
                f"⏳ [{i + 1}/30] Still running... Progress: {status.get('progress', {}) if status else 'unknown'}"
            )

        logger.info("✅ Test complete")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_background_worker())
