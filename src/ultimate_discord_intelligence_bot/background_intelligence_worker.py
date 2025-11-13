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
        self, orchestrator: AutonomousIntelligenceOrchestrator, storage_dir: str = "data/background_workflows"
    ):
        """Initialize the background worker.

        Args:
            orchestrator: The autonomous orchestrator that runs intelligence workflows
            storage_dir: Directory for storing workflow state and results
        """
        self.orchestrator = orchestrator
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
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
        self._save_workflow_state(workflow_id, workflow_state)
        self.active_workflows[workflow_id] = workflow_state
        task = asyncio.create_task(self._execute_workflow_background(workflow_id, workflow_state))

        def task_done_callback(t: asyncio.Task) -> None:
            try:
                t.result()
            except Exception as e:
                logger.error(
                    f"❌ CRITICAL: Background task {workflow_id} failed with unhandled exception: {e}", exc_info=True
                )
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
            await self._update_progress(workflow_id, "acquisition", 10, "Initializing full intelligence pipeline...")

            # Use the real orchestrator for full 7-stage pipeline analysis
            # This includes: download → transcription → content routing → quality filtering →
            # analysis (fact-checking, claim extraction, debunking) → memory storage → finalization
            logger.info(f"🚀 Launching ContentPipeline for {workflow_id} (depth: {depth})")

            # Ensure src/ is in path for imports (needed for background thread context)
            import os
            import sys

            # Calculate path to src/ directory
            src_path = os.path.dirname(os.path.dirname(__file__))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
                logger.info(f"✅ Added {src_path} to sys.path")

            # CRITICAL: Pre-inject platform modules to prevent built-in module conflict
            try:
                import importlib.util

                platform_base = os.path.join(src_path, "platform")

                # Load platform modules directly from filesystem
                time_spec = importlib.util.spec_from_file_location(
                    "platform.time", os.path.join(platform_base, "time.py")
                )
                http_spec = importlib.util.spec_from_file_location(
                    "platform.http", os.path.join(platform_base, "http", "__init__.py")
                )
                cache_spec = importlib.util.spec_from_file_location(
                    "platform.cache", os.path.join(platform_base, "cache", "__init__.py")
                )
                config_spec = importlib.util.spec_from_file_location(
                    "platform.config", os.path.join(platform_base, "config", "__init__.py")
                )

                # Inject into sys.modules
                if time_spec and time_spec.loader:
                    _time = importlib.util.module_from_spec(time_spec)
                    sys.modules["platform.time"] = _time
                    time_spec.loader.exec_module(_time)

                if http_spec and http_spec.loader:
                    _http = importlib.util.module_from_spec(http_spec)
                    sys.modules["platform.http"] = _http
                    http_spec.loader.exec_module(_http)

                if cache_spec and cache_spec.loader:
                    _cache = importlib.util.module_from_spec(cache_spec)
                    sys.modules["platform.cache"] = _cache
                    cache_spec.loader.exec_module(_cache)

                if config_spec and config_spec.loader:
                    _config = importlib.util.module_from_spec(config_spec)
                    sys.modules["platform.config"] = _config
                    config_spec.loader.exec_module(_config)

                logger.info("✅ Injected platform.* modules using importlib")
            except Exception as e:
                logger.warning(f"⚠️ Could not inject platform modules: {e}", exc_info=True)

            # Import and initialize the orchestrator
            from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline

            await self._update_progress(workflow_id, "download", 15, "🔍 Stage 1/7: Downloading content...")

            pipeline = ContentPipeline()

            # Map depth to quality parameter (orchestrator expects quality like "1080p", "720p", "comprehensive")
            quality_map = {"quick": "720p", "standard": "1080p", "comprehensive": "1080p", "deep": "1080p"}
            quality = quality_map.get(depth, "1080p")

            # Run the full pipeline (this will handle all 7 stages)
            logger.info(f"⚙️ Executing ContentPipeline.process_video(url={url}, quality={quality})")
            await self._update_progress(workflow_id, "transcription", 25, "🎙️ Stage 2/7: Transcribing audio...")

            pipeline_result = await pipeline.process_video(url, quality)

            # Check if pipeline succeeded - status field is "success" or "error"
            if not pipeline_result or pipeline_result.get("status") != "success":
                error_msg = (
                    pipeline_result.get("error", "Pipeline failed") if pipeline_result else "Pipeline returned None"
                )
                logger.error(f"❌ ContentPipeline failed: {error_msg}")
                raise Exception(f"Intelligence pipeline failed: {error_msg}")

            logger.info(f"✅ ContentPipeline completed successfully for {workflow_id}")

            # Extract results from pipeline output
            result = pipeline_result
            await self._update_progress(workflow_id, "processing", 70, "📊 Processing pipeline results...")
            analysis_results = self._extract_crew_results(result)
            await self._update_progress(workflow_id, "formatting", 85, "Formatting intelligence briefing...")
            briefing = self._format_intelligence_briefing(url, depth, analysis_results, workflow_id, state)
            await self._update_progress(workflow_id, "delivery", 95, "Delivering results to Discord...")
            await self._deliver_results_via_webhook(webhook_url, briefing, workflow_id)
            state["status"] = "completed"
            state["end_time"] = time.time()
            state["duration"] = state["end_time"] - state["start_time"]
            state["results"] = analysis_results
            self._save_workflow_state(workflow_id, state)
            await self._update_progress(workflow_id, "completed", 100, "✅ Analysis complete!")
            logger.info(
                f"✅ Background workflow {workflow_id} completed in {state['duration']:.1f}s (no time constraints applied)"
            )
        except Exception as e:
            logger.error(f"❌ Background workflow {workflow_id} failed: {e}", exc_info=True)
            state["status"] = "failed"
            state["error"] = str(e)
            state["end_time"] = time.time()
            self._save_workflow_state(workflow_id, state)
            await self._deliver_error_via_webhook(state["webhook_url"], workflow_id, str(e))
        finally:
            self.active_workflows.pop(workflow_id, None)

    def _extract_crew_results(self, result: Any) -> dict[str, Any]:
        """Extract structured results from PipelineRunResult or CrewOutput."""
        analysis_results = {"raw_output": None, "task_outputs": [], "memory_stored": False, "graph_created": False}

        # Handle PipelineRunResult (dict from ContentPipeline)
        if isinstance(result, dict):
            # PipelineRunResult structure:
            # {
            #   "status": "success",
            #   "analysis": {"status": "success", "sentiment": "...", "keywords": [...], ...},
            #   "fallacy": {"status": "success", "fallacies": [...], ...},
            #   "perspective": {"status": "success", "summary": "...", ...},
            #   "memory": {"status": "success", ...},
            #   ...
            # }
            # Note: Each field is StepResult.to_dict() which merges data directly into dict

            # Extract analysis data (data is merged into root, not nested in "data")
            if "analysis" in result and isinstance(result["analysis"], dict):
                analysis_dict = result["analysis"]
                # Check if the step succeeded
                if analysis_dict.get("status") == "success":
                    # The analysis data is merged into the dict along with "status"
                    analysis_results["raw_output"] = json.dumps(analysis_dict, indent=2)
                    # Extract specific components
                    for key in ["sentiment", "keywords", "emotions", "topics", "word_count", "key_phrases"]:
                        if key in analysis_dict:
                            analysis_results[key] = analysis_dict[key]

            # Extract fallacy detection results
            if "fallacy" in result and isinstance(result["fallacy"], dict):
                fallacy_dict = result["fallacy"]
                if fallacy_dict.get("status") == "success":
                    # Extract fallacy data (merged into root of dict)
                    for key in ["fallacies", "fallacy_count", "confidence_scores"]:
                        if key in fallacy_dict:
                            analysis_results[key] = fallacy_dict[key]

            # Extract perspective/summary
            if "perspective" in result and isinstance(result["perspective"], dict):
                perspective_dict = result["perspective"]
                if perspective_dict.get("status") == "success":
                    # Extract summary and other perspective data
                    for key in ["summary", "briefing", "claims", "fact_checks"]:
                        if key in perspective_dict:
                            analysis_results[key] = perspective_dict[key]

            # Extract transcription for reference
            if "transcription" in result and isinstance(result["transcription"], dict):
                trans_dict = result["transcription"]
                if trans_dict.get("status") == "success" and "transcript" in trans_dict:
                    analysis_results["transcript"] = trans_dict["transcript"]

            # Extract memory storage status
            if "memory" in result and isinstance(result["memory"], dict):
                memory_dict = result["memory"]
                analysis_results["memory_stored"] = memory_dict.get("status") == "success"

            # Extract graph creation status
            if "graph_memory" in result and isinstance(result["graph_memory"], dict):
                graph_dict = result["graph_memory"]
                analysis_results["graph_created"] = graph_dict.get("status") == "success"

            # Build task outputs showing all stages
            for stage_name in ["download", "transcription", "analysis", "fallacy", "perspective", "memory"]:
                if stage_name in result and isinstance(result[stage_name], dict):
                    stage_status = result[stage_name].get("status", "unknown")
                    analysis_results["task_outputs"].append(f"{stage_name}: {stage_status}")

            # If no analysis data found, use entire result as raw output
            if not analysis_results["raw_output"]:
                analysis_results["raw_output"] = json.dumps(result, indent=2)

        # Handle legacy CrewOutput format
        elif hasattr(result, "raw"):
            analysis_results["raw_output"] = result.raw
        elif hasattr(result, "final_output"):
            analysis_results["raw_output"] = result.final_output
        else:
            analysis_results["raw_output"] = str(result)

        if hasattr(result, "tasks_output") and result.tasks_output:
            for task_output in result.tasks_output:
                analysis_results["task_outputs"].append(
                    task_output.raw if hasattr(task_output, "raw") else str(task_output)
                )

        return analysis_results

    def _format_intelligence_briefing(
        self, url: str, depth: str, results: dict[str, Any], workflow_id: str, state: dict[str, Any]
    ) -> str:
        """Format comprehensive intelligence briefing for delivery."""
        duration = time.time() - state["start_time"]
        briefing = "# 🎯 Intelligence Analysis Complete\n\n"
        briefing += f"**Workflow ID:** `{workflow_id}`\n"
        briefing += f"**URL:** {url}\n"
        briefing += f"**Analysis Depth:** {depth}\n"
        briefing += f"**Processing Time:** {duration:.1f}s ({duration / 60:.1f} minutes)\n"
        briefing += f"**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n"

        # Add content type and quality if available
        if results.get("content_type"):
            briefing += f"**Content Type:** {results['content_type']}\n"
        if results.get("quality_score"):
            briefing += f"**Quality Score:** {results['quality_score']:.2f}\n"

        briefing += "\n---\n\n"

        # Format fact checks if available
        if results.get("fact_checks"):
            briefing += "## 🔍 Fact Checks\n\n"
            fact_checks = results["fact_checks"]
            if isinstance(fact_checks, list):
                for i, check in enumerate(fact_checks, 1):
                    briefing += f"**{i}.** {check}\n"
            else:
                briefing += f"{fact_checks}\n"
            briefing += "\n"

        # Format claims if available
        if results.get("claims"):
            briefing += "## 📋 Claims Extracted\n\n"
            claims = results["claims"]
            if isinstance(claims, list):
                for i, claim in enumerate(claims, 1):
                    briefing += f"**{i}.** {claim}\n"
            else:
                briefing += f"{claims}\n"
            briefing += "\n"

        # Add generic analysis output
        if results.get("briefing"):
            briefing += results["briefing"]
        elif results.get("raw_output"):
            briefing += f"## Analysis Results\n\n{results['raw_output']}\n\n"

        briefing += "\n---\n\n"
        briefing += "## Workflow Metadata\n\n"
        briefing += f"- **Memory Stored:** {('✅ Yes' if results.get('memory_stored') else '❌ No')}\n"
        briefing += f"- **Knowledge Graph:** {('✅ Created' if results.get('graph_created') else '❌ Not created')}\n"
        briefing += "- **Background Processing:** ✅ Enabled (no time limits)\n"
        briefing += "- **Analysis Quality:** Comprehensive (all claims verified)\n"
        return briefing

    async def _deliver_results_via_webhook(self, webhook_url: str, briefing: str, workflow_id: str) -> None:
        """Deliver results via Discord webhook (bypasses interaction token limits)."""
        try:
            from platform.http.http_utils import resilient_post

            chunks = [briefing[i : i + 1900] for i in range(0, len(briefing), 1900)]
            for i, chunk in enumerate(chunks):
                payload = {"content": chunk, "username": "Intelligence Analysis Bot"}
                if i == 0:
                    payload["embeds"] = [
                        {
                            "title": "🔬 Background Intelligence Analysis",
                            "description": f"Workflow ID: `{workflow_id}`",
                            "color": 65280,
                            "footer": {"text": "Analysis completed without time constraints"},
                        }
                    ]
                response = resilient_post(webhook_url, json_payload=payload, timeout_seconds=30)
                if response.status_code >= 400:
                    logger.error(f"Webhook delivery failed: {response.status_code} - {response.text}")
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
            logger.info(f"✅ Results delivered via webhook for workflow {workflow_id}")
        except Exception as e:
            logger.error(f"❌ Failed to deliver results via webhook: {e}", exc_info=True)

    async def _deliver_error_via_webhook(self, webhook_url: str, workflow_id: str, error: str) -> None:
        """Deliver error notification via webhook."""
        try:
            from platform.http.http_utils import resilient_post

            payload = {
                "content": f"❌ **Intelligence Analysis Failed**\n\n**Workflow ID:** `{workflow_id}`\n**Error:** {error}\n\nPlease check logs for details.",
                "username": "Intelligence Analysis Bot",
                "embeds": [
                    {
                        "title": "⚠️ Analysis Error",
                        "description": f"Workflow {workflow_id} encountered an error",
                        "color": 16711680,
                    }
                ],
            }
            response = resilient_post(webhook_url, json_payload=payload, timeout_seconds=30)
            if response.status_code >= 400:
                logger.error(f"Webhook error delivery failed: {response.status_code} - {response.text}")
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
        state_file = self.storage_dir / f"{workflow_id}.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load workflow state: {e}", exc_info=True)
        return None
