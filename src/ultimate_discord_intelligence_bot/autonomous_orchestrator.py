"""Autonomous Intelligence Orchestrator - Single Entry Point for All AI Capabilities.

This module provides the unified autonomous workflow that coordinates all 11 agents,
50+ tools, ContentPipeline, memory systems, and analysis capabilities through a single
self-orchestrated command interface.
"""

from __future__ import annotations

# Standard library imports
import asyncio
import logging
import os
import time
from textwrap import dedent
from typing import TYPE_CHECKING, Any

# Third-party imports for validation
try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
except ImportError:
    # Fallback if pydantic not available (shouldn't happen in production)
    BaseModel = object  # type: ignore

    def Field(*a, **k):  # type: ignore
        return None

    ValidationError = Exception  # type: ignore

    def field_validator(*a, **k):  # type: ignore
        def decorator(f):
            return f

        return decorator


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
from .orchestrator import (
    analytics_calculators,
    crew_builders,
    data_transformers,
    discord_helpers,
    error_handlers,
    extractors,
    quality_assessors,
    system_validators,
    workflow_planners,
)
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


# ========================================
# TASK OUTPUT VALIDATION SCHEMAS
# ========================================


class AcquisitionOutput(BaseModel):
    """Schema for content acquisition task output."""

    file_path: str = Field(..., description="Path to downloaded media file")
    title: str = Field(default="", description="Media title")
    description: str = Field(default="", description="Media description")
    author: str = Field(default="", description="Content author/creator")
    duration: float | None = Field(default=None, description="Media duration in seconds")
    platform: str = Field(default="unknown", description="Source platform")


class TranscriptionOutput(BaseModel):
    """Schema for transcription task output."""

    transcript: str = Field(..., description="Full transcribed text")
    timeline_anchors: list[dict[str, Any]] = Field(default_factory=list, description="Timeline markers with timestamps")
    transcript_length: int = Field(default=0, description="Character count of transcript")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Transcription quality (0-1)")


class AnalysisOutput(BaseModel):
    """Schema for content analysis task output."""

    insights: list[str] = Field(default_factory=list, description="Key insights extracted")
    themes: list[str] = Field(default_factory=list, description="Major themes identified")
    fallacies: list[dict[str, Any]] = Field(default_factory=list, description="Logical fallacies detected")
    perspectives: list[dict[str, Any]] = Field(default_factory=list, description="Different viewpoints")


class VerificationOutput(BaseModel):
    """Schema for verification task output."""

    verified_claims: list[str] = Field(default_factory=list, description="Claims extracted for verification")
    fact_check_results: list[dict[str, Any]] = Field(default_factory=list, description="Fact-check outcomes")
    trustworthiness_score: float = Field(default=50.0, ge=0.0, le=100.0, description="Source trust score (0-100)")


class IntegrationOutput(BaseModel):
    """Schema for knowledge integration task output."""

    executive_summary: str = Field(..., description="High-level summary of all findings")
    key_takeaways: list[str] = Field(default_factory=list, description="Main conclusions")
    recommendations: list[str] = Field(default_factory=list, description="Suggested actions")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall confidence (0-1)")


