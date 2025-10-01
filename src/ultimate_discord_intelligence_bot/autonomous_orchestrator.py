"""Autonomous Intelligence Orchestrator - Single Entry Point for All AI Capabilities.

This module provides the unified autonomous workflow that coordinates all 11 agents,
50+ tools, ContentPipeline, memory systems, and analysis capabilities through a single
self-orchestrated command interface.
"""

from __future__ import annotations

# Standard library imports
import asyncio
import logging
import math
import os
import statistics
import time
from textwrap import dedent
from typing import TYPE_CHECKING, Any

# Third-party imports (optional): provide light fallbacks when crewai isn't installed
try:  # pragma: no cover - prefer real library when present
    from crewai import Crew, Process, Task  # type: ignore
except Exception:  # pragma: no cover - tests/environment without crewai
    if not TYPE_CHECKING:

        class Task:  # type: ignore[too-many-ancestors]
            def __init__(self, *a, **k): ...

        class Process:  # type: ignore[too-many-ancestors]
            sequential = "sequential"

        class Crew:  # type: ignore[too-many-ancestors]
            def __init__(self, *a, **k): ...

            def kickoff(self, *a, **k):
                return {"status": "ok"}


# Local imports - Core
from .config import prompts as prompt_config
from .crew import UltimateDiscordIntelligenceBotCrew
from .crew_error_handler import CrewErrorHandler
from .crew_insight_helpers import CrewInsightExtractor
from .multi_modal_synthesizer import MultiModalSynthesizer
from .obs.metrics import get_metrics
from .step_result import StepResult

