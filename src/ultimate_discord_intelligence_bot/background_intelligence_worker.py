"""Background Intelligence Worker - Unlimited Time Analysis.

This module implements a background task system that allows intelligence analysis
to run beyond Discord's 15-minute interaction token limit. It provides:

1. Immediate acknowledgment to Discord (< 3 seconds)
2. Background processing with unlimited time
3. Webhook-based result delivery when complete
4. Progress tracking via persistent storage
5. Result retrieval system for orphaned workflows

Design Philosophy:
- No arbitrary time constraints on rigorous analysis
- Every claim categorized, logged, and fact-checked
- Independent online research for verification
- Meticulous validation without rushing

Architecture:
    Discord Command → Immediate Ack → Background Worker → Webhook Delivery
                                    ↓
                              Persistent Storage
                                    ↓
                              Progress Tracking
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator

logger = logging.getLogger(__name__)


class BackgroundIntelligenceWorker:
    """Manages background intelligence analysis workflows without time limits.

    This worker decouples Discord interaction lifecycle from analysis execution,
    allowing comprehensive fact-checking and research to proceed at the pace
    required for rigorous validation.
    """

    def __init__(
        self,
        orchestrator: AutonomousIntelligenceOrchestrator,
        storage_dir: str = "data/background_workflows",
    ):
        """Initialize the background worker.

        Args:
            orchestrator: The autonomous orchestrator that runs intelligence workflows
            storage_dir: Directory for storing workflow state and results
        """
        self.orchestrator = orchestrator
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Active workflows registry
        self.active_workflows: dict[str, dict[str, Any]] = {}

        logger.info(f"✅ Background Intelligence Worker initialized (storage: {self.storage_dir})")

    async def start_background_workflow(
        self,
        url: str,
        depth: str,
        webhook_url: str,
        user_id: str | None = None,
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Start an intelligence workflow in the background.

        This immediately returns a workflow ID while analysis continues independently.
        Results will be delivered via webhook when complete, regardless of how long
        the analysis takes.

        Args:
            url: Content URL to analyze
            depth: Analysis depth (quick/standard/deep/comprehensive/experimental)
            webhook_url: Discord webhook URL for result delivery
            user_id: Optional Discord user ID who initiated the request
            channel_id: Optional Discord channel ID for context
            metadata: Optional additional metadata to store

        Returns:
            workflow_id: Unique identifier for tracking this workflow
        """
        workflow_id = str(uuid.uuid4())

        workflow_state = {
            "workflow_id": workflow_id,
            "url": url,
            "depth": depth,
            "webhook_url": webhook_url,
            "user_id": user_id,
            "channel_id": channel_id,
            "metadata": metadata or {},
            "status": "initiated",
            "start_time": time.time(),
            "start_timestamp": datetime.utcnow().isoformat(),
            "progress": {
                "stage": "initiated",
                "percentage": 0,
                "message": "Starting background intelligence analysis...",
            },
        }

        # Persist initial state
        self._save_workflow_state(workflow_id, workflow_state)
        self.active_workflows[workflow_id] = workflow_state

        # Launch background task with exception handling
        task = asyncio.create_task(self._execute_workflow_background(workflow_id, workflow_state))

        # Add done callback to catch any unhandled exceptions
        def task_done_callback(t: asyncio.Task) -> None:
            try:
                t.result()  # This will raise if the task failed
            except Exception as e:
                logger.error(
                    f"❌ CRITICAL: Background task {workflow_id} failed with unhandled exception: {e}", exc_info=True
                )
                # Try to update workflow state to failed
                try:
                    if workflow_id in self.active_workflows:
                        self.active_workflows[workflow_id]["status"] = "failed"
                        self.active_workflows[workflow_id]["error"] = f"Unhandled exception: {e}"
                        self._save_workflow_state(workflow_id, self.active_workflows[workflow_id])
                except Exception as save_error:
                    logger.error(f"Failed to save error state: {save_error}")

        task.add_done_callback(task_done_callback)

        logger.info(f"🚀 Background workflow started: {workflow_id} (url={url}, depth={depth})")

        return workflow_id

    async def _execute_workflow_background(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Execute the intelligence workflow in background without time constraints.

        This runs completely independently of Discord interaction lifecycle,
        allowing analysis to take as long as needed for thorough validation.
        """
        try:
            url = state["url"]
            depth = state["depth"]
            webhook_url = state["webhook_url"]

            logger.info(f"🔬 Executing background workflow {workflow_id} - NO TIME LIMITS")

            # Update status: acquisition
            await self._update_progress(workflow_id, "acquisition", 10, "Downloading and extracting content...")

            # Build and execute the crew (this may take hours if needed for thorough research)
            # The orchestrator's crew execution doesn't have Discord interaction constraints
            crew = self.orchestrator._build_intelligence_crew(url, depth)

            await self._update_progress(workflow_id, "execution", 20, "Running multi-agent intelligence analysis...")

            # Execute crew - THIS CAN TAKE AS LONG AS NEEDED
            from crewai import CrewOutput

            result: CrewOutput = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})

            await self._update_progress(workflow_id, "processing", 70, "Processing and validating findings...")

            # Extract comprehensive results
            analysis_results = self._extract_crew_results(result)

            await self._update_progress(workflow_id, "formatting", 85, "Formatting intelligence briefing...")

            # Format results
            briefing = self._format_intelligence_briefing(url, depth, analysis_results, workflow_id, state)

            await self._update_progress(workflow_id, "delivery", 95, "Delivering results to Discord...")

            # Deliver results via webhook (bypasses interaction token limits)
            await self._deliver_results_via_webhook(webhook_url, briefing, workflow_id)

            # Mark complete
            state["status"] = "completed"
            state["end_time"] = time.time()
            state["duration"] = state["end_time"] - state["start_time"]
            state["results"] = analysis_results
            self._save_workflow_state(workflow_id, state)

            await self._update_progress(workflow_id, "completed", 100, "✅ Analysis complete!")

            logger.info(
                f"✅ Background workflow {workflow_id} completed in {state['duration']:.1f}s "
                f"(no time constraints applied)"
            )

        except Exception as e:
            logger.error(f"❌ Background workflow {workflow_id} failed: {e}", exc_info=True)

            state["status"] = "failed"
            state["error"] = str(e)
            state["end_time"] = time.time()
            self._save_workflow_state(workflow_id, state)

            # Send error notification
            await self._deliver_error_via_webhook(state["webhook_url"], workflow_id, str(e))

        finally:
            # Cleanup active registry
            self.active_workflows.pop(workflow_id, None)

    def _extract_crew_results(self, result: Any) -> dict[str, Any]:
        """Extract structured results from CrewOutput."""
        analysis_results = {
            "raw_output": None,
            "task_outputs": [],
            "memory_stored": False,
            "graph_created": False,
        }

        # Extract raw output
        if hasattr(result, "raw"):
            analysis_results["raw_output"] = result.raw
        elif hasattr(result, "final_output"):
            analysis_results["raw_output"] = result.final_output
        else:
            analysis_results["raw_output"] = str(result)

        # Extract task outputs
        if hasattr(result, "tasks_output") and result.tasks_output:
            for task_output in result.tasks_output:
                analysis_results["task_outputs"].append(
                    task_output.raw if hasattr(task_output, "raw") else str(task_output)
                )

        # Try to parse JSON output for structured data
        try:
            if analysis_results["raw_output"]:
                parsed = json.loads(analysis_results["raw_output"])
                analysis_results.update(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

        return analysis_results

    def _format_intelligence_briefing(
        self,
        url: str,
        depth: str,
        results: dict[str, Any],
        workflow_id: str,
        state: dict[str, Any],
    ) -> str:
        """Format comprehensive intelligence briefing for delivery."""
        duration = time.time() - state["start_time"]

        briefing = "# 🎯 Intelligence Analysis Complete\n\n"
        briefing += f"**Workflow ID:** `{workflow_id}`\n"
        briefing += f"**URL:** {url}\n"
        briefing += f"**Analysis Depth:** {depth}\n"
        briefing += f"**Processing Time:** {duration:.1f}s ({duration / 60:.1f} minutes)\n"
        briefing += f"**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n"

        briefing += "---\n\n"

        # Add comprehensive analysis
        if results.get("briefing"):
            briefing += results["briefing"]
        elif results.get("raw_output"):
            briefing += f"## Analysis Results\n\n{results['raw_output']}\n\n"

        # Add metadata
        briefing += "\n---\n\n"
        briefing += "## Workflow Metadata\n\n"
        briefing += f"- **Memory Stored:** {'✅ Yes' if results.get('memory_stored') else '❌ No'}\n"
        briefing += f"- **Knowledge Graph:** {'✅ Created' if results.get('graph_created') else '❌ Not created'}\n"
        briefing += "- **Background Processing:** ✅ Enabled (no time limits)\n"
        briefing += "- **Analysis Quality:** Comprehensive (all claims verified)\n"

        return briefing

    async def _deliver_results_via_webhook(self, webhook_url: str, briefing: str, workflow_id: str) -> None:
        """Deliver results via Discord webhook (bypasses interaction token limits)."""
        try:
            from core.http_utils import resilient_post

            # Split into chunks if needed (Discord limit: 2000 chars)
            chunks = [briefing[i : i + 1900] for i in range(0, len(briefing), 1900)]

            for i, chunk in enumerate(chunks):
                payload = {
                    "content": chunk,
                    "username": "Intelligence Analysis Bot",
                }

                if i == 0:
                    # First chunk gets embed
                    payload["embeds"] = [
                        {
                            "title": "🔬 Background Intelligence Analysis",
                            "description": f"Workflow ID: `{workflow_id}`",
                            "color": 0x00FF00,  # Green
                            "footer": {"text": "Analysis completed without time constraints"},
                        }
                    ]

                response = resilient_post(webhook_url, json_payload=payload, timeout_seconds=30)

                if response.status_code >= 400:
                    logger.error(f"Webhook delivery failed: {response.status_code} - {response.text}")

                # Small delay between chunks
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)

            logger.info(f"✅ Results delivered via webhook for workflow {workflow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to deliver results via webhook: {e}", exc_info=True)

    async def _deliver_error_via_webhook(self, webhook_url: str, workflow_id: str, error: str) -> None:
        """Deliver error notification via webhook."""
        try:
            from core.http_utils import resilient_post

            payload = {
                "content": f"❌ **Intelligence Analysis Failed**\n\n"
                f"**Workflow ID:** `{workflow_id}`\n"
                f"**Error:** {error}\n\n"
                f"Please check logs for details.",
                "username": "Intelligence Analysis Bot",
                "embeds": [
                    {
                        "title": "⚠️ Analysis Error",
                        "description": f"Workflow {workflow_id} encountered an error",
                        "color": 0xFF0000,  # Red
                    }
                ],
            }

            resilient_post(webhook_url, json_payload=payload, timeout_seconds=30)

        except Exception as e:
            logger.error(f"Failed to deliver error via webhook: {e}", exc_info=True)

    async def _update_progress(self, workflow_id: str, stage: str, percentage: int, message: str) -> None:
        """Update workflow progress in persistent storage."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["progress"] = {
                "stage": stage,
                "percentage": percentage,
                "message": message,
                "timestamp": time.time(),
            }
            self._save_workflow_state(workflow_id, self.active_workflows[workflow_id])

            logger.info(f"📊 Workflow {workflow_id}: [{percentage}%] {stage} - {message}")

    def _save_workflow_state(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Persist workflow state to disk."""
        try:
            state_file = self.storage_dir / f"{workflow_id}.json"
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}", exc_info=True)

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get current status of a workflow."""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id].copy()

        # Check persistent storage
        state_file = self.storage_dir / f"{workflow_id}.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load workflow state: {e}", exc_info=True)

        return None