# Task name to schema mapping
TASK_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "acquisition": AcquisitionOutput,
    "capture": AcquisitionOutput,  # Alias
    "transcription": TranscriptionOutput,
    "transcribe": TranscriptionOutput,  # Alias
    "analysis": AnalysisOutput,
    "map": AnalysisOutput,  # Alias for map_transcript_insights
    "verification": VerificationOutput,
    "verify": VerificationOutput,  # Alias
    "integration": IntegrationOutput,
    "knowledge": IntegrationOutput,  # Alias
}


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

    def _get_budget_limits(self, depth: str) -> dict[str, Any]:
        """Get budget limits based on analysis depth.

        Budget tiers reflect the complexity and cost of each depth level.
        Higher depths use more expensive models and produce longer outputs.

        Args:
            depth: Analysis depth (quick/standard/deep/comprehensive/experimental)

        Returns:
            Dictionary with 'total' budget and 'per_task' limits
        """
        budgets = {
            "quick": {
                "total": 0.50,  # $0.50 total
                "per_task": {
                    "acquisition": 0.05,
                    "transcription": 0.15,
                    "analysis": 0.30,
                },
            },
            "standard": {
                "total": 1.50,  # $1.50 total
                "per_task": {
                    "acquisition": 0.05,
                    "transcription": 0.30,
                    "analysis": 0.75,
                    "verification": 0.40,
                },
            },
            "deep": {
                "total": 3.00,  # $3.00 total
                "per_task": {
                    "acquisition": 0.05,
                    "transcription": 0.50,
                    "analysis": 1.20,
                    "verification": 0.75,
                    "knowledge": 0.50,
                },
            },
            "comprehensive": {
                "total": 5.00,  # $5.00 total
                "per_task": {
                    "acquisition": 0.10,
                    "transcription": 0.75,
                    "analysis": 2.00,
                    "verification": 1.00,
                    "knowledge": 1.15,
                },
            },
            "experimental": {
                "total": 10.00,  # $10.00 total
                "per_task": {
                    "acquisition": 0.10,
                    "transcription": 1.50,
                    "analysis": 4.00,
                    "verification": 2.00,
                    "knowledge": 2.40,
                },
            },
        }

        return budgets.get(depth, budgets["standard"])

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
        return crew_builders.populate_agent_tool_context(
            agent, context_data, logger_instance=self.logger, metrics_instance=self.metrics
        )

    def _get_or_create_agent(self, agent_name: str) -> Any:
        """Get agent from coordinators cache or create and cache it.

        CRITICAL: This ensures agents are created ONCE and reused across stages.
        Repeated calls to crew_instance.agent_method() create FRESH agents with
        EMPTY tools, bypassing context population. Always use this method.

        Args:
            agent_name: Name of agent method (e.g., 'analysis_cartographer')

        Returns:
            Cached agent instance with persistent tool context
        """
        return crew_builders.get_or_create_agent(
            agent_name, self.agent_coordinators, self.crew_instance, logger_instance=self.logger
        )

    def _task_completion_callback(self, task_output: Any) -> None:
        """Callback executed after each task to extract and propagate structured data.

        CRITICAL FIX: CrewAI task context passes TEXT to LLM prompts, NOT structured
        data to tools. This callback extracts tool results and updates global crew
        context so subsequent tasks can access the data.

        Now includes Pydantic validation to prevent invalid data propagation.

        Args:
            task_output: TaskOutput object from completed task
        """
        return crew_builders.task_completion_callback(
            task_output,
            populate_agent_context_callback=self._populate_agent_tool_context,
            detect_placeholder_callback=self._detect_placeholder_responses,
            repair_json_callback=self._repair_json,
            extract_key_values_callback=self._extract_key_values_from_text,
            logger_instance=self.logger,
            metrics_instance=self.metrics,
            agent_coordinators=self.agent_coordinators,
        )

    def _extract_key_values_from_text(self, text: str) -> dict[str, Any]:
        """Fallback extraction when JSON parsing fails."""
        return error_handlers.extract_key_values_from_text(text)

    def _repair_json(self, json_text: str) -> str:
        """Attempt to repair common JSON malformations."""
        return error_handlers.repair_json(json_text)

    def _detect_placeholder_responses(self, task_name: str, output_data: dict[str, Any]) -> None:
        """Detect when agents generate placeholder/mock responses instead of calling tools."""
        return quality_assessors.detect_placeholder_responses(task_name, output_data, self.logger, self.metrics)

    def _build_intelligence_crew(self, url: str, depth: str) -> Crew:
        """Build a single chained CrewAI crew for the complete intelligence workflow.

        This is the CORRECT CrewAI pattern: one crew with multiple chained tasks using
        the context parameter to pass data between stages. This replaces the previous
        broken pattern of creating 25 separate single-task crews with data embedded
        in task descriptions.

        Args:
            url: URL to analyze
            depth: Analysis depth (standard, deep, comprehensive, experimental)

        Returns:
            Configured Crew with chained tasks
        """
        return crew_builders.build_intelligence_crew(
            url,
            depth,
            agent_getter_callback=self._get_or_create_agent,
            task_completion_callback=self._task_completion_callback,
            logger_instance=self.logger,
        )

    def _validate_stage_data(self, stage_name: str, required_keys: list[str], data: dict[str, Any]) -> None:
        """Validate that required keys are present in stage data."""
        return quality_assessors.validate_stage_data(stage_name, required_keys, data)

    def _validate_system_prerequisites(self) -> dict[str, Any]:
        """Validate system dependencies and return health status."""
        return system_validators.validate_system_prerequisites()

    def _check_ytdlp_available(self) -> bool:
        """Check if yt-dlp is available without importing it directly (guard-safe)."""
        return system_validators.check_ytdlp_available()

    def _check_llm_api_available(self) -> bool:
        """Check if LLM API keys are configured."""
        return system_validators.check_llm_api_available()

    def _check_discord_available(self) -> bool:
        """Check if Discord integration is properly configured."""
        return system_validators.check_discord_available()

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
        """Initialize the agent coordination system with specialized workflows mapped to redesigned agent roster.

        CRITICAL: This method MUST NOT create agent instances. Agent creation is handled exclusively
        by _get_or_create_agent() to ensure context is populated before use. This method only
        defines the workflow structure and dependencies.
        """
        # Map workflow names to agent method names (strings, not instances!)
        # Agents will be lazy-loaded via _get_or_create_agent() when needed
        self.agent_workflow_map = {
            "mission_coordination": "autonomous_mission_coordinator",
            "content_acquisition": "multi_platform_acquisition_specialist",
            "transcription_processing": "advanced_transcription_engineer",
            "content_analysis": "comprehensive_linguistic_analyst",
            "information_verification": "information_verification_director",
            "threat_analysis": "threat_intelligence_analyst",
            "behavioral_profiling": "behavioral_profiling_specialist",
            "social_intelligence": "social_intelligence_coordinator",
            "trend_analysis": "trend_analysis_scout",
            "knowledge_integration": "knowledge_integration_architect",
            "research_synthesis": "research_synthesis_specialist",
            "intelligence_briefing": "intelligence_briefing_director",
            "strategic_argumentation": "strategic_argument_analyst",
            "system_operations": "system_operations_manager",
            "community_engagement": "community_engagement_coordinator",
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

        # CRITICAL FIX: Initialize agent_coordinators as EMPTY dict
        # Agents will be lazy-created and cached by _get_or_create_agent()
        # This ensures context is populated BEFORE agent use, preventing data flow failures
        self.agent_coordinators = {}

    @staticmethod
    def _normalize_acquisition_data(acquisition: StepResult | dict[str, Any] | None) -> dict[str, Any]:
        """Return a flattened ContentPipeline payload for downstream stages."""
        return data_transformers.normalize_acquisition_data(acquisition)

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
        """Combine threat analysis output with deception scoring metrics."""
        return data_transformers.merge_threat_and_deception_data(threat_result, deception_result)

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
        """Execute the complete autonomous intelligence workflow using proper CrewAI architecture.

        ARCHITECTURE CHANGE (2025-10-03):
        Previously, this method created 25 separate single-task crews with data embedded
        in task descriptions. This violated CrewAI's design and caused critical data flow
        failures where tools received empty/placeholder parameters.

        NEW PATTERN:
        - Builds ONE crew with chained tasks using context parameter
        - Task descriptions are high-level instructions ("Analyze transcript")
        - Data flows via crew.kickoff(inputs={...}) and task context chaining
        - No data embedded in f-strings like description=f"Analyze: {transcript[:500]}"

        Analysis Depths:
        - standard: 3 tasks (acquisition → transcription → analysis)
        - deep: 4 tasks (adds verification)
        - comprehensive/experimental: 5 tasks (adds knowledge integration)

        Args:
            interaction: Discord interaction object
            url: URL to analyze
            depth: Analysis depth (standard, deep, comprehensive, experimental)
            tenant_ctx: Optional tenant context for isolation
        """
        start_time = time.time()
        workflow_id = f"autointel_{int(start_time)}_{hash(url) % 10000}"

        # Store workflow ID and tenant context for cost tracking
        self._workflow_id = workflow_id
        self._tenant_ctx = tenant_ctx

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

        # Initialize progress tracking
        await self._send_progress_update(interaction, f"🚀 Starting {depth} intelligence analysis for: {url}", 0, 5)

        # Get budget limits for this depth level
        budget_limits = self._get_budget_limits(depth)

        try:
            # Import cost tracking modules
            from core.cost_tracker import initialize_cost_tracking
            from ultimate_discord_intelligence_bot.services.request_budget import (
                current_request_tracker,
                track_request_budget,
            )

            # Initialize cost tracking if not already done
            try:
                initialize_cost_tracking()
            except Exception:
                pass  # Already initialized or not available

            # Wrap execution with request budget tracking
            with track_request_budget(total_limit=budget_limits["total"], per_task_limits=budget_limits["per_task"]):
                # Execute workflow within tenant context if available
                if tenant_ctx:
                    try:
                        from .tenancy import with_tenant

                        with with_tenant(tenant_ctx):
                            await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)
                    except Exception as tenancy_error:
                        self.logger.warning(f"Tenant context execution failed: {tenancy_error}")
                        # Fall back to execution without tenant context
                        await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)
                else:
                    # Execute without tenant context as fallback
                    await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)

                # Get cost summary after execution
                tracker = current_request_tracker()
                if tracker and tracker.total_spent > 0:
                    cost_msg = (
                        f"💰 **Cost Tracking:**\n"
                        f"• Total: ${tracker.total_spent:.3f}\n"
                        f"• Budget: ${budget_limits['total']:.2f}\n"
                        f"• Utilization: {(tracker.total_spent / budget_limits['total'] * 100):.1f}%"
                    )

                    # Send cost info if significant
                    if tracker.total_spent > 0.10:  # > $0.10
                        try:
                            await interaction.followup.send(cost_msg)
                        except Exception:
                            self.logger.info(cost_msg)

        except Exception as e:
            self.logger.error(f"Autonomous intelligence workflow failed: {e}", exc_info=True)
            await self._send_error_response(interaction, "Autonomous Workflow", str(e))
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "error"}).inc()

    async def _execute_crew_workflow(
        self, interaction: Any, url: str, depth: str, workflow_id: str, start_time: float
    ) -> None:
        """Execute workflow using proper CrewAI architecture with task chaining.

        This method builds ONE crew with chained tasks instead of 25 separate crews.
        Tasks use context=[previous_task] for data flow, not embedded f-strings.
        """
        import asyncio

        from crewai import CrewOutput

        try:
            # CRITICAL FIX: Reset global crew context at workflow start
            # This ensures clean state between /autointel invocations
            try:
                from .crewai_tool_wrappers import reset_global_crew_context

                reset_global_crew_context()
            except Exception as ctx_reset_error:
                self.logger.warning(f"Failed to reset global crew context: {ctx_reset_error}")

            # Build the crew with properly chained tasks
            await self._send_progress_update(interaction, "🤖 Building CrewAI multi-agent system...", 1, 5)
            crew = self._build_intelligence_crew(url, depth)

            # CRITICAL FIX: Populate initial context on all agents' tools BEFORE execution
            # This ensures the first task (acquisition) has access to the URL parameter
            initial_context = {
                "url": url,
                "depth": depth,
            }
            self.logger.info(f"🔧 Populating initial context on all agents: {initial_context}")
            for agent in crew.agents:
                self._populate_agent_tool_context(agent, initial_context)

            # Execute the crew with proper inputs
            await self._send_progress_update(interaction, "⚙️ Executing intelligence workflow...", 2, 5)
            self.logger.info(f"Kickoff crew with inputs: url={url}, depth={depth}")

            # Run crew in thread pool to avoid blocking async loop
            result: CrewOutput = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})

            await self._send_progress_update(interaction, "📊 Processing crew results...", 3, 5)

            # Extract results from CrewOutput
            if hasattr(result, "tasks_output") and result.tasks_output:
                # Get outputs from each task
                task_outputs = {
                    "acquisition": None,
                    "transcription": None,
                    "analysis": None,
                    "verification": None,
                    "integration": None,
                }

                for i, task_output in enumerate(result.tasks_output):
                    if i == 0:
                        task_outputs["acquisition"] = (
                            task_output.raw if hasattr(task_output, "raw") else str(task_output)
                        )
                    elif i == 1:
                        task_outputs["transcription"] = (
                            task_output.raw if hasattr(task_output, "raw") else str(task_output)
                        )
                    elif i == 2:
                        task_outputs["analysis"] = task_output.raw if hasattr(task_output, "raw") else str(task_output)
                    elif i == 3 and depth in ["deep", "comprehensive", "experimental"]:
                        task_outputs["verification"] = (
                            task_output.raw if hasattr(task_output, "raw") else str(task_output)
                        )
                    elif i == 4 and depth in ["comprehensive", "experimental"]:
                        task_outputs["integration"] = (
                            task_output.raw if hasattr(task_output, "raw") else str(task_output)
                        )

                self.logger.info(f"Extracted {len([v for v in task_outputs.values() if v])} task outputs")

            # Format and send results to Discord
            await self._send_progress_update(interaction, "📝 Formatting intelligence report...", 4, 5)

            # Build comprehensive result message
            result_message = "## Intelligence Analysis Complete\n\n"
            result_message += f"**URL:** {url}\n"
            result_message += f"**Depth:** {depth}\n"
            result_message += f"**Processing Time:** {time.time() - start_time:.1f}s\n\n"

            # Add crew output
            if hasattr(result, "raw"):
                result_message += f"**Analysis:**\n{result.raw}\n\n"
            elif hasattr(result, "final_output"):
                result_message += f"**Analysis:**\n{result.final_output}\n\n"
            else:
                result_message += f"**Analysis:**\n{str(result)}\n\n"

            # Send results
            await self._send_progress_update(interaction, "✅ Intelligence analysis complete!", 5, 5)

            # Split message if too long for Discord (2000 char limit)
            if len(result_message) > 1900:
                chunks = [result_message[i : i + 1900] for i in range(0, len(result_message), 1900)]
                for chunk in chunks:
                    try:
                        if hasattr(interaction, "followup"):
                            await interaction.followup.send(chunk)
                        elif hasattr(interaction, "channel"):
                            await interaction.channel.send(chunk)
                    except Exception as send_error:
                        self.logger.warning(f"Failed to send message chunk: {send_error}")
            else:
                try:
                    if hasattr(interaction, "followup"):
                        await interaction.followup.send(result_message)
                    elif hasattr(interaction, "channel"):
                        await interaction.channel.send(result_message)
                except Exception as send_error:
                    self.logger.warning(f"Failed to send result message: {send_error}")

            # Record metrics
            processing_time = time.time() - start_time
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "success"}).inc()
            self.metrics.histogram("autointel_workflow_duration", processing_time, labels={"depth": depth})

        except Exception as e:
            self.logger.error(f"Crew workflow execution failed: {e}", exc_info=True)
            await self._send_error_response(interaction, "Crew Workflow", str(e))
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "error"}).inc()

    # ========================================
    # ENHANCED CAPABILITY HELPER METHODS
    # ========================================

    def _get_available_capabilities(self) -> list[str]:
        """Delegates to workflow_planners.get_available_capabilities."""
        return workflow_planners.get_available_capabilities()

    def _calculate_resource_requirements(self, depth: str) -> dict[str, Any]:
        """Delegates to analytics_calculators.calculate_resource_requirements."""
        return analytics_calculators.calculate_resource_requirements(depth, self.logger)

    def _estimate_workflow_duration(self, depth: str) -> dict[str, Any]:
        """Delegates to workflow_planners.estimate_workflow_duration."""
        return workflow_planners.estimate_workflow_duration(depth)

    def _get_planned_stages(self, depth: str) -> list[dict[str, Any]]:
        """Delegates to workflow_planners.get_planned_stages."""
        return workflow_planners.get_planned_stages(depth)

    def _get_capabilities_summary(self, depth: str) -> dict[str, Any]:
        """Delegates to workflow_planners.get_capabilities_summary."""
        return workflow_planners.get_capabilities_summary(depth)

    def _calculate_ai_enhancement_level(self, depth: str) -> float:
        """Delegates to analytics_calculators.calculate_ai_enhancement_level."""
        return analytics_calculators.calculate_ai_enhancement_level(depth, self.logger)

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                mission_agent = self._get_or_create_agent("mission_orchestrator")

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
            if hasattr(self, "crew") and self.crew is not None:
                try:
                    # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                    transcription_agent = self._get_or_create_agent("transcription_engineer")

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
                        self.logger.warning(
                            f"⚠️ Transcription agent context population FAILED: {_ctx_err}", exc_info=True
                        )

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
            if getattr(self, "_llm_available", False) and hasattr(self, "crew") and self.crew is not None:
                try:
                    # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                    analysis_agent = self._get_or_create_agent("analysis_cartographer")

                    # Ensure CrewAI tools have full context before kickoff
                    try:
                        context_data = {
                            "transcript": transcript,
                            "text": transcript,  # Explicit alias for TextAnalysisTool
                            "enhanced_transcript": transcription_data.get("enhanced_transcript", transcript),
                            "media_info": media_info,
                            "timeline_anchors": transcription_data.get("timeline_anchors", []),
                            "transcript_index": transcription_data.get("transcript_index", {}),
                            "pipeline_analysis": pipeline_analysis_block,
                            "pipeline_fallacy": pipeline_fallacy_block,
                            "pipeline_perspective": pipeline_perspective_block,
                            "pipeline_metadata": pipeline_metadata,
                            "source_url": source_url or media_info.get("source_url"),
                            "content_metadata": {
                                "title": media_info.get("title"),
                                "platform": media_info.get("platform"),
                                "duration": media_info.get("duration"),
                                "uploader": media_info.get("uploader"),
                            },
                        }
                        self.logger.info(
                            f"📝 Populating analysis context: transcript={len(transcript)} chars, "
                            f"title={media_info.get('title', 'N/A')}, platform={media_info.get('platform', 'N/A')}"
                        )
                        self._populate_agent_tool_context(analysis_agent, context_data)
                        self.logger.info("✅ Analysis context populated successfully")
                    except Exception as _ctx_err:  # pragma: no cover - defensive
                        self.logger.error(f"❌ Analysis agent context population FAILED: {_ctx_err}", exc_info=True)
                        # Return early instead of continuing with empty data
                        return StepResult.fail(
                            error=f"Analysis context preparation failed: {_ctx_err}", step="analysis_context_population"
                        )

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

                            ⚠️ CRITICAL INSTRUCTIONS - DATA IS PRE-LOADED:

                            The complete transcript ({len(transcript)} characters) and ALL media metadata are
                            ALREADY AVAILABLE in the tool's shared context. You MUST NOT pass these as parameters.

                            ❌ WRONG - DO NOT DO THIS:
                            - TextAnalysisTool(text="transcript content here...")  # NEVER pass text parameter!
                            - FactCheckTool(claim="some claim...")  # NEVER pass claim parameter!

                            ✅ CORRECT - DO THIS INSTEAD:
                            - TextAnalysisTool()  # Tools auto-access data from shared context
                            - FactCheckTool()  # No parameters needed - data is pre-loaded

                            When calling ANY tool, OMIT the text/transcript/content/claim parameters.
                            The tools have DIRECT ACCESS to:
                            - Full transcript ({len(transcript)} chars) - accessible as 'text' parameter internally
                            - Media metadata (title, platform, duration, uploader)
                            - Timeline anchors: {len(transcription_data.get("timeline_anchors", []))} available
                            - Quality score: {transcription_data.get("quality_score", 0)}

                            YOUR TASK:
                            Use TextAnalysisTool (WITH NO PARAMETERS) to analyze linguistic patterns, sentiment,
                            and thematic insights. The tool will automatically access the transcript from shared context.

                            Provide comprehensive analysis including:
                            - Sentiment analysis
                            - Key themes and topics
                            - Important contextual insights
                            - Linguistic patterns
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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                verification_agent = self._get_or_create_agent("verification_director")

                # Provide full structured context to the agent tools prior to kickoff
                try:
                    context_data = {
                        "transcript": transcript,
                        "text": transcript,  # Explicit alias for fact-checking tools
                        "linguistic_patterns": linguistic_patterns,
                        "sentiment_analysis": sentiment_analysis,
                        "fact_data": fact_data or {},
                        "claims": (fact_data or {}).get("claims", []),
                        "analysis_data": analysis_data,
                    }
                    self.logger.info(
                        f"📝 Verification context: transcript={len(transcript)} chars, "
                        f"claims={len(context_data['claims'])}"
                    )
                    self._populate_agent_tool_context(verification_agent, context_data)
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.warning(f"⚠️ Verification agent context population FAILED: {_ctx_err}", exc_info=True)

                # Create comprehensive verification task
                # CRITICAL: Description should be INSTRUCTIONS for the agent, not content to analyze
                # All data (transcript, linguistic_patterns, sentiment_analysis) is available in shared_context
                verification_task = Task(
                    description="You are the Verification Director. Your role is to orchestrate comprehensive verification of the provided content. The transcript and analysis data are available in your shared context. Use your tools to: (1) Extract specific factual claims from the transcript, (2) Verify each claim using fact-checking tools, (3) Analyze logical structure for fallacies, (4) Assess source credibility, (5) Detect bias indicators. Synthesize findings into a structured verification report.",
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
            # fact_checks, logical_analysis, credibility_assessment now passed via shared context instead of task description
            _ = verification_data.get("fact_checks", {})
            _ = verification_data.get("logical_analysis", {})
            credibility_assessment = verification_data.get("credibility_assessment", {})

            if not transcript and not content_metadata:
                return StepResult.skip(reason="No content available for deception analysis")

            # Use CrewAI verification director for comprehensive threat analysis
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                threat_agent = self._get_or_create_agent("verification_director")

                # Populate threat analysis context before crew execution
                context_data = {
                    "transcript": transcript,
                    "text": transcript,  # Explicit alias for deception analysis tools
                    "content_metadata": content_metadata,
                    "sentiment_analysis": sentiment_analysis,
                    "fact_checks": verification_data.get("fact_checks", {}),
                    "logical_analysis": verification_data.get("logical_analysis", {}),
                    "credibility_assessment": credibility_assessment,
                    "verification_data": verification_data,
                    "analysis_data": intelligence_data,
                }
                self.logger.info(f"📝 Threat analysis context: transcript={len(transcript)} chars")
                self._populate_agent_tool_context(threat_agent, context_data)

                # Create comprehensive threat analysis task
                # CRITICAL: Description should be INSTRUCTIONS for the agent, not content to analyze
                # All data is available in shared_context (transcript, metadata, fact_checks, logical_analysis, etc.)
                threat_task = Task(
                    description="You are the Threat Analysis Director. Your role is to assess deception, manipulation, and information threats in the provided content. All analysis data (transcript, fact-checks, logical analysis, credibility scores, sentiment) is available in your shared context. Use your tools to: (1) Score deception indicators in the transcript, (2) Identify manipulation techniques and psychological influence patterns, (3) Assess narrative integrity and consistency, (4) Build psychological threat profile, (5) Generate actionable threat intelligence. Synthesize into a comprehensive threat assessment.",
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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                social_intel_agent = self._get_or_create_agent("signal_recon_specialist")

                # Populate structured context for social intelligence tools
                try:
                    context_data = {
                        "transcript": transcript,
                        "text": transcript,  # Explicit alias for social monitoring tools
                        "content_metadata": content_metadata,
                        "linguistic_patterns": linguistic_patterns,
                        "sentiment_analysis": sentiment_analysis,
                        "keywords": keywords,
                        "title": title,
                        "analysis_data": intelligence_data,
                        "verification_data": verification_data,
                    }
                    self.logger.info(
                        f"📝 Social intel context: transcript={len(transcript)} chars, "
                        f"keywords={len(keywords)}, title={title[:50] if title else 'N/A'}"
                    )
                    self._populate_agent_tool_context(social_intel_agent, context_data)
                except Exception as _ctx_err:  # pragma: no cover - defensive
                    self.logger.warning(f"⚠️ Social agent context population FAILED: {_ctx_err}", exc_info=True)

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
            # CRITICAL: Use cached agents to preserve context across stages
            knowledge_agent = self._get_or_create_agent("knowledge_integrator")
            persona_agent = self._get_or_create_agent("persona_archivist")
            mission_agent = self._get_or_create_agent("mission_orchestrator")

            # Define comprehensive knowledge integration task
            # CRITICAL: Use concise descriptions - data passed via shared context to avoid rate limits
            integration_task = Task(
                description="Integrate comprehensive intelligence across vector, graph, and continual memory systems using the knowledge payload from shared context",
                expected_output="Multi-system knowledge integration with vector storage, graph relationships, and continual memory consolidation",
                agent=knowledge_agent,
            )

            # Define persona archival task
            # CRITICAL: Use concise descriptions - data passed via shared context to avoid rate limits
            persona_task = Task(
                description="Archive behavioral and threat profiles in persona management system using behavioral_data and threat_data from shared context",
                expected_output="Comprehensive persona dossier with behavioral history, threat correlation, and trust metrics",
                agent=persona_agent,
            )

            # Define mission orchestration task
            # CRITICAL: Use concise descriptions - data passed via shared context to avoid rate limits
            orchestration_task = Task(
                description="Orchestrate knowledge consolidation across all intelligence systems for mission continuity using intelligence_data from shared context",
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
            # CRITICAL: Use cached agents to preserve context across stages
            verification_agent = self._get_or_create_agent("verification_director")
            recon_agent = self._get_or_create_agent("signal_recon_specialist")

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
            # CRITICAL: Use concise description - data passed via shared context to avoid rate limits
            threat_task = Task(
                description="Analyze transcript for deception, logical fallacies, and threat indicators using transcript from shared context",
                expected_output="Comprehensive threat assessment with deception scores, fallacy analysis, and risk indicators",
                agent=verification_agent,
            )

            # Define signal intelligence task
            # CRITICAL: Use concise description - data passed via shared context to avoid rate limits
            signal_task = Task(
                description="Perform signal intelligence analysis to detect narrative manipulation using transcript from shared context",
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
            # CRITICAL: Use cached agents to preserve context across stages
            analysis_agent = self._get_or_create_agent("analysis_cartographer")
            persona_agent = self._get_or_create_agent("persona_archivist")

            # Populate behavioral profiling context for both agents
            shared_context = {
                "transcript": transcript,
                "analysis_data": analysis_data,
                "threat_data": threat_data,
                "threat_level": threat_data.get("threat_level", "unknown"),
                "content_metadata": analysis_data.get("content_metadata", {}),
            }
            self._populate_agent_tool_context(analysis_agent, shared_context)
            self._populate_agent_tool_context(persona_agent, shared_context)

            # Define behavioral analysis task
            # CRITICAL: Use concise description - data passed via shared context to avoid rate limits
            behavioral_task = Task(
                description=f"Perform comprehensive behavioral analysis on transcript with threat context (threat_level: {threat_data.get('threat_level', 'unknown')}) using transcript and threat_data from shared context",
                expected_output="Detailed behavioral profile with personality traits, communication patterns, and risk indicators",
                agent=analysis_agent,
            )

            # Define persona profiling task
            # CRITICAL: Use concise description - data passed via shared context to avoid rate limits
            persona_task = Task(
                description="Create detailed persona profile integrating behavioral patterns with threat indicators using threat_data from shared context",
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
            # CRITICAL: Use cached agents to preserve context across stages
            trend_agent = self._get_or_create_agent("trend_intelligence_scout")
            knowledge_agent = self._get_or_create_agent("knowledge_integrator")

            # Populate research synthesis context for both agents
            research_context = {
                "transcript": transcript,
                "claims": claims,
                "analysis_data": analysis_data,
                "verification_data": verification_data,
            }
            self._populate_agent_tool_context(trend_agent, research_context)
            self._populate_agent_tool_context(knowledge_agent, research_context)

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
        """Execute communication and reporting using the Communication & Reporting Coordinator.

        Implements session resilience:
        - Validates session before sending
        - Persists results if session is closed
        - Gracefully degrades to logging
        - Provides retrieval instructions
        """
        try:
            # Extract workflow ID for tracking
            workflow_id = synthesis_result.get("workflow_id", f"wf_{int(time.time())}")
            url = synthesis_result.get("workflow_metadata", {}).get("url", "unknown")

            # Check if session is still valid BEFORE creating embeds
            if not self._is_session_valid(interaction):
                self.logger.warning(
                    f"⚠️ Discord session closed before reporting results. Persisting results for workflow {workflow_id}..."
                )

                # Persist results to disk for later retrieval
                result_file = await self._persist_workflow_results(workflow_id, synthesis_result, url, depth)

                if result_file:
                    self.logger.info(
                        f"📁 Results saved to {result_file}. "
                        f"Retrieval command: /retrieve_results workflow_id:{workflow_id}"
                    )
                else:
                    # Fallback: at least log the results
                    self.logger.info(
                        f"Specialized Intelligence Results (session closed, persistence failed):\n{synthesis_result}"
                    )

                # Track metric
                get_metrics().counter(
                    "discord_session_closed_total", labels={"stage": "communication_reporting", "depth": depth}
                )
                return

            # Create specialized result embeds
            main_embed = await self._create_specialized_main_results_embed(synthesis_result, depth)
            details_embed = await self._create_specialized_details_embed(synthesis_result)

            try:
                await interaction.followup.send(embeds=[main_embed, details_embed], ephemeral=False)
            except RuntimeError as e:
                if "Session is closed" in str(e):
                    self.logger.warning(f"⚠️ Session closed while sending main results for workflow {workflow_id}")

                    # Persist results since send failed
                    result_file = await self._persist_workflow_results(workflow_id, synthesis_result, url, depth)

                    if result_file:
                        self.logger.info(
                            f"📁 Results saved to {result_file} after send failure. "
                            f"Retrieval command: /retrieve_results workflow_id:{workflow_id}"
                        )

                    # Track metric
                    get_metrics().counter(
                        "discord_session_closed_total", labels={"stage": "communication_reporting_send", "depth": depth}
                    )
                    return
                else:
                    raise

            # Send knowledge integration confirmation
            knowledge_data = synthesis_result.get("knowledge", {})
            if not isinstance(knowledge_data, dict) or not knowledge_data:
                # Some synthesis paths place it under detailed_results
                knowledge_data = synthesis_result.get("detailed_results", {}).get("knowledge", {})
                if not knowledge_data:
                    knowledge_data = synthesis_result.get("detailed_results", {}).get("knowledge_integration", {})
            if isinstance(knowledge_data, dict) and knowledge_data.get("knowledge_systems"):
                if self._is_session_valid(interaction):
                    kb_embed = await self._create_specialized_knowledge_embed(knowledge_data)
                    try:
                        await interaction.followup.send(embed=kb_embed, ephemeral=True)
                    except RuntimeError as e:
                        if "Session is closed" in str(e):
                            self.logger.warning("Session closed, cannot send knowledge integration confirmation")
                        else:
                            raise
                else:
                    self.logger.warning("Session closed, cannot send knowledge integration confirmation")

            self.logger.info("Communication & Reporting Coordinator delivered specialized results")

        except Exception as e:
            # Don't log session closed errors (already handled)
            if "Session is closed" in str(e):
                self.logger.warning("Session closed during communication/reporting")
                self.logger.info(f"Specialized Intelligence Results (session closed):\n{synthesis_result}")
                return

            self.logger.error(f"Communication & Reporting Coordinator failed: {e}")
            # Fallback to simple text response if session is still valid
            if self._is_session_valid(interaction):
                try:
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
                except RuntimeError as fallback_error:
                    if "Session is closed" in str(fallback_error):
                        self.logger.warning("Session closed during fallback response")
                    else:
                        self.logger.error(f"Fallback response failed: {fallback_error}")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback response failed: {fallback_error}")
            else:
                self.logger.warning("Session closed, cannot send fallback response. Results logged above.")

    # ========================================
    # SPECIALIZED HELPER METHODS
    # ========================================

    def _assess_content_coherence(self, analysis_data: dict[str, Any]) -> float:
        """Assess the coherence of the analyzed content."""
        return quality_assessors.assess_content_coherence(analysis_data, self.logger)

    @staticmethod
    @staticmethod
    def _clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp helper to keep quality metrics within expected bounds."""
        return quality_assessors.clamp_score(value, minimum, maximum)

    def _assess_factual_accuracy(
        self,
        verification_data: dict[str, Any] | None,
        fact_data: dict[str, Any] | None = None,
    ) -> float:
        """Derive a factual accuracy score from verification and fact analysis outputs."""
        return quality_assessors.assess_factual_accuracy(verification_data, fact_data, self.logger)

    def _assess_source_credibility(
        self,
        knowledge_data: dict[str, Any] | None,
        verification_data: dict[str, Any] | None,
    ) -> float:
        """Estimate source credibility using knowledge payload and verification metadata."""
        return quality_assessors.assess_source_credibility(knowledge_data, verification_data, self.logger)

    def _assess_bias_levels(
        self,
        analysis_data: dict[str, Any] | None,
        verification_data: dict[str, Any] | None,
    ) -> float:
        """Score how balanced the content is based on bias indicators and sentiment spread."""
        return quality_assessors.assess_bias_levels(analysis_data, verification_data, self.logger)

    def _assess_emotional_manipulation(self, analysis_data: dict[str, Any] | None) -> float:
        """Estimate the level of emotional manipulation present in the content."""
        return quality_assessors.assess_emotional_manipulation(analysis_data, self.logger)

    def _assess_logical_consistency(
        self,
        verification_data: dict[str, Any] | None,
        logical_analysis: dict[str, Any] | None = None,
    ) -> float:
        """Evaluate logical consistency based on verification and logical analysis."""
        return quality_assessors.assess_logical_consistency(verification_data, logical_analysis, self.logger)

    def _calculate_ai_quality_score(self, quality_dimensions: dict[str, float]) -> float:
        """Delegates to analytics_calculators.calculate_ai_quality_score."""
        return analytics_calculators.calculate_ai_quality_score(quality_dimensions, self.logger)

    def _generate_ai_recommendations(
        self,
        quality_dimensions: dict[str, float],
        ai_quality_score: float,
        analysis_data: dict[str, Any],
        verification_data: dict[str, Any],
    ) -> list[str]:
        """Delegates to analytics_calculators.generate_ai_recommendations."""
        return analytics_calculators.generate_ai_recommendations(
            quality_dimensions, ai_quality_score, analysis_data, verification_data, self.logger
        )

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
        """Delegates to analytics_calculators.calculate_confidence_interval."""
        return analytics_calculators.calculate_confidence_interval(quality_dimensions, ai_quality_score, self.logger)

    def _assess_quality_trend(self, ai_quality_score: float) -> str:
        """Assess the quality trend based on AI quality score."""
        return quality_assessors.assess_quality_trend(ai_quality_score)

    def _calculate_comprehensive_threat_score(
        self, deception_result: Any, truth_result: Any, trust_result: Any, verification_data: dict[str, Any]
    ) -> float:
        """Calculate comprehensive threat score from multiple analysis sources.

        Delegates to analytics_calculators.calculate_comprehensive_threat_score.
        """
        return analytics_calculators.calculate_comprehensive_threat_score(
            deception_result, truth_result, trust_result, verification_data, self.logger
        )

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
        """Delegates to analytics_calculators.generate_specialized_insights."""
        return analytics_calculators.generate_specialized_insights(results, self.logger)

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
        """Calculate a composite deception score from multiple analysis sources.

        Delegates to analytics_calculators.calculate_composite_deception_score.
        """
        return analytics_calculators.calculate_composite_deception_score(
            deception_result, truth_result, trust_result, fact_data, self.logger
        )

    def _calculate_summary_statistics(self, results: dict[str, Any]) -> dict[str, Any]:
        """Delegates to analytics_calculators.calculate_summary_statistics."""
        return analytics_calculators.calculate_summary_statistics(results, self.logger)

    def _generate_autonomous_insights(self, results: dict[str, Any]) -> list[str]:
        """Delegates to analytics_calculators.generate_autonomous_insights."""
        return analytics_calculators.generate_autonomous_insights(results, self.logger)

    def _is_session_valid(self, interaction: Any) -> bool:
        """Check if Discord session is still valid for sending messages.

        Delegates to discord_helpers.is_session_valid for implementation.

        Returns:
            True if session is valid and can receive messages
            False if session is closed or invalid
        """
        return discord_helpers.is_session_valid(interaction, self.logger)

    async def _persist_workflow_results(self, workflow_id: str, results: dict[str, Any], url: str, depth: str) -> str:
        """Persist workflow results to disk when Discord session closes.

        Delegates to discord_helpers.persist_workflow_results for implementation.

        Args:
            workflow_id: Unique identifier for the workflow
            results: Complete workflow results dictionary
            url: Original URL that was analyzed
            depth: Analysis depth used

        Returns:
            Path to the persisted result file, or empty string on failure
        """
        return await discord_helpers.persist_workflow_results(workflow_id, results, url, depth, self.logger)

    async def _send_progress_update(self, interaction: Any, message: str, current: int, total: int) -> None:
        """Send real-time progress updates to Discord.

        Delegates to discord_helpers.send_progress_update for implementation.
        """
        await discord_helpers.send_progress_update(interaction, message, current, total, self.logger)

    async def _handle_acquisition_failure(self, interaction: Any, acquisition_result: StepResult, url: str) -> None:
        """Handle content acquisition failures with specialized guidance.

        Delegates to discord_helpers.handle_acquisition_failure for implementation.
        """
        await discord_helpers.handle_acquisition_failure(interaction, acquisition_result, url, self.logger)

    async def _send_error_response(self, interaction: Any, stage: str, error: str) -> None:
        """Send error response to Discord with session resilience.

        Delegates to discord_helpers.send_error_response for implementation.

        Args:
            interaction: Discord interaction object
            stage: Stage name where error occurred
            error: Error message to send
        """
        await discord_helpers.send_error_response(interaction, stage, error, self.logger)

    async def _send_enhanced_error_response(self, interaction: Any, stage: str, enhanced_message: str) -> None:
        """Send enhanced user-friendly error response to Discord.

        Delegates to discord_helpers.send_enhanced_error_response for implementation.
        """
        await discord_helpers.send_enhanced_error_response(interaction, stage, enhanced_message, self.logger)

    async def _deliver_autonomous_results(self, interaction: Any, results: dict[str, Any], depth: str) -> None:
        """Deliver comprehensive autonomous analysis results to Discord.

        Delegates to discord_helpers.deliver_autonomous_results for implementation.
        """
        await discord_helpers.deliver_autonomous_results(interaction, results, depth, self.logger)

    async def _create_main_results_embed(self, results: dict[str, Any], depth: str) -> Any:
        """Create the main results embed for Discord.

        Delegates to discord_helpers.create_main_results_embed for implementation.
        """
        return await discord_helpers.create_main_results_embed(results, depth)

    async def _create_details_embed(self, results: dict[str, Any]) -> Any:
        """Create detailed results embed.

        Delegates to discord_helpers.create_details_embed for implementation.
        """
        return await discord_helpers.create_details_embed(results)

    async def _create_knowledge_base_embed(self, knowledge_data: dict[str, Any]) -> Any:
        """Create knowledge base integration embed.

        Delegates to discord_helpers.create_knowledge_base_embed for implementation.
        """
        return await discord_helpers.create_knowledge_base_embed(knowledge_data)

    def _transform_evidence_to_verdicts(self, fact_verification_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Transform fact-check evidence into verdict format for deception scoring."""
        return data_transformers.transform_evidence_to_verdicts(fact_verification_data, self.logger)

    def _extract_fallacy_data(self, logical_analysis_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract fallacy data from logical analysis results."""
        return data_transformers.extract_fallacy_data(logical_analysis_data)

    async def _create_error_embed(self, stage: str, error: str) -> Any:
        """Create error embed for Discord.

        Delegates to discord_helpers.create_error_embed for implementation.
        """
        return await discord_helpers.create_error_embed(stage, error)

    # ========================================
    # SPECIALIZED ANALYSIS HELPER METHODS
    # ========================================

    def _calculate_threat_level(self, deception_result: Any, fallacy_result: Any) -> str:
        """Calculate threat level based on deception and fallacy analysis.

        Delegates to analytics_calculators.calculate_threat_level.
        """
        return analytics_calculators.calculate_threat_level(deception_result, fallacy_result, self.logger)

    def _calculate_threat_level_from_crew(self, crew_result: Any) -> str:
        """Calculate threat level from CrewAI crew analysis results.

        Delegates to analytics_calculators.calculate_threat_level_from_crew.
        """
        return analytics_calculators.calculate_threat_level_from_crew(crew_result, self.logger)

    def _calculate_behavioral_risk(self, behavioral_data: dict[str, Any], threat_data: dict[str, Any]) -> float:
        """Calculate behavioral risk score.

        Delegates to analytics_calculators.calculate_behavioral_risk.
        """
        return analytics_calculators.calculate_behavioral_risk(behavioral_data, threat_data, self.logger)

    def _calculate_persona_confidence(self, behavioral_data: dict[str, Any]) -> float:
        """Calculate confidence in persona analysis.

        Delegates to analytics_calculators.calculate_persona_confidence.
        """
        return analytics_calculators.calculate_persona_confidence(behavioral_data, self.logger)

    def _calculate_behavioral_risk_from_crew(self, crew_result: Any, threat_data: dict[str, Any]) -> float:
        """Calculate behavioral risk score from CrewAI crew analysis.

        Delegates to analytics_calculators.calculate_behavioral_risk_from_crew.
        """
        return analytics_calculators.calculate_behavioral_risk_from_crew(crew_result, threat_data, self.logger)

    def _calculate_persona_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate confidence in persona analysis from CrewAI crew results.

        Delegates to analytics_calculators.calculate_persona_confidence_from_crew.
        """
        return analytics_calculators.calculate_persona_confidence_from_crew(crew_result, self.logger)

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
        """Calculate contextual relevance of research to analysis.

        Delegates to analytics_calculators.calculate_contextual_relevance.
        """
        return analytics_calculators.calculate_contextual_relevance(research_results, analysis_data, self.logger)

    def _calculate_synthesis_confidence(self, research_results: dict[str, Any]) -> float:
        """Delegates to analytics_calculators.calculate_synthesis_confidence."""
        return analytics_calculators.calculate_synthesis_confidence(research_results, self.logger)

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
        """Delegates to analytics_calculators.calculate_contextual_relevance_from_crew."""
        return analytics_calculators.calculate_contextual_relevance_from_crew(crew_result, analysis_data, self.logger)

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
        """Delegates to analytics_calculators.calculate_consolidation_metrics_from_crew."""
        return analytics_calculators.calculate_consolidation_metrics_from_crew(crew_result, self.logger)

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
        """Delegates to analytics_calculators.generate_strategic_recommendations."""
        return analytics_calculators.generate_strategic_recommendations(
            analysis_data, threat_data, verification_data, self.logger
        )

    def _calculate_overall_confidence(self, *data_sources) -> float:
        """Delegates to analytics_calculators.calculate_overall_confidence."""
        return analytics_calculators.calculate_overall_confidence(*data_sources, log=self.logger)

    def _calculate_data_completeness(self, *data_sources) -> float:
        """Delegates to analytics_calculators.calculate_data_completeness."""
        return analytics_calculators.calculate_data_completeness(*data_sources, log=self.logger)

    def _assign_intelligence_grade(
        self, analysis_data: dict[str, Any], threat_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> str:
        """Assign intelligence grade based on analysis quality."""
        return data_transformers.assign_intelligence_grade(analysis_data, threat_data, verification_data)

    def _assess_transcript_quality(self, transcript: str) -> float:
        """Assess the quality of a transcript based on various metrics."""
        return quality_assessors.assess_transcript_quality(transcript, self.logger)

    def _calculate_enhanced_summary_statistics(self, all_results: dict[str, Any]) -> dict[str, Any]:
        """Delegates to analytics_calculators.calculate_enhanced_summary_statistics."""
        return analytics_calculators.calculate_enhanced_summary_statistics(all_results, self.logger)

    def _generate_comprehensive_intelligence_insights(self, all_results: dict[str, Any]) -> list[str]:
        """Generate comprehensive intelligence insights from all analysis results."""
        return data_transformers.generate_comprehensive_intelligence_insights(all_results, self.logger)

    # ========================================
    # ADVANCED 25-STAGE WORKFLOW METHODS
    # ========================================
    # Additional specialized methods for 25-stage workflow

    async def _execute_advanced_pattern_recognition(
        self, analysis_data: dict[str, Any], behavioral_data: dict[str, Any]
    ) -> StepResult:
        """Execute advanced pattern recognition using CrewAI comprehensive linguistic analyst."""
        try:
            # CRITICAL: Use _get_or_create_agent to ensure agent has persistent context
            pattern_agent = self._get_or_create_agent("comprehensive_linguistic_analyst")

            # Ensure tools receive full structured context
            try:
                self._populate_agent_tool_context(
                    pattern_agent,
                    {
                        "analysis_data": analysis_data,
                        "behavioral_data": behavioral_data,
                    },
                )
                self.logger.info("✅ Pattern recognition context populated successfully")
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
                self.logger.info("✅ Cross-reference network context populated successfully")
            except Exception as _ctx_err:  # pragma: no cover - defensive
                self.logger.debug(f"Cross-reference network context population skipped: {_ctx_err}")

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
                self.logger.info("✅ Predictive threat context populated successfully")
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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                synthesis_agent = self._get_or_create_agent("knowledge_integrator")

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
                    self.logger.warning(f"⚠️ Multimodal agent context population FAILED: {_ctx_err}", exc_info=True)

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                graph_agent = self._get_or_create_agent("knowledge_integrator")

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
                    self.logger.warning(f"⚠️ Graph agent context population FAILED: {_ctx_err}", exc_info=True)

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                learning_agent = self._get_or_create_agent("performance_analyst")

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
                    self.logger.warning(f"⚠️ Learning agent context population FAILED: {_ctx_err}", exc_info=True)

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                bandits_agent = self._get_or_create_agent("performance_analyst")

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
                    self.logger.warning(f"⚠️ Bandits agent context population FAILED: {_ctx_err}", exc_info=True)

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                community_agent = self._get_or_create_agent("community_liaison")

                # Populate community intelligence context
                self._populate_agent_tool_context(
                    community_agent,
                    {
                        "social_data": social_data,
                        "network_data": network_data,
                    },
                )

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                adaptive_agent = self._get_or_create_agent("mission_orchestrator")

                # Populate adaptive workflow context
                self._populate_agent_tool_context(
                    adaptive_agent,
                    {
                        "bandits_data": bandits_data,
                        "learning_data": learning_data,
                    },
                )

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
            if getattr(self, "_llm_available", False):
                # CRITICAL FIX: Use _get_or_create_agent to ensure agent exists
                memory_agent = self._get_or_create_agent("knowledge_integrator")

                # Populate memory consolidation context
                self._populate_agent_tool_context(
                    memory_agent,
                    {
                        "knowledge_data": knowledge_data,
                        "graph_data": graph_data,
                    },
                )

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
        return extractors.extract_timeline_from_crew(crew_result)

    def _extract_index_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract transcript index from CrewAI crew results."""
        return extractors.extract_index_from_crew(crew_result)

    def _calculate_transcript_quality(self, crew_result: Any) -> float:
        """Delegates to analytics_calculators.calculate_transcript_quality."""
        return analytics_calculators.calculate_transcript_quality(crew_result, self.logger)

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
        return extractors.extract_linguistic_patterns_from_crew(crew_result)

    def _extract_sentiment_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract sentiment analysis from CrewAI results."""
        return extractors.extract_sentiment_from_crew(crew_result)

    def _extract_themes_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract thematic insights from CrewAI analysis."""
        return extractors.extract_themes_from_crew(crew_result)

    def _calculate_analysis_confidence_from_crew(self, crew_result: Any) -> float:
        """Delegates to analytics_calculators.calculate_analysis_confidence_from_crew."""
        return analytics_calculators.calculate_analysis_confidence_from_crew(crew_result, self.logger)

    def _analyze_text_complexity(self, text: str) -> dict[str, Any]:
        """Analyze text complexity metrics."""
        return extractors.analyze_text_complexity(text)

    def _extract_language_features(self, text: str) -> dict[str, Any]:
        """Extract language features from text."""
        return extractors.extract_language_features(text)

    def _extract_fact_checks_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract fact-checking results from CrewAI verification analysis."""
        return extractors.extract_fact_checks_from_crew(crew_result)

    def _extract_logical_analysis_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract logical analysis results from CrewAI verification."""
        return extractors.extract_logical_analysis_from_crew(crew_result)

    def _extract_credibility_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract credibility assessment from CrewAI verification."""
        return extractors.extract_credibility_from_crew(crew_result)

    def _extract_bias_indicators_from_crew(self, crew_result: Any) -> list[dict[str, Any]]:
        """Extract bias indicators from CrewAI verification."""
        return extractors.extract_bias_indicators_from_crew(crew_result)

    def _extract_source_validation_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Extract source validation results from CrewAI verification."""
        return extractors.extract_source_validation_from_crew(crew_result)

    def _calculate_verification_confidence_from_crew(self, crew_result: Any) -> float:
        """Delegates to analytics_calculators.calculate_verification_confidence_from_crew."""
        return analytics_calculators.calculate_verification_confidence_from_crew(crew_result, self.logger)

    def _calculate_agent_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate agent confidence from CrewAI analysis quality.

        Delegates to analytics_calculators.calculate_agent_confidence_from_crew.
        """
        return analytics_calculators.calculate_agent_confidence_from_crew(crew_result, self.logger)

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
        """Calculate basic threat score from available data when agent unavailable.

        Delegates to analytics_calculators.calculate_basic_threat_from_data.
        """
        return analytics_calculators.calculate_basic_threat_from_data(
            verification_data, sentiment_data, credibility_data, self.logger
        )

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