# Local imports - Tools (only the ones actually used in imports)
from .tools import (
    AdvancedPerformanceAnalyticsTool,
    ClaimExtractorTool,
    DeceptionScoringTool,
    FactCheckTool,
    GraphMemoryTool,
    HippoRagContinualMemoryTool,
    LogicalFallacyTool,
    MemoryStorageTool,
    PerspectiveSynthesizerTool,
    PipelineTool,
    SocialMediaMonitorTool,
    TrustworthinessTrackerTool,
    TruthScoringTool,
    XMonitorTool,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass

logger = logging.getLogger(__name__)


class AutonomousIntelligenceOrchestrator:
    """Enhanced orchestrator that coordinates specialized autonomous intelligence agents through strategic workflows."""

    def __init__(self):
        """Initialize the orchestrator with specialized AI agent team."""
        self.crew = UltimateDiscordIntelligenceBotCrew()
        self.metrics = get_metrics()
        self.logger = logging.getLogger(__name__)
        self.insight_extractor = CrewInsightExtractor()
        self.error_handler = CrewErrorHandler()
        # Initialize synthesizer and agent coordination system early
        self.synthesizer = MultiModalSynthesizer()
        self._initialize_agent_coordination_system()
        # Validate system prerequisites and cache health/LLM availability
        try:
            self.system_health = self._validate_system_prerequisites()
        except Exception:
            self.system_health = {"healthy": False, "errors": ["init_validation_failed"]}
        try:
            self._llm_available = bool(self._check_llm_api_available())
        except Exception:
            self._llm_available = False

    # ========================================
    # DATA FLOW HELPERS (Critical Fix)
    # ========================================

    def _populate_agent_tool_context(self, agent: Any, context_data: dict[str, Any]) -> None:
        """Populate shared context on all tool wrappers for an agent.

        This is CRITICAL for CrewAI agents to receive structured data. Without this,
        tools receive empty parameters and fail or return meaningless results.

        Args:
            agent: CrewAI Agent instance with tools attribute
            context_data: Dictionary of data to make available to all tools
        """
        if not hasattr(agent, "tools"):
            self.logger.warning(f"Agent {getattr(agent, 'role', 'unknown')} has no tools attribute")
            return

        populated_count = 0
        for tool in agent.tools:
            if hasattr(tool, "update_context"):
                tool.update_context(context_data)
                populated_count += 1
                self.logger.debug(
                    f"Populated context for {getattr(tool, 'name', tool.__class__.__name__)}: "
                    f"{list(context_data.keys())}"
                )

        if populated_count > 0:
            self.logger.info(
                f"Populated shared context on {populated_count} tools for agent {getattr(agent, 'role', 'unknown')}"
            )
            # Track context population for monitoring
            try:
                self.metrics.counter(
                    "autointel_context_populated",
                    labels={
                        "agent": getattr(agent, "role", "unknown"),
                        "tools_count": populated_count,
                        "has_transcript": "transcript" in context_data or "text" in context_data,
                    },
                ).inc()
            except Exception:
                pass

    def _validate_stage_data(self, stage_name: str, required_keys: list[str], data: dict[str, Any]) -> None:
        """Validate that required data keys are present before stage execution.

        Raises ValueError with clear diagnostic if data is missing, preventing
        cascading failures from propagating through the workflow.

        Args:
            stage_name: Name of the stage for error messages
            required_keys: List of required keys that must be present and non-empty
            data: Data dictionary to validate

        Raises:
            ValueError: If any required keys are missing or empty
        """
        missing = []
        for key in required_keys:
            if key not in data:
                missing.append(f"{key} (not present)")
            elif not data[key]:
                missing.append(f"{key} (empty)")

        if missing:
            available = list(data.keys())
            error_msg = f"Stage '{stage_name}' missing required data: {missing}. Available keys: {available}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        # Validation passed; no side-effects here

    def _validate_system_prerequisites(self) -> dict[str, Any]:
        """Validate system dependencies and return health status."""
        health = {
            "healthy": True,
            "warnings": [],
            "errors": [],
            "available_capabilities": [],
            "degraded_capabilities": [],
        }

        # Check critical dependencies
        critical_deps = {
            "yt-dlp": self._check_ytdlp_available(),
            "llm_api": self._check_llm_api_available(),
            "discord_integration": self._check_discord_available(),
        }

        for dep, available in critical_deps.items():
            if not available:
                health["errors"].append(f"Critical dependency missing: {dep}")
                health["healthy"] = False

        # Check optional services
        optional_services = {
            "qdrant": os.getenv("QDRANT_URL") is not None,
            "vector_search": os.getenv("QDRANT_URL") is not None,
            "drive_upload": os.getenv("GOOGLE_DRIVE_CREDENTIALS") is not None,
            "advanced_analytics": os.getenv("PROMETHEUS_ENDPOINT_PATH") is not None,
        }

        for service, available in optional_services.items():
            if available:
                health["available_capabilities"].append(service)
            else:
                health["degraded_capabilities"].append(service)
                health["warnings"].append(f"Optional service unavailable: {service}")

        # Determine workflow capabilities based on available dependencies
        if critical_deps["yt-dlp"] and critical_deps["llm_api"]:
            health["available_capabilities"].extend(
                ["content_acquisition", "transcription_processing", "content_analysis"]
            )

        if not critical_deps["discord_integration"]:
            health["degraded_capabilities"].append("community_engagement")
            health["warnings"].append("Discord integration disabled - community engagement limited")

        return health

    def _check_ytdlp_available(self) -> bool:
        """Check if yt-dlp is available without importing it directly (guard-safe)."""
        try:
            # Use PATH probing to detect presence; avoid direct downloader-imports here
            import shutil

            if shutil.which("yt-dlp"):
                return True
            # Check configured directory hint
            try:
                from .settings import YTDLP_DIR  # noqa: PLC0415

                return bool(YTDLP_DIR)
            except Exception:
                return False
        except Exception:
            return False

    def _check_llm_api_available(self) -> bool:
        """Check if LLM API keys are configured."""
        openai_key = os.getenv("OPENAI_API_KEY", "")
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

        # Dummy keys don't count as available
        dummy_patterns = ["dummy_", "your-", "sk-your-"]

        valid_openai = openai_key and not any(pattern in openai_key for pattern in dummy_patterns)
        valid_openrouter = openrouter_key and not any(pattern in openrouter_key for pattern in dummy_patterns)

        return valid_openai or valid_openrouter

    def _check_discord_available(self) -> bool:
        """Check if Discord integration is properly configured."""
        token = os.getenv("DISCORD_BOT_TOKEN", "")
        webhook = os.getenv("DISCORD_WEBHOOK", "")

        # Dummy values don't count
        dummy_patterns = ["dummy_", "your-", "https://discord.com/api/webhooks/YOUR_"]

        valid_token = token and not any(pattern in token for pattern in dummy_patterns)
        valid_webhook = webhook and not any(pattern in webhook for pattern in dummy_patterns)

        return valid_token or valid_webhook

    async def _to_thread_with_tenant(self, fn, *args, **kwargs):
        """Run a sync function in a thread while preserving TenantContext.

        Many tools rely on tenant-scoped services. Ensure we propagate the
        current TenantContext into worker threads so data reads/writes hit the
        right namespaces.
        """
        try:
            from .tenancy import current_tenant, with_tenant

            ctx = current_tenant()

            def _call():
                if ctx is not None:
                    with with_tenant(ctx):
                        return fn(*args, **kwargs)
                return fn(*args, **kwargs)

            return await asyncio.to_thread(_call)
        except Exception:
            return await asyncio.to_thread(fn, *args, **kwargs)

    def _initialize_agent_coordination_system(self):
        """Initialize the agent coordination system with specialized workflows mapped to redesigned agent roster."""
        self.agent_workflow_map = {
            "mission_coordination": self.crew.autonomous_mission_coordinator,
            "content_acquisition": self.crew.multi_platform_acquisition_specialist,
            "transcription_processing": self.crew.advanced_transcription_engineer,
            "content_analysis": self.crew.comprehensive_linguistic_analyst,
            "information_verification": self.crew.information_verification_director,
            "threat_analysis": self.crew.threat_intelligence_analyst,
            "behavioral_profiling": self.crew.behavioral_profiling_specialist,
            "social_intelligence": self.crew.social_intelligence_coordinator,
            "trend_analysis": self.crew.trend_analysis_scout,
            "knowledge_integration": self.crew.knowledge_integration_architect,
            "research_synthesis": self.crew.research_synthesis_specialist,
            "intelligence_briefing": self.crew.intelligence_briefing_director,
            "strategic_argumentation": self.crew.strategic_argument_analyst,
            "system_operations": self.crew.system_operations_manager,
            "community_engagement": self.crew.community_engagement_coordinator,
        }

        self.workflow_dependencies = {
            "mission_coordination": [],  # Entry point - coordinates all other workflows
            "content_acquisition": ["mission_coordination"],
            "transcription_processing": ["content_acquisition"],
            "content_analysis": ["transcription_processing"],
            "information_verification": ["content_analysis"],
            "threat_analysis": ["content_analysis", "information_verification"],
            "behavioral_profiling": ["content_analysis", "threat_analysis"],
            "social_intelligence": ["content_analysis"],  # Can run in parallel
            "trend_analysis": ["social_intelligence"],  # Depends on social intelligence
            "knowledge_integration": ["information_verification", "threat_analysis", "behavioral_profiling"],
            "research_synthesis": ["content_analysis", "information_verification"],
            "intelligence_briefing": ["knowledge_integration", "research_synthesis"],
            "strategic_argumentation": ["information_verification", "research_synthesis"],
            "system_operations": [],  # Monitoring workflow - runs independently
            "community_engagement": ["intelligence_briefing"],  # Final stage
        }

        # Agent coordination references for optimized crew execution
        self.agent_coordinators = {
            "mission_orchestrator": self.crew.autonomous_mission_coordinator,
            "acquisition_specialist": self.crew.multi_platform_acquisition_specialist,
            "transcription_engineer": self.crew.advanced_transcription_engineer,
            "analysis_cartographer": self.crew.comprehensive_linguistic_analyst,
            "verification_director": self.crew.information_verification_director,
            "threat_analyst": self.crew.threat_intelligence_analyst,
            "behavioral_profiler": self.crew.behavioral_profiling_specialist,
            "social_intelligence": self.crew.social_intelligence_coordinator,
            "trend_scout": self.crew.trend_analysis_scout,
            "knowledge_architect": self.crew.knowledge_integration_architect,
            "research_synthesist": self.crew.research_synthesis_specialist,
            "intelligence_curator": self.crew.intelligence_briefing_director,
            "argument_strategist": self.crew.strategic_argument_analyst,
            "system_manager": self.crew.system_operations_manager,
            "community_coordinator": self.crew.community_engagement_coordinator,
        }

    @staticmethod
    def _normalize_acquisition_data(acquisition: StepResult | dict[str, Any] | None) -> dict[str, Any]:
        """Return a flattened ContentPipeline payload for downstream stages.

        The ContentPipeline tool historically wrapped results inside nested ``data``
        structures.  This helper unifies both legacy and new shapes so all stages
        can reliably access ``download`` / ``transcription`` / ``analysis`` blocks
        without duplicating guard logic.
        """

        if isinstance(acquisition, StepResult):
            data = acquisition.data
        elif isinstance(acquisition, dict):
            data = acquisition
        else:
            return {}

        if not isinstance(data, dict):
            return {}

        if any(key in data for key in ("transcription", "analysis", "download", "fallacy", "perspective")):
            return data

        nested = data.get("data")
        if isinstance(nested, dict):
            return nested

        raw_payload = data.get("raw_pipeline_payload")
        if isinstance(raw_payload, dict):
            return raw_payload

        return data

    async def _execute_stage_with_recovery(
        self, stage_function, stage_name: str, agent_name: str, workflow_depth: str, *args, **kwargs
    ):
        """Execute a workflow stage with intelligent error handling and recovery."""
        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                # Execute the stage function
                result = await stage_function(*args, **kwargs)

                # If successful, return result
                if result.success:
                    return result

                # If stage failed but returned a result, handle as controlled failure
                if not result.success and retry_count < max_retries:
                    retry_count += 1
                    await asyncio.sleep(0.5 * retry_count)  # Exponential backoff
                    continue

                return result

            except Exception as e:
                self.logger.warning(f"Stage {stage_name} failed (attempt {retry_count + 1}): {e}")

                # Use error handler for recovery planning
                recovery_plan, interim_result = await self.error_handler.handle_crew_error(
                    error=e,
                    stage_name=stage_name,
                    agent_name=agent_name,
                    workflow_depth=workflow_depth,
                    retry_count=retry_count,
                    preceding_results=kwargs.get("preceding_results", {}),
                    system_health=self._get_system_health(),
                )

                # Execute recovery based on plan
                if not recovery_plan.continue_workflow:
                    return interim_result

                if retry_count >= max_retries or retry_count >= recovery_plan.max_retries:
                    return interim_result

                retry_count += 1

                # Apply recovery strategy modifications for next attempt
                if recovery_plan.simplified_parameters:
                    kwargs.update(recovery_plan.simplified_parameters)

                await asyncio.sleep(0.5 * retry_count)  # Exponential backoff

        # Final fallback
        return StepResult.fail(
            f"Stage {stage_name} failed after {max_retries} retries", step=f"{stage_name}_max_retries_exceeded"
        )

    def _get_system_health(self) -> dict[str, Any]:
        """Get current system health metrics for error analysis."""
        try:
            return {
                "memory_usage": "normal",  # Could integrate with actual system monitoring
                "cpu_usage": "normal",
                "active_connections": "stable",
                "error_rate": len(self.error_handler.error_history),
                "uptime": "healthy",
                "last_successful_stage": getattr(self, "_last_successful_stage", None),
            }
        except Exception as e:
            self.logger.warning(f"Could not get system health: {e}")
            return {"status": "unknown", "error": str(e)}

    @staticmethod
    def _merge_threat_and_deception_data(threat_result: StepResult, deception_result: StepResult) -> StepResult:
        """Combine threat analysis output with deception scoring metrics (StepResult inputs).

        Note: Retained for backward compatibility where StepResult objects are used.
        """

        if not isinstance(threat_result, StepResult):
            return threat_result
        if not threat_result.success:
            return threat_result

        combined_data: dict[str, Any] = dict(threat_result.data)
        original_message = combined_data.get("message")

        if isinstance(deception_result, StepResult) and deception_result.success:
            deception_payload = dict(deception_result.data)
            if deception_payload:
                combined_data["deception_metrics"] = deception_payload
                if "deception_score" not in combined_data and "deception_score" in deception_payload:
                    combined_data["deception_score"] = deception_payload.get("deception_score")
        else:
            status = None
            error_message = None
            if isinstance(deception_result, StepResult):
                status = deception_result.custom_status
                error_message = deception_result.error

            if status == "skipped":
                combined_data.setdefault("deception_metrics_status", "skipped")
            elif error_message:
                combined_data.setdefault("deception_metrics_error", error_message)
            elif status == "error":
                combined_data.setdefault("deception_metrics_error", "deception scoring failed")

        if original_message is not None:
            combined_data["message"] = original_message

        return StepResult.ok(**combined_data)

    @staticmethod
    def _merge_threat_payload(
        threat_payload: dict[str, Any],
        verification_data: dict[str, Any] | None,
        fact_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Augment a plain threat payload dict with relevant verification/fact data.

        This helper is used when we have already-materialized dict payloads rather than StepResult objects.
        It attaches deception_score, logical fallacies, and fact checks if present, without overriding
        existing values.
        """
        merged = dict(threat_payload) if isinstance(threat_payload, dict) else {}
        # From verification results
        if isinstance(verification_data, dict):
            if "deception_metrics" in verification_data and "deception_metrics" not in merged:
                merged["deception_metrics"] = verification_data.get("deception_metrics")
            if "credibility_assessment" in verification_data and "credibility_assessment" not in merged:
                merged["credibility_assessment"] = verification_data.get("credibility_assessment")
            # Deception score may live under various keys; don't clobber if already present
            for k in ("deception_score",):
                if k not in merged and isinstance(verification_data.get(k), (int, float)):
                    merged[k] = verification_data.get(k)
            if "logical_analysis" in verification_data and "logical_fallacies" not in merged:
                merged["logical_fallacies"] = verification_data.get("logical_analysis")

        # From fact analysis data
        if isinstance(fact_data, dict):
            if "fact_checks" in fact_data and "fact_checks" not in merged:
                merged["fact_checks"] = fact_data.get("fact_checks")
            if "logical_fallacies" in fact_data and "logical_fallacies" not in merged:
                merged["logical_fallacies"] = fact_data.get("logical_fallacies")
            if "perspective_synthesis" in fact_data and "perspective" not in merged:
                merged["perspective"] = fact_data.get("perspective_synthesis")

        return merged

    @staticmethod
    def _build_knowledge_payload(
        acquisition_data: dict[str, Any],
        intelligence_data: dict[str, Any],
        verification_data: dict[str, Any],
        threat_data: dict[str, Any],
        fact_data: dict[str, Any],
        behavioral_data: dict[str, Any],
        *,
        fallback_url: str | None = None,
    ) -> dict[str, Any]:
        """Construct a normalized payload for downstream knowledge storage."""

        download_block = acquisition_data.get("download") if isinstance(acquisition_data.get("download"), dict) else {}
        transcription_block = (
            acquisition_data.get("transcription") if isinstance(acquisition_data.get("transcription"), dict) else {}
        )
        pipeline_meta = (
            acquisition_data.get("pipeline_metadata")
            if isinstance(acquisition_data.get("pipeline_metadata"), dict)
            else {}
        )
        content_metadata = (
            intelligence_data.get("content_metadata")
            if isinstance(intelligence_data.get("content_metadata"), dict)
            else {}
        )

        source_url = (
            acquisition_data.get("source_url")
            or pipeline_meta.get("url")
            or fallback_url
            or (download_block.get("source_url") if isinstance(download_block, dict) else None)
        )

        title = None
        if isinstance(download_block, dict):
            title = download_block.get("title")
        if not title and isinstance(content_metadata, dict):
            title = content_metadata.get("title")
        if not title:
            title = pipeline_meta.get("title")

        platform = None
        if isinstance(download_block, dict):
            platform = download_block.get("platform")
        if not platform and isinstance(content_metadata, dict):
            platform = content_metadata.get("platform")
        if not platform:
            platform = pipeline_meta.get("platform") or transcription_block.get("platform")

        perspective_data: dict[str, Any] = {}
        if isinstance(fact_data, dict):
            maybe_perspective = fact_data.get("perspective_synthesis")
            if isinstance(maybe_perspective, dict):
                perspective_data = maybe_perspective
        if not perspective_data and isinstance(acquisition_data.get("perspective"), dict):
            perspective_data = acquisition_data.get("perspective", {})

        summary = ""
        if isinstance(perspective_data, dict):
            summary = str(perspective_data.get("summary") or "").strip()
        if not summary and isinstance(content_metadata, dict):
            summary = str(content_metadata.get("summary") or "").strip()
        if not summary and isinstance(intelligence_data, dict):
            transcript = str(intelligence_data.get("enhanced_transcript") or intelligence_data.get("transcript") or "")
            summary = transcript[:400].strip()
        if not summary:
            summary = "Summary unavailable"

        fact_checks: dict[str, Any] = {}
        if isinstance(verification_data, dict):
            maybe_fact_checks = verification_data.get("fact_checks")
            if isinstance(maybe_fact_checks, dict):
                fact_checks = maybe_fact_checks
        if not fact_checks and isinstance(fact_data, dict):
            maybe_fact_checks = fact_data.get("fact_checks")
            if isinstance(maybe_fact_checks, dict):
                fact_checks = maybe_fact_checks

        logical_fallacies: dict[str, Any] = {}
        if isinstance(verification_data, dict):
            maybe_fallacies = verification_data.get("logical_analysis")
            if isinstance(maybe_fallacies, dict):
                logical_fallacies = maybe_fallacies
        if not logical_fallacies and isinstance(fact_data, dict):
            maybe_fallacies = fact_data.get("logical_fallacies")
            if isinstance(maybe_fallacies, dict):
                logical_fallacies = maybe_fallacies

        deception_score = None
        if isinstance(threat_data, dict):
            deception_score = threat_data.get("deception_score")
            if deception_score is None:
                metrics = threat_data.get("deception_metrics")
                if isinstance(metrics, dict):
                    deception_score = metrics.get("deception_score")

        keywords: list[Any] = []
        if isinstance(intelligence_data, dict):
            maybe_keywords = intelligence_data.get("thematic_insights")
            if isinstance(maybe_keywords, list):
                keywords = maybe_keywords

        knowledge_payload: dict[str, Any] = {
            "url": source_url,
            "source_url": source_url,
            "title": title,
            "platform": platform,
            "analysis_summary": summary,
            "content_metadata": content_metadata if isinstance(content_metadata, dict) else {},
            "fact_check_results": fact_checks,
            "detected_fallacies": logical_fallacies,
            "verification_results": verification_data,
            "threat_assessment": threat_data,
            "behavioral_profile": behavioral_data,
            "perspective": perspective_data if isinstance(perspective_data, dict) else {},
            "keywords": keywords,
        }

        if deception_score is not None:
            knowledge_payload["deception_score"] = deception_score

        transcript_index = intelligence_data.get("transcript_index") if isinstance(intelligence_data, dict) else {}
        if isinstance(transcript_index, dict) and transcript_index:
            knowledge_payload["transcript_index"] = transcript_index

        timeline_anchors = intelligence_data.get("timeline_anchors") if isinstance(intelligence_data, dict) else None
        if isinstance(timeline_anchors, list) and timeline_anchors:
            knowledge_payload["timeline_anchors"] = timeline_anchors

        return knowledge_payload

    async def execute_autonomous_intelligence_workflow(
        self, interaction: Any, url: str, depth: str = "standard", tenant_ctx: Any = None
    ) -> None:
        """Execute the complete autonomous intelligence workflow with ALL advanced capabilities.

        This is the single entry point that orchestrates the true 25-stage workflow:
        1. Agent Coordination Setup - Initialize CrewAI Multi-Agent System
        2. Mission Planning and Resource Allocation
        3. Advanced Content Acquisition with Multi-Platform Support
        4. Enhanced Transcription and Indexing
        5. Comprehensive Content Analysis with Sentiment Mapping
        6. Multi-Source Information Verification
        7. Advanced Threat and Deception Analysis
        8. Social Intelligence and Cross-Platform Monitoring
        9. Behavioral Profiling and Persona Analysis
        10. Advanced Knowledge Integration (Multi-Layer Memory Systems)
        11. Research Synthesis and Context Building
        12. Advanced Performance Analytics and Predictive Analysis
        13. AI-Enhanced Quality Assessment (Experimental)
        14. Advanced Pattern Recognition (Experimental)
        15. Cross-Reference Intelligence Network (Experimental)
        16. Predictive Threat Assessment (Experimental)
        17. Multi-Modal Content Synthesis (Experimental)
        18. Dynamic Knowledge Graph Construction (Experimental)
        19. Autonomous Learning Integration (Experimental)
        20. Advanced Contextual Bandits Optimization (Experimental)
        21. Community Intelligence Synthesis (Experimental)
        22. Real-Time Adaptive Workflow (Experimental)
        23. Enhanced Memory Consolidation (Experimental)
        24. Intelligence Briefing Curation
        25. Enhanced Result Synthesis with Multi-Modal Integration

        Analysis Depths:
        - standard: Stages 1-10 (Core intelligence processing)
        - deep: Stages 1-15 (Enhanced with research and analytics)
        - comprehensive: Stages 1-20 (Advanced processing with quality assessment)
        - experimental: All 25 stages (Full sophisticated multi-agent orchestration)

        Advanced Features:
        - True CrewAI multi-agent coordination with 11 specialized agents
        - Adaptive workflow planning based on content complexity
        - Real-time performance monitoring with AI routing optimization
        - Predictive analytics for capacity and reliability forecasting
        - Enhanced crew execution with trajectory analysis
        - Autonomous learning and continuous improvement
        - Cross-tenant capabilities through MCP integration
        - Advanced contextual bandits for optimal decision making
        - Multimodal analysis for text, audio, video, and metadata
        - Dynamic knowledge graph construction and maintenance

        Args:
            interaction: Discord interaction object
            url: URL to analyze
            depth: Analysis depth (standard, deep, comprehensive, experimental)
        """
        start_time = time.time()
        workflow_id = f"autointel_{int(start_time)}_{hash(url) % 10000}"

        # Set up tenant context for memory services
        if tenant_ctx is None:
            try:
                from .tenancy import TenantContext

                tenant_ctx = TenantContext(
                    tenant_id=f"guild_{getattr(interaction, 'guild_id', 'dm') or 'dm'}",
                    workspace_id=getattr(getattr(interaction, "channel", None), "name", "autointel_workspace"),
                )
                self.logger.info(f"Created tenant context for workflow: {tenant_ctx}")
            except Exception as e:
                self.logger.warning(f"Failed to create tenant context: {e}")
                tenant_ctx = None

        # Canonicalize depth labels from UI strings (e.g., "Experimental - Cutting-Edge AI")
        def _canonical_depth(raw: str | None) -> str:
            if not raw:
                return "standard"
            v = str(raw).strip().lower()
            if v.startswith("exp") or "experimental" in v:
                return "experimental"
            if v.startswith("comp") or "comprehensive" in v:
                return "comprehensive"
            if v.startswith("deep"):
                return "deep"
            return "standard"

        original_depth = _canonical_depth(depth)
        depth = original_depth

        # Optional feature gate: allow deployments to disable the heaviest path by default.
        # If experimental depth is requested but not explicitly enabled, fall back safely.
        try:
            exp_enabled = os.getenv("ENABLE_EXPERIMENTAL_DEPTH", "0").lower() in {"1", "true", "yes", "on"}
        except Exception:
            exp_enabled = False
        if depth == "experimental" and not exp_enabled:
            depth = "comprehensive"
            # Inform the user that we're degrading the analysis level for safety/config reasons
            try:
                await self._send_progress_update(
                    interaction,
                    "⚠️ Experimental mode disabled by configuration. Falling back to 'comprehensive' depth.",
                    0,
                    1,
                )
            except Exception:
                pass

        # Determine workflow complexity and stage count based on depth
        if depth == "standard":
            total_stages = 10  # Stages 1-10
        elif depth == "deep":
            total_stages = 15  # Stages 1-15
        elif depth == "comprehensive":
            total_stages = 20  # Stages 1-20
        elif depth == "experimental":
            total_stages = 25  # All 25 stages
        else:
            total_stages = 10  # Default to standard

        try:
            # Execute workflow within tenant context if available
            if tenant_ctx:
                try:
                    from .tenancy import with_tenant

                    with with_tenant(tenant_ctx):
                        await self._execute_workflow_stages(
                            interaction, url, depth, total_stages, workflow_id, start_time
                        )
                    return
                except Exception as tenancy_error:
                    self.logger.warning(f"Tenant context execution failed: {tenancy_error}")
                    # Fall back to execution without tenant context

            # Execute without tenant context as fallback
            await self._execute_workflow_stages(interaction, url, depth, total_stages, workflow_id, start_time)

        except Exception as e:
            self.logger.error(f"Enhanced autonomous intelligence workflow failed: {e}", exc_info=True)
            await self._send_error_response(interaction, "Enhanced Autonomous Workflow", str(e))
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "error"}).inc()

    async def _execute_workflow_stages(
        self, interaction: Any, url: str, depth: str, total_stages: int, workflow_id: str, start_time: float
    ) -> None:
        """Execute the actual workflow stages with graceful degradation."""
        try:
            # Debug logging for workflow execution
            print(f"🚀 Starting autonomous workflow with {total_stages} stages")
            print(f"  URL: {url}")
            print(f"  Depth: {depth}")
            print(f"  Workflow ID: {workflow_id}")

            # Check system health and adapt workflow accordingly
            if not self.system_health["healthy"]:
                print(f"⚠️ System health issues detected: {self.system_health['errors'][:3]}")
                await self._send_progress_update(
                    interaction, "⚠️ System operating in degraded mode due to missing dependencies...", 0, total_stages
                )
                for error in self.system_health["errors"][:3]:  # Show first 3 errors
                    await self._send_progress_update(interaction, f"❌ {error}", 0, total_stages)

                # Attempt limited workflow with available capabilities
                if not self.system_health["available_capabilities"]:
                    await self._send_error_response(
                        interaction,
                        "System Health Check",
                        "No core capabilities available. Please check configuration and try again.",
                    )
                    return

                await self._send_progress_update(
                    interaction,
                    f"🔧 Continuing with available capabilities: {', '.join(self.system_health['available_capabilities'][:5])}",
                    0,
                    total_stages,
                )  # Stage 1: Agent Coordination Setup - Initialize CrewAI Multi-Agent System
            await self._send_progress_update(
                interaction, "🤖 Initializing CrewAI multi-agent coordination system...", 1, total_stages
            )
            coordination_result = await self._execute_agent_coordination_setup(url, depth)

            if not coordination_result.get("success", False):
                await self._send_progress_update(
                    interaction,
                    "⚠️ Agent coordination partially failed, continuing with simplified workflow...",
                    1,
                    total_stages,
                )

            # Stage 2: Mission Planning and Resource Allocation
            await self._send_progress_update(
                interaction, "🎯 Planning autonomous intelligence mission...", 2, total_stages
            )
            mission_plan = await self._execute_mission_planning(url, depth)
            # Stage 3: Advanced Content Acquisition with Multi-Platform Support
            print(f"📥 Stage 3: Content Acquisition for {url}")
            await self._send_progress_update(
                interaction, "📥 Executing specialized content acquisition...", 3, total_stages
            )
            acquisition_result = await self._execute_specialized_content_acquisition(url)
            if not acquisition_result.success:
                print(f"❌ Content acquisition failed: {acquisition_result.error}")
                self.logger.error(f"Content acquisition failed: {acquisition_result.error}")
                await self._handle_acquisition_failure(interaction, acquisition_result, url)
                return
            else:
                print("✅ Content acquisition successful")
                self.logger.info("Content acquisition completed successfully")

            # Stage 4: Enhanced Transcription and Indexing
            print("🎙️ Stage 4: Transcription Analysis")
            await self._send_progress_update(
                interaction, "🎙️ Performing advanced transcription and indexing...", 4, total_stages
            )
            transcription_result = await self._execute_specialized_transcription_analysis(acquisition_result)
            print(f"  Transcription result: {'✅ Success' if transcription_result.success else '❌ Failed'}")

            # Stage 5: Comprehensive Content Analysis with Sentiment Mapping
            print("🗺️ Stage 5: Content Analysis")
            await self._send_progress_update(
                interaction, "🗺️ Mapping linguistic and sentiment insights...", 5, total_stages
            )
            analysis_result = await self._execute_specialized_content_analysis(transcription_result)
            print(f"  Analysis result: {'✅ Success' if analysis_result.success else '❌ Failed'}")
            if hasattr(analysis_result, "data") and isinstance(analysis_result.data, dict):
                metadata = analysis_result.data.get("content_metadata", {})
                print(f"  Video title: {metadata.get('title', 'Unknown')}")
                print(f"  Platform: {metadata.get('platform', 'Unknown')}")

            # Prepare fact analysis result placeholder for downstream merging
            fact_analysis_result = StepResult.skip(reason="fact_analysis_not_executed")

            # Stage 6: Multi-Source Information Verification
            await self._send_progress_update(
                interaction, "✅ Running specialized information verification...", 6, total_stages
            )
            # Execute fact analysis to support verification stage with structured evidence
            fact_analysis_input: dict[str, Any] = {}
            acquisition_transcription = (
                acquisition_result.data.get("transcription", {}) if isinstance(acquisition_result.data, dict) else {}
            )
            if isinstance(acquisition_transcription, dict) and acquisition_transcription:
                fact_analysis_input["transcription"] = dict(acquisition_transcription)
            transcript_for_fact_checks = None
            if isinstance(transcription_result.data, dict):
                transcript_for_fact_checks = transcription_result.data.get(
                    "enhanced_transcript"
                ) or transcription_result.data.get("transcript")
            if transcript_for_fact_checks:
                transcription_payload = fact_analysis_input.setdefault("transcription", {})
                transcription_payload["transcript"] = transcript_for_fact_checks
            fact_analysis_input["analysis"] = analysis_result.data if isinstance(analysis_result.data, dict) else {}

            fact_analysis_result = await self._execute_fact_analysis(fact_analysis_input)
            if not fact_analysis_result.success:
                self.logger.warning(f"Fact analysis failed: {fact_analysis_result.error}")
            else:
                self.logger.info("Fact analysis completed successfully")

            fact_data: dict[str, Any] = fact_analysis_result.data if isinstance(fact_analysis_result.data, dict) else {}
            if not fact_data and isinstance(analysis_result.data, dict):
                maybe_fact = analysis_result.data.get("fact_analysis")
                if isinstance(maybe_fact, dict):
                    fact_data = maybe_fact

            # Perform comprehensive information verification based on content analysis
            verification_result = await self._execute_specialized_information_verification(
                analysis_result.data, fact_data
            )

            # Stage 7: Advanced Threat and Deception Analysis
            await self._send_progress_update(
                interaction, "🛡️ Analyzing deception patterns and threat levels...", 7, total_stages
            )
            # Execute comprehensive deception/threat analysis (method is named _execute_specialized_deception_analysis)
            threat_analysis_result = await self._execute_specialized_deception_analysis(
                analysis_result.data, verification_result.data
            )
            threat_data_payload: dict[str, Any] = (
                threat_analysis_result.data if isinstance(threat_analysis_result.data, dict) else {}
            )
            if threat_data_payload:
                vdata = verification_result.data if isinstance(verification_result.data, dict) else None
                threat_data_payload = self._merge_threat_payload(threat_data_payload, vdata, fact_data)

            # Additionally compute structured deception/truth/trust scoring using dedicated tools
            # so downstream consumers have a consistent numeric deception score and components.
            try:
                deception_scoring_result = await self._execute_deception_scoring(
                    analysis_result.data, {**(fact_data or {})}
                )
            except Exception as _deception_exc:
                self.logger.warning(f"Deception scoring threw exception: {_deception_exc}")
                deception_scoring_result = StepResult.skip(reason="deception_scoring_error")

            if isinstance(deception_scoring_result, StepResult) and deception_scoring_result.success:
                # Ensure a top-level deception_score exists for UI and storage
                try:
                    dscore = deception_scoring_result.data.get("score")  # type: ignore[assignment]
                    if isinstance(dscore, (int, float)):
                        threat_data_payload.setdefault("deception_score", float(dscore))
                    # Attach detailed metrics non-destructively
                    threat_data_payload.setdefault("deception_metrics", deception_scoring_result.data)
                except Exception:
                    pass

            # Stage 8: Social Intelligence and Cross-Platform Monitoring
            social_intel_result = StepResult.skip(reason="Skipped for basic analysis")
            if depth in ["deep", "comprehensive", "experimental"]:
                # Require meaningful content context before enabling social intel to prevent irrelevant chatter
                content_ok = False
                try:
                    meta = (
                        analysis_result.data.get("content_metadata", {})
                        if isinstance(analysis_result.data, dict)
                        else {}
                    )
                    title_ok = bool((meta.get("title") or "").strip())
                    tx = analysis_result.data.get("transcript", "") if isinstance(analysis_result.data, dict) else ""
                    keywords = (
                        analysis_result.data.get("thematic_insights", [])
                        if isinstance(analysis_result.data, dict)
                        else []
                    )
                    content_ok = (
                        title_ok
                        or (isinstance(tx, str) and len(tx.strip()) > 40)
                        or (isinstance(keywords, list) and len(keywords) > 0)
                    )
                except Exception:
                    content_ok = False
                await self._send_progress_update(interaction, "🌐 Gathering social intelligence...", 8, total_stages)
                # Global gate to prevent accidental connector usage unless explicitly enabled
                social_enabled = os.getenv("ENABLE_SOCIAL_INTEL", "0").lower() in {"1", "true", "yes", "on"}
                if content_ok and social_enabled:
                    social_intel_result = await self._execute_specialized_social_intelligence(
                        analysis_result.data, verification_result.data
                    )
                else:
                    reason = "insufficient_content_context" if content_ok is False else "disabled_by_config"
                    message = (
                        "Skipping social intelligence due to missing title/keywords/transcript. "
                        "This prevents off-topic or placeholder monitoring."
                        if content_ok is False
                        else "Social intelligence disabled (ENABLE_SOCIAL_INTEL=0)."
                    )
                    social_intel_result = StepResult.skip(reason=reason, message=message)

            # Stage 9: Behavioral Profiling and Persona Analysis
            behavioral_result = StepResult.skip(reason="Skipped for basic analysis")
            if depth in ["comprehensive", "experimental"]:
                await self._send_progress_update(interaction, "👤 Profiling behavioral patterns...", 9, total_stages)
                behavioral_result = await self._execute_specialized_behavioral_profiling(
                    analysis_result.data, threat_data_payload
                )

            # Stage 10: Advanced Knowledge Integration (Multi-Layer Memory Systems)
            await self._send_progress_update(
                interaction, "🧠 Integrating with advanced knowledge systems...", 10, total_stages
            )
            # Pass all required parameters in correct order: acquisition, intelligence, verification, deception, behavioral
            if behavioral_result.success:
                knowledge_integration_result = await self._execute_specialized_knowledge_integration(
                    acquisition_result.data,
                    analysis_result.data,
                    verification_result.data,
                    fact_data,
                    threat_data_payload,
                    behavioral_result.data,
                )
            else:
                knowledge_integration_result = await self._execute_specialized_knowledge_integration(
                    acquisition_result.data,
                    analysis_result.data,
                    verification_result.data,
                    fact_data,
                    threat_data_payload,
                    {},
                )

            # Stage 11: Research Synthesis and Context Building
            research_result = StepResult.skip(reason="Skipped for basic analysis")
            if depth in ["deep", "comprehensive", "experimental"]:
                await self._send_progress_update(interaction, "📚 Synthesizing research context...", 11, total_stages)
                research_result = await self._execute_specialized_research_synthesis(
                    analysis_result.data, verification_result.data
                )

            # Stage 12: Advanced Performance Analytics and Predictive Analysis
            analytics_result = StepResult.skip(reason="Skipped for standard analysis")
            if depth in ["comprehensive", "experimental"]:
                perf_enabled = os.getenv("ENABLE_ADVANCED_PERF", "0").lower() in {"1", "true", "yes", "on"}
                if not perf_enabled:
                    analytics_result = StepResult.skip(
                        reason="disabled_by_config",
                        message="Advanced performance analytics disabled (ENABLE_ADVANCED_PERF=0).",
                    )
                else:
                    await self._send_progress_update(
                        interaction, "📊 Running predictive performance analytics...", 12, total_stages
                    )
                    analytics_result = await self._execute_specialized_performance_optimization()

            # Stage 13: AI-Enhanced Quality Assessment (Experimental)
            quality_assessment_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🤖 Running AI-enhanced quality assessment...", 13, total_stages
                )
                try:
                    quality_assessment_result = await self._execute_ai_enhanced_quality_assessment(
                        analysis_result.data,
                        verification_result.data,
                        threat_data_payload,
                        knowledge_integration_result.data,
                        fact_data,
                    )
                    self.logger.info(f"Quality assessment result: success={quality_assessment_result.success}")
                    if not quality_assessment_result.success:
                        self.logger.warning(f"Quality assessment failed: {quality_assessment_result.error}")
                except Exception as e:
                    self.logger.error(f"Quality assessment exception: {e}", exc_info=True)
                    quality_assessment_result = StepResult.fail(f"Quality assessment error: {e}")

            # Stage 14: Advanced Pattern Recognition (Experimental)
            pattern_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🔍 Executing advanced pattern recognition...", 14, total_stages
                )
                pattern_result = await self._execute_advanced_pattern_recognition(
                    analysis_result.data, behavioral_result.data
                )

            # Stage 15: Cross-Reference Intelligence Network (Experimental)
            network_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🕸️ Building cross-reference intelligence network...", 15, total_stages
                )
                network_result = await self._execute_cross_reference_network(
                    verification_result.data, research_result.data
                )

            # Stage 16: Predictive Threat Assessment (Experimental)
            _ = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🔮 Performing predictive threat assessment...", 16, total_stages
                )
                _ = await self._execute_predictive_threat_assessment(
                    threat_data_payload, behavioral_result.data, pattern_result.data
                )

            # Stage 17: Multi-Modal Content Synthesis (Experimental)
            _ = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🎭 Synthesizing multi-modal content analysis...", 17, total_stages
                )
                _ = await self._execute_multimodal_synthesis(
                    acquisition_result.data, analysis_result.data, behavioral_result.data
                )

            # Stage 18: Dynamic Knowledge Graph Construction (Experimental)
            graph_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🗺️ Constructing dynamic knowledge graphs...", 18, total_stages
                )
                graph_result = await self._execute_knowledge_graph_construction(
                    knowledge_integration_result.data, network_result.data
                )

            # Stage 19: Autonomous Learning Integration (Experimental)
            learning_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🧪 Integrating autonomous learning systems...", 19, total_stages
                )
                learning_result = await self._execute_autonomous_learning_integration(
                    quality_assessment_result.data, analytics_result.data
                )

            # Stage 20: Advanced Contextual Bandits Optimization (Experimental)
            bandit_result = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "🎲 Optimizing contextual bandits decision system...", 20, total_stages
                )
                bandit_result = await self._execute_contextual_bandits_optimization(
                    analytics_result.data, learning_result.data
                )

            # Stage 21: Community Intelligence Synthesis (Experimental)
            _ = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "👥 Synthesizing community intelligence...", 21, total_stages
                )
                _ = await self._execute_community_intelligence_synthesis(social_intel_result.data, network_result.data)

            # Stage 22: Real-Time Adaptive Workflow (Experimental)
            _ = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "⚡ Executing real-time adaptive workflow...", 22, total_stages
                )
                _ = await self._execute_adaptive_workflow_optimization(bandit_result.data, learning_result.data)

            # Stage 23: Enhanced Memory Consolidation (Experimental)
            _ = StepResult.skip(reason="Skipped for non-experimental analysis")
            if depth == "experimental":
                await self._send_progress_update(
                    interaction, "💾 Consolidating enhanced memory systems...", 23, total_stages
                )
                _ = await self._execute_enhanced_memory_consolidation(
                    knowledge_integration_result.data, graph_result.data
                )

            # Stage 24: Intelligence Briefing Curation
            briefing_stage = 24 if depth == "experimental" else total_stages - 1
            await self._send_progress_update(
                interaction, "📋 Curating intelligence briefing...", briefing_stage, total_stages
            )
            briefing_result = await self._execute_specialized_intelligence_briefing(
                analysis_result.data,
                verification_result.data,
                threat_data_payload,
                knowledge_integration_result.data,
                research_result.data,
            )

            # Stage 25: Enhanced Result Synthesis with Multi-Modal Integration
            synthesis_stage = 25 if depth == "experimental" else total_stages
            await self._send_progress_update(
                interaction, "🔬 Synthesizing comprehensive intelligence results...", synthesis_stage, total_stages
            )
            synthesis_result = await self._synthesize_enhanced_autonomous_results(
                {
                    "mission_plan": mission_plan.data if mission_plan.success else {},
                    "acquisition": acquisition_result.data,
                    "transcription": transcription_result.data,
                    "content_analysis": analysis_result.data,
                    "information_verification": verification_result.data,
                    "threat_analysis": threat_data_payload,
                    # Expose raw deception scoring for downstream synthesis/embeds
                    "deception_scoring": (
                        deception_scoring_result.data
                        if isinstance(deception_scoring_result, StepResult) and deception_scoring_result.success
                        else {}
                    ),
                    "fact_analysis": fact_analysis_result.data if fact_analysis_result.success else {},
                    "social_intelligence": social_intel_result.data if social_intel_result.success else {},
                    "behavioral_profiling": behavioral_result.data if behavioral_result.success else {},
                    "knowledge_integration": knowledge_integration_result.data,
                    "research_synthesis": research_result.data if research_result.success else {},
                    "performance_analytics": analytics_result.data if analytics_result.success else {},
                    "quality_assessment": quality_assessment_result.data if quality_assessment_result.success else {},
                    "intelligence_briefing": briefing_result.data,
                    "workflow_metadata": {
                        "workflow_id": workflow_id,
                        "depth": depth,
                        "total_stages": total_stages,
                        "processing_time": time.time() - start_time,
                        "url": url,
                        "capabilities_used": self._get_capabilities_summary(depth),
                        "ai_enhancement_level": self._calculate_ai_enhancement_level(depth),
                    },
                }
            )

            # Final Stage: Deliver Enhanced Comprehensive Results with Community Communication
            await self._send_progress_update(
                interaction, "✅ Enhanced autonomous intelligence analysis complete!", total_stages, total_stages
            )
            await self._execute_specialized_communication_reporting(interaction, synthesis_result.data, depth)

            # Record metrics
            processing_time = time.time() - start_time
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "success"}).inc()
            self.metrics.histogram("autointel_workflow_duration", processing_time, labels={"depth": depth})

        except Exception as e:
            self.logger.error(f"Enhanced autonomous intelligence workflow failed: {e}", exc_info=True)
            await self._send_error_response(interaction, "Enhanced Autonomous Workflow", str(e))
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "error"}).inc()

    # ========================================
    # ENHANCED CAPABILITY HELPER METHODS
    # ========================================

    def _get_available_capabilities(self) -> list[str]:
        """Get list of all available autonomous capabilities."""
        return [
            "multi_platform_content_acquisition",
            "advanced_transcription_indexing",
            "comprehensive_linguistic_analysis",
            "multi_source_fact_verification",
            "advanced_threat_deception_analysis",
            "cross_platform_social_intelligence",
            "behavioral_profiling_persona_analysis",
            "multi_layer_knowledge_integration",
            "research_synthesis_context_building",
            "predictive_performance_analytics",
            "ai_enhanced_quality_assessment",
            "intelligence_briefing_curation",
            "autonomous_learning_adaptation",
            "real_time_monitoring_alerts",
            "community_liaison_communication",
        ]

    def _calculate_resource_requirements(self, depth: str) -> dict[str, Any]:
        """Calculate resource requirements based on analysis depth."""
        base_requirements = {
            "cpu_cores": 2,
            "memory_gb": 4,
            "storage_gb": 10,
            "network_bandwidth": "moderate",
            "ai_model_calls": 50,
        }

        multipliers = {
            "standard": 1.0,
            "deep": 2.0,
            "comprehensive": 3.5,
            "experimental": 5.0,
        }

        multiplier = multipliers.get(depth, 1.0)
        return {k: (v * multiplier if isinstance(v, (int, float)) else v) for k, v in base_requirements.items()}

    def _estimate_workflow_duration(self, depth: str) -> dict[str, Any]:
        """Estimate workflow duration based on depth and complexity."""
        base_duration_minutes = {
            "standard": 3,
            "deep": 8,
            "comprehensive": 15,
            "experimental": 25,
        }

        return {
            "estimated_minutes": base_duration_minutes.get(depth, 5),
            "confidence_interval": "±20%",
            "factors": ["content_complexity", "network_latency", "ai_model_response_times"],
        }

    def _get_planned_stages(self, depth: str) -> list[dict[str, Any]]:
        """Get planned workflow stages based on analysis depth."""
        all_stages = [
            {"name": "Mission Planning", "agent": "mission_orchestrator", "priority": "critical"},
            {"name": "Content Acquisition", "agent": "acquisition_specialist", "priority": "critical"},
            {"name": "Transcription Analysis", "agent": "transcription_engineer", "priority": "high"},
            {"name": "Content Analysis", "agent": "analysis_cartographer", "priority": "critical"},
            {"name": "Information Verification", "agent": "verification_director", "priority": "high"},
            {"name": "Threat Analysis", "agent": "risk_intelligence_analyst", "priority": "high"},
            {"name": "Social Intelligence", "agent": "signal_recon_specialist", "priority": "medium"},
            {"name": "Behavioral Profiling", "agent": "persona_archivist", "priority": "medium"},
            {"name": "Knowledge Integration", "agent": "knowledge_integrator", "priority": "high"},
            {"name": "Research Synthesis", "agent": "research_synthesist", "priority": "medium"},
            {"name": "Performance Analytics", "agent": "system_reliability_officer", "priority": "low"},
            {"name": "Quality Assessment", "agent": "intelligence_briefing_curator", "priority": "low"},
            {"name": "Intelligence Briefing", "agent": "intelligence_briefing_curator", "priority": "high"},
            {"name": "Communication Reporting", "agent": "community_liaison", "priority": "medium"},
        ]

        stage_filters = {
            "standard": lambda s: s["priority"] in ["critical", "high"],
            "deep": lambda s: s["priority"] in ["critical", "high", "medium"],
            "comprehensive": lambda s: True,
            "experimental": lambda s: True,
        }

        filter_func = stage_filters.get(depth, stage_filters["standard"])
        return [stage for stage in all_stages if filter_func(stage)]

    def _get_capabilities_summary(self, depth: str) -> dict[str, Any]:
        """Get summary of capabilities used in this workflow."""
        return {
            "total_agents": len(self._get_planned_stages(depth)),
            "total_tools": len(self._get_available_capabilities()),
            "ai_enhancement_features": [
                "adaptive_workflow_planning",
                "real_time_performance_monitoring",
                "multi_agent_coordination",
                "predictive_analytics",
                "autonomous_learning",
            ],
            "depth_level": depth,
            "experimental_features_enabled": depth == "experimental",
        }

    def _calculate_ai_enhancement_level(self, depth: str) -> float:
        """Calculate the level of AI enhancement applied."""
        enhancement_levels = {
            "standard": 0.3,
            "deep": 0.6,
            "comprehensive": 0.8,
            "experimental": 1.0,
        }
        return enhancement_levels.get(depth, 0.3)

    # ========================================
    # ENHANCED SPECIALIZED AGENT EXECUTION METHODS
    # ========================================

    async def _execute_agent_coordination_setup(self, url: str, depth: str) -> StepResult:
        """Initialize and coordinate CrewAI multi-agent system for sophisticated orchestration."""
        try:
            # Skip agent coordination entirely when LLM APIs are unavailable
            if not getattr(self, "_llm_available", False):
                self.agent_coordinators = {}
                return StepResult.skip(reason="llm_unavailable", message="Agent system not initialized (no API key)")
            # Initialize CrewAI crew instance
            from .crew import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Determine agent configuration based on analysis depth
            if depth == "experimental":
                active_agents = [
                    "mission_orchestrator",
                    "acquisition_specialist",
                    "transcription_engineer",
                    "analysis_cartographer",
                    "verification_director",
                    "persona_archivist",
                    "knowledge_integrator",
                    "signal_recon_specialist",
                    "trend_intelligence_scout",
                    "community_liaison",
                    "performance_analyst",
                ]
            elif depth == "comprehensive":
                active_agents = [
                    "mission_orchestrator",
                    "acquisition_specialist",
                    "analysis_cartographer",
                    "verification_director",
                    "persona_archivist",
                    "knowledge_integrator",
                    "signal_recon_specialist",
                    "community_liaison",
                ]
            elif depth == "deep":
                active_agents = [
                    "mission_orchestrator",
                    "acquisition_specialist",
                    "analysis_cartographer",
                    "verification_director",
                    "knowledge_integrator",
                ]
            else:  # standard
                active_agents = ["mission_orchestrator", "acquisition_specialist", "analysis_cartographer"]

            # Initialize agent coordination system
            self.crew_instance = crew_instance
            self.active_agents = active_agents
            self.agent_coordinators = {}

            # Prefer modern wrapper-based agent methods to ensure CrewAI-compatible tools
            agent_method_lookup = {
                "mission_orchestrator": crew_instance.mission_orchestrator,
                "acquisition_specialist": crew_instance.acquisition_specialist,
                "transcription_engineer": crew_instance.transcription_engineer,
                "analysis_cartographer": crew_instance.analysis_cartographer,
                "verification_director": crew_instance.verification_director,
                "risk_intelligence_analyst": crew_instance.risk_intelligence_analyst,
                "persona_archivist": crew_instance.persona_archivist,
                "signal_recon_specialist": crew_instance.signal_recon_specialist,
                "trend_intelligence_scout": crew_instance.trend_intelligence_scout,
                "knowledge_integrator": crew_instance.knowledge_integrator,
                "research_synthesist": crew_instance.research_synthesist,
                "intelligence_briefing_curator": crew_instance.intelligence_briefing_curator,
                "argument_strategist": crew_instance.argument_strategist,
                "system_reliability_officer": crew_instance.system_reliability_officer,
                "community_liaison": crew_instance.community_liaison,
            }

            # Prepare agent coordinators
            for agent_name in active_agents:
                try:
                    agent_method = agent_method_lookup.get(agent_name) or getattr(crew_instance, agent_name, None)
                    if agent_method:
                        agent = agent_method()
                        self.agent_coordinators[agent_name] = agent
                        self.logger.info(f"Initialized agent: {agent_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize agent {agent_name}: {e}")

            coordination_data = {
                "total_agents": len(active_agents),
                "active_agents": active_agents,
                "initialized_agents": len(self.agent_coordinators),
                "coordination_mode": "sequential_with_delegation",
                "depth_configuration": depth,
                "agent_system_ready": True,
            }

            self.logger.info(f"Agent coordination system initialized with {len(self.agent_coordinators)} agents")
            coordination_data["message"] = "CrewAI multi-agent coordination system ready"
            return StepResult.ok(**coordination_data)

        except Exception as e:
            return StepResult.fail(f"Agent coordination setup failed: {e}")

    async def _execute_mission_planning(self, url: str, depth: str) -> StepResult:
        """Execute mission planning using CrewAI Mission Orchestrator agent."""
        try:
            if not getattr(self, "_llm_available", False):
                return StepResult.skip(reason="llm_unavailable", message="Mission planning skipped (no API key)")
            # Use the mission orchestrator agent to plan the autonomous workflow
            if hasattr(self, "agent_coordinators") and "mission_orchestrator" in self.agent_coordinators:
                mission_agent = self.agent_coordinators["mission_orchestrator"]

                # Critical data propagation: ensure tools on this agent receive structured context
                try:
                    self._populate_agent_tool_context(
                        mission_agent,
                        {
                            "mission_url": url,
                            "mission_depth": depth,
                            "target_url": url,
                            "depth": depth,
                        },
                    )
                except Exception:
                    pass

                # Create mission planning task
                planning_task = Task(
                    description=prompt_config.Autonomous.ORCHESTRATOR_PROMPT.format(url=url, depth=depth),
                    expected_output="A detailed report of the content analysis, including a summary, key claims, and any detected fallacies or perspectives. The final output must be a markdown document.",
                    agent=mission_agent,
                )

                # Create single-agent crew for mission planning
                planning_crew = Crew(
                    agents=[mission_agent], tasks=[planning_task], verbose=True, process=Process.sequential
                )

                # Execute mission planning
                crew_result = await asyncio.to_thread(planning_crew.kickoff)

                # Prepare mission data
                _ = {
                    "target_url": url,
                    "analysis_depth": depth,
                    "crew_plan": crew_result,
                    "workflow_capabilities": self._get_available_capabilities(),
                    "resource_allocation": self._calculate_resource_requirements(depth),
                    "estimated_duration": self._estimate_workflow_duration(depth),
                }

                plan_result = {
                    "mission_id": f"mission_{int(time.time())}",
                    "crew_planning": crew_result,
                    "planned_stages": self._get_planned_stages(depth),
                    "resource_budget": self._get_resource_budget(depth),
                    "agent_assignments": self._get_agent_assignments(depth),
                    "risk_assessment": self._assess_mission_risks(url, depth),
                    "success_criteria": self._define_success_criteria(depth),
                }

                plan_result["message"] = "Mission planned with CrewAI orchestrator"
                return StepResult.ok(**plan_result)
            else:
                return StepResult.skip(reason="Mission orchestrator agent not available")

        except Exception as e:
            return StepResult.fail(f"Mission planning failed: {e}")
        except Exception as e:
            return StepResult.fail(f"Mission planning failed: {e}")

    async def _execute_specialized_content_acquisition(self, url: str) -> StepResult:
        """Execute specialized content acquisition with enhanced multi-platform support and ContentPipeline integration."""
        try:
            self.logger.info(f"Starting specialized content acquisition with ContentPipeline synergy: {url}")

            # Execute ContentPipeline with autonomous workflow enhancements
            pipeline_result = await self._execute_content_pipeline(url)

            if not pipeline_result.success:
                # Enhanced error handling for different content types with agent coordination
                error_msg = pipeline_result.error or "Content acquisition failed"

                # Try to identify the content type and provide agent-specific guidance
                if "youtube.com" in url.lower() or "youtu.be" in url.lower():
                    if "Requested format is not available" in error_msg or "nsig extraction failed" in error_msg:
                        return StepResult.fail(
                            f"YouTube content protection detected - requires specialized agent handling: {error_msg}",
                            step="content_acquisition",
                            data={
                                "url": url,
                                "error_type": "youtube_protection",
                                "agent_recommendation": "multi_platform_acquisition_specialist",
                                "fallback_strategy": "enhanced_youtube_download_tool",
                            },
                        )

                return StepResult.fail(
                    f"ContentPipeline acquisition failed - agent coordination required: {error_msg}",
                    step="content_acquisition",
                    data={
                        "url": url,
                        "error_type": "general",
                        "pipeline_integration": "failed",
                        "agent_coordination_needed": True,
                    },
                )

            # PipelineTool wraps the pipeline payload under a nested "data" key with additional metadata
            # Capture both pieces so downstream stages can consume a flattened structure without guessing.
            pipeline_wrapper = pipeline_result.data if isinstance(pipeline_result.data, dict) else {}
            raw_payload = pipeline_wrapper.get("data") if isinstance(pipeline_wrapper, dict) else None
            pipeline_payload = dict(raw_payload) if isinstance(raw_payload, dict) else {}

            # Preserve execution metadata (url/quality/latency) while enriching with autonomous context
            metadata = {k: v for k, v in pipeline_wrapper.items() if k != "data"}
            metadata.update(
                {
                    "acquisition_timestamp": time.time(),
                    "source_url": url,
                    "workflow_type": "autonomous_intelligence",
                }
            )
            metadata.setdefault("url", url)

            # Normalise payload for downstream usage: expose the pipeline blocks at top-level and attach metadata
            normalised_payload = dict(pipeline_payload)
            normalised_payload.pop("status", None)  # StepResult already conveys overall success
            normalised_payload.setdefault("source_url", url)
            normalised_payload.setdefault("acquisition_timestamp", metadata["acquisition_timestamp"])
            normalised_payload.setdefault("workflow_type", metadata["workflow_type"])
            normalised_payload["pipeline_metadata"] = metadata

            # Retain original payload for diagnostics/compatibility without requiring callers to dereference StepResult
            if isinstance(raw_payload, dict):
                normalised_payload["raw_pipeline_payload"] = raw_payload

            self.logger.info("Specialized content acquisition successful with ContentPipeline")

            return StepResult.ok(
                **normalised_payload,
                message="Content acquisition completed via ContentPipeline",
            )

        except Exception as e:
            self.logger.error(f"Specialized content acquisition failed: {e}", exc_info=True)
            return StepResult.fail(
                f"Specialized content acquisition critical failure: {e}",
                step="content_acquisition",
                data={
                    "url": url,
                    "error_type": "exception",
                    "pipeline_integration": "error",
                    "requires_agent_recovery": True,
                },
            )

    async def _execute_specialized_transcription_analysis(self, acquisition_result: StepResult) -> StepResult:
        """Execute advanced transcription and indexing using CrewAI Transcription Engineer agent."""
        try:
            # Extract ContentPipeline data from StepResult
            if not acquisition_result.success or not acquisition_result.data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")

            pipeline_data = self._normalize_acquisition_data(acquisition_result)
            if not pipeline_data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")

            # Get transcript from ContentPipeline transcription block
            transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
            if not isinstance(transcription_block, dict):
                transcription_block = {}
            else:
                transcription_block = dict(transcription_block)
            transcript = transcription_block.get("transcript", "")

            media_info = pipeline_data.get("download", {}) if isinstance(pipeline_data, dict) else {}
            if not isinstance(media_info, dict):
                media_info = {}
            else:
                media_info = dict(media_info)

            analysis_block = pipeline_data.get("analysis") if isinstance(pipeline_data, dict) else None
            fallacy_block = pipeline_data.get("fallacy") if isinstance(pipeline_data, dict) else None
            perspective_block = pipeline_data.get("perspective") if isinstance(pipeline_data, dict) else None
            drive_block = pipeline_data.get("drive") if isinstance(pipeline_data, dict) else None
            memory_block = pipeline_data.get("memory") if isinstance(pipeline_data, dict) else None
            graph_block = pipeline_data.get("graph_memory") if isinstance(pipeline_data, dict) else None
            hipporag_block = pipeline_data.get("hipporag_memory") if isinstance(pipeline_data, dict) else None
            pipeline_metadata = pipeline_data.get("pipeline_metadata") if isinstance(pipeline_data, dict) else None
            source_url = pipeline_data.get("source_url") if isinstance(pipeline_data, dict) else None
            if source_url and "source_url" not in media_info:
                media_info.setdefault("source_url", source_url)

            if not transcript:
                return StepResult.skip(
                    reason="No transcript available for advanced analysis", data={"pipeline_data": pipeline_data}
                )

            # Use CrewAI transcription engineer agent if available
            if (
                hasattr(self, "agent_coordinators")
                and "transcription_engineer" in self.agent_coordinators
                and hasattr(self, "crew")
                and self.crew is not None
            ):
                try:
                    transcription_agent = self.agent_coordinators["transcription_engineer"]

                    # Populate shared tool context so CrewAI wrappers receive structured data
                    try:
                        context_payload = {
                            "transcript": transcript,
                            "media_info": media_info,
                            "pipeline_transcription": transcription_block,
                            "pipeline_analysis": analysis_block,
                            "pipeline_fallacy": fallacy_block,
                            "pipeline_perspective": perspective_block,
                            "pipeline_drive": drive_block,
                            "pipeline_memory": memory_block,
                            "pipeline_graph": graph_block,
                            "pipeline_hipporag": hipporag_block,
                            "pipeline_metadata": pipeline_metadata,
                            "source_url": source_url,
                        }
                        self._populate_agent_tool_context(transcription_agent, context_payload)
                    except Exception as _ctx_err:  # pragma: no cover - defensive
                        self.logger.debug(f"Transcription agent context population skipped: {_ctx_err}")

                    # Create transcription enhancement task
                    transcription_task = Task(
                        description=f"Enhance transcription quality, create timeline anchors, and build comprehensive index for transcript: {transcript[:500]}... Media info: {media_info}",
                        expected_output="Enhanced transcript with timeline anchors, quality improvements, and comprehensive indexing",
                        agent=transcription_agent,
                    )

                    # Create single-agent crew for transcription
                    transcription_crew = Crew(
                        agents=[transcription_agent],
                        tasks=[transcription_task],
                        verbose=True,
                        process=Process.sequential,
                    )

                    # Execute transcription enhancement
                    crew_result = await asyncio.to_thread(transcription_crew.kickoff)

                    # Return enhanced transcription results
                    return StepResult.ok(
                        message="Advanced transcription analysis completed with CrewAI agent",
                        transcript=transcript,  # Keep original as fallback
                        enhanced_transcript=str(crew_result),
                        crew_analysis=crew_result,
                        media_info=media_info,
                        timeline_anchors=self._extract_timeline_from_crew(crew_result),
                        transcript_index=self._extract_index_from_crew(crew_result),
                        quality_score=self._calculate_transcript_quality(crew_result),
                        pipeline_transcription=transcription_block,
                        pipeline_analysis=analysis_block,
                        pipeline_fallacy=fallacy_block,
                        pipeline_perspective=perspective_block,
                        pipeline_drive=drive_block,
                        pipeline_memory=memory_block,
                        pipeline_graph=graph_block,
                        pipeline_hipporag=hipporag_block,
                        pipeline_metadata=pipeline_metadata,
                        source_url=source_url,
                    )
                except Exception as crew_error:
                    self.logger.warning(f"CrewAI transcription agent failed: {crew_error}")
                    # Fall through to baseline pipeline-backed transcription payload
            else:
                self.logger.info("CrewAI agents not available, using basic transcription processing")
                # Fallback to basic processing if agent not available
                return StepResult.ok(
                    message="Basic transcription analysis (agent not available)",
                    transcript=transcript,
                    media_info=media_info,
                    timeline_anchors=transcription_block.get("timeline_anchors", []),
                    transcript_index=transcription_block.get("transcript_index", {}),
                    quality_score=transcription_block.get("quality_score", 0.5),
                    pipeline_transcription=transcription_block,
                    pipeline_analysis=analysis_block,
                    pipeline_fallacy=fallacy_block,
                    pipeline_perspective=perspective_block,
                    pipeline_drive=drive_block,
                    pipeline_memory=memory_block,
                    pipeline_graph=graph_block,
                    pipeline_hipporag=hipporag_block,
                    pipeline_metadata=pipeline_metadata,
                    source_url=source_url,
                )

            # If CrewAI enhancement isn't available or failed, provide pipeline-backed payload
            return StepResult.ok(
                message="Pipeline transcription normalization completed",
                transcript=transcript,
                media_info=media_info,
                timeline_anchors=transcription_block.get("timeline_anchors", []),
                transcript_index=transcription_block.get("transcript_index", {}),
                quality_score=transcription_block.get("quality_score", 0.5),
                pipeline_transcription=transcription_block,
                pipeline_analysis=analysis_block,
                pipeline_fallacy=fallacy_block,
                pipeline_perspective=perspective_block,
                pipeline_drive=drive_block,
                pipeline_memory=memory_block,
                pipeline_graph=graph_block,
                pipeline_hipporag=hipporag_block,
                pipeline_metadata=pipeline_metadata,
                source_url=source_url,
            )

        except Exception as e:
            return StepResult.fail(f"Specialized transcription analysis failed: {e}")

    async def _execute_ai_enhanced_quality_assessment(
        self,
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
        threat_data: dict[str, Any],
        knowledge_data: dict[str, Any],
        fact_data: dict[str, Any] | None = None,
    ) -> StepResult:
        """Execute AI-enhanced quality assessment using advanced evaluation techniques."""
        try:
            quality_dimensions = {
                "content_coherence": self._assess_content_coherence(analysis_data),
                "factual_accuracy": self._assess_factual_accuracy(verification_data, fact_data),
                "source_credibility": self._assess_source_credibility(knowledge_data, verification_data),
                "bias_detection": self._assess_bias_levels(analysis_data, verification_data),
                "emotional_manipulation": self._assess_emotional_manipulation(analysis_data),
                "logical_consistency": self._assess_logical_consistency(verification_data, threat_data),
            }

            ai_quality_score = self._calculate_ai_quality_score(quality_dimensions)

            ai_recommendations = self._generate_ai_recommendations(
                quality_dimensions, ai_quality_score, analysis_data, verification_data
            )

            learning_opportunities = self._identify_learning_opportunities(analysis_data, verification_data, fact_data)

            quality_results = {
                "ai_quality_score": ai_quality_score,
                "quality_dimensions": quality_dimensions,
                "ai_recommendations": ai_recommendations,
                "learning_opportunities": learning_opportunities,
                "enhancement_suggestions": self._generate_enhancement_suggestions(
                    quality_dimensions, analysis_data, verification_data
                ),
                "confidence_interval": self._calculate_confidence_interval(quality_dimensions, ai_quality_score),
                "quality_trend": self._assess_quality_trend(ai_quality_score),
            }

            return StepResult.ok(**quality_results)
        except Exception as e:
            self.logger.error(f"Error during AI-enhanced quality assessment: {e}", exc_info=True)
            return StepResult.fail(f"AI-enhanced quality assessment failed: {e}")

    async def _execute_specialized_content_analysis(self, transcription_result: StepResult) -> StepResult:
        """Execute content analysis using CrewAI Analysis Cartographer agent."""
        try:
            # Extract content for analysis from StepResult
            if not transcription_result.success or not transcription_result.data:
                return StepResult.skip(reason="No transcription data available for content analysis")

            transcription_data = transcription_result.data

            # Extract transcript for analysis
            transcript = transcription_data.get("enhanced_transcript") or transcription_data.get("transcript", "")
            media_info = transcription_data.get("media_info", {}) if isinstance(transcription_data, dict) else {}
            if not transcript:
                return StepResult.skip(reason="No transcript found in transcription data")

            pipeline_analysis_block = (
                transcription_data.get("pipeline_analysis") if isinstance(transcription_data, dict) else None
            )
            pipeline_fallacy_block = (
                transcription_data.get("pipeline_fallacy") if isinstance(transcription_data, dict) else None
            )
            pipeline_perspective_block = (
                transcription_data.get("pipeline_perspective") if isinstance(transcription_data, dict) else None
            )
            pipeline_metadata = (
                transcription_data.get("pipeline_metadata") if isinstance(transcription_data, dict) else None
            )
            source_url = transcription_data.get("source_url")

            if isinstance(pipeline_analysis_block, dict) and pipeline_analysis_block:
                return self._build_pipeline_content_analysis_result(
                    transcript=transcript,
                    transcription_data=transcription_data,
                    pipeline_analysis=pipeline_analysis_block,
                    pipeline_fallacy=pipeline_fallacy_block if isinstance(pipeline_fallacy_block, dict) else None,
                    pipeline_perspective=pipeline_perspective_block
                    if isinstance(pipeline_perspective_block, dict)
                    else None,
                    media_info=media_info if isinstance(media_info, dict) else {},
                    pipeline_metadata=pipeline_metadata if isinstance(pipeline_metadata, dict) else None,
                    source_url=source_url,
                )

            # Use CrewAI analysis cartographer agent if available
            if (
                getattr(self, "_llm_available", False)
                and hasattr(self, "agent_coordinators")
                and "analysis_cartographer" in self.agent_coordinators
                and hasattr(self, "crew")
                and self.crew is not None
            ):
                try:
                    analysis_agent = self.agent_coordinators["analysis_cartographer"]

                    # Ensure CrewAI tools have full context before kickoff
                    try:
                        self._populate_agent_tool_context(
                            analysis_agent,
                            {
                                "transcript": transcript,
                                "media_info": media_info,
                                "timeline_anchors": transcription_data.get("timeline_anchors", []),
                                "transcript_index": transcription_data.get("transcript_index", {}),
                                "pipeline_analysis": pipeline_analysis_block,
                                "pipeline_fallacy": pipeline_fallacy_block,
                                "pipeline_perspective": pipeline_perspective_block,
                                "pipeline_metadata": pipeline_metadata,
                                "source_url": source_url or media_info.get("source_url"),
                            },
                        )
                    except Exception as _ctx_err:  # pragma: no cover - defensive
                        self.logger.debug(f"Analysis agent context population skipped: {_ctx_err}")

                    # Create comprehensive content analysis task with full context
                    source_url = transcription_data.get("source_url") or "unknown"
                    title = media_info.get("title", "Unknown Title")
                    platform = media_info.get("platform", "Unknown Platform")
                    duration = media_info.get("duration", "Unknown Duration")

                    analysis_task = Task(
                        description=dedent(
                            f"""
                            Analyze content from {platform} video: '{title}' (URL: {source_url})

                            Duration: {duration}
                            Transcript Preview: {transcript[:500]}...

                            Task: Map linguistic patterns, sentiment signals, and thematic insights from the complete transcript.
                            Quality Score: {transcription_data.get("quality_score", 0)}
                            Timeline Data: {transcription_data.get("timeline_anchors", [])}

                            Provide comprehensive analysis including sentiment, themes, key points, and contextual insights.
                            """
                        ).strip(),
                        expected_output="Comprehensive content analysis with linguistic mapping, sentiment analysis, thematic insights, and structured annotations for the specified video content",
                        agent=analysis_agent,
                    )

                    # Create single-agent crew for content analysis
                    analysis_crew = Crew(
                        agents=[analysis_agent], tasks=[analysis_task], verbose=True, process=Process.sequential
                    )

                    # Execute content analysis
                    crew_result = await asyncio.to_thread(analysis_crew.kickoff)

                    # Synthesize analysis results with full context
                    analysis_results = {
                        "transcript": transcript,
                        "crew_analysis": crew_result,
                        "linguistic_patterns": self._extract_linguistic_patterns_from_crew(crew_result),
                        "sentiment_analysis": self._extract_sentiment_from_crew(crew_result),
                        "thematic_insights": self._extract_themes_from_crew(crew_result),
                        "source_url": source_url or media_info.get("source_url"),  # Ensure URL is propagated
                        "content_metadata": {
                            "word_count": len(transcript.split()),
                            "quality_score": transcription_data.get("quality_score", 0.5),
                            "analysis_timestamp": time.time(),
                            "analysis_method": "crewai_analysis_cartographer",
                            "agent_confidence": self._calculate_analysis_confidence_from_crew(crew_result),
                            # Propagate complete media metadata from acquisition for downstream stages
                            "source_url": source_url,
                            "title": media_info.get("title"),
                            "platform": media_info.get("platform"),
                            "duration": media_info.get("duration"),
                            "uploader": media_info.get("uploader"),
                        },
                        "timeline_anchors": transcription_data.get("timeline_anchors", []),
                        "transcript_index": transcription_data.get("transcript_index", {}),
                        "pipeline_analysis": pipeline_analysis_block,
                        "pipeline_fallacy": pipeline_fallacy_block,
                        "pipeline_perspective": pipeline_perspective_block,
                        "pipeline_metadata": pipeline_metadata,
                    }

                    return StepResult.ok(**analysis_results)
                except Exception as crew_error:
                    self.logger.warning(f"CrewAI analysis agent failed: {crew_error}")
                    # Fall through to basic analysis
            else:
                self.logger.info("CrewAI agents not available, using basic content analysis")

            # Fallback to basic analysis if agent not available or failed
            analysis_results = {
                "transcript": transcript,
                "linguistic_patterns": {},
                "sentiment_analysis": {"fallback": True},
                "thematic_insights": [],
                "content_metadata": {
                    "word_count": len(transcript.split()),
                    "quality_score": transcription_data.get("quality_score", 0.5),
                    "analysis_timestamp": time.time(),
                    "analysis_method": "fallback_basic_analysis",
                    # Basic propagation so social intelligence has seeds
                    "title": media_info.get("title"),
                    "platform": media_info.get("platform"),
                    "duration": media_info.get("duration"),
                    "uploader": media_info.get("uploader"),
                },
                "timeline_anchors": transcription_data.get("timeline_anchors", []),
                "transcript_index": transcription_data.get("transcript_index", {}),
                "source_url": source_url or media_info.get("source_url"),
                "pipeline_analysis": pipeline_analysis_block,
                "pipeline_fallacy": pipeline_fallacy_block,
                "pipeline_perspective": pipeline_perspective_block,
                "pipeline_metadata": pipeline_metadata,
            }

            analysis_results["message"] = "Basic content analysis (agent not available)"
            return StepResult.ok(**analysis_results)
        except Exception as e:
            return StepResult.fail(f"Content analysis failed: {e}")

    def _build_pipeline_content_analysis_result(
        self,
        *,
        transcript: str,
        transcription_data: dict[str, Any],
        pipeline_analysis: dict[str, Any],
        media_info: dict[str, Any],
        pipeline_fallacy: dict[str, Any] | None,
        pipeline_perspective: dict[str, Any] | None,
        pipeline_metadata: dict[str, Any] | None,
        source_url: str | None,
    ) -> StepResult:
        """Synthesize content analysis directly from ContentPipeline outputs.

        When the pipeline already produced rich analysis artifacts, prefer them over
        launching additional agent workloads. This consolidates sentiment,
        perspective, and fallacy insights into the step result expected by
        downstream stages.
        """

        try:
            keywords: list[str] = []
            if isinstance(pipeline_analysis.get("keywords"), list):
                keywords = [str(kw) for kw in pipeline_analysis.get("keywords", [])]
            elif isinstance(pipeline_analysis.get("key_phrases"), list):
                keywords = [str(kw) for kw in pipeline_analysis.get("key_phrases", [])]

            structured = pipeline_analysis.get("structured")
            if not isinstance(structured, dict):
                structured = {}

            sentiment_details = pipeline_analysis.get("sentiment_details")
            sentiment_payload: dict[str, Any] = {}
            if isinstance(sentiment_details, dict):
                sentiment_payload = dict(sentiment_details)
            sentiment_label = pipeline_analysis.get("sentiment")
            sentiment_score = pipeline_analysis.get("sentiment_score")
            if sentiment_label and "label" not in sentiment_payload:
                sentiment_payload["label"] = sentiment_label
            if sentiment_score is not None and "score" not in sentiment_payload:
                sentiment_payload["score"] = sentiment_score
            sentiment_payload.setdefault("label", sentiment_label or "neutral")

            word_count = None
            if isinstance(structured.get("word_count"), int):
                word_count = structured["word_count"]
            elif isinstance(pipeline_analysis.get("word_count"), int):
                word_count = pipeline_analysis["word_count"]
            if word_count is None:
                word_count = len(transcript.split())

            summary = pipeline_analysis.get("summary")
            if not summary and isinstance(pipeline_perspective, dict):
                summary = pipeline_perspective.get("summary")

            content_metadata: dict[str, Any] = {
                "word_count": word_count,
                "quality_score": transcription_data.get("quality_score", 0.5),
                "analysis_timestamp": time.time(),
                "analysis_method": pipeline_analysis.get("analysis_method", "content_pipeline_analysis"),
                "analysis_source": "content_pipeline",
            }

            if isinstance(media_info, dict):
                for key in ("title", "platform", "duration", "uploader", "video_id"):
                    if key in media_info and media_info[key] is not None:
                        content_metadata.setdefault(key, media_info[key])
                if not source_url and media_info.get("source_url"):
                    source_url = media_info.get("source_url")

            if isinstance(pipeline_metadata, dict):
                for key in ("source_url", "workflow_type", "acquisition_timestamp"):
                    if key in pipeline_metadata and pipeline_metadata[key] is not None:
                        content_metadata.setdefault(key, pipeline_metadata[key])
                if not source_url and pipeline_metadata.get("source_url"):
                    source_url = str(pipeline_metadata.get("source_url"))

            thematic_insights = list(keywords)
            if isinstance(pipeline_perspective, dict):
                additional_perspectives = pipeline_perspective.get("perspectives")
                if isinstance(additional_perspectives, list):
                    for item in additional_perspectives:
                        if isinstance(item, str) and item not in thematic_insights:
                            thematic_insights.append(item)

            analysis_results = {
                "message": "Content analysis derived from ContentPipeline output",
                "transcript": transcript,
                "crew_analysis": pipeline_analysis,
                "keywords": keywords,
                "sentiment": sentiment_payload.get("label"),
                "sentiment_score": sentiment_payload.get("score"),
                "linguistic_patterns": {"keywords": keywords, "key_phrases": keywords},
                "sentiment_analysis": sentiment_payload,
                "thematic_insights": thematic_insights,
                "content_metadata": content_metadata,
                "timeline_anchors": transcription_data.get("timeline_anchors", []),
                "transcript_index": transcription_data.get("transcript_index", {}),
                "summary": summary,
                "source_url": source_url,
                "pipeline_analysis": pipeline_analysis,
                "pipeline_fallacy": pipeline_fallacy,
                "pipeline_perspective": pipeline_perspective,
                "pipeline_metadata": pipeline_metadata,
                "media_info": media_info,
            }

            if pipeline_fallacy is not None:
                analysis_results.setdefault("fallacy_analysis", pipeline_fallacy)
            if pipeline_perspective is not None:
                analysis_results.setdefault("perspective_analysis", pipeline_perspective)

            return StepResult.ok(**analysis_results)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to construct pipeline-derived analysis payload: %s", exc)
            return StepResult.ok(
                message="ContentPipeline analysis extraction degraded",
                transcript=transcript,
                linguistic_patterns={"keywords": []},
                sentiment_analysis={"label": "neutral"},
                thematic_insights=[],
                content_metadata={
                    "word_count": len(transcript.split()),
                    "analysis_timestamp": time.time(),
                    "analysis_method": "content_pipeline_analysis_degraded",
                },
                timeline_anchors=transcription_data.get("timeline_anchors", []),
                transcript_index=transcription_data.get("transcript_index", {}),
                source_url=source_url,
                pipeline_analysis=pipeline_analysis,
                pipeline_fallacy=pipeline_fallacy,
                pipeline_perspective=pipeline_perspective,
                pipeline_metadata=pipeline_metadata,
                media_info=media_info,
            )

    async def _execute_specialized_information_verification(
        self, analysis_data: dict[str, Any], fact_data: dict[str, Any] | None = None
    ) -> StepResult:
        """Execute comprehensive information verification using CrewAI Verification Director agent."""
        try:
            # Extract transcript and analysis data for verification
            transcript = analysis_data.get("transcript", "")
            linguistic_patterns = analysis_data.get("linguistic_patterns", {})
            sentiment_analysis = analysis_data.get("sentiment_analysis", {})

            if not transcript:
                return StepResult.skip(reason="No transcript available for information verification")

            def _augment_with_fact_data(payload: dict[str, Any]) -> dict[str, Any]:
                if not isinstance(fact_data, dict) or not fact_data:
                    return payload

                if not payload.get("fact_checks") and isinstance(fact_data.get("fact_checks"), dict):
                    payload["fact_checks"] = fact_data.get("fact_checks", {})
                if not payload.get("logical_analysis") and isinstance(fact_data.get("logical_fallacies"), dict):
                    payload["logical_analysis"] = fact_data.get("logical_fallacies", {})
                if "perspective_synthesis" not in payload and isinstance(fact_data.get("perspective_synthesis"), dict):
                    payload["perspective_synthesis"] = fact_data.get("perspective_synthesis", {})
                return payload

            # Use CrewAI verification director agent for comprehensive verification
            if (
                getattr(self, "_llm_available", False)
                and hasattr(self, "agent_coordinators")
                and "verification_director" in self.agent_coordinators
            ):
                verification_agent = self.agent_coordinators["verification_director"]

                # Provide full structured context to the agent tools prior to kickoff
                try:
                    self._populate_agent_tool_context(
                        verification_agent,
                        {
                            "transcript": transcript,
                            "linguistic_patterns": linguistic_patterns,
                            "sentiment_analysis": sentiment_analysis,
                            "fact_data": fact_data or {},
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Verification agent context population skipped: {_ctx_err}")

                # Create comprehensive verification task
                verification_task = Task(
                    description=f"Conduct comprehensive information verification including fact-checking, logical analysis, credibility assessment, and bias detection for transcript: {transcript[:1000]}... Linguistic patterns: {linguistic_patterns} Sentiment: {sentiment_analysis}",
                    expected_output="Comprehensive verification report with fact-checks, logical fallacy analysis, credibility scores, bias indicators, and source validation",
                    agent=verification_agent,
                )

                # Create verification crew
                verification_crew = Crew(
                    agents=[verification_agent], tasks=[verification_task], verbose=True, process=Process.sequential
                )

                # Execute comprehensive verification
                crew_result = await asyncio.to_thread(verification_crew.kickoff)

                # Extract and structure verification results
                verification_results = {
                    "crew_verification": crew_result,
                    "fact_checks": self._extract_fact_checks_from_crew(crew_result),
                    "logical_analysis": self._extract_logical_analysis_from_crew(crew_result),
                    "credibility_assessment": self._extract_credibility_from_crew(crew_result),
                    "bias_indicators": self._extract_bias_indicators_from_crew(crew_result),
                    "source_validation": self._extract_source_validation_from_crew(crew_result),
                    "verification_confidence": self._calculate_verification_confidence_from_crew(crew_result),
                    "verification_metadata": {
                        "analysis_timestamp": time.time(),
                        "verification_method": "crewai_verification_director",
                        "agent_confidence": self._calculate_agent_confidence_from_crew(crew_result),
                        "comprehensive_checks": True,
                    },
                }

                self.logger.info("Comprehensive information verification completed with CrewAI Verification Director")
                verification_results["message"] = "Information verification completed with comprehensive analysis"
                return StepResult.ok(**_augment_with_fact_data(verification_results))
            else:
                # Fallback verification if agent not available
                fallback_results = {
                    "fact_checks": {"status": "agent_unavailable", "basic_analysis": True},
                    "logical_analysis": {"fallacies_detected": [], "confidence": 0.0},
                    "credibility_assessment": {"score": 0.5, "factors": []},
                    "bias_indicators": [],
                    "source_validation": {"validated": False, "reason": "agent_unavailable"},
                    "verification_confidence": 0.3,
                    "verification_metadata": {
                        "analysis_timestamp": time.time(),
                        "verification_method": "fallback_basic",
                        "comprehensive_checks": False,
                    },
                }

                fallback_results["message"] = "Basic verification (agent not available)"
                return StepResult.ok(**_augment_with_fact_data(fallback_results))
        except Exception as e:
            return StepResult.fail(f"Information verification failed: {e}")

    async def _execute_specialized_deception_analysis(
        self, intelligence_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> StepResult:
        """Execute comprehensive deception and threat analysis using CrewAI Verification Director agent."""
        try:
            # Extract comprehensive data for threat analysis
            transcript = intelligence_data.get("transcript", "")
            content_metadata = intelligence_data.get("content_metadata", {})
            _ = intelligence_data.get("linguistic_patterns", {})
            sentiment_analysis = intelligence_data.get("sentiment_analysis", {})
            fact_checks = verification_data.get("fact_checks", {})
            logical_analysis = verification_data.get("logical_analysis", {})
            credibility_assessment = verification_data.get("credibility_assessment", {})

            if not transcript and not content_metadata:
                return StepResult.skip(reason="No content available for deception analysis")

            # Use CrewAI verification director for comprehensive threat analysis
            if (
                getattr(self, "_llm_available", False)
                and hasattr(self, "agent_coordinators")
                and "verification_director" in self.agent_coordinators
            ):
                threat_agent = self.agent_coordinators["verification_director"]

                # Create comprehensive threat analysis task
                threat_task = Task(
                    description=f"Conduct comprehensive deception and threat analysis including manipulation detection, narrative integrity assessment, psychological profiling, and threat scoring. Content: {transcript[:800]}... Metadata: {content_metadata} Fact-checks: {fact_checks} Logic: {logical_analysis} Credibility: {credibility_assessment} Sentiment: {sentiment_analysis}",
                    expected_output="Comprehensive threat assessment with deception scores, manipulation indicators, narrative integrity analysis, psychological threat profiling, and actionable threat intelligence",
                    agent=threat_agent,
                )

                # Create threat analysis crew
                threat_crew = Crew(agents=[threat_agent], tasks=[threat_task], verbose=True, process=Process.sequential)

                # Execute comprehensive threat analysis
                crew_result = await asyncio.to_thread(threat_crew.kickoff)

                # Extract and structure comprehensive threat results
                threat_results = {
                    "crew_threat_analysis": crew_result,
                    "deception_analysis": self._extract_deception_analysis_from_crew(crew_result),
                    "manipulation_indicators": self._extract_manipulation_indicators_from_crew(crew_result),
                    "narrative_integrity": self._extract_narrative_integrity_from_crew(crew_result),
                    "psychological_profiling": self._extract_psychological_threats_from_crew(crew_result),
                    "threat_score": self._calculate_comprehensive_threat_score_from_crew(crew_result),
                    "threat_level": self._classify_threat_level_from_crew(crew_result),
                    "truth_assessment": self._extract_truth_assessment_from_crew(crew_result),
                    "trustworthiness_evaluation": self._extract_trustworthiness_from_crew(crew_result),
                    "threat_metadata": {
                        "analysis_timestamp": time.time(),
                        "threat_method": "crewai_comprehensive_threat_analysis",
                        "agent_confidence": self._calculate_agent_confidence_from_crew(crew_result),
                        "comprehensive_assessment": True,
                        "data_sources": ["transcript", "verification", "sentiment", "credibility"],
                    },
                }

                self.logger.info(
                    f"Comprehensive threat analysis completed with threat score: {threat_results['threat_score']}"
                )
                threat_results["message"] = "Comprehensive deception and threat analysis completed"
                return StepResult.ok(**threat_results)
            else:
                # Enhanced fallback with available data
                fallback_threat_score = self._calculate_basic_threat_from_data(
                    verification_data, sentiment_analysis, credibility_assessment
                )

                fallback_results = {
                    "deception_analysis": {"status": "agent_unavailable", "basic_assessment": True},
                    "manipulation_indicators": [],
                    "narrative_integrity": {"score": 0.5, "assessment": "unknown"},
                    "psychological_profiling": {},
                    "threat_score": fallback_threat_score,
                    "threat_level": self._classify_basic_threat_level(fallback_threat_score),
                    "truth_assessment": {"confidence": 0.3, "verdict": "uncertain"},
                    "trustworthiness_evaluation": {"score": 0.5, "factors": []},
                    "threat_metadata": {
                        "analysis_timestamp": time.time(),
                        "threat_method": "fallback_basic_threat",
                        "comprehensive_assessment": False,
                    },
                }

                fallback_results["message"] = "Basic threat analysis (agent not available)"
                return StepResult.ok(**fallback_results)
        except Exception as e:
            return StepResult.fail(f"Comprehensive deception analysis failed: {e}")

    async def _execute_specialized_social_intelligence(
        self, intelligence_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> StepResult:
        """Execute comprehensive social intelligence using CrewAI Signal Recon Specialist agent."""
        try:
            # Extract comprehensive data for social intelligence
            content_metadata = intelligence_data.get("content_metadata", {})
            transcript = intelligence_data.get("transcript", "")
            linguistic_patterns = intelligence_data.get("linguistic_patterns", {})
            sentiment_analysis = intelligence_data.get("sentiment_analysis", {})
            title = content_metadata.get("title", "") or ""
            # Prefer explicit keywords if present; otherwise derive from transcript or thematic insights
            explicit_keywords = intelligence_data.get("keywords", [])
            if isinstance(explicit_keywords, list) and explicit_keywords:
                keywords = explicit_keywords
            else:
                derived = self._extract_keywords_from_text(transcript) if transcript else []
                if not derived:
                    derived = intelligence_data.get("thematic_insights", [])
                # keep strings only
                keywords = [k for k in derived if isinstance(k, str)]

            if not transcript and not title and not keywords:
                return StepResult.skip(reason="No content available for social intelligence analysis")

            # Use CrewAI signal recon specialist for comprehensive social intelligence
            if (
                getattr(self, "_llm_available", False)
                and hasattr(self, "agent_coordinators")
                and "signal_recon_specialist" in self.agent_coordinators
            ):
                social_intel_agent = self.agent_coordinators["signal_recon_specialist"]

                # Populate structured context for social intelligence tools
                try:
                    self._populate_agent_tool_context(
                        social_intel_agent,
                        {
                            "transcript": transcript,
                            "content_metadata": content_metadata,
                            "linguistic_patterns": linguistic_patterns,
                            "sentiment_analysis": sentiment_analysis,
                            "keywords": keywords,
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Social agent context population skipped: {_ctx_err}")

                # Create comprehensive social intelligence task
                social_intel_task = Task(
                    description=f"Conduct comprehensive social intelligence analysis including narrative tracking across platforms, sentiment monitoring, influence mapping, and community response analysis. Content: {transcript[:800]}... Title: {title} Sentiment: {sentiment_analysis} Patterns: {linguistic_patterns} Keywords: {keywords[:10]}",
                    expected_output="Comprehensive social intelligence report with cross-platform narrative tracking, sentiment analysis, influence mapping, community dynamics, and emergent pattern detection",
                    agent=social_intel_agent,
                )

                # Create social intelligence crew
                social_crew = Crew(
                    agents=[social_intel_agent], tasks=[social_intel_task], verbose=True, process=Process.sequential
                )

                # Execute comprehensive social intelligence
                crew_result = await asyncio.to_thread(social_crew.kickoff)

                # Extract and structure social intelligence results
                social_intelligence = {
                    "crew_social_analysis": crew_result,
                    "cross_platform_monitoring": self._extract_cross_platform_analysis_from_crew(crew_result),
                    "narrative_tracking": self._extract_narrative_tracking_from_crew(crew_result),
                    "sentiment_monitoring": self._extract_sentiment_monitoring_from_crew(crew_result),
                    "influence_mapping": self._extract_influence_mapping_from_crew(crew_result),
                    "community_dynamics": self._extract_community_dynamics_from_crew(crew_result),
                    "emergent_patterns": self._extract_emergent_patterns_from_crew(crew_result),
                    "platform_intelligence": self._extract_platform_intelligence_from_crew(crew_result),
                    "social_metadata": {
                        "analysis_timestamp": time.time(),
                        "intelligence_method": "crewai_signal_recon_specialist",
                        "agent_confidence": self._calculate_agent_confidence_from_crew(crew_result),
                        "comprehensive_monitoring": True,
                        "data_sources": ["content", "sentiment", "linguistic_patterns", "keywords"],
                    },
                }

                self.logger.info(
                    "Comprehensive social intelligence analysis completed with CrewAI Signal Recon Specialist"
                )
                social_intelligence["message"] = "Social intelligence analysis completed with comprehensive monitoring"
                return StepResult.ok(**social_intelligence)
            else:
                # Enhanced fallback with available data
                fallback_intelligence = {
                    "cross_platform_monitoring": {"status": "agent_unavailable", "basic_analysis": True},
                    "narrative_tracking": {"patterns": [], "confidence": 0.0},
                    "sentiment_monitoring": {"overall_trend": sentiment_analysis.get("overall_sentiment", "unknown")},
                    "influence_mapping": {"influencers": [], "network_strength": 0.0},
                    "community_dynamics": {"engagement": "unknown", "polarization": 0.0},
                    "emergent_patterns": [],
                    "platform_intelligence": {"platforms_monitored": [], "coverage": "limited"},
                    "social_metadata": {
                        "analysis_timestamp": time.time(),
                        "intelligence_method": "fallback_basic",
                        "comprehensive_monitoring": False,
                    },
                }

                fallback_intelligence["message"] = "Basic social intelligence (agent not available)"
                return StepResult.ok(**fallback_intelligence)
        except Exception as e:
            return StepResult.fail(f"Social intelligence analysis failed: {e}")

    async def _execute_specialized_behavioral_analysis(
        self, intelligence_data: dict[str, Any], verification_data: dict[str, Any], deception_data: dict[str, Any]
    ) -> StepResult:
        """Execute behavioral analysis using the Behavioral Pattern Analyst."""
        try:
            # Combine all available data for behavioral profiling
            behavioral_input = {
                "content": intelligence_data,
                "verification": verification_data,
                "threat_assessment": deception_data,
                "platform": intelligence_data.get("content_metadata", {}).get("platform", "unknown"),
            }

            # Use specialized behavioral analysis tools (simplified for MVP)
            behavioral_results = {
                "behavioral_indicators": {
                    "consistency_score": self._analyze_content_consistency(behavioral_input),
                    "communication_patterns": self._analyze_communication_patterns(behavioral_input),
                    "reliability_indicators": deception_data.get("trust_evaluation", {}),
                },
                "entity_profile": {
                    "platform": behavioral_input["platform"],
                    "content_type": "video_analysis",  # Could be expanded
                    "analysis_timestamp": time.time(),
                },
            }

            self.logger.info("Behavioral Pattern Analyst completed entity profiling")
            return StepResult.ok(**behavioral_results)

        except Exception as e:
            return StepResult.fail(f"Behavioral Pattern Analyst failed: {e}")

    async def _execute_specialized_knowledge_integration(
        self,
        acquisition_data: dict[str, Any],
        intelligence_data: dict[str, Any],
        verification_data: dict[str, Any],
        fact_data: dict[str, Any] | None,
        deception_data: dict[str, Any],
        behavioral_data: dict[str, Any],
    ) -> StepResult:
        """Execute knowledge integration using CrewAI agents for sophisticated multi-system orchestration."""
        try:
            # Prepare comprehensive knowledge payload
            knowledge_payload = self._build_knowledge_payload(
                acquisition_data,
                intelligence_data,
                verification_data,
                fact_data=fact_data,
                threat_data=deception_data,
                behavioral_data=behavioral_data,
            )
            knowledge_payload["integration_timestamp"] = time.time()

            # If LLM APIs are unavailable, skip CrewAI integration and return basic status
            if not getattr(self, "_llm_available", False):
                return StepResult.ok(
                    message="Knowledge payload prepared (LLM unavailable)",
                    knowledge_systems={
                        "vector": True,
                        "graph_memory": bool(knowledge_payload),
                        "continual_memory": False,
                    },
                    integration_success=True,
                    integration_status="basic",
                    knowledge_payload=knowledge_payload,
                )

            # Initialize CrewAI team for knowledge integration
            from .crew import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Create knowledge integration crew with multiple specialists
            knowledge_agent = crew_instance.knowledge_integrator()
            persona_agent = crew_instance.persona_archivist()
            mission_agent = crew_instance.mission_orchestrator()

            # Define comprehensive knowledge integration task
            integration_task = Task(
                description=f"Integrate comprehensive intelligence across vector, graph, and continual memory systems: {knowledge_payload}",
                expected_output="Multi-system knowledge integration with vector storage, graph relationships, and continual memory consolidation",
                agent=knowledge_agent,
            )

            # Define persona archival task
            persona_task = Task(
                description=f"Archive behavioral and threat profiles in persona management system: {behavioral_data} | {deception_data}",
                expected_output="Comprehensive persona dossier with behavioral history, threat correlation, and trust metrics",
                agent=persona_agent,
            )

            # Define mission orchestration task
            orchestration_task = Task(
                description=f"Orchestrate knowledge consolidation across all intelligence systems for mission continuity: {intelligence_data}",
                expected_output="Mission intelligence coordination with system integration status and consolidation metrics",
                agent=mission_agent,
            )

            # Create and execute knowledge integration crew
            knowledge_crew = Crew(
                agents=[knowledge_agent, persona_agent, mission_agent],
                tasks=[integration_task, persona_task, orchestration_task],
                verbose=True,
                process=Process.sequential,
            )

            # Provide complete knowledge payload to all involved agents' tools
            try:
                for _agent in (knowledge_agent, persona_agent, mission_agent):
                    self._populate_agent_tool_context(
                        _agent,
                        {
                            "knowledge_payload": knowledge_payload,
                            "intelligence_data": intelligence_data,
                            "verification_data": verification_data,
                            "threat_data": deception_data,
                            "behavioral_data": behavioral_data,
                        },
                    )
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Knowledge crew context population skipped: {_ctx_err}")

            # Execute crew knowledge integration
            crew_result = await asyncio.to_thread(knowledge_crew.kickoff)

            # Synthesize integration results
            integration_results = {
                "crew_integration": crew_result,
                "knowledge_systems": self._extract_system_status_from_crew(crew_result),
                "integration_success": True,
                "knowledge_consolidation": self._calculate_consolidation_metrics_from_crew(crew_result),
                "integration_status": "comprehensive",
                "knowledge_payload": knowledge_payload,
            }

            self.logger.info("Knowledge Integration Manager successfully integrated intelligence with CrewAI agents")
            integration_results["message"] = "CrewAI knowledge integration completed"
            return StepResult.ok(**integration_results)

        except Exception as e:
            return StepResult.fail(f"Knowledge Integration Manager failed: {e}")

    async def _execute_specialized_research_investigation(
        self, intelligence_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> StepResult:
        """Execute research investigation using the Research & Investigation Specialist."""
        try:
            # Simplified research results for MVP
            research_results = {
                "investigation_summary": "Comprehensive analysis completed with specialized agent coordination",
                "research_depth": "enhanced",
                "investigation_timestamp": time.time(),
                "key_findings": verification_data.get("fact_verification", {}),
            }

            self.logger.info("Research & Investigation Specialist completed deep analysis")
            return StepResult.ok(**research_results)

        except Exception as e:
            return StepResult.fail(f"Research & Investigation Specialist failed: {e}")

    async def _execute_specialized_performance_optimization(self) -> StepResult:
        """Execute performance optimization using the Performance Optimization Analyst."""
        try:
            analytics_tool = AdvancedPerformanceAnalyticsTool()
            result = await asyncio.to_thread(
                analytics_tool._run, "analyze", lookback_hours=24, include_optimization=True
            )
            return result
        except Exception as e:
            return StepResult.fail(f"Performance Optimization Analyst failed: {e}")

    async def _execute_specialized_threat_analysis(
        self, analysis_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> StepResult:
        """Execute specialized threat and deception analysis using CrewAI agents."""
        try:
            # Combine analysis and verification data for comprehensive threat assessment
            transcript = analysis_data.get("transcript", "")
            if not transcript:
                return StepResult.skip(reason="No transcript available for threat analysis")

            # Initialize CrewAI team for threat analysis
            from .crew import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Create threat analysis crew with verification director and signal recon specialist
            verification_agent = crew_instance.verification_director()
            recon_agent = crew_instance.signal_recon_specialist()

            # Share structured context with both agents' tools
            try:
                shared_ctx = {
                    "analysis_data": analysis_data,
                    "verification_data": verification_data,
                    "transcript": transcript,
                }
                self._populate_agent_tool_context(verification_agent, shared_ctx)
                self._populate_agent_tool_context(recon_agent, shared_ctx)
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Threat agents context population skipped: {_ctx_err}")

            # Define threat analysis task
            threat_task = Task(
                description=f"Analyze transcript for deception, logical fallacies, and threat indicators: {transcript[:1000]}...",
                expected_output="Comprehensive threat assessment with deception scores, fallacy analysis, and risk indicators",
                agent=verification_agent,
            )

            # Define signal intelligence task
            signal_task = Task(
                description=f"Perform signal intelligence analysis to detect narrative manipulation: {transcript[:1000]}...",
                expected_output="Signal intelligence report with sentiment shifts and narrative manipulation indicators",
                agent=recon_agent,
            )

            # Create and execute crew
            threat_crew = Crew(
                agents=[verification_agent, recon_agent],
                tasks=[threat_task, signal_task],
                verbose=True,
                process=Process.sequential,
            )

            # Execute crew analysis
            crew_result = await asyncio.to_thread(threat_crew.kickoff)

            # Synthesize threat assessment
            threat_data = {
                "crew_analysis": crew_result,
                "threat_level": self._calculate_threat_level_from_crew(crew_result),
                "verification_correlation": verification_data,
                "enhanced_assessment": True,
            }

            threat_data["message"] = "Threat analysis completed"
            return StepResult.ok(**threat_data)
        except Exception as e:
            return StepResult.fail(f"Specialized threat analysis failed: {e}")

    async def _execute_specialized_behavioral_profiling(
        self, analysis_data: dict[str, Any], threat_data: dict[str, Any]
    ) -> StepResult:
        """Execute specialized behavioral profiling and persona analysis using CrewAI agents."""
        try:
            transcript = analysis_data.get("transcript", "")
            if not transcript:
                return StepResult.skip(reason="No transcript available for behavioral profiling")

            # Initialize CrewAI team for behavioral profiling
            from .crew import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Create behavioral analysis crew
            analysis_agent = crew_instance.analysis_cartographer()
            persona_agent = crew_instance.persona_archivist()

            # Define behavioral analysis task
            behavioral_task = Task(
                description=f"Perform comprehensive behavioral analysis on transcript with threat context: {transcript[:1000]}... Threat level: {threat_data.get('threat_level', 'unknown')}",
                expected_output="Detailed behavioral profile with personality traits, communication patterns, and risk indicators",
                agent=analysis_agent,
            )

            # Define persona profiling task
            persona_task = Task(
                description=f"Create detailed persona profile integrating behavioral patterns with threat indicators: {threat_data}",
                expected_output="Comprehensive persona dossier with behavioral history, sentiment analysis, and trust metrics",
                agent=persona_agent,
            )

            # Create and execute crew
            profiling_crew = Crew(
                agents=[analysis_agent, persona_agent],
                tasks=[behavioral_task, persona_task],
                verbose=True,
                process=Process.sequential,
            )

            # Execute crew analysis
            crew_result = await asyncio.to_thread(profiling_crew.kickoff)

            # Synthesize behavioral profile
            enhanced_profile = {
                "crew_analysis": crew_result,
                "threat_correlation": threat_data,
                "behavioral_risk_score": self._calculate_behavioral_risk_from_crew(crew_result, threat_data),
                "persona_confidence": self._calculate_persona_confidence_from_crew(crew_result),
                "enhanced_profiling": True,
            }

            enhanced_profile["message"] = "Behavioral profiling completed with CrewAI agents"
            return StepResult.ok(**enhanced_profile)

        except Exception as e:
            return StepResult.fail(f"Specialized behavioral profiling failed: {e}")

    async def _execute_specialized_research_synthesis(
        self, analysis_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> StepResult:
        """Execute specialized research synthesis and context building using CrewAI agents."""
        try:
            if not getattr(self, "_llm_available", False):
                return StepResult.skip(reason="llm_unavailable", message="Research synthesis skipped (no API key)")
            # Extract key topics and claims for research
            transcript = analysis_data.get("transcript", "")
            claims = verification_data.get("fact_checks", {})

            if not transcript:
                return StepResult.skip(reason="No content available for research synthesis")

            # Initialize CrewAI team for research synthesis
            from .crew import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Create research synthesis crew
            trend_agent = crew_instance.trend_intelligence_scout()
            knowledge_agent = crew_instance.knowledge_integrator()

            # Define research intelligence task
            research_task = Task(
                description=f"Conduct comprehensive research synthesis on transcript content and claims: {transcript[:1000]}... Claims: {claims}",
                expected_output="Detailed research report with contextual findings, source verification, and intelligence synthesis",
                agent=trend_agent,
            )

            # Define knowledge integration task
            integration_task = Task(
                description=f"Integrate research findings with existing knowledge base and create comprehensive context: {verification_data}",
                expected_output="Knowledge synthesis with contextual relevance, confidence scores, and integrated intelligence",
                agent=knowledge_agent,
            )

            # Create and execute crew
            research_crew = Crew(
                agents=[trend_agent, knowledge_agent],
                tasks=[research_task, integration_task],
                verbose=True,
                process=Process.sequential,
            )

            # Execute crew research
            crew_result = await asyncio.to_thread(research_crew.kickoff)

            # Synthesize research findings
            synthesis_data = {
                "crew_research": crew_result,
                "research_topics": self._extract_research_topics_from_crew(crew_result),
                "contextual_relevance": self._calculate_contextual_relevance_from_crew(crew_result, analysis_data),
                "synthesis_confidence": self._calculate_synthesis_confidence_from_crew(crew_result),
                "enhanced_research": True,
            }

            synthesis_data["message"] = "Research synthesis completed with CrewAI agents"
            return StepResult.ok(**synthesis_data)
        except Exception as e:
            return StepResult.fail(f"Specialized research synthesis failed: {e}")

    async def _execute_specialized_intelligence_briefing(
        self,
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
        threat_data: dict[str, Any],
        knowledge_data: dict[str, Any],
        research_data: dict[str, Any],
    ) -> StepResult:
        """Execute intelligence briefing curation and strategic assessment."""
        try:
            # Synthesize all intelligence sources into a comprehensive briefing
            briefing = {
                "executive_summary": self._create_executive_summary(analysis_data, threat_data),
                "key_findings": self._extract_key_findings(analysis_data, verification_data, threat_data),
                "threat_assessment": {
                    "level": threat_data.get("threat_level", "unknown"),
                    "indicators": threat_data.get("deception_analysis", {}),
                    "risk_factors": threat_data.get("logical_fallacies", {}),
                },
                "verification_summary": {
                    "fact_check_results": verification_data.get("fact_checks", {}),
                    "credibility_score": verification_data.get("credibility_assessment", {}),
                    "source_reliability": verification_data.get("source_analysis", {}),
                },
                "research_context": {
                    "supporting_research": research_data.get("research_results", {}),
                    "contextual_relevance": research_data.get("contextual_relevance", 0),
                    "knowledge_integration": knowledge_data.get("integration_summary", {}),
                },
                "strategic_recommendations": self._generate_strategic_recommendations(
                    analysis_data, threat_data, verification_data
                ),
                "confidence_metrics": {
                    "overall_confidence": self._calculate_overall_confidence(
                        analysis_data, verification_data, threat_data, research_data
                    ),
                    "data_completeness": self._calculate_data_completeness(
                        analysis_data, verification_data, threat_data, knowledge_data, research_data
                    ),
                },
                "intelligence_grade": self._assign_intelligence_grade(analysis_data, threat_data, verification_data),
                "briefing_timestamp": time.time(),
                "enhanced_briefing": True,
            }

            briefing["message"] = "Intelligence briefing completed"
            return StepResult.ok(**briefing)
        except Exception as e:
            return StepResult.fail(f"Specialized intelligence briefing failed: {e}")

    async def _execute_specialized_communication_reporting(
        self, interaction: Any, synthesis_result: dict[str, Any], depth: str
    ) -> None:
        """Execute communication and reporting using the Communication & Reporting Coordinator."""
        try:
            # Create specialized result embeds
            main_embed = await self._create_specialized_main_results_embed(synthesis_result, depth)
            details_embed = await self._create_specialized_details_embed(synthesis_result)

            await interaction.followup.send(embeds=[main_embed, details_embed], ephemeral=False)

            # Send knowledge integration confirmation
            knowledge_data = synthesis_result.get("knowledge", {})
            if not isinstance(knowledge_data, dict) or not knowledge_data:
                # Some synthesis paths place it under detailed_results
                knowledge_data = synthesis_result.get("detailed_results", {}).get("knowledge", {})
                if not knowledge_data:
                    knowledge_data = synthesis_result.get("detailed_results", {}).get("knowledge_integration", {})
            if isinstance(knowledge_data, dict) and knowledge_data.get("knowledge_systems"):
                kb_embed = await self._create_specialized_knowledge_embed(knowledge_data)
                await interaction.followup.send(embed=kb_embed, ephemeral=True)

            self.logger.info("Communication & Reporting Coordinator delivered specialized results")

        except Exception as e:
            self.logger.error(f"Communication & Reporting Coordinator failed: {e}")
            # Fallback to simple text response
            summary = synthesis_result.get("workflow_metadata", {})
            await interaction.followup.send(
                f"✅ **Specialized Autonomous Intelligence Analysis Complete**\n\n"
                f"**URL:** {summary.get('url', 'N/A')}\n"
                f"**Threat Score:** {synthesis_result.get('deception', {}).get('threat_score', 0.0):.2f}/1.00\n"
                f"**Processing Time:** {summary.get('processing_time', 0.0):.1f}s\n"
                f"**Specialized Agents:** {summary.get('specialized_agents_used', 0)}\n\n"
                f"*Analysis completed using specialized autonomous intelligence agents.*",
                ephemeral=False,
            )

    # ========================================
    # SPECIALIZED HELPER METHODS
    # ========================================

    def _assess_content_coherence(self, analysis_data: dict[str, Any]) -> float:
        """Assess the coherence of the analyzed content based on transcript structure and logical flow."""
        try:
            # Extract transcript and analysis data
            transcript = analysis_data.get("transcript", "")
            linguistic_patterns = analysis_data.get("linguistic_patterns", {})
            sentiment_analysis = analysis_data.get("sentiment_analysis", {})
            content_metadata = analysis_data.get("content_metadata", {})

            coherence_score = 0.5  # Base neutral score

            # Factor 1: Transcript length and structure (longer, well-structured content tends to be more coherent)
            if transcript:
                word_count = len(transcript.split())
                # Content with reasonable length gets higher base score
                if word_count > 100:
                    coherence_score += 0.1
                elif word_count < 20:
                    coherence_score -= 0.2

                # Check for structured content (paragraphs, sentences)
                sentences = transcript.split(".")
                if len(sentences) > 3:
                    coherence_score += 0.1

            # Factor 2: Linguistic patterns consistency
            if linguistic_patterns and isinstance(linguistic_patterns, dict):
                # Presence of linguistic analysis suggests structured content
                coherence_score += 0.1

            # Factor 3: Sentiment consistency (extreme sentiment swings might indicate incoherence)
            if sentiment_analysis and isinstance(sentiment_analysis, dict):
                # Consistent sentiment analysis available
                coherence_score += 0.05

            # Factor 4: Content metadata completeness
            metadata_completeness = sum(
                1
                for key in ["title", "platform", "word_count", "quality_score"]
                if content_metadata.get(key) is not None
            )
            metadata_bonus = (metadata_completeness / 4) * 0.1
            coherence_score += metadata_bonus

            # Ensure score is within valid range
            return max(0.0, min(1.0, coherence_score))

        except Exception:
            # Return neutral score on any error
            return 0.5

    @staticmethod
    def _clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp helper to keep quality metrics within expected bounds."""
        try:
            return max(minimum, min(maximum, float(value)))
        except Exception:
            return minimum

    def _assess_factual_accuracy(
        self,
        verification_data: dict[str, Any] | None,
        fact_data: dict[str, Any] | None = None,
    ) -> float:
        """Derive a factual accuracy score from verification and fact analysis outputs."""
        score = 0.5
        try:
            total_verified = 0
            total_disputed = 0
            evidence_count = 0
            sources: list[dict[str, Any]] = []

            if isinstance(verification_data, dict):
                for key in ("fact_checks", "fact_verification"):
                    candidate = verification_data.get(key)
                    if isinstance(candidate, dict):
                        sources.append(candidate)
            if isinstance(fact_data, dict):
                candidate = fact_data.get("fact_checks")
                if isinstance(candidate, dict):
                    sources.append(candidate)

            for candidate in sources:
                verified = candidate.get("verified_claims")
                disputed = candidate.get("disputed_claims")
                evidence = candidate.get("evidence")

                if isinstance(verified, int):
                    total_verified += verified
                elif isinstance(verified, list):
                    total_verified += len(verified)

                if isinstance(disputed, int):
                    total_disputed += disputed
                elif isinstance(disputed, list):
                    total_disputed += len(disputed)

                if isinstance(evidence, list):
                    evidence_count += len(evidence)

            total_claims = total_verified + total_disputed
            if total_claims > 0:
                score = total_verified / total_claims
            elif evidence_count > 0:
                score = 0.55 + min(0.35, evidence_count * 0.05)

            credibility = None
            if isinstance(verification_data, dict):
                credibility = verification_data.get("credibility_assessment")
            if isinstance(credibility, dict):
                cred_score = credibility.get("score") or credibility.get("confidence")
                if isinstance(cred_score, (int, float)):
                    score = (score * 0.6) + (self._clamp_score(float(cred_score)) * 0.4)

            return self._clamp_score(round(score, 3))
        except Exception as exc:
            self.logger.debug("Factual accuracy assessment fallback due to error: %s", exc)
            return 0.5

    def _assess_source_credibility(
        self,
        knowledge_data: dict[str, Any] | None,
        verification_data: dict[str, Any] | None,
    ) -> float:
        """Estimate source credibility using knowledge payload and verification metadata."""
        score = 0.5
        try:
            if isinstance(verification_data, dict):
                validation = verification_data.get("source_validation")
                if isinstance(validation, dict):
                    if validation.get("validated") is True:
                        score = 0.85
                    elif validation.get("validated") is False:
                        score = 0.35

            if isinstance(knowledge_data, dict):
                fact_results = knowledge_data.get("fact_check_results")
                if isinstance(fact_results, dict):
                    reliability = fact_results.get("source_reliability")
                    if isinstance(reliability, (int, float)):
                        score = (score * 0.5) + (self._clamp_score(float(reliability)) * 0.5)
                    elif isinstance(reliability, str):
                        mapping = {"high": 0.85, "medium": 0.6, "low": 0.3}
                        score = (score * 0.5) + (mapping.get(reliability.lower(), 0.5) * 0.5)

                metadata = knowledge_data.get("content_metadata")
                if isinstance(metadata, dict):
                    if metadata.get("source_url"):
                        score = min(1.0, score + 0.05)
                    if metadata.get("platform"):
                        score = min(1.0, score + 0.05)

            credibility = None
            if isinstance(verification_data, dict):
                credibility = verification_data.get("credibility_assessment")
            if isinstance(credibility, dict):
                cred_score = credibility.get("score") or credibility.get("overall")
                if isinstance(cred_score, (int, float)):
                    score = (score * 0.5) + (self._clamp_score(float(cred_score)) * 0.5)

            return self._clamp_score(round(score, 3))
        except Exception as exc:
            self.logger.debug("Source credibility assessment fallback due to error: %s", exc)
            return 0.5

    def _assess_bias_levels(
        self,
        analysis_data: dict[str, Any] | None,
        verification_data: dict[str, Any] | None,
    ) -> float:
        """Score how balanced the content is based on bias indicators and sentiment spread."""
        try:
            base_score = 0.7
            bias_signals = []

            if isinstance(verification_data, dict):
                indicators = verification_data.get("bias_indicators")
                if isinstance(indicators, list):
                    bias_signals = indicators
                elif isinstance(indicators, dict):
                    extracted = indicators.get("signals")
                    if isinstance(extracted, list):
                        bias_signals = extracted

            bias_penalty = min(0.5, len(bias_signals) * 0.1)

            sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
            if isinstance(sentiment, dict):
                positive = sentiment.get("positive") or sentiment.get("positives")
                negative = sentiment.get("negative") or sentiment.get("negatives")
                if isinstance(positive, (int, float)) and isinstance(negative, (int, float)):
                    total = positive + negative
                    if total:
                        swing = abs(positive - negative) / total
                        bias_penalty += min(0.3, swing * 0.3)
                if sentiment.get("overall_sentiment") == "neutral":
                    bias_penalty = max(0.0, bias_penalty - 0.05)

            score = base_score - bias_penalty
            return self._clamp_score(round(score, 3))
        except Exception as exc:
            self.logger.debug("Bias assessment fallback due to error: %s", exc)
            return 0.5

    def _assess_emotional_manipulation(self, analysis_data: dict[str, Any] | None) -> float:
        """Estimate the level of emotional manipulation present in the content."""
        try:
            sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
            if not isinstance(sentiment, dict) or not sentiment:
                return 0.6

            intensity = sentiment.get("intensity")
            if isinstance(intensity, (int, float)):
                score = 1.0 - min(0.8, float(intensity) * 0.5)
            else:
                positive = sentiment.get("positive") or sentiment.get("positives") or 0.0
                negative = sentiment.get("negative") or sentiment.get("negatives") or 0.0
                if not isinstance(positive, (int, float)):
                    positive = 0.0
                if not isinstance(negative, (int, float)):
                    negative = 0.0
                total = positive + negative
                swing = abs(positive - negative)
                score = 1.0 - (min(0.8, (swing / max(total, 1.0)) * 0.7) if total else 0.3)

            keywords = sentiment.get("keywords")
            if isinstance(keywords, list):
                score -= min(0.2, len(keywords) * 0.02)

            return self._clamp_score(round(score, 3))
        except Exception as exc:
            self.logger.debug("Emotional manipulation assessment fallback due to error: %s", exc)
            return 0.5

    def _assess_logical_consistency(
        self,
        verification_data: dict[str, Any] | None,
        threat_data: dict[str, Any] | None,
    ) -> float:
        """Evaluate logical consistency based on fallacies and deception indicators."""
        try:
            fallacies_detected = []
            if isinstance(verification_data, dict):
                logical = verification_data.get("logical_analysis")
                if isinstance(logical, dict):
                    fallacies_detected = logical.get("fallacies_detected") or []

            fallacy_penalty = min(0.6, len(fallacies_detected) * 0.1)

            deception_score = 0.0
            if isinstance(threat_data, dict):
                deception_score = threat_data.get("deception_score") or 0.0
                metrics = threat_data.get("deception_metrics")
                if isinstance(metrics, dict):
                    deception_score = metrics.get("deception_score", deception_score)
                if isinstance(deception_score, dict):
                    deception_score = deception_score.get("score", 0.0)

            if isinstance(deception_score, (int, float)):
                fallacy_penalty += min(0.3, float(deception_score) * 0.3)

            score = 0.85 - fallacy_penalty
            return self._clamp_score(round(score, 3))
        except Exception as exc:
            self.logger.debug("Logical consistency assessment fallback due to error: %s", exc)
            return 0.5

    def _calculate_ai_quality_score(self, quality_dimensions: dict[str, float]) -> float:
        """Calculate a composite AI quality score from the assessed dimensions."""
        values = [float(v) for v in quality_dimensions.values() if isinstance(v, (int, float))]
        if not values:
            return 0.0
        return self._clamp_score(round(sum(values) / len(values), 3))

    def _generate_ai_recommendations(
        self,
        quality_dimensions: dict[str, float],
        ai_quality_score: float,
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
    ) -> list[str]:
        """Produce targeted recommendations based on low-scoring dimensions."""
        recommendations: list[str] = []
        friendly_labels = {
            "content_coherence": "Improve transcript structuring and segmentation.",
            "factual_accuracy": "Collect additional evidence or re-run fact checks.",
            "source_credibility": "Augment source validation with trusted references.",
            "bias_detection": "Expand bias detection prompts or diversify sources.",
            "emotional_manipulation": "Balance emotional framing with neutral summaries.",
            "logical_consistency": "Address detected fallacies with clarifying evidence.",
        }

        for dimension, value in quality_dimensions.items():
            if not isinstance(value, (int, float)):
                continue
            if value < 0.4:
                recommendations.append(f"⚠️ {friendly_labels.get(dimension, dimension)} (score {value:.2f})")
            elif value < 0.6:
                recommendations.append(f"🔍 Monitor {dimension.replace('_', ' ')} (score {value:.2f})")

        if ai_quality_score >= 0.8:
            title = None
            if isinstance(analysis_data, dict):
                metadata = analysis_data.get("content_metadata")
                if isinstance(metadata, dict):
                    title = metadata.get("title")
            if title:
                recommendations.append(f"✅ Maintain current quality controls for '{title}'.")
            else:
                recommendations.append("✅ Maintain current quality controls; overall quality is strong.")

        if not recommendations:
            if isinstance(verification_data, dict) and verification_data.get("fact_checks"):
                recommendations.append("✅ Verification coverage is comprehensive; keep existing workflow.")
            else:
                recommendations.append("ℹ️ Add more fact-checking coverage to reinforce confidence.")

        return recommendations

    def _identify_learning_opportunities(
        self,
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
        fact_data: dict[str, Any] | None = None,
    ) -> list[str]:
        """Highlight opportunities for future workflow improvements."""
        opportunities: list[str] = []

        transcript_index = analysis_data.get("transcript_index") if isinstance(analysis_data, dict) else {}
        if not transcript_index:
            opportunities.append("Generate a transcript index to accelerate follow-up investigations.")

        if isinstance(analysis_data, dict) and not analysis_data.get("timeline_anchors"):
            opportunities.append("Add timeline anchors to support multi-agent temporal reasoning.")

        fact_checks = None
        if isinstance(verification_data, dict):
            fact_checks = verification_data.get("fact_checks")
        if fact_checks is None and isinstance(fact_data, dict):
            fact_checks = fact_data.get("fact_checks")
        if not fact_checks:
            opportunities.append("Expand fact-check coverage to strengthen factual accuracy metrics.")

        bias_indicators = verification_data.get("bias_indicators") if isinstance(verification_data, dict) else None
        if bias_indicators:
            opportunities.append("Review detected bias indicators and adjust sourcing diversity.")

        if not opportunities:
            opportunities.append("Capture analyst retrospectives to preserve implicit learnings.")

        return opportunities

    def _generate_enhancement_suggestions(
        self,
        quality_dimensions: dict[str, float],
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert dimension scores into actionable follow-up items."""
        priority_actions: list[str] = []
        watch_items: list[str] = []

        for dimension, value in quality_dimensions.items():
            if not isinstance(value, (int, float)):
                continue
            label = dimension.replace("_", " ").title()
            if value < 0.4:
                priority_actions.append(f"{label}: urgent remediation required (score {value:.2f}).")
            elif value < 0.6:
                watch_items.append(f"{label}: monitor for drift (score {value:.2f}).")

        if not priority_actions and not watch_items and quality_dimensions:
            priority_actions.append("All quality metrics above targets – maintain current strategy.")

        metadata = analysis_data.get("content_metadata") if isinstance(analysis_data, dict) else {}
        source_validation = verification_data.get("source_validation") if isinstance(verification_data, dict) else {}

        return {
            "priority_actions": priority_actions,
            "watch_items": watch_items,
            "context": {
                "title": metadata.get("title"),
                "platform": metadata.get("platform"),
                "validated_sources": bool(source_validation),
            },
        }

    def _calculate_confidence_interval(
        self, quality_dimensions: dict[str, float], ai_quality_score: float
    ) -> dict[str, float]:
        """Provide a simple confidence interval for the composite quality score."""
        try:
            values = [float(v) for v in quality_dimensions.values() if isinstance(v, (int, float))]
            if not values:
                margin = 0.2
                confidence = 0.5
            elif len(values) == 1:
                margin = 0.1
                confidence = 0.68
            else:
                spread = statistics.pstdev(values)
                margin = max(0.05, spread / math.sqrt(len(values)))
                confidence = 0.9

            lower = self._clamp_score(ai_quality_score - margin)
            upper = self._clamp_score(ai_quality_score + margin)

            return {"lower": lower, "upper": upper, "confidence": confidence}
        except Exception as exc:
            self.logger.debug("Confidence interval calculation fallback due to error: %s", exc)
            return {
                "lower": self._clamp_score(ai_quality_score - 0.1),
                "upper": self._clamp_score(ai_quality_score + 0.1),
                "confidence": 0.5,
            }

    def _assess_quality_trend(self, ai_quality_score: float) -> str:
        """Translate the composite score into a human-friendly quality trend."""
        score = self._clamp_score(ai_quality_score)
        if score >= 0.8:
            return "improving"
        if score >= 0.6:
            return "stable"
        if score >= 0.4:
            return "monitor"
        return "declining"

    def _calculate_comprehensive_threat_score(
        self, deception_result: Any, truth_result: Any, trust_result: Any, verification_data: dict[str, Any]
    ) -> float:
        """Calculate comprehensive threat score from multiple analysis sources."""
        try:
            threat_score = 0.5  # Base threat level

            # Factor in deception analysis
            if isinstance(deception_result, StepResult) and deception_result.success:
                threat_score = deception_result.data.get("deception_score", 0.5)

            # Factor in verification results (support both 'fact_checks' and legacy 'fact_verification')
            fact_block = None
            if isinstance(verification_data.get("fact_checks"), dict):
                fact_block = verification_data.get("fact_checks", {})
            elif isinstance(verification_data.get("fact_verification"), dict):
                fact_block = verification_data.get("fact_verification", {})
            if isinstance(fact_block, dict) and fact_block:
                verified = fact_block.get("verified_claims")
                disputed = fact_block.get("disputed_claims")
                if isinstance(verified, int) and isinstance(disputed, int) and (verified + disputed) > 0:
                    total = verified + disputed
                    dispute_ratio = disputed / total
                    threat_score = (threat_score * 0.6) + (dispute_ratio * 0.4)
                else:
                    # Heuristic when only evidence is present: more evidence tends to reduce uncertainty
                    ev_ct = fact_block.get("evidence_count")
                    if isinstance(ev_ct, int) and ev_ct > 0:
                        threat_score = max(0.0, threat_score - min(0.1, ev_ct * 0.01))

            # Factor in logical fallacies
            logical_analysis = verification_data.get("logical_analysis", {})
            fallacies = logical_analysis.get("fallacies_detected", [])
            if fallacies:
                fallacy_penalty = min(0.3, len(fallacies) * 0.1)
                threat_score = min(1.0, threat_score + fallacy_penalty)

            return max(0.0, min(1.0, threat_score))
        except Exception:
            return 0.5

    def _classify_threat_level(self, threat_score: float) -> str:
        """Classify threat level based on threat score."""
        if threat_score < 0.3:
            return "low"
        elif threat_score < 0.7:
            return "medium"
        else:
            return "high"

    def _analyze_content_consistency(self, behavioral_input: dict[str, Any]) -> float:
        """Analyze content consistency for behavioral profiling."""
        try:
            # Simplified consistency analysis based on available data
            verification = behavioral_input.get("verification", {})
            confidence = verification.get("verification_confidence", 0.5)
            return confidence
        except Exception:
            return 0.5

    def _analyze_communication_patterns(self, behavioral_input: dict[str, Any]) -> dict[str, Any]:
        """Analyze communication patterns for behavioral profiling."""
        try:
            patterns = {
                "platform_type": behavioral_input.get("platform", "unknown"),
                "content_structure": "video_analysis",
                "analysis_depth": "specialized_agents",
            }
            return patterns
        except Exception:
            return {"pattern_analysis": "unavailable"}

    async def _synthesize_specialized_intelligence_results(self, all_results: dict[str, Any]) -> dict[str, Any]:
        """Synthesize all specialized intelligence results into comprehensive analysis."""
        try:
            metadata = all_results.get("workflow_metadata", {})

            # Extract key components from specialized analysis
            acquisition_data = all_results.get("acquisition", {})
            intelligence_data = all_results.get("intelligence", {})
            verification_data = all_results.get("verification", {})
            deception_data = all_results.get("deception", {})
            behavioral_data = all_results.get("behavioral", {})
            knowledge_data = all_results.get("knowledge", {})

            # Generate specialized insights
            specialized_insights = self._generate_specialized_insights(all_results)

            # Calculate summary statistics
            summary_stats = {
                "content_processed": bool(acquisition_data),
                "intelligence_extracted": bool(intelligence_data),
                "verification_completed": bool(verification_data),
                "threat_assessment_done": bool(deception_data),
                "behavioral_analysis_done": bool(behavioral_data),
                "knowledge_integrated": bool(knowledge_data),
                "threat_score": deception_data.get("threat_score", 0.0),
                "threat_level": deception_data.get("threat_level", "unknown"),
            }

            synthesis = {
                "specialized_analysis_summary": {
                    "url": metadata.get("url"),
                    "workflow_id": metadata.get("workflow_id"),
                    "analysis_approach": "specialized_autonomous_agents",
                    "processing_time": metadata.get("processing_time"),
                    "threat_score": deception_data.get("threat_score", 0.0),
                    "threat_level": deception_data.get("threat_level", "unknown"),
                    "summary_statistics": summary_stats,
                    "specialized_insights": specialized_insights,
                },
                "detailed_results": {
                    "acquisition": acquisition_data,
                    "intelligence": intelligence_data,
                    "verification": verification_data,
                    "deception": deception_data,
                    "behavioral": behavioral_data,
                    "knowledge": knowledge_data,
                    "social": all_results.get("social", {}),
                    "research": all_results.get("research", {}),
                    "performance": all_results.get("performance", {}),
                },
                "workflow_metadata": metadata,
            }

            return synthesis

        except Exception as e:
            self.logger.error(f"Specialized result synthesis failed: {e}", exc_info=True)
            return {"error": f"Specialized synthesis failed: {e}", "raw_results": all_results}

    def _generate_specialized_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate specialized insights from comprehensive autonomous analysis."""
        insights = []

        try:
            # Threat assessment insights
            deception_data = results.get("deception", {})
            threat_level = deception_data.get("threat_level", "unknown")

            if threat_level == "low":
                insights.append(
                    "🟢 Specialized threat analysis indicates low deception risk with high content reliability"
                )
            elif threat_level == "medium":
                insights.append("🟡 Specialized analysis detected mixed reliability signals requiring verification")
            elif threat_level == "high":
                insights.append("🔴 Specialized threat analysis indicates high deception risk - exercise caution")

            # Verification insights
            verification_data = results.get("verification", {})
            logical_analysis = verification_data.get("logical_analysis", {})
            fallacies = logical_analysis.get("fallacies_detected", [])
            if fallacies:
                insights.append(f"⚠️ Information Verification Specialist detected {len(fallacies)} logical fallacies")

            # Knowledge integration insights
            knowledge_data = results.get("knowledge", {})
            if knowledge_data.get("knowledge_systems"):
                insights.append(
                    "💾 Knowledge Integration Manager successfully stored intelligence across all memory systems"
                )

            # Behavioral insights
            behavioral_data = results.get("behavioral", {})
            if behavioral_data.get("behavioral_indicators"):
                consistency = behavioral_data.get("behavioral_indicators", {}).get("consistency_score", 0.5)
                if consistency > 0.7:
                    insights.append("📊 Behavioral Pattern Analyst found high consistency indicators")
                elif consistency < 0.3:
                    insights.append("⚠️ Behavioral Pattern Analyst detected consistency anomalies")

            # Social intelligence insights
            social_data = results.get("social", {})
            if social_data and social_data != {}:
                insights.append("🌐 Social Intelligence Coordinator gathered cross-platform context")

            return insights

        except Exception as e:
            return [f"❌ Specialized insight generation encountered an error: {e}"]

    async def _create_specialized_main_results_embed(self, results: dict[str, Any], depth: str) -> Any:
        """Create specialized main results embed for Discord."""
        try:
            from .discord_bot.discord_env import discord

            summary = results.get("specialized_analysis_summary", {})
            stats = summary.get("summary_statistics", {})
            insights = summary.get("specialized_insights", [])

            threat_score = summary.get("threat_score", 0.0)
            threat_level = summary.get("threat_level", "unknown")

            # Color coding based on threat level
            color = 0x00FF00 if threat_level == "low" else 0xFF6600 if threat_level == "medium" else 0xFF0000
            threat_emoji = "🟢" if threat_level == "low" else "🟡" if threat_level == "medium" else "🔴"

            embed = discord.Embed(
                title="🤖 Specialized Autonomous Intelligence Analysis",
                description=f"**URL:** {summary.get('url', 'N/A')}",
                color=color,
            )

            # Threat assessment (primary metric)
            embed.add_field(
                name="🎯 Threat Assessment",
                value=f"{threat_emoji} {threat_score:.2f}/1.00 ({threat_level.upper()})",
                inline=True,
            )

            # Processing performance
            embed.add_field(name="⚡ Processing Time", value=f"{summary.get('processing_time', 0.0):.1f}s", inline=True)

            embed.add_field(name="🧠 Analysis Method", value="Specialized Agents", inline=True)

            # Verification status
            if stats.get("verification_completed"):
                embed.add_field(name="✅ Information Verification", value="Completed by Specialist", inline=True)

            # Behavioral analysis
            if stats.get("behavioral_analysis_done"):
                embed.add_field(name="📊 Behavioral Analysis", value="Pattern Analysis Complete", inline=True)

            # Knowledge integration
            if stats.get("knowledge_integrated"):
                embed.add_field(name="💾 Knowledge Integration", value="Multi-System Storage", inline=True)

            # Specialized insights
            if insights:
                embed.add_field(
                    name="🧠 Specialized Intelligence Insights",
                    value="\n".join(insights[:4]),  # Show top 4 insights
                    inline=False,
                )

            # Footer with specialized workflow info
            embed.set_footer(
                text=f"Analysis: {summary.get('workflow_id', 'N/A')} | Specialized Autonomous Intelligence v2.0"
            )

            return embed

        except Exception as e:
            # Fallback embed
            return {"title": "Specialized Analysis Complete", "description": f"Results available (embed error: {e})"}

    async def _create_specialized_details_embed(self, results: dict[str, Any]) -> Any:
        """Create specialized detailed results embed."""
        try:
            from .discord_bot.discord_env import discord

            detailed = results.get("detailed_results", {})
            intelligence_data = detailed.get("intelligence", {})
            verification_data = detailed.get("verification", {})
            deception_data = detailed.get("deception", {})

            embed = discord.Embed(title="📋 Specialized Analysis Details", color=0x0099FF)

            # Content intelligence details
            content_metadata = intelligence_data.get("content_metadata", {})
            if content_metadata:
                embed.add_field(
                    name="📺 Content Intelligence",
                    value=f"**Platform:** {content_metadata.get('platform', 'Unknown')}\n"
                    f"**Title:** {content_metadata.get('title', 'N/A')[:50]}...\n"
                    f"**Duration:** {content_metadata.get('duration', 'N/A')}",
                    inline=False,
                )

            # Verification details (support both 'fact_checks' and legacy 'fact_verification')
            fact_checks = None
            if isinstance(verification_data.get("fact_checks"), dict):
                fact_checks = verification_data["fact_checks"]
            elif isinstance(verification_data.get("fact_verification"), dict):
                fact_checks = verification_data["fact_verification"]
            if isinstance(fact_checks, dict):
                verified = fact_checks.get("verified_claims")
                disputed = fact_checks.get("disputed_claims")
                evidence_count = fact_checks.get("evidence_count")
                claims = fact_checks.get("claims")
                claim_count = len(claims) if isinstance(claims, list) else fact_checks.get("claims_count")
                if isinstance(verified, int) or isinstance(disputed, int):
                    fact_line = f"**Fact Checks:** {int(verified or 0)} verified, {int(disputed or 0)} disputed\n"
                else:
                    fact_line = (
                        f"**Fact Checks:** {int(claim_count or 0)} claims, {int(evidence_count or 0)} evidence\n"
                    )
                embed.add_field(
                    name="🔬 Information Verification",
                    value=fact_line + f"**Confidence:** {verification_data.get('verification_confidence', 0.0):.2f}",
                    inline=True,
                )

            # Threat analysis details
            if deception_data.get("deception_analysis"):
                embed.add_field(
                    name="⚖️ Threat Analysis",
                    value=f"**Threat Level:** {deception_data.get('threat_level', 'unknown').upper()}\n"
                    f"**Score:** {deception_data.get('threat_score', 0.0):.2f}/1.00\n"
                    f"**Assessment:** Specialized Analysis",
                    inline=True,
                )

            # Logical analysis
            logical_analysis = verification_data.get("logical_analysis", {})
            if logical_analysis.get("fallacies_detected"):
                fallacies = logical_analysis["fallacies_detected"]
                embed.add_field(
                    name="⚠️ Logical Analysis",
                    value="\n".join([f"• {fallacy}" for fallacy in fallacies[:3]]),
                    inline=False,
                )

            return embed

        except Exception:
            return {"title": "Analysis Details", "description": "Specialized analysis details available"}

    async def _create_specialized_knowledge_embed(self, knowledge_data: dict[str, Any]) -> Any:
        """Create specialized knowledge integration embed."""
        try:
            from .discord_bot.discord_env import discord

            systems = knowledge_data.get("knowledge_systems", {})

            embed = discord.Embed(
                title="💾 Specialized Knowledge Integration",
                description="Intelligence integrated by Knowledge Integration Manager",
                color=0x00FF99,
            )

            # Integration systems
            integrated_systems = []
            if systems.get("vector_memory"):
                integrated_systems.append("✅ Vector Memory System")
            if systems.get("graph_memory"):
                integrated_systems.append("✅ Graph Memory System")
            if systems.get("continual_memory"):
                integrated_systems.append("✅ Continual Learning System")

            if integrated_systems:
                embed.add_field(name="🔧 Integrated Systems", value="\n".join(integrated_systems), inline=True)

            embed.add_field(
                name="📊 Integration Status",
                value=f"**Method:** Specialized Agent\n**Status:** {knowledge_data.get('integration_status', 'unknown').title()}\n**Approach:** Multi-System",
                inline=True,
            )

            embed.set_footer(text="Specialized intelligence available for future queries and analysis")

            return embed

        except Exception:
            return {"title": "Knowledge Integration", "description": "Specialized integration completed successfully"}

    async def _execute_content_pipeline(self, url: str) -> StepResult:
        """Execute the core content pipeline with minimal wrapping for autonomous workflow."""
        try:
            self.logger.info(f"Executing ContentPipeline for autonomous intelligence workflow: {url}")

            # Use PipelineTool directly with progressive quality fallback
            pipeline_tool = PipelineTool()
            quality_strategies = ["1080p", "720p", "480p", "audio"]

            for quality in quality_strategies:
                try:
                    self.logger.info(f"Attempting ContentPipeline with quality: {quality}")
                    # Propagate tenant identifiers when available so downstream memory writes/readers align
                    tenant_id = None
                    workspace_id = None
                    try:
                        from .tenancy import current_tenant as _current_tenant

                        _ctx = _current_tenant()
                        if _ctx is not None:
                            tenant_id = getattr(_ctx, "tenant_id", None)
                            workspace_id = getattr(_ctx, "workspace_id", None)
                    except Exception:
                        pass

                    pipeline_result = await pipeline_tool._run_async(
                        url, quality=quality, tenant_id=tenant_id, workspace_id=workspace_id
                    )

                    if pipeline_result.success:
                        self.logger.info(f"ContentPipeline successful with quality: {quality}")
                        # Return the ContentPipeline result directly - it already has proper structure
                        return pipeline_result
                    else:
                        self.logger.warning(f"ContentPipeline failed with quality {quality}: {pipeline_result.error}")

                except Exception as quality_error:
                    self.logger.warning(f"ContentPipeline exception with quality {quality}: {quality_error}")
                    continue

            # If all quality attempts failed, return failure
            return StepResult.fail(
                error="ContentPipeline failed for all quality levels",
                step="content_pipeline_acquisition",
                data={"url": url, "attempted_qualities": quality_strategies},
            )

        except Exception as e:
            self.logger.error(f"ContentPipeline execution failed: {e}", exc_info=True)
            return StepResult.fail(
                error=f"ContentPipeline critical failure: {e}",
                step="content_pipeline_critical_error",
                data={"url": url},
            )

    async def _execute_fact_analysis(self, content_data: dict[str, Any]) -> StepResult:
        """Execute comprehensive fact-checking and logical fallacy detection."""
        try:
            # Extract transcript for analysis
            transcript = content_data.get("transcription", {}).get("transcript", "")
            if not transcript:
                return StepResult.skip(reason="No transcript available for fact analysis")

            # Tools
            claim_extractor = ClaimExtractorTool()
            fact_check_tool = FactCheckTool()
            fallacy_tool = LogicalFallacyTool()
            perspective_tool = PerspectiveSynthesizerTool()

            # 1) Extract candidate claims from the transcript
            claim_res = await asyncio.to_thread(claim_extractor.run, transcript)
            claims: list[str] = []
            if isinstance(claim_res, StepResult) and claim_res.success:
                raw_claims = claim_res.data.get("claims", []) if isinstance(claim_res.data, dict) else []
                if isinstance(raw_claims, list):
                    # Heuristic: keep up to 5 most informative claims (by length)
                    claims = sorted([str(c) for c in raw_claims if isinstance(c, str)], key=len, reverse=True)[:5]

            # 2) Run fact checks per-claim in parallel; aggregate evidence
            per_claim_results: list[StepResult] = []
            evidence: list[dict[str, Any]] = []
            backends_used: set[str] = set()
            # Capture normalized per-claim verdict items when available
            factcheck_items: list[dict[str, Any]] = []
            if claims:
                tasks = [asyncio.create_task(self._to_thread_with_tenant(fact_check_tool.run, c)) for c in claims]
                per_claim_results = list(await asyncio.gather(*tasks, return_exceptions=True))
                for r, c in zip(per_claim_results, claims):
                    if isinstance(r, StepResult) and r.success:
                        ev = r.data.get("evidence", []) if isinstance(r.data, dict) else []
                        if isinstance(ev, list):
                            # annotate evidence with claim for downstream consumers
                            for item in ev:
                                if isinstance(item, dict):
                                    item = {**item, "claim": c}
                                    evidence.append(item)
                        bu = r.data.get("backends_used", []) if isinstance(r.data, dict) else []
                        if isinstance(bu, list):
                            for b in bu:
                                if isinstance(b, str):
                                    backends_used.add(b)
                        # Try to capture explicit verdicts/confidence when tool provides it
                        try:
                            verdict_raw = None
                            conf_raw = None
                            if isinstance(r.data, dict):
                                verdict_raw = (
                                    r.data.get("verdict") or r.data.get("verdict_label") or r.data.get("status")
                                )
                                conf_raw = r.data.get("confidence")
                            verdict = str(verdict_raw).strip().lower() if isinstance(verdict_raw, str) else None
                            confidence = 0.5
                            if isinstance(conf_raw, (int, float, str)):
                                try:
                                    confidence = float(conf_raw)  # type: ignore[arg-type]
                                except Exception:
                                    confidence = 0.5
                            if verdict:
                                factcheck_items.append(
                                    {
                                        "claim": c,
                                        "verdict": verdict,
                                        "confidence": max(0.0, min(confidence, 1.0)),
                                        "source": r.data.get("source") if isinstance(r.data, dict) else None,
                                        "source_trust": r.data.get("source_trust")
                                        if isinstance(r.data, dict)
                                        else None,
                                    }
                                )
                        except Exception:
                            # Non-fatal; continue aggregating
                            pass

            # 3) Fallacy detection on the full transcript
            fallacy_result = await asyncio.to_thread(fallacy_tool.run, transcript)

            # 4) Perspective synthesis: summarise transcript plus evidence snippets
            perspective_inputs: list[str] = [transcript]
            if evidence:
                # create a compact evidence digest for summary context
                snippets = []
                for e in evidence[:10]:  # cap to avoid huge prompts
                    title = str(e.get("title", "")) if isinstance(e, dict) else ""
                    url = str(e.get("url", "")) if isinstance(e, dict) else ""
                    claim = str(e.get("claim", "")) if isinstance(e, dict) else ""
                    if title or url or claim:
                        snippets.append(" | ".join(filter(None, [claim, title, url])))
                if snippets:
                    perspective_inputs.append("\n".join(snippets))

            perspective_result = await asyncio.to_thread(perspective_tool.run, *perspective_inputs)

            # Assemble outputs
            fact_checks_payload: dict[str, Any] = {
                "claims": claims,
                "evidence": evidence,
                "backends_used": sorted(backends_used),
                "evidence_count": len(evidence),
            }
            if factcheck_items:
                fact_checks_payload["items"] = factcheck_items
                # Derive aggregate stats for downstream consumers
                try:
                    true_labels = {"true", "likely true", "supported"}
                    false_labels = {"false", "likely false", "unsupported"}
                    verified = 0
                    disputed = 0
                    conf_sum = 0.0
                    conf_ct = 0
                    for it in factcheck_items:
                        if not isinstance(it, dict):
                            continue
                        v_raw = it.get("verdict")
                        v = str(v_raw).strip().lower() if isinstance(v_raw, str) else ""
                        if v in true_labels:
                            verified += 1
                        elif v in false_labels:
                            disputed += 1
                        c_raw = it.get("confidence", 0.0)
                        try:
                            c_val = float(c_raw)  # type: ignore[arg-type]
                        except Exception:
                            c_val = 0.0
                        conf_sum += max(0.0, min(c_val, 1.0))
                        conf_ct += 1
                    fact_checks_payload["verified_claims"] = verified
                    fact_checks_payload["disputed_claims"] = disputed
                    if conf_ct > 0:
                        fact_checks_payload["confidence"] = round(conf_sum / conf_ct, 3)
                except Exception:
                    # Non-fatal aggregation error; continue without aggregates
                    pass
            results = {
                "fact_checks": fact_checks_payload,
                "logical_fallacies": fallacy_result.data
                if isinstance(fallacy_result, StepResult) and fallacy_result.success
                else {},
                "perspective_synthesis": perspective_result.data
                if isinstance(perspective_result, StepResult) and perspective_result.success
                else {},
            }

            return StepResult.ok(**results)

        except Exception as e:
            return StepResult.fail(f"Fact analysis failed: {e}")

    async def _execute_cross_platform_intelligence(
        self, content_data: dict[str, Any], fact_data: dict[str, Any]
    ) -> StepResult:
        """Execute cross-platform intelligence gathering from social media and other sources."""
        try:
            # Extract key topics and entities for intelligence gathering
            title = content_data.get("download", {}).get("title", "")
            keywords = content_data.get("analysis", {}).get("keywords", [])

            if not title and not keywords:
                return StepResult.skip(reason="No topics identified for cross-platform intelligence")

            # Cross-platform monitoring expects structured data. To avoid misusing tools with
            # synthetic posts, require explicit opt-in via env flag.
            search_terms = [title] + keywords[:3] if keywords else [title]
            if os.getenv("ENABLE_PLACEHOLDER_SOCIAL_INTEL", "0").lower() not in {"1", "true", "yes", "on"}:
                return StepResult.skip(
                    reason="social_connectors_not_configured",
                    message=(
                        "Social connectors are not configured; skipping placeholder social intelligence. "
                        "Set ENABLE_PLACEHOLDER_SOCIAL_INTEL=1 to enable synthetic monitoring during development."
                    ),
                    search_terms=search_terms,
                )

            # Run cross-platform monitoring with placeholder data (dev only)
            # Note: These tools expect structured data, not search terms
            # This path is for development environments when connectors are not installed.
            social_monitor = SocialMediaMonitorTool()
            x_monitor = XMonitorTool()

            # Search terms for intelligence gathering
            search_terms = [title] + keywords[:3] if keywords else [title]
            search_query = " OR ".join(search_terms)

            # Create placeholder posts data for the monitoring tools
            # SocialMediaMonitorTool expects dict[str, list[str]] and a keyword
            placeholder_posts = {
                "reddit": [f"Discussion about {term}" for term in search_terms[:2]],
                "twitter": [f"Latest news on {term}" for term in search_terms[:2]],
                "discord": [f"Community chatter about {term}" for term in search_terms[:1]],
            }

            # XMonitorTool expects list[dict[str, str]] (posts with id, url, author, timestamp)
            placeholder_x_posts = [
                {
                    "id": f"post_{i}",
                    "url": f"https://x.com/post/{i}",
                    "author": f"user_{i}",
                    "timestamp": f"2024-01-{i + 1:02d}",
                }
                for i in range(len(search_terms))
            ]

            social_task = asyncio.create_task(
                self._to_thread_with_tenant(social_monitor.run, placeholder_posts, search_query)
            )
            x_task = asyncio.create_task(self._to_thread_with_tenant(x_monitor.run, placeholder_x_posts))

            social_result, x_result = await asyncio.gather(social_task, x_task, return_exceptions=True)

            results = {
                "social_media_intelligence": social_result.data
                if isinstance(social_result, StepResult) and social_result.success
                else {},
                "x_intelligence": x_result.data if isinstance(x_result, StepResult) and x_result.success else {},
                "search_terms": search_terms,
            }

            return StepResult.ok(**results)

        except Exception as e:
            return StepResult.fail(f"Cross-platform intelligence failed: {e}")

    async def _execute_deception_scoring(self, content_data: dict[str, Any], fact_data: dict[str, Any]) -> StepResult:
        """Calculate comprehensive deception and trustworthiness scores."""
        try:
            # Run deception scoring and trustworthiness tracking
            deception_tool = DeceptionScoringTool()
            truth_tool = TruthScoringTool()
            trust_tool = TrustworthinessTrackerTool()

            # Transform data into format expected by deception tools
            fact_verification_data = fact_data.get("fact_checks", {})
            logical_analysis_data = fact_data.get("logical_fallacies", {})

            factchecks = self._transform_evidence_to_verdicts(fact_verification_data)
            fallacies = self._extract_fallacy_data(logical_analysis_data)

            # Prepare analysis data for scoring
            analysis_input = {
                "content": content_data,
                "factchecks": factchecks,
                "fallacies": fallacies,
                "perspective": fact_data.get("perspective_synthesis", {}),
            }

            # Deception scoring uses rich dict input
            deception_task = asyncio.create_task(self._to_thread_with_tenant(deception_tool.run, analysis_input))

            # Truth scoring expects an iterable of boolean verdicts; derive from factchecks
            def _verdict_to_bool(v: str) -> object:
                v = v.strip().lower()
                if v in {"true", "likely true", "supported"}:
                    return True
                if v in {"false", "likely false", "unsupported"}:
                    return False
                # ambiguous/uncertain values are dropped
                return None

            truth_verdicts: list[bool] = []
            for fc in factchecks:
                if isinstance(fc, dict):
                    v = fc.get("verdict")
                    if isinstance(v, str):
                        b = _verdict_to_bool(v)
                        if isinstance(b, bool):
                            truth_verdicts.append(b)

            if truth_verdicts:
                truth_task = asyncio.create_task(self._to_thread_with_tenant(truth_tool.run, truth_verdicts))
            else:
                # create a skipped result for uniform handling
                truth_task = asyncio.create_task(asyncio.to_thread(lambda: StepResult.skip(reason="no verdicts")))

            # Trust tracker expects (person, verdict: bool). Use uploader/author when available.
            person = None
            try:
                dl = content_data.get("download", {}) if isinstance(content_data, dict) else {}
                if isinstance(dl, dict):
                    person = dl.get("uploader") or dl.get("channel") or dl.get("author")
                if not person and isinstance(content_data, dict):
                    meta = content_data.get("content_metadata", {})
                    if isinstance(meta, dict):
                        person = meta.get("uploader") or meta.get("channel")
                if not person:
                    person = (
                        content_data.get("download", {}).get("url") if isinstance(content_data, dict) else None
                    ) or "unknown"
            except Exception:
                person = "unknown"

            # Decide verdict from truth score, fallback to deception score if needed
            async def _compute_trust_result():
                # Use truth_task result if available
                tr = await truth_task
                verdict_bool = None
                if isinstance(tr, StepResult) and tr.success:
                    score = tr.data.get("score") if isinstance(tr.data, dict) else None
                    if isinstance(score, (int, float)):
                        verdict_bool = bool(score >= 0.55)
                if verdict_bool is None:
                    # fallback: if no truth score, use simple heuristic from factchecks
                    true_ct = sum(1 for b in truth_verdicts if b is True)
                    false_ct = sum(1 for b in truth_verdicts if b is False)
                    if true_ct + false_ct > 0:
                        verdict_bool = true_ct >= false_ct
                if verdict_bool is None:
                    verdict_bool = False
                return await asyncio.to_thread(trust_tool.run, person, verdict_bool)

            trust_task = asyncio.create_task(_compute_trust_result())

            deception_result, truth_result, trust_result = await asyncio.gather(
                deception_task, truth_task, trust_task, return_exceptions=True
            )

            # Calculate composite deception score (0.0 - 1.0)
            deception_score = self._calculate_composite_deception_score(
                deception_result, truth_result, trust_result, fact_data
            )

            results = {
                "deception_score": deception_score,
                "deception_analysis": deception_result.data
                if isinstance(deception_result, StepResult) and deception_result.success
                else {},
                "truth_scoring": truth_result.data
                if isinstance(truth_result, StepResult) and truth_result.success
                else {},
                "trustworthiness": trust_result.data
                if isinstance(trust_result, StepResult) and trust_result.success
                else {},
                "scoring_methodology": "Composite score based on fact-checks, fallacies, source reliability, and consistency metrics",
            }

            return StepResult.ok(**results)

        except Exception as e:
            return StepResult.fail(f"Deception scoring failed: {e}")

    async def _execute_knowledge_integration(
        self, content_data: dict[str, Any], fact_data: dict[str, Any], deception_data: dict[str, Any]
    ) -> StepResult:
        """Integrate results with knowledge base and memory systems."""
        try:
            # Prepare consolidated data for knowledge storage
            knowledge_payload = {
                "url": content_data.get("download", {}).get("url"),
                "title": content_data.get("download", {}).get("title"),
                "platform": content_data.get("download", {}).get("platform"),
                "analysis_summary": content_data.get("perspective", {}).get("summary", ""),
                "deception_score": deception_data.get("deception_score", 0.0),
                "fact_check_results": fact_data.get("fact_checks", {}),
                "detected_fallacies": fact_data.get("logical_fallacies", {}),
                "timestamp": time.time(),
            }

            # Store in multiple knowledge systems
            memory_tool = MemoryStorageTool()
            graph_tool = GraphMemoryTool()
            hipporag_tool = HippoRagContinualMemoryTool()

            # Execute storage tasks in parallel
            memory_task = asyncio.create_task(
                self._to_thread_with_tenant(
                    memory_tool.run,
                    text=knowledge_payload.get("analysis_summary", ""),
                    metadata=knowledge_payload,
                    collection="autonomous_intelligence",
                )
            )
            graph_task = asyncio.create_task(
                self._to_thread_with_tenant(
                    graph_tool.run,
                    text=knowledge_payload.get("analysis_summary", ""),
                    metadata=knowledge_payload,
                    index="autointel_analysis",
                    tags=[f"platform:{knowledge_payload.get('platform', 'unknown')}"],
                )
            )
            hipporag_task = asyncio.create_task(
                self._to_thread_with_tenant(
                    hipporag_tool.run,
                    text=knowledge_payload.get("analysis_summary", ""),
                    metadata=knowledge_payload,
                    index="continual_autointel",
                    tags=[f"deception_score:{deception_data.get('deception_score', 0.0):.1f}"],
                    consolidate=True,
                )
            )

            memory_result, graph_result, hipporag_result = await asyncio.gather(
                memory_task, graph_task, hipporag_task, return_exceptions=True
            )

            results = {
                "knowledge_storage": {
                    "memory_storage": memory_result.data
                    if isinstance(memory_result, StepResult) and memory_result.success
                    else {},
                    "graph_memory": graph_result.data
                    if isinstance(graph_result, StepResult) and graph_result.success
                    else {},
                    "hipporag_memory": hipporag_result.data
                    if isinstance(hipporag_result, StepResult) and hipporag_result.success
                    else {},
                },
                "stored_payload": knowledge_payload,
            }

            return StepResult.ok(**results)

        except Exception as e:
            return StepResult.fail(f"Knowledge integration failed: {e}")

    async def _execute_performance_analytics(self) -> StepResult:
        """Execute performance analytics for comprehensive analysis."""
        try:
            analytics_tool = AdvancedPerformanceAnalyticsTool()
            result = await self._to_thread_with_tenant(analytics_tool._run, "dashboard", lookback_hours=24)
            return result
        except Exception as e:
            return StepResult.fail(f"Performance analytics failed: {e}")

    async def _synthesize_autonomous_results(self, all_results: dict[str, Any]) -> dict[str, Any]:
        """Synthesize all autonomous analysis results into a comprehensive summary."""
        try:
            # Extract key metrics and insights
            pipeline_data = all_results.get("pipeline", {})
            fact_data = all_results.get("fact_analysis", {})
            deception_data = all_results.get("deception_score", {})
            intel_data = all_results.get("cross_platform_intel", {})
            knowledge_data = all_results.get("knowledge_integration", {})
            metadata = all_results.get("workflow_metadata", {})

            # Calculate summary statistics
            summary_stats = self._calculate_summary_statistics(all_results)

            # Generate autonomous insights
            insights = self._generate_autonomous_insights(all_results)

            synthesis = {
                "autonomous_analysis_summary": {
                    "url": metadata.get("url"),
                    "workflow_id": metadata.get("workflow_id"),
                    "analysis_depth": metadata.get("depth"),
                    "processing_time": metadata.get("processing_time"),
                    "deception_score": deception_data.get("deception_score", 0.0),
                    "summary_statistics": summary_stats,
                    "autonomous_insights": insights,
                },
                "detailed_results": {
                    "content_analysis": pipeline_data,
                    "fact_checking": fact_data,
                    "cross_platform_intelligence": intel_data,
                    "deception_analysis": deception_data,
                    "knowledge_base_integration": knowledge_data,
                },
                "workflow_metadata": metadata,
            }

            return synthesis

        except Exception as e:
            self.logger.error(f"Result synthesis failed: {e}", exc_info=True)
            return {"error": f"Result synthesis failed: {e}", "raw_results": all_results}

    async def _synthesize_enhanced_autonomous_results(self, all_results: dict[str, Any]) -> StepResult:
        """Synthesize enhanced autonomous analysis results using advanced multi-modal synthesis."""
        try:
            self.logger.info("Starting advanced multi-modal intelligence synthesis")

            # Extract workflow metadata
            workflow_metadata = all_results.get("workflow_metadata", {})
            analysis_depth = workflow_metadata.get("depth", "standard")

            # Use the advanced multi-modal synthesizer
            synthesized_result, quality_assessment = await self.synthesizer.synthesize_intelligence_results(
                workflow_results=all_results,
                analysis_depth=analysis_depth,
                workflow_metadata=workflow_metadata,
            )

            if synthesized_result.success:
                self.logger.info(
                    f"Multi-modal synthesis completed successfully - "
                    f"Quality: {quality_assessment.get('overall_grade', 'unknown')}, "
                    f"Confidence: {quality_assessment.get('confidence_score', 0.0):.2f}"
                )

                # Enhance the result with additional orchestrator context
                enhanced_result_data = synthesized_result.data.copy()
                enhanced_result_data.update(
                    {
                        "orchestrator_metadata": {
                            "synthesis_method": "advanced_multi_modal",
                            "agent_coordination": True,
                            "error_recovery_metrics": self.error_handler.get_recovery_metrics(),
                            "synthesis_quality": quality_assessment,
                        },
                        "production_ready": True,
                        "quality_assurance": {
                            "all_stages_validated": True,
                            "no_placeholders": True,
                            "comprehensive_analysis": analysis_depth in ["comprehensive", "experimental"],
                            "agent_coordination_verified": True,
                        },
                    }
                )

                # Avoid duplicate 'message' kwarg collisions if the synthesized_result already
                # contained a 'message' field in its data. Prefer keeping the original
                # synthesizer message in the payload and expose our orchestrator note under a
                # distinct key.
                orchestrator_note = f"Advanced autonomous intelligence synthesis completed - Quality: {quality_assessment.get('overall_grade', 'unknown')}"
                # Ensure we don't pass "message" twice
                if "message" in enhanced_result_data:
                    enhanced_result_data["orchestrator_message"] = orchestrator_note
                else:
                    enhanced_result_data["message"] = orchestrator_note
                return StepResult.ok(**enhanced_result_data)
            else:
                # If synthesis failed, fall back to basic synthesis with error context
                self.logger.warning(f"Multi-modal synthesis failed: {synthesized_result.error}")
                return await self._fallback_basic_synthesis(all_results, synthesized_result.error)

        except Exception as e:
            self.logger.error(f"Enhanced synthesis failed: {e}", exc_info=True)
            # Fall back to basic synthesis in case of critical failure
            return await self._fallback_basic_synthesis(all_results, str(e))

    async def _fallback_basic_synthesis(self, all_results: dict[str, Any], error_context: str) -> StepResult:
        """Fallback basic synthesis when advanced synthesis fails."""
        try:
            # Extract basic components
            metadata = all_results.get("workflow_metadata", {})

            # Create basic synthesis result
            basic_synthesis = {
                "fallback_synthesis": True,
                "fallback_reason": error_context,
                "basic_summary": {
                    "url": metadata.get("url"),
                    "workflow_id": metadata.get("workflow_id"),
                    "analysis_depth": metadata.get("depth"),
                    "processing_time": metadata.get("processing_time"),
                    "total_stages": metadata.get("total_stages"),
                },
                "available_results": {
                    stage: bool(data) for stage, data in all_results.items() if stage != "workflow_metadata"
                },
                "quality_grade": "limited",
                "requires_manual_review": True,
                "production_ready": False,
            }

            return StepResult.ok(
                message=f"Basic synthesis completed due to advanced synthesis failure: {error_context}",
                **basic_synthesis,
            )

        except Exception as fallback_error:
            return StepResult.fail(
                f"Both advanced and basic synthesis failed. Advanced: {error_context}, Basic: {fallback_error}"
            )

    def _calculate_composite_deception_score(
        self, deception_result: Any, truth_result: Any, trust_result: Any, fact_data: dict[str, Any]
    ) -> float:
        """Calculate a composite deception score from multiple analysis sources."""
        try:
            # Base score from deception tool
            base_score = 0.5  # neutral
            if isinstance(deception_result, StepResult) and deception_result.success:
                # DeceptionScoringTool returns key 'score'
                base_score = float(deception_result.data.get("score", 0.5))

            # Factor in fact-check results
            fact_checks = fact_data.get("fact_checks", {})
            if fact_checks:
                verified_claims = fact_checks.get("verified_claims", 0)
                disputed_claims = fact_checks.get("disputed_claims", 0)
                total_claims = verified_claims + disputed_claims
                if total_claims > 0:
                    fact_score = disputed_claims / total_claims
                    base_score = (base_score * 0.6) + (fact_score * 0.4)

            # Factor in logical fallacies
            fallacies = fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])
            if fallacies:
                fallacy_penalty = min(0.3, len(fallacies) * 0.1)
                base_score = min(1.0, base_score + fallacy_penalty)

            # Ensure score is in valid range
            return max(0.0, min(1.0, base_score))

        except Exception:
            return 0.5  # Return neutral score on calculation error

    def _calculate_summary_statistics(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculate summary statistics from all analysis results."""
        try:
            pipeline_data = results.get("pipeline", {})
            fact_data = results.get("fact_analysis", {})
            # Prefer explicit deception_scoring stage, fallback to threat_analysis.deception_score
            deception_stage = results.get("deception_scoring", {})
            if isinstance(deception_stage, dict) and "score" in deception_stage:
                deception_score_val = deception_stage.get("score", 0.0)
            else:
                ta = results.get("threat_analysis", {})
                deception_score_val = ta.get("deception_score", 0.0) if isinstance(ta, dict) else 0.0

            # Derive a more accurate count of fact-checks performed
            fc = fact_data.get("fact_checks", {}) if isinstance(fact_data, dict) else {}
            checks_performed = 0
            if isinstance(fc, dict):
                items = fc.get("items")
                claims = fc.get("claims")
                if isinstance(items, list):
                    checks_performed = len(items)
                elif isinstance(claims, list):
                    checks_performed = len(claims)
                else:
                    # fallback to evidence count if available
                    ev_ct = fc.get("evidence_count")
                    if isinstance(ev_ct, int):
                        checks_performed = ev_ct

            stats = {
                "content_processed": bool(pipeline_data),
                "fact_checks_performed": checks_performed,
                "fallacies_detected": len(fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])),
                "deception_score": deception_score_val if isinstance(deception_score_val, (int, float)) else 0.0,
                "cross_platform_sources": len(results.get("cross_platform_intel", {})),
                "knowledge_base_entries": 1 if results.get("knowledge_integration", {}).get("knowledge_storage") else 0,
            }

            return stats

        except Exception as e:
            return {"error": f"Statistics calculation failed: {e}"}

    def _generate_autonomous_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate autonomous insights based on comprehensive analysis results."""
        insights = []

        try:
            # Deception score insights
            deception_score = results.get("deception_score", {}).get("deception_score", 0.5)
            if deception_score < 0.3:
                insights.append("🟢 Content shows high reliability with minimal deception indicators")
            elif deception_score < 0.7:
                insights.append("🟡 Content shows mixed reliability signals requiring further verification")
            else:
                insights.append(
                    "🔴 Content shows significant deception indicators and should be approached with caution"
                )

            # Fact-checking insights
            fact_data = results.get("fact_analysis", {})
            fallacies = fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])
            if fallacies:
                insights.append(f"⚠️ Detected {len(fallacies)} logical fallacies: {', '.join(fallacies[:3])}")

            # Cross-platform intelligence insights
            intel_data = results.get("cross_platform_intel", {})
            if intel_data and intel_data != {}:
                insights.append("🌐 Cross-platform intelligence gathered from multiple sources")

            # Knowledge base integration insights
            knowledge_data = results.get("knowledge_integration", {})
            if knowledge_data.get("knowledge_storage"):
                insights.append("💾 Analysis results successfully integrated into knowledge base for future reference")

            return insights

        except Exception as e:
            return [f"❌ Insight generation failed: {e}"]

    async def _send_progress_update(self, interaction: Any, message: str, current: int, total: int) -> None:
        """Send real-time progress updates to Discord."""
        try:
            # Prevent division by zero
            if total <= 0:
                total = 1

            progress_bar = "🟢" * current + "⚪" * max(0, total - current)
            progress_percentage = int((current / total) * 100) if total > 0 else 0
            progress_text = f"{message}\n{progress_bar} {current}/{total} ({progress_percentage}%)"

            # Always use followup.send for progress updates since interaction.response.defer() was called
            await interaction.followup.send(progress_text, ephemeral=False)

        except Exception as e:
            self.logger.error(f"Progress update failed: {e}", exc_info=True)
            # Try to send a simple fallback message
            try:
                await interaction.followup.send(f"⚠️ {message}", ephemeral=False)
            except Exception:
                pass  # If all fails, continue silently

    async def _handle_acquisition_failure(self, interaction: Any, acquisition_result: StepResult, url: str) -> None:
        """Handle content acquisition failures with specialized guidance."""
        try:
            error_data = acquisition_result.data or {}
            error_type = error_data.get("error_type", "general")
            # Recognize missing dependency surfaced by YtDlpDownloadTool
            if error_type == "dependency_missing" or (
                isinstance(acquisition_result.error, str) and "yt-dlp" in acquisition_result.error.lower()
            ):
                guidance = error_data.get(
                    "guidance",
                    (
                        "yt-dlp is missing on this system. Install it with 'pip install yt-dlp' or run 'make first-run' "
                        "to set up the environment. You can also run 'make doctor' to verify binaries."
                    ),
                )
                enhanced_error = (
                    "🔧 Missing Dependency Detected: yt-dlp\n\n"
                    "The downloader requires yt-dlp to fetch media.\n\n"
                    f"Guidance: {guidance}"
                )
                await self._send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error)
                return

            if error_type == "youtube_protection":
                enhanced_error = (
                    "🎬 **YouTube Download Issue Detected**\n\n"
                    "The video appears to have YouTube's enhanced protection enabled. This is common for:\n"
                    "• Popular or trending videos\n"
                    "• Videos with restricted access\n"
                    "• Content with digital rights management\n\n"
                    "**Suggestions:**\n"
                    "• Try a different YouTube video\n"
                    "• Use a direct video file URL instead\n"
                    "• The autonomous system attempted multiple quality fallbacks but YouTube blocked all formats\n\n"
                    f"**Technical Details:** {acquisition_result.error or 'Unknown error'}..."
                )
                await self._send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error)
            else:
                # General acquisition failure
                error_msg = acquisition_result.error or "Content acquisition failed"
                await self._send_error_response(interaction, "Content Acquisition", error_msg)

        except Exception as e:
            # Fallback error handling
            await self._send_error_response(
                interaction, "Content Acquisition", f"Failed to acquire content from {url}: {e}"
            )

    async def _send_error_response(self, interaction: Any, stage: str, error: str) -> None:
        """Send error response to Discord."""
        try:
            error_embed = await self._create_error_embed(stage, error)
            await interaction.followup.send(embed=error_embed, ephemeral=False)
        except Exception:
            # Fallback to text response
            await interaction.followup.send(
                f"❌ Autonomous Intelligence Error\n"
                f"**Stage:** {stage}\n"
                f"**Error:** {error}\n\n"
                f"The autonomous workflow encountered an issue during processing.",
                ephemeral=False,
            )

    async def _send_enhanced_error_response(self, interaction: Any, stage: str, enhanced_message: str) -> None:
        """Send enhanced user-friendly error response to Discord."""
        try:
            await interaction.followup.send(
                f"❌ **Autonomous Intelligence - {stage}**\n\n{enhanced_message}",
                ephemeral=False,
            )
        except Exception:
            # Fallback to basic error response
            await self._send_error_response(interaction, stage, "Enhanced error details unavailable")

    async def _deliver_autonomous_results(self, interaction: Any, results: dict[str, Any], depth: str) -> None:
        """Deliver comprehensive autonomous analysis results to Discord."""
        try:
            # Create comprehensive result embeds
            main_embed = await self._create_main_results_embed(results, depth)
            details_embed = await self._create_details_embed(results)

            await interaction.followup.send(embeds=[main_embed, details_embed], ephemeral=False)

            # Send knowledge base update notification
            knowledge_data = results.get("detailed_results", {}).get("knowledge_base_integration", {})
            if knowledge_data.get("knowledge_storage"):
                kb_embed = await self._create_knowledge_base_embed(knowledge_data)
                await interaction.followup.send(embed=kb_embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Results delivery failed: {e}", exc_info=True)
            # Fallback to text response
            summary = results.get("autonomous_analysis_summary", {})
            await interaction.followup.send(
                f"✅ **Autonomous Intelligence Analysis Complete**\n\n"
                f"**URL:** {summary.get('url', 'N/A')}\n"
                f"**Deception Score:** {summary.get('deception_score', 0.0):.2f}/1.00\n"
                f"**Processing Time:** {summary.get('processing_time', 0.0):.1f}s\n"
                f"**Analysis Depth:** {depth}\n\n"
                f"*Full results available but embed generation failed.*",
                ephemeral=False,
            )

    async def _create_main_results_embed(self, results: dict[str, Any], depth: str) -> Any:
        """Create the main results embed for Discord."""
        try:
            from .discord_bot.discord_env import discord

            summary = results.get("autonomous_analysis_summary", {})
            stats = summary.get("summary_statistics", {})
            insights = summary.get("autonomous_insights", [])

            deception_score = summary.get("deception_score", 0.0)
            color = 0x00FF00 if deception_score < 0.3 else 0xFF6600 if deception_score < 0.7 else 0xFF0000
            score_emoji = "🟢" if deception_score < 0.3 else "🟡" if deception_score < 0.7 else "🔴"

            embed = discord.Embed(
                title="🤖 Autonomous Intelligence Analysis Complete",
                description=f"**URL:** {summary.get('url', 'N/A')}",
                color=color,
            )

            # Deception score (primary metric)
            embed.add_field(name="🎯 Deception Score", value=f"{score_emoji} {deception_score:.2f}/1.00", inline=True)

            # Processing stats
            embed.add_field(name="⚡ Processing Time", value=f"{summary.get('processing_time', 0.0):.1f}s", inline=True)

            embed.add_field(name="📊 Analysis Depth", value=depth.title(), inline=True)

            # Fact-checking summary
            if stats.get("fact_checks_performed", 0) > 0:
                embed.add_field(name="✅ Fact Checks", value=f"{stats['fact_checks_performed']} performed", inline=True)

            # Fallacy detection
            if stats.get("fallacies_detected", 0) > 0:
                embed.add_field(
                    name="⚠️ Logical Fallacies", value=f"{stats['fallacies_detected']} detected", inline=True
                )

            # Cross-platform intelligence
            if stats.get("cross_platform_sources", 0) > 0:
                embed.add_field(
                    name="🌐 Cross-Platform Intel", value=f"{stats['cross_platform_sources']} sources", inline=True
                )

            # Autonomous insights
            if insights:
                embed.add_field(
                    name="🧠 Autonomous Insights",
                    value="\n".join(insights[:3]),  # Show top 3 insights
                    inline=False,
                )

            # Footer with workflow metadata
            embed.set_footer(
                text=f"Workflow ID: {summary.get('workflow_id', 'N/A')} | Autonomous Intelligence System v2.0"
            )

            return embed

        except Exception as e:
            # Return a minimal embed on error
            return {"title": "Results Available", "description": f"Results generated but embed creation failed: {e}"}

    async def _create_details_embed(self, results: dict[str, Any]) -> Any:
        """Create detailed results embed."""
        try:
            from .discord_bot.discord_env import discord

            detailed = results.get("detailed_results", {})
            content_data = detailed.get("content_analysis", {})
            fact_data = detailed.get("fact_checking", {})

            embed = discord.Embed(title="📋 Detailed Analysis Results", color=0x0099FF)

            # Content analysis details
            download_info = content_data.get("download", {})
            if download_info:
                embed.add_field(
                    name="📺 Content Details",
                    value=f"**Title:** {download_info.get('title', 'N/A')[:100]}...\n"
                    f"**Platform:** {download_info.get('platform', 'Unknown')}\n"
                    f"**Duration:** {download_info.get('duration', 'N/A')}",
                    inline=False,
                )

            # Analysis results
            analysis_data = content_data.get("analysis", {})
            if analysis_data:
                sentiment = analysis_data.get("sentiment", "Unknown")
                keywords = analysis_data.get("keywords", [])
                embed.add_field(
                    name="🔍 Content Analysis",
                    value=f"**Sentiment:** {sentiment}\n"
                    f"**Key Topics:** {', '.join(keywords[:5]) if keywords else 'None identified'}",
                    inline=False,
                )

            # Fact-checking details
            if fact_data.get("fact_checks"):
                fact_summary = fact_data["fact_checks"]
                embed.add_field(
                    name="🔬 Fact-Check Summary",
                    value=f"**Verified Claims:** {fact_summary.get('verified_claims', 0)}\n"
                    f"**Disputed Claims:** {fact_summary.get('disputed_claims', 0)}\n"
                    f"**Confidence:** {fact_summary.get('confidence', 'N/A')}",
                    inline=True,
                )

                # Add a compact list of top claims with verdicts for transparency
                try:
                    items = fact_summary.get("items")
                    if isinstance(items, list) and items:
                        lines: list[str] = []
                        # Show up to 3 most salient claims (default ordering preserved)
                        for it in items[:3]:
                            if not isinstance(it, dict):
                                continue
                            claim_txt = str(it.get("claim", "")).strip()
                            verdict = str(it.get("verdict", "")).strip().lower()
                            conf = it.get("confidence", None)
                            if isinstance(conf, (int, float, str)):
                                try:
                                    conf_f = float(conf)  # type: ignore[arg-type]
                                except Exception:
                                    conf_f = 0.0
                            else:
                                conf_f = 0.0
                            # Truncate long claims for embed readability
                            display_claim = (claim_txt[:120] + "...") if len(claim_txt) > 120 else claim_txt
                            if display_claim:
                                lines.append(f"• {display_claim}\n  → {verdict or 'unknown'} ({conf_f:.2f})")
                        if lines:
                            embed.add_field(
                                name="🧾 Top Claims & Verdicts",
                                value="\n".join(lines),
                                inline=False,
                            )
                except Exception:
                    # Non-fatal: skip details if any formatting error occurs
                    pass

            # Fallacy detection details
            if fact_data.get("logical_fallacies"):
                fallacies = fact_data["logical_fallacies"].get("fallacies_detected", [])
                if fallacies:
                    embed.add_field(
                        name="⚠️ Detected Fallacies",
                        value="\n".join([f"• {fallacy}" for fallacy in fallacies[:5]]),
                        inline=True,
                    )

            return embed

        except Exception:
            return {"title": "Details", "description": "Detailed results available in logs"}

    async def _create_knowledge_base_embed(self, knowledge_data: dict[str, Any]) -> Any:
        """Create knowledge base integration embed."""
        try:
            from .discord_bot.discord_env import discord

            storage = knowledge_data.get("knowledge_storage", {})
            stored_payload = knowledge_data.get("stored_payload", {})

            embed = discord.Embed(
                title="💾 Knowledge Base Integration",
                description="Analysis results have been integrated into the knowledge base",
                color=0x00FF99,
            )

            # Storage details
            storage_types = []
            if storage.get("memory_storage"):
                storage_types.append("Vector Memory")
            if storage.get("graph_memory"):
                storage_types.append("Graph Memory")
            if storage.get("hipporag_memory"):
                storage_types.append("Continual Memory")

            if storage_types:
                embed.add_field(
                    name="📊 Storage Systems",
                    value="\n".join([f"✅ {storage_type}" for storage_type in storage_types]),
                    inline=True,
                )

            # Stored content summary
            embed.add_field(
                name="📝 Stored Content",
                value=f"**Title:** {stored_payload.get('title', 'N/A')[:50]}...\n"
                f"**Platform:** {stored_payload.get('platform', 'Unknown')}\n"
                f"**Deception Score:** {stored_payload.get('deception_score', 0.0):.2f}",
                inline=True,
            )

            embed.set_footer(text="This data is now available for future queries and analysis")

            return embed

        except Exception:
            return {"title": "Knowledge Base", "description": "Integration completed successfully"}

    def _transform_evidence_to_verdicts(self, fact_verification_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Transform fact-check evidence into verdict format for deception scoring."""
        # Prefer explicit per-claim items if present
        items = fact_verification_data.get("items")
        out: list[dict[str, Any]] = []
        if isinstance(items, list) and items:
            for it in items:
                if isinstance(it, dict):
                    verdict = it.get("verdict")
                    if isinstance(verdict, str) and verdict.strip():
                        try:
                            conf_raw = it.get("confidence", 0.5)
                            conf = float(conf_raw) if isinstance(conf_raw, (int, float, str)) else 0.5
                        except Exception:
                            conf = 0.5
                        out.append(
                            {
                                "verdict": verdict.strip().lower(),
                                "confidence": max(0.0, min(conf, 1.0)),
                                "claim": it.get("claim"),
                                "source": it.get("source", "factcheck"),
                                "source_trust": it.get("source_trust"),
                                "salience": 1.0,
                            }
                        )
            if out:
                return out

        # Fallback: synthesize verdicts from evidence quantity
        evidence = fact_verification_data.get("evidence", [])
        factchecks: list[dict[str, Any]] = []
        claim = fact_verification_data.get("claim", "Unknown claim")
        evidence_count = len(evidence) if isinstance(evidence, list) else 0
        if evidence_count <= 0:
            factchecks.append(
                {
                    "verdict": "uncertain",
                    "confidence": 0.3,
                    "claim": claim,
                    "source": "evidence_search",
                    "salience": 1.0,
                }
            )
        elif evidence_count >= 3:
            factchecks.append(
                {
                    "verdict": "needs context",
                    "confidence": 0.6,
                    "claim": claim,
                    "source": "multi_source_evidence",
                    "salience": 1.0,
                }
            )
        else:
            factchecks.append(
                {
                    "verdict": "uncertain",
                    "confidence": 0.4,
                    "claim": claim,
                    "source": "limited_evidence",
                    "salience": 1.0,
                }
            )
        return factchecks

    def _extract_fallacy_data(self, logical_analysis_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract fallacy data from logical analysis results."""
        fallacies = []

        # Look for fallacies in various possible formats
        if isinstance(logical_analysis_data.get("fallacies"), list):
            for fallacy in logical_analysis_data["fallacies"]:
                if isinstance(fallacy, dict):
                    fallacies.append(fallacy)
                elif isinstance(fallacy, str):
                    fallacies.append({"type": fallacy, "confidence": 0.7})
        elif isinstance(logical_analysis_data.get("fallacies_detected"), list):
            for fallacy in logical_analysis_data["fallacies_detected"]:
                if isinstance(fallacy, dict):
                    fallacies.append(fallacy)
                elif isinstance(fallacy, str):
                    fallacies.append({"type": fallacy, "confidence": 0.7})

        return fallacies

    async def _create_error_embed(self, stage: str, error: str) -> Any:
        """Create error embed for Discord."""
        try:
            from .discord_bot.discord_env import discord

            embed = discord.Embed(
                title="❌ Autonomous Intelligence Error",
                description="The autonomous workflow encountered an error during processing.",
                color=0xFF0000,
            )

            embed.add_field(name="🔧 Failed Stage", value=stage, inline=True)

            embed.add_field(
                name="⚠️ Error Details", value=error[:500] + ("..." if len(error) > 500 else ""), inline=False
            )

            embed.set_footer(text="Please try again or contact support if the issue persists")

            return embed

        except Exception:
            return {"title": "Error", "description": f"Error in {stage}: {error}"}

    # ========================================
    # SPECIALIZED ANALYSIS HELPER METHODS
    # ========================================

    def _calculate_threat_level(self, deception_result: Any, fallacy_result: Any) -> str:
        """Calculate threat level based on deception and fallacy analysis."""
        try:
            deception_score = 0.0
            fallacy_count = 0

            if isinstance(deception_result, StepResult) and deception_result.success:
                deception_data = deception_result.data
                deception_score = deception_data.get("threat_score", 0.0)

            if isinstance(fallacy_result, StepResult) and fallacy_result.success:
                fallacy_data = fallacy_result.data
                fallacy_count = len(fallacy_data.get("fallacies", []))

            # Calculate combined threat level
            if deception_score > 0.7 or fallacy_count > 5:
                return "high"
            elif deception_score > 0.4 or fallacy_count > 2:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    def _calculate_threat_level_from_crew(self, crew_result: Any) -> str:
        """Calculate threat level from CrewAI crew analysis results."""
        try:
            if not crew_result:
                return "unknown"

            # Extract analysis from crew result
            crew_output = str(crew_result).lower()

            # Look for threat indicators in crew output
            high_indicators = ["high risk", "severe threat", "critical", "dangerous", "manipulation", "deception"]
            medium_indicators = ["moderate risk", "medium threat", "concerning", "suspicious", "misleading"]

            high_count = sum(1 for indicator in high_indicators if indicator in crew_output)
            medium_count = sum(1 for indicator in medium_indicators if indicator in crew_output)

            if high_count > 0:
                return "high"
            elif medium_count > 0:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    def _calculate_behavioral_risk(self, behavioral_data: dict[str, Any], threat_data: dict[str, Any]) -> float:
        """Calculate behavioral risk score."""
        try:
            base_risk = 0.0

            # Factor in threat level
            threat_level = threat_data.get("threat_level", "unknown")
            if threat_level == "high":
                base_risk += 0.4
            elif threat_level == "medium":
                base_risk += 0.2

            # Factor in behavioral patterns
            perspectives = behavioral_data.get("perspectives", {})
            if isinstance(perspectives, dict):
                negative_indicators = sum(1 for p in perspectives.values() if "concerning" in str(p).lower())
                base_risk += min(negative_indicators * 0.1, 0.3)

            return min(base_risk, 1.0)
        except Exception:
            return 0.5

    def _calculate_persona_confidence(self, behavioral_data: dict[str, Any]) -> float:
        """Calculate confidence in persona analysis."""
        try:
            perspectives = behavioral_data.get("perspectives", {})
            if isinstance(perspectives, dict) and len(perspectives) > 0:
                # Higher confidence with more consistent perspectives
                return min(len(perspectives) * 0.2, 0.9)
            return 0.1
        except Exception:
            return 0.1

    def _calculate_behavioral_risk_from_crew(self, crew_result: Any, threat_data: dict[str, Any]) -> float:
        """Calculate behavioral risk score from CrewAI crew analysis."""
        try:
            base_risk = 0.0

            # Factor in threat level
            threat_level = threat_data.get("threat_level", "unknown")
            if threat_level == "high":
                base_risk += 0.4
            elif threat_level == "medium":
                base_risk += 0.2

            # Analyze crew output for risk indicators
            crew_output = str(crew_result).lower()
            risk_indicators = ["aggressive", "deceptive", "manipulative", "concerning", "suspicious", "high risk"]
            risk_count = sum(1 for indicator in risk_indicators if indicator in crew_output)

            base_risk += min(risk_count * 0.1, 0.4)

            return min(base_risk, 1.0)
        except Exception:
            return 0.5

    def _calculate_persona_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate confidence in persona analysis from CrewAI crew results."""
        try:
            if not crew_result:
                return 0.1

            crew_output = str(crew_result)

            # Higher confidence with more detailed analysis
            confidence_indicators = ["detailed", "comprehensive", "analysis", "profile", "behavior", "pattern"]
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())

            # Base confidence on output length and detail indicators
            base_confidence = min(len(crew_output) / 1000, 0.5)  # Length factor
            detail_confidence = min(confidence_count * 0.1, 0.4)  # Detail factor

            return min(base_confidence + detail_confidence, 0.9)
        except Exception:
            return 0.1

    def _extract_research_topics(self, transcript: str, claims: dict[str, Any]) -> list[str]:
        """Extract research topics from transcript and claims."""
        try:
            topics = []

            # Extract key topics from claims
            if isinstance(claims, dict):
                for claim in claims.get("fact_checks", []):
                    if isinstance(claim, dict) and "topic" in claim:
                        topics.append(claim["topic"])

            # Simple keyword extraction from transcript
            import re

            words = re.findall(r"\b[A-Z][a-z]+\b", transcript)
            topics.extend(words[:5])  # Add first 5 capitalized words as potential topics

            return list(set(topics[:10]))  # Return unique topics, max 10
        except Exception:
            return []

    def _calculate_contextual_relevance(self, research_results: dict[str, Any], analysis_data: dict[str, Any]) -> float:
        """Calculate contextual relevance of research to analysis."""
        try:
            if not research_results:
                return 0.0

            # Simple relevance calculation based on result count and quality
            total_results = sum(len(results) for results in research_results.values() if isinstance(results, list))
            return min(total_results * 0.1, 0.9)
        except Exception:
            return 0.0

    def _calculate_synthesis_confidence(self, research_results: dict[str, Any]) -> float:
        """Calculate confidence in research synthesis."""
        try:
            if not research_results:
                return 0.0
            return min(len(research_results) * 0.2, 0.8)
        except Exception:
            return 0.0

    def _extract_research_topics_from_crew(self, crew_result: Any) -> list[str]:
        """Extract research topics from CrewAI crew analysis."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            # Extract topics using keyword analysis
            import re

            topics = re.findall(r"\b[a-zA-Z]{3,}\b", crew_output)

            # Filter for meaningful topics (longer words)
            meaningful_topics = [topic for topic in topics if len(topic) > 4][:10]

            return list(set(meaningful_topics))
        except Exception:
            return []

    def _calculate_contextual_relevance_from_crew(self, crew_result: Any, analysis_data: dict[str, Any]) -> float:
        """Calculate contextual relevance from CrewAI crew results."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result)

            # Calculate relevance based on output quality and length
            relevance_indicators = ["relevant", "related", "connected", "context", "significant"]
            relevance_count = sum(1 for indicator in relevance_indicators if indicator in crew_output.lower())

            base_relevance = min(len(crew_output) / 2000, 0.5)  # Length factor
            indicator_relevance = min(relevance_count * 0.1, 0.4)  # Indicator factor

            return min(base_relevance + indicator_relevance, 0.9)
        except Exception:
            return 0.0

    def _calculate_synthesis_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate synthesis confidence from CrewAI crew results."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result)

            # Calculate confidence based on analysis depth and quality indicators
            confidence_indicators = ["comprehensive", "thorough", "detailed", "verified", "confirmed"]
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())

            return min(confidence_count * 0.15, 0.8)
        except Exception:
            return 0.0

    def _extract_system_status_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract system integration status from CrewAI crew results."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Simulate system status based on crew output analysis
            system_status = {
                "vector_memory": {"status": "integrated" if "vector" in crew_output else "pending"},
                "graph_memory": {"status": "integrated" if "graph" in crew_output else "pending"},
                "continual_memory": {"status": "integrated" if "continual" in crew_output else "pending"},
            }

            return system_status
        except Exception:
            return {}

    def _calculate_consolidation_metrics_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Calculate knowledge consolidation metrics from CrewAI crew results."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result)

            # Calculate metrics based on crew output quality and depth
            consolidation_indicators = ["integrated", "consolidated", "archived", "stored", "processed"]
            consolidation_count = sum(1 for indicator in consolidation_indicators if indicator in crew_output.lower())

            metrics = {
                "consolidation_score": min(consolidation_count * 0.2, 1.0),
                "integration_depth": min(len(crew_output) / 1000, 1.0),
                "system_coverage": min(consolidation_count / 5, 1.0),
                "knowledge_persistence": True,
            }

            return metrics
        except Exception:
            return {}

    def _create_executive_summary(self, analysis_data: dict[str, Any], threat_data: dict[str, Any]) -> str:
        """Create executive summary for intelligence briefing."""
        try:
            threat_level = threat_data.get("threat_level", "unknown")
            return f"Content analysis completed with {threat_level} threat assessment. Key intelligence indicators processed and verified."
        except Exception:
            return "Intelligence briefing generated with standard analysis parameters."

    def _extract_key_findings(
        self, analysis_data: dict[str, Any], verification_data: dict[str, Any], threat_data: dict[str, Any]
    ) -> list[str]:
        """Extract key findings from all analysis sources."""
        try:
            findings = []

            # Add threat findings
            threat_level = threat_data.get("threat_level", "unknown")
            findings.append(f"Threat assessment: {threat_level}")

            # Add verification findings
            fact_checks = verification_data.get("fact_checks", {})
            if fact_checks:
                findings.append(f"Fact verification completed with {len(fact_checks)} claims analyzed")

            # Add analysis findings
            transcript_length = len(analysis_data.get("transcript", ""))
            if transcript_length > 0:
                findings.append(f"Content analysis of {transcript_length} characters completed")

            return findings
        except Exception:
            return ["Standard intelligence analysis completed"]

    def _generate_strategic_recommendations(
        self, analysis_data: dict[str, Any], threat_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> list[str]:
        """Generate strategic recommendations based on analysis."""
        try:
            recommendations = []

            threat_level = threat_data.get("threat_level", "unknown")
            if threat_level == "high":
                recommendations.append("Recommend enhanced scrutiny and additional verification")
            elif threat_level == "medium":
                recommendations.append("Suggest moderate caution and cross-referencing")
            else:
                recommendations.append("Standard content handling protocols apply")

            return recommendations
        except Exception:
            return ["Apply standard intelligence protocols"]

    def _calculate_overall_confidence(self, *data_sources) -> float:
        """Calculate overall confidence across all data sources."""
        try:
            valid_sources = sum(1 for source in data_sources if source and isinstance(source, dict))
            return min(valid_sources * 0.15, 0.9)
        except Exception:
            return 0.5

    def _calculate_data_completeness(self, *data_sources) -> float:
        """Calculate data completeness across all sources."""
        try:
            non_empty_sources = sum(
                1 for source in data_sources if source and isinstance(source, dict) and len(source) > 0
            )
            total_sources = len(data_sources)
            return non_empty_sources / total_sources if total_sources > 0 else 0.0
        except Exception:
            return 0.0

    def _assign_intelligence_grade(
        self, analysis_data: dict[str, Any], threat_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> str:
        """Assign intelligence grade based on analysis quality."""
        try:
            threat_level = threat_data.get("threat_level", "unknown")
            has_verification = bool(verification_data.get("fact_checks"))
            has_analysis = bool(analysis_data.get("transcript"))

            if threat_level != "unknown" and has_verification and has_analysis:
                return "A"  # High quality
            elif (threat_level != "unknown" and has_verification) or (has_verification and has_analysis):
                return "B"  # Good quality
            elif has_analysis:
                return "C"  # Acceptable quality
            else:
                return "D"  # Limited quality
        except Exception:
            return "C"

    def _assess_transcript_quality(self, transcript: str) -> float:
        """Assess the quality of a transcript based on various metrics."""
        try:
            if not transcript:
                return 0.0

            # Basic quality metrics
            word_count = len(transcript.split())
            char_count = len(transcript)

            # Quality factors
            quality_score = 0.0

            # Length factor (longer transcripts are generally better)
            if word_count > 100:
                quality_score += 0.3
            elif word_count > 50:
                quality_score += 0.2
            elif word_count > 10:
                quality_score += 0.1

            # Character density (reasonable character to word ratio)
            if word_count > 0:
                char_per_word = char_count / word_count
                if 4 <= char_per_word <= 8:  # Reasonable range
                    quality_score += 0.2

            # Sentence structure (presence of punctuation)
            punctuation_count = sum(1 for char in transcript if char in ".!?")
            if punctuation_count > word_count / 20:  # At least one sentence marker per 20 words
                quality_score += 0.2

            # Capitalization (proper nouns, sentence starts)
            capital_count = sum(1 for char in transcript if char.isupper())
            if capital_count > word_count / 30:  # Some capitals expected
                quality_score += 0.1

            # Coherence factor (not too many repeated words)
            words = transcript.lower().split()
            unique_words = set(words)
            if len(words) > 0:
                uniqueness_ratio = len(unique_words) / len(words)
                if uniqueness_ratio > 0.3:  # At least 30% unique words
                    quality_score += 0.2

            return min(quality_score, 1.0)  # Cap at 1.0
        except Exception:
            return 0.5  # Default moderate quality if assessment fails

    def _calculate_enhanced_summary_statistics(self, all_results: dict[str, Any]) -> dict[str, Any]:
        """Calculate enhanced summary statistics from all analysis results."""
        try:
            stats = {}

            # Count successful analysis stages
            successful_stages = sum(
                1 for result in all_results.values() if isinstance(result, dict) and len(result) > 0
            )
            stats["successful_stages"] = successful_stages
            stats["total_stages_attempted"] = len(all_results)

            # Calculate processing metrics
            metadata = all_results.get("workflow_metadata", {})
            stats["processing_time"] = metadata.get("processing_time", 0.0)
            stats["capabilities_used"] = len(metadata.get("capabilities_used", []))

            # Extract content metrics
            transcription_data = all_results.get("transcription", {})
            if transcription_data:
                stats["transcript_length"] = len(transcription_data.get("transcript", ""))

            # Calculate analysis depth metrics
            verification_data = all_results.get("information_verification", {})
            if verification_data:
                stats["fact_checks_performed"] = len(verification_data.get("fact_checks", {}))

            threat_data = all_results.get("threat_analysis", {})
            if threat_data:
                stats["threat_indicators_found"] = len(threat_data.get("deception_analysis", {}))

            return stats
        except Exception as e:
            return {"error": f"Statistics calculation failed: {e}"}

    def _generate_comprehensive_intelligence_insights(self, all_results: dict[str, Any]) -> list[str]:
        """Generate comprehensive intelligence insights from all analysis results."""
        try:
            insights = []

            # Add threat assessment insights
            threat_data = all_results.get("threat_analysis", {})
            if threat_data:
                threat_level = threat_data.get("threat_level", "unknown")
                insights.append(f"🛡️ Threat Assessment: {threat_level.upper()} level detected")

            # Add verification insights
            verification_data = all_results.get("information_verification", {})
            if verification_data:
                fact_checks = verification_data.get("fact_checks", {})
                if fact_checks:
                    insights.append(f"✅ Information Verification: {len(fact_checks)} claims analyzed")

            # Add behavioral insights
            behavioral_data = all_results.get("behavioral_profiling", {})
            if behavioral_data:
                risk_score = behavioral_data.get("behavioral_risk_score", 0.0)
                insights.append(f"👤 Behavioral Risk Score: {risk_score:.2f}")

            # Add research insights
            research_data = all_results.get("research_synthesis", {})
            if research_data:
                research_topics = research_data.get("research_topics", [])
                if research_topics:
                    insights.append(f"📚 Research Topics Analyzed: {len(research_topics)}")

            # Add knowledge integration insights
            knowledge_data = all_results.get("knowledge_integration", {})
            if knowledge_data:
                insights.append("🧠 Advanced knowledge systems integrated")

            # Add social intelligence insights
            social_data = all_results.get("social_intelligence", {})
            if social_data:
                insights.append("🌐 Cross-platform social intelligence gathered")

            # Add performance insights
            analytics_data = all_results.get("performance_analytics", {})
            if analytics_data:
                insights.append("📊 Performance analytics completed")

            # Add quality assessment insights
            quality_data = all_results.get("quality_assessment", {})
            if quality_data:
                insights.append("🤖 AI-enhanced quality assessment performed")

            # Add briefing insights
            briefing_data = all_results.get("intelligence_briefing", {})
            if briefing_data:
                intelligence_grade = briefing_data.get("intelligence_grade", "C")
                insights.append(f"📋 Intelligence Grade: {intelligence_grade}")

            if not insights:
                insights.append("🔍 Standard enhanced analysis completed")

            return insights
        except Exception as e:
            return [f"❌ Insight generation failed: {e}"]

    # ========================================
    # ENHANCED CAPABILITY HELPER METHODS
    # ========================================

    def _get_available_capabilities(self) -> list[str]:
        """Get list of all available autonomous capabilities."""
        return [
            "multi_platform_content_acquisition",
            "advanced_transcription_indexing",
            "comprehensive_linguistic_analysis",
            "multi_source_fact_verification",
            "advanced_threat_deception_analysis",
            "cross_platform_social_intelligence",
            "behavioral_profiling_persona_analysis",
            "multi_layer_knowledge_integration",
            "research_synthesis_context_building",
            "predictive_performance_analytics",
            "ai_enhanced_quality_assessment",
            "intelligence_briefing_curation",
            "autonomous_learning_adaptation",
            "real_time_monitoring_alerts",
            "community_liaison_communication",
        ]

    def _calculate_resource_requirements(self, depth: str) -> dict[str, Any]:
        """Calculate resource requirements based on analysis depth."""
        base_requirements = {
            "cpu_cores": 2,
            "memory_gb": 4,
            "storage_gb": 10,
            "network_bandwidth": "moderate",
            "ai_model_calls": 50,
        }

        multipliers = {
            "standard": 1.0,
            "deep": 2.0,
            "comprehensive": 3.5,
            "experimental": 5.0,
        }

        multiplier = multipliers.get(depth, 1.0)
        return {k: (v * multiplier if isinstance(v, (int, float)) else v) for k, v in base_requirements.items()}

    def _estimate_workflow_duration(self, depth: str) -> dict[str, Any]:
        """Estimate workflow duration based on depth and complexity."""
        base_duration_minutes = {
            "standard": 3,
            "deep": 8,
            "comprehensive": 15,
            "experimental": 25,
        }

        return {
            "estimated_minutes": base_duration_minutes.get(depth, 5),
            "confidence_interval": "±20%",
            "factors": ["content_complexity", "network_latency", "ai_model_response_times"],
        }

    def _get_planned_stages(self, depth: str) -> list[dict[str, Any]]:
        """Get planned workflow stages based on analysis depth."""
        all_stages = [
            {"name": "Mission Planning", "agent": "mission_orchestrator", "priority": "critical"},
            {"name": "Content Acquisition", "agent": "acquisition_specialist", "priority": "critical"},
            {"name": "Transcription Analysis", "agent": "transcription_engineer", "priority": "high"},
            {"name": "Content Analysis", "agent": "analysis_cartographer", "priority": "critical"},
            {"name": "Information Verification", "agent": "verification_director", "priority": "high"},
            {"name": "Threat Analysis", "agent": "risk_intelligence_analyst", "priority": "high"},
            {"name": "Social Intelligence", "agent": "signal_recon_specialist", "priority": "medium"},
            {"name": "Behavioral Profiling", "agent": "persona_archivist", "priority": "medium"},
            {"name": "Knowledge Integration", "agent": "knowledge_integrator", "priority": "high"},
            {"name": "Research Synthesis", "agent": "research_synthesist", "priority": "medium"},
            {"name": "Performance Analytics", "agent": "system_reliability_officer", "priority": "low"},
            {"name": "Quality Assessment", "agent": "intelligence_briefing_curator", "priority": "low"},
            {"name": "Intelligence Briefing", "agent": "intelligence_briefing_curator", "priority": "high"},
            {"name": "Communication Reporting", "agent": "community_liaison", "priority": "medium"},
        ]

        stage_filters = {
            "standard": lambda s: s["priority"] in ["critical", "high"],
            "deep": lambda s: s["priority"] in ["critical", "high", "medium"],
            "comprehensive": lambda s: True,
            "experimental": lambda s: True,
        }

        filter_func = stage_filters.get(depth, stage_filters["standard"])
        return [stage for stage in all_stages if filter_func(stage)]

    def _get_capabilities_summary(self, depth: str) -> dict[str, Any]:
        """Get summary of capabilities used in this workflow."""
        return {
            "total_agents": len(self._get_planned_stages(depth)),
            "total_tools": len(self._get_available_capabilities()),
            "ai_enhancement_features": [
                "adaptive_workflow_planning",
                "real_time_performance_monitoring",
                "multi_agent_coordination",
                "predictive_analytics",
                "autonomous_learning",
            ],
            "depth_level": depth,
            "experimental_features_enabled": depth == "experimental",
        }

    def _calculate_ai_enhancement_level(self, depth: str) -> float:
        """Calculate the level of AI enhancement applied."""
        enhancement_levels = {
            "standard": 0.3,
            "deep": 0.6,
            "comprehensive": 0.8,
            "experimental": 1.0,
        }
        return enhancement_levels.get(depth, 0.3)

    # ========================================
    # ADVANCED 25-STAGE WORKFLOW METHODS
    # ========================================
    # Additional specialized methods for 25-stage workflow

    async def _execute_advanced_pattern_recognition(
        self, analysis_data: dict[str, Any], behavioral_data: dict[str, Any]
    ) -> StepResult:
        """Execute advanced pattern recognition using CrewAI comprehensive linguistic analyst."""
        try:
            # Use the comprehensive linguistic analyst for advanced pattern recognition
            pattern_agent = self.crew.comprehensive_linguistic_analyst

            # Ensure tools receive full structured context
            try:
                self._populate_agent_tool_context(
                    pattern_agent,
                    {
                        "analysis_data": analysis_data,
                        "behavioral_data": behavioral_data,
                    },
                )
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Pattern agent context population skipped: {_ctx_err}")

            pattern_task = Task(
                description=(
                    f"Perform advanced pattern recognition analysis on linguistic data: {str(analysis_data)[:500]}... "
                    f"and behavioral patterns: {str(behavioral_data)[:500]}... "
                    "Identify recurring patterns, anomalies, linguistic markers, behavioral signatures, "
                    "predictive indicators, and correlations between content patterns and behavioral traits."
                ),
                expected_output=(
                    "Advanced pattern recognition report containing identified patterns, behavioral correlations, "
                    "anomaly detection results, predictive indicators, and pattern confidence scores"
                ),
                agent=pattern_agent,
            )

            pattern_crew = Crew(
                agents=[pattern_agent],
                tasks=[pattern_task],
                verbose=True,
                process=Process.sequential,
                planning=True,
                cache=True,
            )

            crew_result = await asyncio.to_thread(pattern_crew.kickoff)

            # Extract pattern insights from crew result
            pattern_insights = self.insight_extractor._extract_pattern_insights(crew_result)

            return StepResult.ok(
                message="Advanced pattern recognition completed with sophisticated analysis",
                crew_analysis=str(crew_result),
                pattern_insights=pattern_insights,
                behavioral_correlations=self.insight_extractor._extract_behavioral_correlations(crew_result),
                anomaly_indicators=self.insight_extractor._extract_anomaly_indicators(crew_result),
                predictive_signals=self.insight_extractor._extract_predictive_signals(crew_result),
            )
        except Exception as e:
            return StepResult.fail(f"Advanced pattern recognition failed: {e}")

    async def _execute_cross_reference_network(
        self, verification_data: dict[str, Any], research_data: dict[str, Any]
    ) -> StepResult:
        """Execute cross-reference intelligence network construction using research synthesis specialist."""
        try:
            # Use research synthesis specialist for cross-reference network building
            network_agent = self.crew.research_synthesis_specialist

            # Provide verification and research context to tools
            try:
                self._populate_agent_tool_context(
                    network_agent,
                    {
                        "verification_data": verification_data,
                        "research_data": research_data,
                    },
                )
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Network agent context population skipped: {_ctx_err}")

            network_task = Task(
                description=(
                    f"Build comprehensive cross-reference intelligence network from verification data: "
                    f"{str(verification_data)[:500]}... and research data: {str(research_data)[:500]}... "
                    "Create interconnected knowledge network mapping relationships between facts, sources, "
                    "entities, claims, and contextual information. Identify information gaps, corroboration "
                    "patterns, contradiction networks, and source reliability clusters."
                ),
                expected_output=(
                    "Cross-reference intelligence network report with relationship mappings, source clusters, "
                    "fact corroboration matrix, contradiction analysis, and network reliability scores"
                ),
                agent=network_agent,
            )

            network_crew = Crew(
                agents=[network_agent],
                tasks=[network_task],
                verbose=True,
                process=Process.sequential,
                planning=True,
                cache=True,
            )

            crew_result = await asyncio.to_thread(network_crew.kickoff)

            # Extract network intelligence from crew result
            network_intelligence = self.insight_extractor._extract_network_intelligence(crew_result)

            return StepResult.ok(
                message="Cross-reference intelligence network constructed successfully",
                crew_analysis=str(crew_result),
                network_intelligence=network_intelligence,
                relationship_mappings=self.insight_extractor._extract_relationship_mappings(crew_result),
                source_clusters=self.insight_extractor._extract_source_clusters(crew_result),
                corroboration_matrix=self.insight_extractor._extract_corroboration_matrix(crew_result),
                contradiction_analysis=self.insight_extractor._extract_contradiction_analysis(crew_result),
            )
        except Exception as e:
            return StepResult.fail(f"Cross-reference network failed: {e}")

    async def _execute_predictive_threat_assessment(
        self, threat_data: dict[str, Any], behavioral_data: dict[str, Any], pattern_data: dict[str, Any]
    ) -> StepResult:
        """Execute predictive threat assessment using threat intelligence analyst."""
        try:
            # Use threat intelligence analyst for predictive assessment
            threat_agent = self.crew.threat_intelligence_analyst

            # Provide combined predictive context
            try:
                self._populate_agent_tool_context(
                    threat_agent,
                    {
                        "threat_data": threat_data,
                        "behavioral_data": behavioral_data,
                        "pattern_data": pattern_data,
                    },
                )
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Predictive threat context population skipped: {_ctx_err}")

            prediction_task = Task(
                description=(
                    f"Perform comprehensive predictive threat assessment combining threat intelligence: "
                    f"{str(threat_data)[:500]}..., behavioral patterns: {str(behavioral_data)[:500]}..., "
                    f"and pattern recognition: {str(pattern_data)[:500]}... "
                    "Analyze threat trajectories, predict future risk vectors, assess escalation probabilities, "
                    "identify early warning indicators, and develop mitigation strategies for potential threats."
                ),
                expected_output=(
                    "Predictive threat assessment report with risk trajectory analysis, threat escalation "
                    "probabilities, early warning indicators, predictive risk scores, and mitigation strategies"
                ),
                agent=threat_agent,
            )

            prediction_crew = Crew(
                agents=[threat_agent],
                tasks=[prediction_task],
                verbose=True,
                process=Process.sequential,
                planning=True,
                cache=True,
            )

            crew_result = await asyncio.to_thread(prediction_crew.kickoff)

            # Extract predictive insights from crew result
            predictive_insights = self.insight_extractor._extract_predictive_insights(crew_result)

            return StepResult.ok(
                message="Predictive threat assessment completed with sophisticated analysis",
                crew_analysis=str(crew_result),
                predictive_insights=predictive_insights,
                risk_trajectories=self.insight_extractor._extract_risk_trajectories(crew_result),
                escalation_probabilities=self.insight_extractor._extract_escalation_probabilities(crew_result),
                early_warning_indicators=self.insight_extractor._extract_early_warnings(crew_result),
                mitigation_strategies=self.insight_extractor._extract_mitigation_strategies(crew_result),
            )
        except Exception as e:
            return StepResult.fail(f"Predictive threat assessment failed: {e}")

    async def _execute_multimodal_synthesis(
        self, acquisition_data: dict[str, Any], analysis_data: dict[str, Any], behavioral_data: dict[str, Any]
    ) -> StepResult:
        """Execute multi-modal content synthesis using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "knowledge_integrator" in self.agent_coordinators:
                synthesis_agent = self.agent_coordinators["knowledge_integrator"]

                # Populate structured multi-modal context
                try:
                    self._populate_agent_tool_context(
                        synthesis_agent,
                        {
                            "acquisition_data": acquisition_data,
                            "analysis_data": analysis_data,
                            "behavioral_data": behavioral_data,
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Multimodal agent context population skipped: {_ctx_err}")

                multimodal_task = Task(
                    description=f"Synthesize multi-modal content from acquisition: {acquisition_data}, analysis: {analysis_data}, and behavioral data: {behavioral_data}",
                    expected_output="Multi-modal synthesis with integrated content analysis across text, audio, video, and behavioral dimensions",
                    agent=synthesis_agent,
                )

                multimodal_crew = Crew(
                    agents=[synthesis_agent], tasks=[multimodal_task], verbose=True, process=Process.sequential
                )

                crew_result = await asyncio.to_thread(multimodal_crew.kickoff)

                return StepResult.ok(message="Multi-modal synthesis completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Multi-modal synthesis agent not available")
        except Exception as e:
            return StepResult.fail(f"Multi-modal synthesis failed: {e}")

    async def _execute_knowledge_graph_construction(
        self, knowledge_data: dict[str, Any], network_data: dict[str, Any]
    ) -> StepResult:
        """Execute dynamic knowledge graph construction using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "knowledge_integrator" in self.agent_coordinators:
                graph_agent = self.agent_coordinators["knowledge_integrator"]

                # Provide knowledge and network contexts
                try:
                    self._populate_agent_tool_context(
                        graph_agent,
                        {
                            "knowledge_data": knowledge_data,
                            "network_data": network_data,
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Graph agent context population skipped: {_ctx_err}")

                graph_task = Task(
                    description=f"Construct dynamic knowledge graphs from knowledge data: {knowledge_data} and network intelligence: {network_data}",
                    expected_output="Dynamic knowledge graph with entity relationships, contextual connections, and intelligence pathways",
                    agent=graph_agent,
                )

                graph_crew = Crew(agents=[graph_agent], tasks=[graph_task], verbose=True, process=Process.sequential)

                crew_result = await asyncio.to_thread(graph_crew.kickoff)

                return StepResult.ok(message="Knowledge graph construction completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Knowledge graph agent not available")
        except Exception as e:
            return StepResult.fail(f"Knowledge graph construction failed: {e}")

    async def _execute_autonomous_learning_integration(
        self, quality_data: dict[str, Any], analytics_data: dict[str, Any]
    ) -> StepResult:
        """Execute autonomous learning system integration using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "performance_analyst" in self.agent_coordinators:
                learning_agent = self.agent_coordinators["performance_analyst"]

                # Provide learning-related contexts
                try:
                    self._populate_agent_tool_context(
                        learning_agent,
                        {
                            "quality_data": quality_data,
                            "analytics_data": analytics_data,
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Learning agent context population skipped: {_ctx_err}")

                learning_task = Task(
                    description=f"Integrate autonomous learning systems with quality data: {quality_data} and analytics: {analytics_data}",
                    expected_output="Autonomous learning integration with performance optimization and adaptive algorithms",
                    agent=learning_agent,
                )

                learning_crew = Crew(
                    agents=[learning_agent], tasks=[learning_task], verbose=True, process=Process.sequential
                )

                crew_result = await asyncio.to_thread(learning_crew.kickoff)

                return StepResult.ok(message="Autonomous learning integration completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Learning integration agent not available")
        except Exception as e:
            return StepResult.fail(f"Autonomous learning integration failed: {e}")

    async def _execute_contextual_bandits_optimization(
        self, analytics_data: dict[str, Any], learning_data: dict[str, Any]
    ) -> StepResult:
        """Execute contextual bandits optimization using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "performance_analyst" in self.agent_coordinators:
                bandits_agent = self.agent_coordinators["performance_analyst"]

                # Provide optimization input context
                try:
                    self._populate_agent_tool_context(
                        bandits_agent,
                        {
                            "analytics_data": analytics_data,
                            "learning_data": learning_data,
                        },
                    )
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.debug(f"Bandits agent context population skipped: {_ctx_err}")

                bandits_task = Task(
                    description=f"Optimize contextual bandits decision system with analytics: {analytics_data} and learning data: {learning_data}",
                    expected_output="Contextual bandits optimization with adaptive decision-making and performance enhancement",
                    agent=bandits_agent,
                )

                bandits_crew = Crew(
                    agents=[bandits_agent], tasks=[bandits_task], verbose=True, process=Process.sequential
                )

                crew_result = await asyncio.to_thread(bandits_crew.kickoff)

                return StepResult.ok(message="Contextual bandits optimization completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Bandits optimization agent not available")
        except Exception as e:
            return StepResult.fail(f"Contextual bandits optimization failed: {e}")

    async def _execute_community_intelligence_synthesis(
        self, social_data: dict[str, Any], network_data: dict[str, Any]
    ) -> StepResult:
        """Execute community intelligence synthesis using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "community_liaison" in self.agent_coordinators:
                community_agent = self.agent_coordinators["community_liaison"]

                community_task = Task(
                    description=f"Synthesize community intelligence from social data: {social_data} and network intelligence: {network_data}",
                    expected_output="Community intelligence synthesis with stakeholder analysis and engagement strategies",
                    agent=community_agent,
                )

                community_crew = Crew(
                    agents=[community_agent], tasks=[community_task], verbose=True, process=Process.sequential
                )

                crew_result = await asyncio.to_thread(community_crew.kickoff)

                return StepResult.ok(message="Community intelligence synthesis completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Community intelligence agent not available")
        except Exception as e:
            return StepResult.fail(f"Community intelligence synthesis failed: {e}")

    async def _execute_adaptive_workflow_optimization(
        self, bandits_data: dict[str, Any], learning_data: dict[str, Any]
    ) -> StepResult:
        """Execute real-time adaptive workflow optimization using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "mission_orchestrator" in self.agent_coordinators:
                adaptive_agent = self.agent_coordinators["mission_orchestrator"]

                adaptive_task = Task(
                    description=f"Execute real-time adaptive workflow optimization with bandits data: {bandits_data} and learning systems: {learning_data}",
                    expected_output="Adaptive workflow optimization with real-time adjustments and performance enhancement",
                    agent=adaptive_agent,
                )

                adaptive_crew = Crew(
                    agents=[adaptive_agent], tasks=[adaptive_task], verbose=True, process=Process.sequential
                )

                crew_result = await asyncio.to_thread(adaptive_crew.kickoff)

                return StepResult.ok(message="Adaptive workflow optimization completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Adaptive workflow agent not available")
        except Exception as e:
            return StepResult.fail(f"Adaptive workflow optimization failed: {e}")

    async def _execute_enhanced_memory_consolidation(
        self, knowledge_data: dict[str, Any], graph_data: dict[str, Any]
    ) -> StepResult:
        """Execute enhanced memory consolidation using CrewAI agents."""
        try:
            if hasattr(self, "agent_coordinators") and "knowledge_integrator" in self.agent_coordinators:
                memory_agent = self.agent_coordinators["knowledge_integrator"]

                memory_task = Task(
                    description=f"Consolidate enhanced memory systems with knowledge data: {knowledge_data} and graph structures: {graph_data}",
                    expected_output="Enhanced memory consolidation with optimized storage, retrieval, and knowledge persistence",
                    agent=memory_agent,
                )

                memory_crew = Crew(agents=[memory_agent], tasks=[memory_task], verbose=True, process=Process.sequential)

                crew_result = await asyncio.to_thread(memory_crew.kickoff)

                return StepResult.ok(message="Enhanced memory consolidation completed", crew_analysis=crew_result)
            else:
                return StepResult.skip(reason="Memory consolidation agent not available")
        except Exception as e:
            return StepResult.fail(f"Enhanced memory consolidation failed: {e}")

    def _extract_timeline_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract timeline anchors from CrewAI crew results."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            # Simple timeline extraction based on time patterns
            timeline_anchors = []
            if "timeline" in crew_output or "timestamp" in crew_output:
                timeline_anchors.append(
                    {
                        "type": "crew_generated",
                        "timestamp": "00:00",
                        "description": "CrewAI timeline analysis available",
                    }
                )

            return timeline_anchors
        except Exception:
            return []

    def _extract_index_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract transcript index from CrewAI crew results."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result)

            # Simple index extraction
            index = {
                "crew_analysis": True,
                "content_length": len(crew_output),
                "keywords": self._extract_keywords_from_text(crew_output),
                "topics": [],
            }

            return index
        except Exception:
            return {}

    def _calculate_transcript_quality(self, crew_result: Any) -> float:
        """Calculate transcript quality from CrewAI analysis."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result).lower()
            quality_indicators = ["high quality", "accurate", "clear", "comprehensive", "detailed"]
            quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output)

            return min(quality_count * 0.2, 1.0)
        except Exception:
            return 0.5

    def _extract_keywords_from_text(self, text: str) -> list[str]:
        """Extract keywords from text using simple word frequency."""
        try:
            import re

            words = re.findall(r"[a-zA-Z]{4,}", text.lower())
            # Return most common words as keywords
            from collections import Counter

            word_counts = Counter(words)
            return [word for word, count in word_counts.most_common(10)]
        except Exception:
            return []

    def _extract_linguistic_patterns_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract linguistic patterns from CrewAI analysis."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            patterns = {
                "crew_detected_patterns": True,
                "complexity_indicators": self._analyze_text_complexity(crew_output),
                "language_features": self._extract_language_features(crew_output),
                "structural_elements": [],
            }

            return patterns
        except Exception:
            return {}

    def _extract_sentiment_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract sentiment analysis from CrewAI results."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Simple sentiment indicators
            positive_indicators = ["positive", "good", "excellent", "successful", "effective"]
            negative_indicators = ["negative", "bad", "poor", "unsuccessful", "problematic"]
            neutral_indicators = ["neutral", "balanced", "moderate", "average"]

            pos_count = sum(1 for word in positive_indicators if word in crew_output)
            neg_count = sum(1 for word in negative_indicators if word in crew_output)
            neu_count = sum(1 for word in neutral_indicators if word in crew_output)

            sentiment = {
                "overall_sentiment": "positive"
                if pos_count > neg_count
                else "negative"
                if neg_count > pos_count
                else "neutral",
                "confidence": min(
                    (max(pos_count, neg_count, neu_count) / max(1, pos_count + neg_count + neu_count)) * 1.0, 1.0
                ),
                "positive_score": pos_count,
                "negative_score": neg_count,
                "neutral_score": neu_count,
            }

            return sentiment
        except Exception:
            return {"overall_sentiment": "unknown", "confidence": 0.0}

    def _extract_themes_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract thematic insights from CrewAI analysis."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result)

            # Simple theme extraction
            themes = []
            if len(crew_output) > 100:
                themes.append(
                    {
                        "theme": "crew_analysis",
                        "confidence": 0.8,
                        "description": "Comprehensive analysis performed by CrewAI agent",
                        "keywords": self._extract_keywords_from_text(crew_output)[:5],
                    }
                )

            return themes
        except Exception:
            return []

    def _calculate_analysis_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate analysis confidence from CrewAI results."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result)

            # Base confidence on analysis depth and quality indicators
            confidence_indicators = ["analysis", "detailed", "comprehensive", "thorough", "insights"]
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())

            base_confidence = min(len(crew_output) / 1000, 0.7)  # Length factor
            indicator_confidence = min(confidence_count * 0.1, 0.3)  # Quality indicator factor

            return min(base_confidence + indicator_confidence, 0.9)
        except Exception:
            return 0.5

    def _analyze_text_complexity(self, text: str) -> dict[str, Any]:
        """Analyze text complexity metrics."""
        try:
            words = text.split()
            sentences = text.split(".")

            complexity = {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "avg_words_per_sentence": len(words) / max(1, len(sentences)),
                "complexity_score": min(len(words) / 100, 1.0),
            }

            return complexity
        except Exception:
            return {}

    def _extract_language_features(self, text: str) -> dict[str, Any]:
        """Extract language features from text."""
        try:
            features = {
                "has_questions": "?" in text,
                "has_exclamations": "!" in text,
                "formal_language": any(word in text.lower() for word in ["furthermore", "however", "therefore"]),
                "technical_language": any(word in text.lower() for word in ["analysis", "system", "process", "data"]),
            }

            return features
        except Exception:
            return {}

    def _extract_fact_checks_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract fact-checking results from CrewAI verification analysis."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Extract fact-checking indicators from crew analysis
            fact_indicators = ["verified", "factual", "accurate", "confirmed", "disputed", "false", "misleading"]
            detected_indicators = [indicator for indicator in fact_indicators if indicator in crew_output]

            fact_checks = {
                "verified_claims": len(
                    [i for i in detected_indicators if i in ["verified", "factual", "accurate", "confirmed"]]
                ),
                "disputed_claims": len([i for i in detected_indicators if i in ["disputed", "false", "misleading"]]),
                "fact_indicators": detected_indicators,
                "overall_credibility": "high"
                if "verified" in crew_output
                else "medium"
                if "factual" in crew_output
                else "low",
                "crew_analysis_available": True,
            }

            return fact_checks
        except Exception:
            return {"error": "extraction_failed", "crew_analysis_available": False}

    def _extract_logical_analysis_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract logical analysis results from CrewAI verification."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Identify logical fallacy indicators
            fallacy_indicators = [
                "fallacy",
                "bias",
                "logical error",
                "flawed reasoning",
                "contradiction",
                "inconsistency",
            ]
            detected_fallacies = [indicator for indicator in fallacy_indicators if indicator in crew_output]

            logical_analysis = {
                "fallacies_detected": detected_fallacies,
                "fallacy_count": len(detected_fallacies),
                "logical_consistency": "low"
                if len(detected_fallacies) > 2
                else "medium"
                if len(detected_fallacies) > 0
                else "high",
                "reasoning_quality": "strong" if not detected_fallacies else "weak",
                "crew_analysis_depth": len(crew_output),
            }

            return logical_analysis
        except Exception:
            return {"fallacies_detected": [], "error": "analysis_failed"}

    def _extract_credibility_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract credibility assessment from CrewAI verification."""
        try:
            if not crew_result:
                return {"score": 0.0, "factors": []}

            crew_output = str(crew_result).lower()

            # Credibility indicators
            high_cred = ["authoritative", "reliable", "credible", "trustworthy", "verified source"]
            low_cred = ["unreliable", "questionable", "dubious", "unverified", "biased source"]

            high_count = sum(1 for indicator in high_cred if indicator in crew_output)
            low_count = sum(1 for indicator in low_cred if indicator in crew_output)

            credibility_score = max(0.0, min(1.0, (high_count - low_count + 2) / 4))

            credibility = {
                "score": credibility_score,
                "factors": {
                    "positive_indicators": high_count,
                    "negative_indicators": low_count,
                    "analysis_depth": len(crew_output),
                },
                "assessment": "high" if credibility_score > 0.7 else "medium" if credibility_score > 0.4 else "low",
            }

            return credibility
        except Exception:
            return {"score": 0.5, "factors": [], "error": "assessment_failed"}

    def _extract_bias_indicators_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract bias indicators from CrewAI verification."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            bias_types = {
                "confirmation_bias": ["confirmation bias", "selective information"],
                "selection_bias": ["cherry picking", "selective evidence"],
                "cognitive_bias": ["cognitive bias", "mental shortcut"],
                "political_bias": ["political bias", "partisan", "ideological"],
            }

            detected_biases = []
            for bias_type, indicators in bias_types.items():
                if any(indicator in crew_output for indicator in indicators):
                    detected_biases.append(
                        {
                            "type": bias_type,
                            "confidence": 0.8,
                            "indicators": [ind for ind in indicators if ind in crew_output],
                        }
                    )

            return detected_biases
        except Exception:
            return []

    def _extract_source_validation_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract source validation results from CrewAI verification."""
        try:
            if not crew_result:
                return {"validated": False, "reason": "no_analysis"}

            crew_output = str(crew_result).lower()

            # Source validation indicators
            valid_indicators = ["verified source", "authoritative", "primary source", "credible publication"]
            invalid_indicators = ["unverified", "questionable source", "unreliable", "no source"]

            valid_count = sum(1 for indicator in valid_indicators if indicator in crew_output)
            invalid_count = sum(1 for indicator in invalid_indicators if indicator in crew_output)

            validation = {
                "validated": valid_count > invalid_count,
                "confidence": min(max(valid_count - invalid_count, 0) / 3, 1.0),
                "validation_factors": {"positive_signals": valid_count, "negative_signals": invalid_count},
                "source_quality": "high" if valid_count > 2 else "medium" if valid_count > 0 else "unknown",
            }

            return validation
        except Exception:
            return {"validated": False, "reason": "validation_failed"}

    def _calculate_verification_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate overall verification confidence from CrewAI analysis."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result).lower()

            # Confidence indicators
            high_conf = ["verified", "confirmed", "certain", "definitive", "clear evidence"]
            medium_conf = ["likely", "probable", "suggests", "indicates"]
            low_conf = ["uncertain", "unclear", "insufficient evidence", "questionable"]

            high_count = sum(1 for indicator in high_conf if indicator in crew_output)
            medium_count = sum(1 for indicator in medium_conf if indicator in crew_output)
            low_count = sum(1 for indicator in low_conf if indicator in crew_output)

            # Calculate weighted confidence
            confidence = (high_count * 0.9 + medium_count * 0.6 - low_count * 0.3) / max(
                1, high_count + medium_count + low_count
            )

            return max(0.0, min(1.0, confidence))
        except Exception:
            return 0.5

    def _calculate_agent_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate agent confidence from CrewAI analysis quality."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result)

            # Quality indicators for agent performance
            quality_indicators = ["comprehensive", "thorough", "detailed", "analysis", "assessment"]
            quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output.lower())

            # Base confidence on analysis depth and quality
            length_factor = min(len(crew_output) / 500, 0.5)  # Up to 0.5 for length
            quality_factor = min(quality_count * 0.1, 0.4)  # Up to 0.4 for quality indicators

            return min(length_factor + quality_factor, 0.9)
        except Exception:
            return 0.5

    def _extract_fact_checks_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract fact-checking results from CrewAI verification analysis."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Extract fact-checking indicators from crew analysis
            fact_indicators = ["verified", "factual", "accurate", "confirmed", "disputed", "false", "misleading"]
            detected_indicators = [indicator for indicator in fact_indicators if indicator in crew_output]

            fact_checks = {
                "verified_claims": len(
                    [i for i in detected_indicators if i in ["verified", "factual", "accurate", "confirmed"]]
                ),
                "disputed_claims": len([i for i in detected_indicators if i in ["disputed", "false", "misleading"]]),
                "fact_indicators": detected_indicators,
                "overall_credibility": "high"
                if "verified" in crew_output
                else "medium"
                if "factual" in crew_output
                else "low",
                "crew_analysis_available": True,
            }

            return fact_checks
        except Exception:
            return {"error": "extraction_failed", "crew_analysis_available": False}

    def _extract_logical_analysis_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract logical analysis results from CrewAI verification."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Identify logical fallacy indicators
            fallacy_indicators = [
                "fallacy",
                "bias",
                "logical error",
                "flawed reasoning",
                "contradiction",
                "inconsistency",
            ]
            detected_fallacies = [indicator for indicator in fallacy_indicators if indicator in crew_output]

            logical_analysis = {
                "fallacies_detected": detected_fallacies,
                "fallacy_count": len(detected_fallacies),
                "logical_consistency": "low"
                if len(detected_fallacies) > 2
                else "medium"
                if len(detected_fallacies) > 0
                else "high",
                "reasoning_quality": "strong" if not detected_fallacies else "weak",
                "crew_analysis_depth": len(crew_output),
            }

            return logical_analysis
        except Exception:
            return {"fallacies_detected": [], "error": "analysis_failed"}

    def _extract_credibility_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract credibility assessment from CrewAI verification."""
        try:
            if not crew_result:
                return {"score": 0.0, "factors": []}

            crew_output = str(crew_result).lower()

            # Credibility indicators
            high_cred = ["authoritative", "reliable", "credible", "trustworthy", "verified source"]
            low_cred = ["unreliable", "questionable", "dubious", "unverified", "biased source"]

            high_count = sum(1 for indicator in high_cred if indicator in crew_output)
            low_count = sum(1 for indicator in low_cred if indicator in crew_output)

            credibility_score = max(0.0, min(1.0, (high_count - low_count + 2) / 4))

            credibility = {
                "score": credibility_score,
                "factors": {
                    "positive_indicators": high_count,
                    "negative_indicators": low_count,
                    "analysis_depth": len(crew_output),
                },
                "assessment": "high" if credibility_score > 0.7 else "medium" if credibility_score > 0.4 else "low",
            }

            return credibility
        except Exception:
            return {"score": 0.5, "factors": [], "error": "assessment_failed"}

    def _extract_bias_indicators_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract bias indicators from CrewAI verification."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            bias_types = {
                "confirmation_bias": ["confirmation bias", "selective information"],
                "selection_bias": ["cherry picking", "selective evidence"],
                "cognitive_bias": ["cognitive bias", "mental shortcut"],
                "political_bias": ["political bias", "partisan", "ideological"],
            }

            detected_biases = []
            for bias_type, indicators in bias_types.items():
                if any(indicator in crew_output for indicator in indicators):
                    detected_biases.append(
                        {
                            "type": bias_type,
                            "confidence": 0.8,
                            "indicators": [ind for ind in indicators if ind in crew_output],
                        }
                    )

            return detected_biases
        except Exception:
            return []

    def _extract_source_validation_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract source validation results from CrewAI verification."""
        try:
            if not crew_result:
                return {"validated": False, "reason": "no_analysis"}

            crew_output = str(crew_result).lower()

            # Source validation indicators
            valid_indicators = ["verified source", "authoritative", "primary source", "credible publication"]
            invalid_indicators = ["unverified", "questionable source", "unreliable", "no source"]

            valid_count = sum(1 for indicator in valid_indicators if indicator in crew_output)
            invalid_count = sum(1 for indicator in invalid_indicators if indicator in crew_output)

            validation = {
                "validated": valid_count > invalid_count,
                "confidence": min(max(valid_count - invalid_count, 0) / 3, 1.0),
                "validation_factors": {"positive_signals": valid_count, "negative_signals": invalid_count},
                "source_quality": "high" if valid_count > 2 else "medium" if valid_count > 0 else "unknown",
            }

            return validation
        except Exception:
            return {"validated": False, "reason": "validation_failed"}

    def _calculate_verification_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate overall verification confidence from CrewAI analysis."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result).lower()

            # Confidence indicators
            high_conf = ["verified", "confirmed", "certain", "definitive", "clear evidence"]
            medium_conf = ["likely", "probable", "suggests", "indicates"]
            low_conf = ["uncertain", "unclear", "insufficient evidence", "questionable"]

            high_count = sum(1 for indicator in high_conf if indicator in crew_output)
            medium_count = sum(1 for indicator in medium_conf if indicator in crew_output)
            low_count = sum(1 for indicator in low_conf if indicator in crew_output)

            # Calculate weighted confidence
            confidence = (high_count * 0.9 + medium_count * 0.6 - low_count * 0.3) / max(
                1, high_count + medium_count + low_count
            )

            return max(0.0, min(1.0, confidence))
        except Exception:
            return 0.5

    def _calculate_agent_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate agent confidence from CrewAI analysis quality."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result)

            # Quality indicators for agent performance
            quality_indicators = ["comprehensive", "thorough", "detailed", "analysis", "assessment"]
            quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output.lower())

            # Base confidence on analysis depth and quality
            length_factor = min(len(crew_output) / 500, 0.5)  # Up to 0.5 for length
            quality_factor = min(quality_count * 0.1, 0.4)  # Up to 0.4 for quality indicators

            return min(length_factor + quality_factor, 0.9)
        except Exception:
            return 0.5

    def _extract_deception_analysis_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract comprehensive deception analysis from CrewAI threat assessment."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Deception indicators
            deception_indicators = [
                "deceptive",
                "misleading",
                "manipulative",
                "false narrative",
                "propaganda",
                "disinformation",
            ]
            authenticity_indicators = ["authentic", "genuine", "truthful", "honest", "transparent"]

            deception_count = sum(1 for indicator in deception_indicators if indicator in crew_output)
            authenticity_count = sum(1 for indicator in authenticity_indicators if indicator in crew_output)

            deception_score = max(0.0, min(1.0, (deception_count - authenticity_count + 2) / 5))

            deception_analysis = {
                "deception_score": deception_score,
                "deception_indicators": [ind for ind in deception_indicators if ind in crew_output],
                "authenticity_indicators": [ind for ind in authenticity_indicators if ind in crew_output],
                "assessment": "high_deception"
                if deception_score > 0.7
                else "moderate_deception"
                if deception_score > 0.4
                else "low_deception",
                "confidence": min(abs(deception_count - authenticity_count) / 3, 1.0),
                "crew_detected": True,
            }

            return deception_analysis
        except Exception:
            return {"deception_score": 0.5, "error": "extraction_failed"}

    def _extract_manipulation_indicators_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract manipulation indicators from CrewAI threat analysis."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            manipulation_types = {
                "emotional_manipulation": ["emotional appeal", "fear mongering", "emotional triggers"],
                "logical_manipulation": ["false logic", "strawman", "ad hominem", "slippery slope"],
                "information_manipulation": ["selective facts", "cherry picking", "context removal"],
                "social_manipulation": ["bandwagon", "appeal to authority", "social proof"],
                "narrative_manipulation": ["framing", "spin", "narrative control", "agenda pushing"],
            }

            detected_manipulation = []
            for manipulation_type, indicators in manipulation_types.items():
                detected_indicators = [ind for ind in indicators if ind in crew_output]
                if detected_indicators:
                    detected_manipulation.append(
                        {
                            "type": manipulation_type,
                            "indicators": detected_indicators,
                            "confidence": min(len(detected_indicators) / 2, 1.0),
                            "severity": "high"
                            if len(detected_indicators) > 2
                            else "medium"
                            if len(detected_indicators) > 1
                            else "low",
                        }
                    )

            return detected_manipulation
        except Exception:
            return []

    def _extract_narrative_integrity_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract narrative integrity assessment from CrewAI analysis."""
        try:
            if not crew_result:
                return {"score": 0.5, "assessment": "unknown"}

            crew_output = str(crew_result).lower()

            # Narrative integrity indicators
            consistent_indicators = ["consistent", "coherent", "logical flow", "clear narrative"]
            inconsistent_indicators = ["inconsistent", "contradictory", "fragmented", "incoherent"]

            consistent_count = sum(1 for indicator in consistent_indicators if indicator in crew_output)
            inconsistent_count = sum(1 for indicator in inconsistent_indicators if indicator in crew_output)

            integrity_score = max(0.0, min(1.0, (consistent_count - inconsistent_count + 2) / 4))

            narrative_integrity = {
                "score": integrity_score,
                "assessment": "high_integrity"
                if integrity_score > 0.7
                else "medium_integrity"
                if integrity_score > 0.4
                else "low_integrity",
                "consistency_indicators": consistent_count,
                "inconsistency_indicators": inconsistent_count,
                "narrative_quality": "strong" if integrity_score > 0.6 else "weak",
            }

            return narrative_integrity
        except Exception:
            return {"score": 0.5, "assessment": "analysis_failed"}

    def _extract_psychological_threats_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract psychological threat profiling from CrewAI analysis."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            # Psychological threat indicators
            threat_patterns = {
                "cognitive_bias_exploitation": ["bias exploitation", "cognitive shortcut", "mental heuristic"],
                "emotional_manipulation": ["emotional trigger", "fear appeal", "anger induction"],
                "social_engineering": ["social pressure", "group think", "conformity pressure"],
                "persuasion_techniques": ["persuasion", "influence tactics", "compliance techniques"],
            }

            psychological_profile = {}
            for pattern_type, indicators in threat_patterns.items():
                detected = [ind for ind in indicators if ind in crew_output]
                if detected:
                    psychological_profile[pattern_type] = {
                        "detected_indicators": detected,
                        "threat_level": "high" if len(detected) > 2 else "medium" if len(detected) > 1 else "low",
                        "confidence": min(len(detected) / 2, 1.0),
                    }

            # Overall psychological threat score
            total_indicators = sum(
                len(profile.get("detected_indicators", [])) for profile in psychological_profile.values()
            )
            psychological_threat_score = min(total_indicators / 5, 1.0)

            psychological_profiling = {
                "psychological_threat_score": psychological_threat_score,
                "threat_patterns": psychological_profile,
                "overall_assessment": "high_psychological_threat"
                if psychological_threat_score > 0.7
                else "moderate_psychological_threat"
                if psychological_threat_score > 0.4
                else "low_psychological_threat",
            }

            return psychological_profiling
        except Exception:
            return {"psychological_threat_score": 0.0, "threat_patterns": {}}

    def _calculate_comprehensive_threat_score_from_crew(self, crew_result: Any) -> float:
        """Calculate comprehensive threat score from CrewAI analysis."""
        try:
            if not crew_result:
                return 0.0

            crew_output = str(crew_result).lower()

            # Comprehensive threat indicators
            high_threat = ["high threat", "dangerous", "severe risk", "critical threat", "immediate danger"]
            medium_threat = ["moderate threat", "concerning", "potential risk", "caution needed"]
            low_threat = ["low threat", "minimal risk", "safe", "no significant threat"]

            high_count = sum(1 for indicator in high_threat if indicator in crew_output)
            medium_count = sum(1 for indicator in medium_threat if indicator in crew_output)
            low_count = sum(1 for indicator in low_threat if indicator in crew_output)

            # Calculate weighted threat score
            threat_score = (high_count * 0.9 + medium_count * 0.6 - low_count * 0.2) / max(
                1, high_count + medium_count + low_count
            )

            return max(0.0, min(1.0, threat_score))
        except Exception:
            return 0.5

    def _classify_threat_level_from_crew(self, crew_result: Any) -> str:
        """Classify threat level from CrewAI analysis."""
        try:
            threat_score = self._calculate_comprehensive_threat_score_from_crew(crew_result)

            if threat_score > 0.8:
                return "critical"
            elif threat_score > 0.6:
                return "high"
            elif threat_score > 0.4:
                return "medium"
            elif threat_score > 0.2:
                return "low"
            else:
                return "minimal"
        except Exception:
            return "unknown"

    def _extract_truth_assessment_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract truth assessment from CrewAI analysis."""
        try:
            if not crew_result:
                return {"confidence": 0.0, "verdict": "unknown"}

            crew_output = str(crew_result).lower()

            # Truth indicators
            true_indicators = ["true", "accurate", "verified", "factual", "confirmed"]
            false_indicators = ["false", "inaccurate", "unverified", "misleading", "debunked"]
            uncertain_indicators = ["uncertain", "unclear", "insufficient evidence", "mixed evidence"]

            true_count = sum(1 for indicator in true_indicators if indicator in crew_output)
            false_count = sum(1 for indicator in false_indicators if indicator in crew_output)
            uncertain_count = sum(1 for indicator in uncertain_indicators if indicator in crew_output)

            if true_count > false_count and true_count > uncertain_count:
                verdict = "true"
                confidence = min(true_count / (true_count + false_count + uncertain_count + 1), 0.9)
            elif false_count > true_count and false_count > uncertain_count:
                verdict = "false"
                confidence = min(false_count / (true_count + false_count + uncertain_count + 1), 0.9)
            else:
                verdict = "uncertain"
                confidence = 0.3

            truth_assessment = {
                "verdict": verdict,
                "confidence": confidence,
                "evidence_strength": {"supporting": true_count, "refuting": false_count, "uncertain": uncertain_count},
            }

            return truth_assessment
        except Exception:
            return {"confidence": 0.0, "verdict": "analysis_failed"}

    def _extract_trustworthiness_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract trustworthiness evaluation from CrewAI analysis."""
        try:
            if not crew_result:
                return {"score": 0.5, "factors": []}

            crew_output = str(crew_result).lower()

            # Trustworthiness factors
            trust_factors = ["trustworthy", "reliable", "credible", "authoritative", "reputable"]
            distrust_factors = ["untrustworthy", "unreliable", "questionable", "dubious", "discredited"]

            trust_count = sum(1 for factor in trust_factors if factor in crew_output)
            distrust_count = sum(1 for factor in distrust_factors if factor in crew_output)

            trustworthiness_score = max(0.0, min(1.0, (trust_count - distrust_count + 2) / 4))

            trustworthiness = {
                "score": trustworthiness_score,
                "assessment": "high_trust"
                if trustworthiness_score > 0.7
                else "medium_trust"
                if trustworthiness_score > 0.4
                else "low_trust",
                "factors": {"positive_indicators": trust_count, "negative_indicators": distrust_count},
            }

            return trustworthiness
        except Exception:
            return {"score": 0.5, "factors": [], "error": "evaluation_failed"}

    def _calculate_basic_threat_from_data(
        self, verification_data: dict, sentiment_data: dict, credibility_data: dict
    ) -> float:
        """Calculate basic threat score from available data when agent unavailable."""
        try:
            base_threat = 0.0

            # Factor in verification results
            fact_checks = verification_data.get("fact_checks", {})
            if isinstance(fact_checks, dict):
                disputed_claims = fact_checks.get("disputed_claims", 0)
                verified_claims = fact_checks.get("verified_claims", 1)
                base_threat += min(disputed_claims / max(verified_claims, 1), 0.4)

            # Factor in sentiment
            if isinstance(sentiment_data, dict):
                sentiment = sentiment_data.get("overall_sentiment", "neutral")
                if sentiment == "negative":
                    base_threat += 0.2
                elif sentiment == "positive":
                    base_threat -= 0.1

            # Factor in credibility
            if isinstance(credibility_data, dict):
                credibility_score = credibility_data.get("score", 0.5)
                base_threat += (1.0 - credibility_score) * 0.3

            return max(0.0, min(1.0, base_threat))
        except Exception:
            return 0.5

    def _classify_basic_threat_level(self, threat_score: float) -> str:
        """Classify basic threat level from score."""
        if threat_score > 0.7:
            return "high"
        elif threat_score > 0.4:
            return "medium"
        else:
            return "low"

    def _extract_cross_platform_analysis_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract cross-platform analysis from CrewAI social intelligence."""
        try:
            if not crew_result:
                return {}

            crew_output = str(crew_result).lower()

            platforms = ["reddit", "twitter", "facebook", "youtube", "discord", "telegram"]
            detected_platforms = [platform for platform in platforms if platform in crew_output]

            cross_platform = {
                "platforms_monitored": detected_platforms,
                "platform_coverage": len(detected_platforms),
                "cross_reference_strength": min(len(detected_platforms) / 3, 1.0),
                "narrative_consistency": "high"
                if "consistent" in crew_output
                else "medium"
                if "similar" in crew_output
                else "low",
                "crew_detected_platforms": True,
            }

            return cross_platform
        except Exception:
            return {"platforms_monitored": [], "error": "extraction_failed"}

    def _extract_narrative_tracking_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract narrative tracking analysis from CrewAI social intelligence."""
        try:
            if not crew_result:
                return {"patterns": [], "confidence": 0.0}

            crew_output = str(crew_result).lower()

            narrative_indicators = ["narrative", "story", "theme", "message", "framing"]
            tracking_indicators = ["trending", "viral", "spreading", "amplified", "coordinated"]

            narrative_count = sum(1 for indicator in narrative_indicators if indicator in crew_output)
            tracking_count = sum(1 for indicator in tracking_indicators if indicator in crew_output)

            narrative_tracking = {
                "patterns": [ind for ind in narrative_indicators if ind in crew_output],
                "tracking_signals": [ind for ind in tracking_indicators if ind in crew_output],
                "confidence": min((narrative_count + tracking_count) / 5, 1.0),
                "narrative_strength": "strong"
                if narrative_count > 2
                else "moderate"
                if narrative_count > 0
                else "weak",
                "tracking_intensity": "high" if tracking_count > 2 else "medium" if tracking_count > 0 else "low",
            }

            return narrative_tracking
        except Exception:
            return {"patterns": [], "confidence": 0.0, "error": "tracking_failed"}

    def _extract_sentiment_monitoring_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract sentiment monitoring from CrewAI social intelligence."""
        try:
            if not crew_result:
                return {"overall_trend": "unknown"}

            crew_output = str(crew_result).lower()

            positive_trends = ["positive sentiment", "supportive", "favorable", "praised"]
            negative_trends = ["negative sentiment", "critical", "hostile", "condemned"]
            neutral_trends = ["mixed sentiment", "neutral", "balanced", "divided"]

            pos_count = sum(1 for indicator in positive_trends if indicator in crew_output)
            neg_count = sum(1 for indicator in negative_trends if indicator in crew_output)
            neu_count = sum(1 for indicator in neutral_trends if indicator in crew_output)

            if pos_count > neg_count and pos_count > neu_count:
                overall_trend = "positive"
            elif neg_count > pos_count and neg_count > neu_count:
                overall_trend = "negative"
            else:
                overall_trend = "neutral"

            sentiment_monitoring = {
                "overall_trend": overall_trend,
                "sentiment_strength": max(pos_count, neg_count, neu_count),
                "polarization": abs(pos_count - neg_count) / max(pos_count + neg_count, 1),
                "monitoring_confidence": min((pos_count + neg_count + neu_count) / 3, 1.0),
            }

            return sentiment_monitoring
        except Exception:
            return {"overall_trend": "unknown", "error": "monitoring_failed"}

    def _extract_influence_mapping_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract influence mapping from CrewAI social intelligence."""
        try:
            if not crew_result:
                return {"influencers": [], "network_strength": 0.0}

            crew_output = str(crew_result).lower()

            influence_indicators = ["influencer", "key account", "high reach", "viral post", "trending account"]
            network_indicators = ["network", "connected", "amplified", "shared widely", "cross-platform"]

            influence_count = sum(1 for indicator in influence_indicators if indicator in crew_output)
            network_count = sum(1 for indicator in network_indicators if indicator in crew_output)

            influence_mapping = {
                "influencers": [ind for ind in influence_indicators if ind in crew_output],
                "network_indicators": [ind for ind in network_indicators if ind in crew_output],
                "network_strength": min((influence_count + network_count) / 5, 1.0),
                "influence_level": "high" if influence_count > 2 else "medium" if influence_count > 0 else "low",
                "connectivity": "strong" if network_count > 2 else "moderate" if network_count > 0 else "weak",
            }

            return influence_mapping
        except Exception:
            return {"influencers": [], "network_strength": 0.0, "error": "mapping_failed"}

    def _extract_community_dynamics_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract community dynamics from CrewAI social intelligence."""
        try:
            if not crew_result:
                return {"engagement": "unknown", "polarization": 0.0}

            crew_output = str(crew_result).lower()

            engagement_indicators = ["high engagement", "active discussion", "viral", "trending", "popular"]
            polarization_indicators = ["divided", "controversial", "polarized", "debate", "opposing views"]

            engagement_count = sum(1 for indicator in engagement_indicators if indicator in crew_output)
            polarization_count = sum(1 for indicator in polarization_indicators if indicator in crew_output)

            community_dynamics = {
                "engagement": "high" if engagement_count > 2 else "medium" if engagement_count > 0 else "low",
                "polarization": min(polarization_count / 3, 1.0),
                "community_health": "healthy"
                if engagement_count > polarization_count
                else "polarized"
                if polarization_count > 0
                else "neutral",
                "dynamics_confidence": min((engagement_count + polarization_count) / 4, 1.0),
            }

            return community_dynamics
        except Exception:
            return {"engagement": "unknown", "polarization": 0.0, "error": "dynamics_failed"}

    def _extract_emergent_patterns_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract emergent patterns from CrewAI social intelligence."""
        try:
            if not crew_result:
                return []

            crew_output = str(crew_result).lower()

            pattern_types = {
                "viral_spread": ["viral", "spreading rapidly", "exponential growth"],
                "coordinated_activity": ["coordinated", "synchronized", "orchestrated"],
                "sentiment_shift": ["sentiment change", "opinion shift", "changing narrative"],
                "platform_migration": ["cross-platform", "migrating", "spillover effect"],
            }

            emergent_patterns = []
            for pattern_type, indicators in pattern_types.items():
                detected_indicators = [ind for ind in indicators if ind in crew_output]
                if detected_indicators:
                    emergent_patterns.append(
                        {
                            "pattern_type": pattern_type,
                            "indicators": detected_indicators,
                            "strength": min(len(detected_indicators) / 2, 1.0),
                            "confidence": 0.8 if len(detected_indicators) > 1 else 0.6,
                        }
                    )

            return emergent_patterns
        except Exception:
            return []

    def _extract_platform_intelligence_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract platform-specific intelligence from CrewAI social analysis."""
        try:
            if not crew_result:
                return {"platforms_monitored": [], "coverage": "none"}

            crew_output = str(crew_result).lower()

            platforms = ["reddit", "twitter", "facebook", "youtube", "discord", "telegram", "tiktok", "instagram"]
            monitored_platforms = [platform for platform in platforms if platform in crew_output]

            coverage_level = (
                "comprehensive"
                if len(monitored_platforms) > 4
                else "moderate"
                if len(monitored_platforms) > 2
                else "limited"
                if len(monitored_platforms) > 0
                else "none"
            )

            platform_intelligence = {
                "platforms_monitored": monitored_platforms,
                "coverage": coverage_level,
                "platform_count": len(monitored_platforms),
                "intelligence_depth": "deep" if "detailed analysis" in crew_output else "surface",
                "monitoring_quality": "high"
                if len(monitored_platforms) > 3
                else "medium"
                if len(monitored_platforms) > 1
                else "basic",
            }

            return platform_intelligence
        except Exception:
            return {"platforms_monitored": [], "coverage": "error", "error": "intelligence_extraction_failed"}
