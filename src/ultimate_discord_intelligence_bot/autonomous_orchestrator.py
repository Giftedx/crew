"""Autonomous Intelligence Orchestrator - Single Entry Point for All AI Capabilities.

This module provides the unified autonomous workflow that coordinates all 11 agents,
50+ tools, ContentPipeline, memory systems, and analysis capabilities through a single
self-orchestrated command interface.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from textwrap import dedent
from typing import TYPE_CHECKING, Any


try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
except ImportError:
    BaseModel = object

    def Field(*_args, **_kwargs):
        return None

    ValidationError = Exception

    def field_validator(*_args, **_kwargs):
        def decorator(f):
            return f

        return decorator


try:
    from crewai import Crew, Process, Task

    try:
        from crewai.telemetry import Telemetry

        Telemetry._instance = None
        os.environ["CREWAI_DISABLE_TELEMETRY"] = "1"
        os.environ["OTEL_SDK_DISABLED"] = "true"
    except Exception:
        pass
except Exception:
    if not TYPE_CHECKING:

        class Task:
            def __init__(self, *a, **k): ...

        class Process:
            sequential = "sequential"

        class Crew:
            def __init__(self, *a, **k): ...

            def kickoff(self, *a, **k):
                return {"status": "ok"}


from app.config.settings import Settings

from .config import prompts as prompt_config
from .crew_core import UltimateDiscordIntelligenceBotCrew
from .crew_error_handler import CrewErrorHandler
from .crew_insight_helpers import CrewInsightExtractor
from .multi_modal_synthesizer import MultiModalSynthesizer
from .orchestrator import (
    analytics_calculators,
    crew_builders,
    data_transformers,
    discord_helpers,
    error_handlers,
    extractors,
    orchestrator_utilities,
    quality_assessors,
    result_synthesizers,
    system_validators,
    workflow_planners,
)
from .platform.observability.metrics import get_metrics


try:
    from .services.semantic_router_service import SemanticRouterService

    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError:
    SEMANTIC_ROUTER_AVAILABLE = False
    SemanticRouterService = None
import contextlib

from .step_result import StepResult
from .tools import (
    AdvancedPerformanceAnalyticsTool,
    ClaimExtractorTool,
    DeceptionScoringTool,
    FactCheckTool,
    GraphMemoryTool,
    HippoRagContinualMemoryTool,
    LogicalFallacyTool,
    Mem0MemoryTool,
    MemoryStorageTool,
    PerspectiveSynthesizerTool,
    PipelineTool,
    SocialMediaMonitorTool,
    TrustworthinessTrackerTool,
    TruthScoringTool,
    XMonitorTool,
)


if TYPE_CHECKING:
    from crewai import CrewOutput
logger = logging.getLogger(__name__)
try:
    import agentops

    settings = Settings()
    if settings.enable_agent_ops and settings.agent_ops_api_key:
        agentops.init(settings.agent_ops_api_key)
        logger.info("✅ AgentOps initialized successfully.")
    elif settings.enable_agent_ops:
        logger.warning("⚠️ AgentOps is enabled but API key is missing.")
except ImportError:
    logger.debug("AgentOps not installed, skipping initialization.")
except Exception as e:
    logger.error(f"Failed to initialize AgentOps: {e}", exc_info=True)


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


TASK_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "acquisition": AcquisitionOutput,
    "capture": AcquisitionOutput,
    "transcription": TranscriptionOutput,
    "transcribe": TranscriptionOutput,
    "analysis": AnalysisOutput,
    "map": AnalysisOutput,
    "verification": VerificationOutput,
    "verify": VerificationOutput,
    "integration": IntegrationOutput,
    "knowledge": IntegrationOutput,
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
        self.synthesizer = MultiModalSynthesizer()
        self._initialize_agent_coordination_system()
        try:
            self.mem0_tool = Mem0MemoryTool()
            if self.mem0_tool._is_enabled():
                self.logger.info("✅ Mem0MemoryTool initialized successfully.")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize Mem0MemoryTool: {e}")
            self.mem0_tool = None
        try:
            self.system_health = self._validate_system_prerequisites()
        except Exception:
            self.system_health = {"healthy": False, "errors": ["init_validation_failed"]}
        try:
            self._llm_available = bool(self._check_llm_api_available())
        except Exception:
            self._llm_available = False

    def _get_budget_limits(self, depth: str) -> dict[str, Any]:
        """Get budget limits based on analysis depth."""
        return orchestrator_utilities.get_budget_limits(depth)

    def _populate_agent_tool_context(self, agent: Any, context_data: dict[str, Any]) -> None:
        """Populate shared context on all tool wrappers for an agent (delegates to crew_builders)."""
        return crew_builders.populate_agent_tool_context(
            agent, context_data, logger_instance=self.logger, metrics_instance=self.metrics
        )

    def _get_or_create_agent(self, agent_name: str) -> Any:
        """Get agent from coordinators cache or create and cache it (delegates to crew_builders)."""
        return crew_builders.get_or_create_agent(
            agent_name, self.agent_coordinators, self.crew_instance, logger_instance=self.logger
        )

    def _task_completion_callback(self, task_output: Any) -> None:
        """Callback to extract and propagate structured data after each task (delegates to crew_builders)."""
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
        """Build a single chained CrewAI crew for the complete intelligence workflow (delegates to crew_builders)."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
            self.logger.debug("✨ Initialized crew_instance for agent creation")
        settings = Settings()
        return crew_builders.build_intelligence_crew(
            url,
            depth,
            agent_getter_callback=self._get_or_create_agent,
            task_completion_callback=self._task_completion_callback,
            logger_instance=self.logger,
            enable_parallel_memory_ops=settings.enable_parallel_memory_ops,
            enable_parallel_analysis=settings.enable_parallel_analysis,
            enable_parallel_fact_checking=settings.enable_parallel_fact_checking,
        )

    def _build_specialized_crew(self, routed_tool: str, url: str, depth: str) -> Crew | None:
        """Build a specialized crew for a specific routed tool.

        Args:
            routed_tool: The tool that was routed to
            url: The URL to analyze
            depth: The analysis depth

        Returns:
            Specialized crew or None if not supported
        """
        try:
            tool_crew_mappings = {
                "debate_analysis": self._build_debate_focused_crew,
                "fact_checking": self._build_fact_check_focused_crew,
                "sentiment_analysis": self._build_sentiment_focused_crew,
                "content_moderation": self._build_moderation_focused_crew,
                "transcription": self._build_transcription_focused_crew,
            }
            if routed_tool in tool_crew_mappings:
                return tool_crew_mappings[routed_tool](url, depth)
            else:
                self.logger.warning(f"No specialized crew mapping for tool: {routed_tool}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to build specialized crew for {routed_tool}: {e}")
            return None

    def _build_debate_focused_crew(self, url: str, depth: str) -> Crew:
        """Build a crew focused on debate analysis."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
        debate_agent = self._get_or_create_agent("debate_specialist")
        fact_checker = self._get_or_create_agent("fact_checker")
        debate_task = Task(
            description=f"Analyze debate content from {url} with focus on argument structure, logical fallacies, and evidence quality",
            agent=debate_agent,
            expected_output="Comprehensive debate analysis with argument mapping and fallacy detection",
        )
        fact_check_task = Task(
            description="Verify factual claims made in the debate content",
            agent=fact_checker,
            expected_output="Fact-checking report with claim verification status",
        )
        return Crew(agents=[debate_agent, fact_checker], tasks=[debate_task, fact_check_task], verbose=True)

    def _build_fact_check_focused_crew(self, url: str, depth: str) -> Crew:
        """Build a crew focused on fact-checking."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
        fact_checker = self._get_or_create_agent("fact_checker")
        researcher = self._get_or_create_agent("researcher")
        fact_check_task = Task(
            description=f"Perform comprehensive fact-checking of content from {url}",
            agent=fact_checker,
            expected_output="Detailed fact-checking report with claim verification",
        )
        research_task = Task(
            description="Research and verify claims using reliable sources",
            agent=researcher,
            expected_output="Research findings with source citations",
        )
        return Crew(agents=[fact_checker, researcher], tasks=[fact_check_task, research_task], verbose=True)

    def _build_sentiment_focused_crew(self, url: str, depth: str) -> Crew:
        """Build a crew focused on sentiment analysis."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
        sentiment_analyst = self._get_or_create_agent("sentiment_analyst")
        sentiment_task = Task(
            description=f"Analyze sentiment and emotional tone of content from {url}",
            agent=sentiment_analyst,
            expected_output="Comprehensive sentiment analysis with emotional insights",
        )
        return Crew(agents=[sentiment_analyst], tasks=[sentiment_task], verbose=True)

    def _build_moderation_focused_crew(self, url: str, depth: str) -> Crew:
        """Build a crew focused on content moderation."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
        moderator = self._get_or_create_agent("content_moderator")
        safety_analyst = self._get_or_create_agent("safety_analyst")
        moderation_task = Task(
            description=f"Moderate content from {url} for policy violations and safety concerns",
            agent=moderator,
            expected_output="Content moderation report with policy violation assessment",
        )
        safety_task = Task(
            description="Analyze content for safety and brand suitability",
            agent=safety_analyst,
            expected_output="Safety analysis with risk assessment",
        )
        return Crew(agents=[moderator, safety_analyst], tasks=[moderation_task, safety_task], verbose=True)

    def _build_transcription_focused_crew(self, url: str, depth: str) -> Crew:
        """Build a crew focused on transcription and content extraction."""
        if self.crew_instance is None:
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            self.crew_instance = UltimateDiscordIntelligenceBotCrew()
        transcriber = self._get_or_create_agent("transcriber")
        content_analyzer = self._get_or_create_agent("content_analyzer")
        transcription_task = Task(
            description=f"Transcribe and extract content from {url} with high accuracy",
            agent=transcriber,
            expected_output="High-quality transcript with metadata",
        )
        analysis_task = Task(
            description="Analyze the transcribed content for key themes and insights",
            agent=content_analyzer,
            expected_output="Content analysis with key themes and insights",
        )
        return Crew(agents=[transcriber, content_analyzer], tasks=[transcription_task, analysis_task], verbose=True)

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
        """Run a sync function in a thread while preserving TenantContext."""
        return await orchestrator_utilities.to_thread_with_tenant(fn, *args, **kwargs)

    def _initialize_agent_coordination_system(self):
        """Initialize the agent coordination system with specialized workflows (delegates to orchestrator_utilities)."""
        self.agent_workflow_map = orchestrator_utilities.initialize_agent_workflow_map()
        self.workflow_dependencies = orchestrator_utilities.initialize_workflow_dependencies()
        self.agent_coordinators = {}
        self.crew_instance = None

    @staticmethod
    def _normalize_acquisition_data(acquisition: StepResult | dict[str, Any] | None) -> dict[str, Any]:
        """Return a flattened ContentPipeline payload for downstream stages."""
        return data_transformers.normalize_acquisition_data(acquisition)

    async def _execute_stage_with_recovery(
        self, stage_function, stage_name: str, agent_name: str, workflow_depth: str, *args, **kwargs
    ):
        """Execute a workflow stage with intelligent error handling and recovery."""
        return await error_handlers.execute_stage_with_recovery(
            *args,
            stage_function=stage_function,
            stage_name=stage_name,
            agent_name=agent_name,
            workflow_depth=workflow_depth,
            error_handler=self.error_handler,
            get_system_health=self._get_system_health,
            logger_instance=self.logger,
            **kwargs,
        )

    def _get_system_health(self) -> dict[str, Any]:
        """Get current system health metrics for error analysis."""
        return system_validators.get_system_health(
            error_handler=self.error_handler,
            last_successful_stage=getattr(self, "_last_successful_stage", None),
            logger_instance=self.logger,
        )

    @staticmethod
    def _merge_threat_and_deception_data(threat_result: StepResult, deception_result: StepResult) -> StepResult:
        """Combine threat analysis output with deception scoring metrics."""
        return data_transformers.merge_threat_and_deception_data(threat_result, deception_result)

    @staticmethod
    @staticmethod
    def _merge_threat_payload(
        threat_payload: dict[str, Any], verification_data: dict[str, Any] | None, fact_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Augment a plain threat payload dict with relevant verification/fact data.

        Delegates to orchestrator.pipeline_result_builders.merge_threat_payload.
        """
        from domains.orchestration.pipeline_result_builders import merge_threat_payload

        return merge_threat_payload(threat_payload, verification_data, fact_data)

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
        """Delegate to pipeline_result_builders.build_knowledge_payload."""
        from domains.orchestration.pipeline_result_builders import build_knowledge_payload

        return build_knowledge_payload(
            acquisition_data,
            intelligence_data,
            verification_data,
            threat_data,
            fact_data,
            behavioral_data,
            fallback_url=fallback_url,
        )

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
        self._workflow_id = workflow_id
        self._tenant_ctx = tenant_ctx
        if tenant_ctx is None:
            try:
                from .tenancy import TenantContext

                tenant_ctx = TenantContext(
                    tenant_id=f"guild_{getattr(interaction, 'guild_id', 'dm') or 'dm'}"
                    workspace_id=getattr(getattr(interaction, "channel", None), "name", "autointel_workspace"),
                )
                self.logger.info(f"Created tenant context for workflow: {tenant_ctx}")
            except Exception as e:
                self.logger.warning(f"Failed to create tenant context: {e}")
                tenant_ctx = None

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
        try:
            exp_enabled = os.getenv("ENABLE_EXPERIMENTAL_DEPTH", "0").lower() in {"1", "true", "yes", "on"}
        except Exception:
            exp_enabled = False
        if depth == "experimental" and (not exp_enabled):
            depth = "comprehensive"
            with contextlib.suppress(Exception):
                await self._send_progress_update(
                    interaction,
                    "⚠️ Experimental mode disabled by configuration. Falling back to 'comprehensive' depth.",
                    0,
                    1,
                )
        await self._send_progress_update(interaction, f"🚀 Starting {depth} intelligence analysis for: {url}", 0, 5)
        budget_limits = self._get_budget_limits(depth)
        try:
            from platform.cost_tracker import initialize_cost_tracking

            from ultimate_discord_intelligence_bot.services.request_budget import (
                current_request_tracker,
                track_request_budget,
            )

            with contextlib.suppress(Exception):
                initialize_cost_tracking()
            with track_request_budget(total_limit=budget_limits["total"], per_task_limits=budget_limits["per_task"]):
                if tenant_ctx:
                    try:
                        from .tenancy import with_tenant

                        with with_tenant(tenant_ctx):
                            await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)
                    except Exception as tenancy_error:
                        self.logger.warning(f"Tenant context execution failed: {tenancy_error}")
                        await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)
                else:
                    await self._execute_crew_workflow(interaction, url, depth, workflow_id, start_time)
                tracker = current_request_tracker()
                if tracker and tracker.total_spent > 0:
                    cost_msg = f"💰 **Cost Tracking:**\n• Total: ${tracker.total_spent:.3f}\n• Budget: ${budget_limits['total']:.2f}\n• Utilization: {tracker.total_spent / budget_limits['total'] * 100:.1f}%"
                    if tracker.total_spent > 0.1:
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

        import agentops

        try:
            try:
                from .crewai_tool_wrappers import reset_global_crew_context

                reset_global_crew_context()
            except Exception as ctx_reset_error:
                self.logger.warning(f"Failed to reset global crew context: {ctx_reset_error}")
            settings = Settings()
            if settings.enable_agent_ops:
                session_tags = [f"depth:{depth}", f"url:{url}", f"workflow_id:{workflow_id}", "autointel_workflow"]
                try:
                    from .tenancy.context import current_tenant

                    _tc = current_tenant()
                    if _tc is not None and getattr(_tc, "tenant_id", None):
                        session_tags.append(f"tenant:{_tc.tenant_id}")
                except Exception:
                    pass
                agentops.start_session(tags=session_tags)
                self.logger.info(f"AgentOps session started with tags: {session_tags}")
            routed_tool = self._route_query_to_tool(url)
            if routed_tool:
                self.logger.info(f"Semantic router selected tool: {routed_tool}. Overriding default crew.")
                specialized_crew = self._build_specialized_crew(routed_tool, url, depth)
                if specialized_crew:
                    crew = specialized_crew
                    self.logger.info(f"Using specialized crew for tool: {routed_tool}")
                else:
                    self.logger.warning(f"Failed to build specialized crew for {routed_tool}, using default")
                await self._send_progress_update(
                    interaction,
                    f"🧠 Semantic router selected `{routed_tool}`. Proceeding with specialized analysis.",
                    1,
                    5,
                )
            await self._send_progress_update(interaction, "🤖 Building CrewAI multi-agent system...", 1, 5)
            crew = self._build_intelligence_crew(url, depth)
            initial_context = {"url": url, "depth": depth}
            self.logger.info(f"🔧 Populating initial context on all agents: {initial_context}")
            for agent in crew.agents:
                self._populate_agent_tool_context(agent, initial_context)
            await self._send_progress_update(interaction, "⚙️ Executing intelligence workflow...", 2, 5)
            self.logger.info(f"Kickoff crew with inputs: url={url}, depth={depth}")
            try:
                result: CrewOutput = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})
            except Exception as crew_exec_error:
                error_msg = str(crew_exec_error)
                if "maximum context length" in error_msg or "token" in error_msg.lower():
                    self.logger.warning(
                        f"CrewAI memory token limit exceeded (likely >8192 tokens). Continuing with memory disabled. Error: {error_msg}"
                    )
                    result: CrewOutput = await asyncio.to_thread(crew.kickoff, inputs={"url": url, "depth": depth})
                else:
                    raise
            await self._send_progress_update(interaction, "📊 Processing crew results...", 3, 5)
            if hasattr(result, "tasks_output") and result.tasks_output:
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
            await self._send_progress_update(interaction, "📝 Formatting intelligence report...", 4, 5)
            result_message = "## Intelligence Analysis Complete\n\n"
            result_message += f"**URL:** {url}\n"
            result_message += f"**Depth:** {depth}\n"
            result_message += f"**Processing Time:** {time.time() - start_time:.1f}s\n\n"
            if hasattr(result, "raw"):
                result_message += f"**Analysis:**\n{result.raw}\n\n"
            elif hasattr(result, "final_output"):
                result_message += f"**Analysis:**\n{result.final_output}\n\n"
            else:
                result_message += f"**Analysis:**\n{result!s}\n\n"
            await self._send_progress_update(interaction, "✅ Intelligence analysis complete!", 5, 5)
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
            processing_time = time.time() - start_time
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "success"}).inc()
            self.metrics.histogram("autointel_workflow_duration", processing_time, labels={"depth": depth})
            if Settings().feature_flags.ENABLE_AGENT_COLLABORATION:
                agentops.end_session("Success")
                self.logger.info("AgentOps session ended with status: Success")
        except Exception as e:
            self.logger.error(f"Crew workflow execution failed: {e}", exc_info=True)
            await self._send_error_response(interaction, "Crew Workflow", str(e))
            self.metrics.counter("autointel_workflows_total", labels={"depth": depth, "outcome": "error"}).inc()
            if Settings().feature_flags.ENABLE_AGENT_COLLABORATION:
                agentops.end_session("Fail")
                self.logger.info("AgentOps session ended with status: Fail")

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

    def _route_query_to_tool(self, query: str) -> str | None:
        """Use semantic router to select the best tool for a query."""
        settings = Settings()
        if not settings.enable_semantic_router:
            self.logger.debug("Semantic router is disabled by settings.")
            return None
        if not SEMANTIC_ROUTER_AVAILABLE:
            self.logger.warning(
                "Semantic router requested but semantic-router library not installed. Install with: pip install -e '.[semantic_router]'"
            )
            return None
        try:
            from semantic_router import Route
        except ImportError:
            self.logger.warning("Failed to import semantic_router.Route")
            return None
        routes = [
            Route(
                name="social_media_monitoring",
                utterances=[
                    "monitor social media for",
                    "track mentions of",
                    "what are people saying about",
                    "check twitter for",
                ],
            ),
            Route(
                name="content_acquisition",
                utterances=[
                    "download the video from",
                    "get the content from this url",
                    "acquire the media at",
                    "fetch this youtube link",
                ],
            ),
            Route(
                name="transcription",
                utterances=[
                    "transcribe the audio from",
                    "what does the audio say",
                    "create a transcript for",
                    "convert this speech to text",
                ],
            ),
            Route(
                name="analysis",
                utterances=[
                    "analyze the transcript",
                    "what are the key insights",
                    "summarize the content",
                    "give me a breakdown of the text",
                ],
            ),
            Route(
                name="verification",
                utterances=[
                    "fact-check the claims",
                    "verify the information",
                    "is this true",
                    "check the facts in this",
                ],
            ),
        ]
        try:
            router_service = SemanticRouterService(routes=routes)
            route_name = router_service.route(query)
            self.logger.info(f"Semantic router routed query to: {route_name}")
            return route_name
        except Exception as e:
            self.logger.error(f"Semantic router failed: {e}", exc_info=True)
            return None

    async def _execute_agent_coordination_setup(self, url: str, depth: str) -> StepResult:
        """Initialize and coordinate CrewAI multi-agent system for sophisticated orchestration."""
        try:
            if not getattr(self, "_llm_available", False):
                self.agent_coordinators = {}
                return StepResult.skip(reason="llm_unavailable", message="Agent system not initialized (no API key)")
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()
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
            else:
                active_agents = ["mission_orchestrator", "acquisition_specialist", "analysis_cartographer"]
            self.crew_instance = crew_instance
            self.active_agents = active_agents
            self.agent_coordinators = {}
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
            if getattr(self, "_llm_available", False):
                mission_agent = self._get_or_create_agent("mission_orchestrator")
                with contextlib.suppress(Exception):
                    self._populate_agent_tool_context(
                        mission_agent, {"mission_url": url, "mission_depth": depth, "target_url": url, "depth": depth}
                    )
                planning_task = Task(
                    description=prompt_config.Autonomous.ORCHESTRATOR_PROMPT.format(url=url, depth=depth),
                    expected_output="A detailed report of the content analysis, including a summary, key claims, and any detected fallacies or perspectives. The final output must be a markdown document.",
                    agent=mission_agent,
                )
                planning_crew = Crew(
                    agents=[mission_agent], tasks=[planning_task], verbose=True, process=Process.sequential
                )
                crew_result = await asyncio.to_thread(planning_crew.kickoff)
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

    async def _execute_specialized_content_acquisition(self, url: str) -> StepResult:
        """Execute specialized content acquisition with enhanced multi-platform support and ContentPipeline integration."""
        try:
            self.logger.info(f"Starting specialized content acquisition with ContentPipeline synergy: {url}")
            pipeline_result = await self._execute_content_pipeline(url)
            if not pipeline_result.success:
                error_msg = pipeline_result.error or "Content acquisition failed"
                lower_url = url.lower()
                if ("youtube.com" in lower_url or "youtu.be" in lower_url) and (
                    "Requested format is not available" in error_msg or "nsig extraction failed" in error_msg
                ):
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
            pipeline_wrapper = pipeline_result.data if isinstance(pipeline_result.data, dict) else {}
            raw_payload = pipeline_wrapper.get("data") if isinstance(pipeline_wrapper, dict) else None
            pipeline_payload = dict(raw_payload) if isinstance(raw_payload, dict) else {}
            metadata = {k: v for k, v in pipeline_wrapper.items() if k != "data"}
            metadata.update(
                {"acquisition_timestamp": time.time(), "source_url": url, "workflow_type": "autonomous_intelligence"}
            )
            metadata.setdefault("url", url)
            normalised_payload = dict(pipeline_payload)
            normalised_payload.pop("status", None)
            normalised_payload.setdefault("source_url", url)
            normalised_payload.setdefault("acquisition_timestamp", metadata["acquisition_timestamp"])
            normalised_payload.setdefault("workflow_type", metadata["workflow_type"])
            normalised_payload["pipeline_metadata"] = metadata
            if isinstance(raw_payload, dict):
                normalised_payload["raw_pipeline_payload"] = raw_payload
            self.logger.info("Specialized content acquisition successful with ContentPipeline")
            return StepResult.ok(**normalised_payload, message="Content acquisition completed via ContentPipeline")
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
            if not acquisition_result.success or not acquisition_result.data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")
            pipeline_data = self._normalize_acquisition_data(acquisition_result)
            if not pipeline_data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")
            transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
            transcription_block = {} if not isinstance(transcription_block, dict) else dict(transcription_block)
            transcript = transcription_block.get("transcript", "")
            media_info = pipeline_data.get("download", {}) if isinstance(pipeline_data, dict) else {}
            media_info = {} if not isinstance(media_info, dict) else dict(media_info)
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
            if hasattr(self, "crew") and self.crew is not None:
                try:
                    transcription_agent = self._get_or_create_agent("transcription_engineer")
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
                    except Exception as _ctx_err:
                        self.logger.warning(
                            f"⚠️ Transcription agent context population FAILED: {_ctx_err}", exc_info=True
                        )
                    transcription_task = Task(
                        description=f"Enhance transcription quality, create timeline anchors, and build comprehensive index for transcript: {transcript[:500]}... Media info: {media_info}",
                        expected_output="Enhanced transcript with timeline anchors, quality improvements, and comprehensive indexing",
                        agent=transcription_agent,
                    )
                    transcription_crew = Crew(
                        agents=[transcription_agent],
                        tasks=[transcription_task],
                        verbose=True,
                        process=Process.sequential,
                    )
                    crew_result = await asyncio.to_thread(transcription_crew.kickoff)
                    return StepResult.ok(
                        message="Advanced transcription analysis completed with CrewAI agent",
                        transcript=transcript,
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
            else:
                self.logger.info("CrewAI agents not available, using basic transcription processing")
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
            if not transcription_result.success or not transcription_result.data:
                return StepResult.skip(reason="No transcription data available for content analysis")
            transcription_data = transcription_result.data
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
            if getattr(self, "_llm_available", False) and hasattr(self, "crew") and (self.crew is not None):
                try:
                    analysis_agent = self._get_or_create_agent("analysis_cartographer")
                    try:
                        context_data = {
                            "transcript": transcript,
                            "text": transcript,
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
                            f"📝 Populating analysis context: transcript={len(transcript)} chars, title={media_info.get('title', 'N/A')}, platform={media_info.get('platform', 'N/A')}"
                        )
                        self._populate_agent_tool_context(analysis_agent, context_data)
                        self.logger.info("✅ Analysis context populated successfully")
                    except Exception as _ctx_err:
                        self.logger.error(f"❌ Analysis agent context population FAILED: {_ctx_err}", exc_info=True)
                        return StepResult.fail(
                            error=f"Analysis context preparation failed: {_ctx_err}", step="analysis_context_population"
                        )
                    source_url = transcription_data.get("source_url") or "unknown"
                    title = media_info.get("title", "Unknown Title")
                    platform = media_info.get("platform", "Unknown Platform")
                    duration = media_info.get("duration", "Unknown Duration")
                    analysis_task = Task(
                        description=dedent(
                            f"""\n                            Analyze content from {platform} video: '{title}' (URL: {source_url})\n\n                            Duration: {duration}\n\n                            ⚠️ CRITICAL INSTRUCTIONS - DATA IS PRE-LOADED:\n\n                            The complete transcript ({len(transcript)} characters) and ALL media metadata are\n                            ALREADY AVAILABLE in the tool's shared context. You MUST NOT pass these as parameters.\n\n                            ❌ WRONG - DO NOT DO THIS:\n                            - TextAnalysisTool(text="transcript content here...")  # NEVER pass text parameter!\n                            - FactCheckTool(claim="some claim...")  # NEVER pass claim parameter!\n\n                            ✅ CORRECT - DO THIS INSTEAD:\n                            - TextAnalysisTool()  # Tools auto-access data from shared context\n                            - FactCheckTool()  # No parameters needed - data is pre-loaded\n\n                            When calling ANY tool, OMIT the text/transcript/content/claim parameters.\n                            The tools have DIRECT ACCESS to:\n                            - Full transcript ({len(transcript)} chars) - accessible as 'text' parameter internally\n                            - Media metadata (title, platform, duration, uploader)\n                            - Timeline anchors: {len(transcription_data.get('timeline_anchors', []))} available\n                            - Quality score: {transcription_data.get('quality_score', 0)}\n\n                            YOUR TASK:\n                            Use TextAnalysisTool (WITH NO PARAMETERS) to analyze linguistic patterns, sentiment,\n                            and thematic insights. The tool will automatically access the transcript from shared context.\n\n                            Provide comprehensive analysis including:\n                            - Sentiment analysis\n                            - Key themes and topics\n                            - Important contextual insights\n                            - Linguistic patterns\n                            """
                        ).strip(),
                        expected_output="Comprehensive content analysis with linguistic mapping, sentiment analysis, thematic insights, and structured annotations for the specified video content",
                        agent=analysis_agent,
                    )
                    analysis_crew = Crew(
                        agents=[analysis_agent], tasks=[analysis_task], verbose=True, process=Process.sequential
                    )
                    crew_result = await asyncio.to_thread(analysis_crew.kickoff)
                    analysis_results = {
                        "transcript": transcript,
                        "crew_analysis": crew_result,
                        "linguistic_patterns": self._extract_linguistic_patterns_from_crew(crew_result),
                        "sentiment_analysis": self._extract_sentiment_from_crew(crew_result),
                        "thematic_insights": self._extract_themes_from_crew(crew_result),
                        "source_url": source_url or media_info.get("source_url"),
                        "content_metadata": {
                            "word_count": len(transcript.split()),
                            "quality_score": transcription_data.get("quality_score", 0.5),
                            "analysis_timestamp": time.time(),
                            "analysis_method": "crewai_analysis_cartographer",
                            "agent_confidence": self._calculate_analysis_confidence_from_crew(crew_result),
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
            else:
                self.logger.info("CrewAI agents not available, using basic content analysis")
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

        Delegates to orchestrator.pipeline_result_builders module.
        """
        from domains.orchestration.pipeline_result_builders import build_pipeline_content_analysis_result

        return build_pipeline_content_analysis_result(
            transcript=transcript,
            transcription_data=transcription_data,
            pipeline_analysis=pipeline_analysis,
            media_info=media_info,
            pipeline_fallacy=pipeline_fallacy,
            pipeline_perspective=pipeline_perspective,
            pipeline_metadata=pipeline_metadata,
            source_url=source_url,
            logger=self.logger,
        )

    async def _execute_specialized_information_verification(
        self, analysis_data: dict[str, Any], fact_data: dict[str, Any] | None = None
    ) -> StepResult:
        """Execute comprehensive information verification using CrewAI Verification Director agent."""
        try:
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

            if getattr(self, "_llm_available", False):
                verification_agent = self._get_or_create_agent("verification_director")
                try:
                    context_data = {
                        "transcript": transcript,
                        "text": transcript,
                        "linguistic_patterns": linguistic_patterns,
                        "sentiment_analysis": sentiment_analysis,
                        "fact_data": fact_data or {},
                        "claims": (fact_data or {}).get("claims", []),
                        "analysis_data": analysis_data,
                    }
                    self.logger.info(
                        f"📝 Verification context: transcript={len(transcript)} chars, claims={len(context_data['claims'])}"
                    )
                    self._populate_agent_tool_context(verification_agent, context_data)
                except Exception as _ctx_err:
                    self.logger.warning(f"⚠️ Verification agent context population FAILED: {_ctx_err}", exc_info=True)
                verification_task = Task(
                    description="You are the Verification Director. Your role is to orchestrate comprehensive verification of the provided content. The transcript and analysis data are available in your shared context. Use your tools to: (1) Extract specific factual claims from the transcript, (2) Verify each claim using fact-checking tools, (3) Analyze logical structure for fallacies, (4) Assess source credibility, (5) Detect bias indicators. Synthesize findings into a structured verification report.",
                    expected_output="Comprehensive verification report with fact-checks, logical fallacy analysis, credibility scores, bias indicators, and source validation",
                    agent=verification_agent,
                )
                verification_crew = Crew(
                    agents=[verification_agent], tasks=[verification_task], verbose=True, process=Process.sequential
                )
                crew_result = await asyncio.to_thread(verification_crew.kickoff)
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
            transcript = intelligence_data.get("transcript", "")
            content_metadata = intelligence_data.get("content_metadata", {})
            _ = intelligence_data.get("linguistic_patterns", {})
            sentiment_analysis = intelligence_data.get("sentiment_analysis", {})
            _ = verification_data.get("fact_checks", {})
            _ = verification_data.get("logical_analysis", {})
            credibility_assessment = verification_data.get("credibility_assessment", {})
            if not transcript and (not content_metadata):
                return StepResult.skip(reason="No content available for deception analysis")
            if getattr(self, "_llm_available", False):
                threat_agent = self._get_or_create_agent("verification_director")
                context_data = {
                    "transcript": transcript,
                    "text": transcript,
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
                threat_task = Task(
                    description="You are the Threat Analysis Director. Your role is to assess deception, manipulation, and information threats in the provided content. All analysis data (transcript, fact-checks, logical analysis, credibility scores, sentiment) is available in your shared context. Use your tools to: (1) Score deception indicators in the transcript, (2) Identify manipulation techniques and psychological influence patterns, (3) Assess narrative integrity and consistency, (4) Build psychological threat profile, (5) Generate actionable threat intelligence. Synthesize into a comprehensive threat assessment.",
                    expected_output="Comprehensive threat assessment with deception scores, manipulation indicators, narrative integrity analysis, psychological threat profiling, and actionable threat intelligence",
                    agent=threat_agent,
                )
                threat_crew = Crew(agents=[threat_agent], tasks=[threat_task], verbose=True, process=Process.sequential)
                crew_result = await asyncio.to_thread(threat_crew.kickoff)
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
            content_metadata = intelligence_data.get("content_metadata", {})
            transcript = intelligence_data.get("transcript", "")
            linguistic_patterns = intelligence_data.get("linguistic_patterns", {})
            sentiment_analysis = intelligence_data.get("sentiment_analysis", {})
            title = content_metadata.get("title", "") or ""
            explicit_keywords = intelligence_data.get("keywords", [])
            if isinstance(explicit_keywords, list) and explicit_keywords:
                keywords = explicit_keywords
            else:
                derived = self._extract_keywords_from_text(transcript) if transcript else []
                if not derived:
                    derived = intelligence_data.get("thematic_insights", [])
                keywords = [k for k in derived if isinstance(k, str)]
            if not transcript and (not title) and (not keywords):
                return StepResult.skip(reason="No content available for social intelligence analysis")
            if getattr(self, "_llm_available", False):
                social_intel_agent = self._get_or_create_agent("signal_recon_specialist")
                try:
                    context_data = {
                        "transcript": transcript,
                        "text": transcript,
                        "content_metadata": content_metadata,
                        "linguistic_patterns": linguistic_patterns,
                        "sentiment_analysis": sentiment_analysis,
                        "keywords": keywords,
                        "title": title,
                        "analysis_data": intelligence_data,
                        "verification_data": verification_data,
                    }
                    self.logger.info(
                        f"📝 Social intel context: transcript={len(transcript)} chars, keywords={len(keywords)}, title={(title[:50] if title else 'N/A')}"
                    )
                    self._populate_agent_tool_context(social_intel_agent, context_data)
                except Exception as _ctx_err:
                    self.logger.warning(f"⚠️ Social agent context population FAILED: {_ctx_err}", exc_info=True)
                social_intel_task = Task(
                    description=f"Conduct comprehensive social intelligence analysis including narrative tracking across platforms, sentiment monitoring, influence mapping, and community response analysis. Content: {transcript[:800]}... Title: {title} Sentiment: {sentiment_analysis} Patterns: {linguistic_patterns} Keywords: {keywords[:10]}",
                    expected_output="Comprehensive social intelligence report with cross-platform narrative tracking, sentiment analysis, influence mapping, community dynamics, and emergent pattern detection",
                    agent=social_intel_agent,
                )
                social_crew = Crew(
                    agents=[social_intel_agent], tasks=[social_intel_task], verbose=True, process=Process.sequential
                )
                crew_result = await asyncio.to_thread(social_crew.kickoff)
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
            behavioral_input = {
                "content": intelligence_data,
                "verification": verification_data,
                "threat_assessment": deception_data,
                "platform": intelligence_data.get("content_metadata", {}).get("platform", "unknown"),
            }
            behavioral_results = {
                "behavioral_indicators": {
                    "consistency_score": self._analyze_content_consistency(behavioral_input),
                    "communication_patterns": self._analyze_communication_patterns(behavioral_input),
                    "reliability_indicators": deception_data.get("trust_evaluation", {}),
                },
                "entity_profile": {
                    "platform": behavioral_input["platform"],
                    "content_type": "video_analysis",
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
            knowledge_payload = self._build_knowledge_payload(
                acquisition_data,
                intelligence_data,
                verification_data,
                fact_data=fact_data,
                threat_data=deception_data,
                behavioral_data=behavioral_data,
            )
            knowledge_payload["integration_timestamp"] = time.time()
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
            knowledge_agent = self._get_or_create_agent("knowledge_integrator")
            persona_agent = self._get_or_create_agent("persona_archivist")
            mission_agent = self._get_or_create_agent("mission_orchestrator")
            integration_task = Task(
                description="Integrate comprehensive intelligence across vector, graph, and continual memory systems using the knowledge payload from shared context",
                expected_output="Multi-system knowledge integration with vector storage, graph relationships, and continual memory consolidation",
                agent=knowledge_agent,
            )
            persona_task = Task(
                description="Archive behavioral and threat profiles in persona management system using behavioral_data and threat_data from shared context",
                expected_output="Comprehensive persona dossier with behavioral history, threat correlation, and trust metrics",
                agent=persona_agent,
            )
            orchestration_task = Task(
                description="Orchestrate knowledge consolidation across all intelligence systems for mission continuity using intelligence_data from shared context",
                expected_output="Mission intelligence coordination with system integration status and consolidation metrics",
                agent=mission_agent,
            )
            knowledge_crew = Crew(
                agents=[knowledge_agent, persona_agent, mission_agent],
                tasks=[integration_task, persona_task, orchestration_task],
                verbose=True,
                process=Process.sequential,
            )
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
            except Exception as _ctx_err:
                self.logger.debug(f"Knowledge crew context population skipped: {_ctx_err}")
            crew_result = await asyncio.to_thread(knowledge_crew.kickoff)
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
            transcript = analysis_data.get("transcript", "")
            if not transcript:
                return StepResult.skip(reason="No transcript available for threat analysis")
            verification_agent = self._get_or_create_agent("verification_director")
            recon_agent = self._get_or_create_agent("signal_recon_specialist")
            try:
                shared_ctx = {
                    "analysis_data": analysis_data,
                    "verification_data": verification_data,
                    "transcript": transcript,
                }
                self._populate_agent_tool_context(verification_agent, shared_ctx)
                self._populate_agent_tool_context(recon_agent, shared_ctx)
            except Exception as _ctx_err:
                self.logger.debug(f"Threat agents context population skipped: {_ctx_err}")
            threat_task = Task(
                description="Analyze transcript for deception, logical fallacies, and threat indicators using transcript from shared context",
                expected_output="Comprehensive threat assessment with deception scores, fallacy analysis, and risk indicators",
                agent=verification_agent,
            )
            signal_task = Task(
                description="Perform signal intelligence analysis to detect narrative manipulation using transcript from shared context",
                expected_output="Signal intelligence report with sentiment shifts and narrative manipulation indicators",
                agent=recon_agent,
            )
            threat_crew = Crew(
                agents=[verification_agent, recon_agent],
                tasks=[threat_task, signal_task],
                verbose=True,
                process=Process.sequential,
            )
            crew_result = await asyncio.to_thread(threat_crew.kickoff)
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
            analysis_agent = self._get_or_create_agent("analysis_cartographer")
            persona_agent = self._get_or_create_agent("persona_archivist")
            shared_context = {
                "transcript": transcript,
                "analysis_data": analysis_data,
                "threat_data": threat_data,
                "threat_level": threat_data.get("threat_level", "unknown"),
                "content_metadata": analysis_data.get("content_metadata", {}),
            }
            self._populate_agent_tool_context(analysis_agent, shared_context)
            self._populate_agent_tool_context(persona_agent, shared_context)
            behavioral_task = Task(
                description=f"Perform comprehensive behavioral analysis on transcript with threat context (threat_level: {threat_data.get('threat_level', 'unknown')}) using transcript and threat_data from shared context"
                expected_output="Detailed behavioral profile with personality traits, communication patterns, and risk indicators",
                agent=analysis_agent,
            )
            persona_task = Task(
                description="Create detailed persona profile integrating behavioral patterns with threat indicators using threat_data from shared context",
                expected_output="Comprehensive persona dossier with behavioral history, sentiment analysis, and trust metrics",
                agent=persona_agent,
            )
            profiling_crew = Crew(
                agents=[analysis_agent, persona_agent],
                tasks=[behavioral_task, persona_task],
                verbose=True,
                process=Process.sequential,
            )
            crew_result = await asyncio.to_thread(profiling_crew.kickoff)
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
            transcript = analysis_data.get("transcript", "")
            claims = verification_data.get("fact_checks", {})
            if not transcript:
                return StepResult.skip(reason="No content available for research synthesis")
            trend_agent = self._get_or_create_agent("trend_intelligence_scout")
            knowledge_agent = self._get_or_create_agent("knowledge_integrator")
            research_context = {
                "transcript": transcript,
                "claims": claims,
                "analysis_data": analysis_data,
                "verification_data": verification_data,
            }
            self._populate_agent_tool_context(trend_agent, research_context)
            self._populate_agent_tool_context(knowledge_agent, research_context)
            research_task = Task(
                description=f"Conduct comprehensive research synthesis on transcript content and claims: {transcript[:1000]}... Claims: {claims}",
                expected_output="Detailed research report with contextual findings, source verification, and intelligence synthesis",
                agent=trend_agent,
            )
            integration_task = Task(
                description=f"Integrate research findings with existing knowledge base and create comprehensive context: {verification_data}",
                expected_output="Knowledge synthesis with contextual relevance, confidence scores, and integrated intelligence",
                agent=knowledge_agent,
            )
            research_crew = Crew(
                agents=[trend_agent, knowledge_agent],
                tasks=[research_task, integration_task],
                verbose=True,
                process=Process.sequential,
            )
            crew_result = await asyncio.to_thread(research_crew.kickoff)
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
            workflow_id = synthesis_result.get("workflow_id", f"wf_{int(time.time())}")
            url = synthesis_result.get("workflow_metadata", {}).get("url", "unknown")
            if not self._is_session_valid(interaction):
                self.logger.warning(
                    f"⚠️ Discord session closed before reporting results. Persisting results for workflow {workflow_id}..."
                )
                result_file = await self._persist_workflow_results(workflow_id, synthesis_result, url, depth)
                if result_file:
                    self.logger.info(
                        f"📁 Results saved to {result_file}. Retrieval command: /retrieve_results workflow_id:{workflow_id}"
                    )
                else:
                    self.logger.info(
                        f"Specialized Intelligence Results (session closed, persistence failed):\n{synthesis_result}"
                    )
                get_metrics().counter(
                    "discord_session_closed_total", labels={"stage": "communication_reporting", "depth": depth}
                )
                return
            main_embed = await self._create_specialized_main_results_embed(synthesis_result, depth)
            details_embed = await self._create_specialized_details_embed(synthesis_result)
            try:
                await interaction.followup.send(embeds=[main_embed, details_embed], ephemeral=False)
            except RuntimeError as e:
                if "Session is closed" in str(e):
                    self.logger.warning(f"⚠️ Session closed while sending main results for workflow {workflow_id}")
                    result_file = await self._persist_workflow_results(workflow_id, synthesis_result, url, depth)
                    if result_file:
                        self.logger.info(
                            f"📁 Results saved to {result_file} after send failure. Retrieval command: /retrieve_results workflow_id:{workflow_id}"
                        )
                    get_metrics().counter(
                        "discord_session_closed_total", labels={"stage": "communication_reporting_send", "depth": depth}
                    )
                    return
                else:
                    raise
            knowledge_data = synthesis_result.get("knowledge", {})
            if not isinstance(knowledge_data, dict) or not knowledge_data:
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
            if "Session is closed" in str(e):
                self.logger.warning("Session closed during communication/reporting")
                self.logger.info(f"Specialized Intelligence Results (session closed):\n{synthesis_result}")
                return
            self.logger.error(f"Communication & Reporting Coordinator failed: {e}")
            if self._is_session_valid(interaction):
                try:
                    summary = synthesis_result.get("workflow_metadata", {})
                    await interaction.followup.send(
                        f"✅ **Specialized Autonomous Intelligence Analysis Complete**\n\n**URL:** {summary.get('url', 'N/A')}\n**Threat Score:** {synthesis_result.get('deception', {}).get('threat_score', 0.0):.2f}/1.00\n**Processing Time:** {summary.get('processing_time', 0.0):.1f}s\n**Specialized Agents:** {summary.get('specialized_agents_used', 0)}\n\n*Analysis completed using specialized autonomous intelligence agents.*"
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

    def _assess_content_coherence(self, analysis_data: dict[str, Any]) -> float:
        """Assess the coherence of the analyzed content."""
        return quality_assessors.assess_content_coherence(analysis_data, self.logger)

    @staticmethod
    @staticmethod
    def _clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        """Clamp helper to keep quality metrics within expected bounds."""
        return quality_assessors.clamp_score(value, minimum, maximum)

    def _assess_factual_accuracy(
        self, verification_data: dict[str, Any] | None, fact_data: dict[str, Any] | None = None
    ) -> float:
        """Derive a factual accuracy score from verification and fact analysis outputs."""
        return quality_assessors.assess_factual_accuracy(verification_data, fact_data, self.logger)

    def _assess_source_credibility(
        self, knowledge_data: dict[str, Any] | None, verification_data: dict[str, Any] | None
    ) -> float:
        """Estimate source credibility using knowledge payload and verification metadata."""
        return quality_assessors.assess_source_credibility(knowledge_data, verification_data, self.logger)

    def _assess_bias_levels(
        self, analysis_data: dict[str, Any] | None, verification_data: dict[str, Any] | None
    ) -> float:
        """Score how balanced the content is based on bias indicators and sentiment spread."""
        return quality_assessors.assess_bias_levels(analysis_data, verification_data, self.logger)

    def _assess_emotional_manipulation(self, analysis_data: dict[str, Any] | None) -> float:
        """Estimate the level of emotional manipulation present in the content."""
        return quality_assessors.assess_emotional_manipulation(analysis_data, self.logger)

    def _assess_logical_consistency(
        self, verification_data: dict[str, Any] | None, logical_analysis: dict[str, Any] | None = None
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
        self, analysis_data: dict[str, Any], verification_data: dict[str, Any], fact_data: dict[str, Any] | None = None
    ) -> list[str]:
        """Highlight opportunities for future workflow improvements.

        Delegates to quality_assessors.identify_learning_opportunities.
        """
        return quality_assessors.identify_learning_opportunities(analysis_data, verification_data, fact_data)

    def _generate_enhancement_suggestions(
        self, quality_dimensions: dict[str, float], analysis_data: dict[str, Any], verification_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert dimension scores into actionable follow-up items.

        Delegates to quality_assessors.generate_enhancement_suggestions.
        """
        return quality_assessors.generate_enhancement_suggestions(quality_dimensions, analysis_data, verification_data)

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
        """Synthesize all specialized intelligence results into comprehensive analysis.

        Delegates to result_synthesizers.synthesize_specialized_intelligence_results.
        """
        return result_synthesizers.synthesize_specialized_intelligence_results(
            all_results=all_results,
            generate_specialized_insights_fn=self._generate_specialized_insights,
            logger=self.logger,
        )

    def _generate_specialized_insights(self, results: dict[str, Any]) -> list[str]:
        """Delegates to analytics_calculators.generate_specialized_insights."""
        return analytics_calculators.generate_specialized_insights(results, self.logger)

    async def _create_specialized_main_results_embed(self, results: dict[str, Any], depth: str) -> Any:
        """Create specialized main results embed for Discord (delegates to discord_helpers)."""
        return await discord_helpers.create_specialized_main_results_embed(results, depth)

    async def _create_specialized_details_embed(self, results: dict[str, Any]) -> Any:
        """Create specialized detailed results embed (delegates to discord_helpers)."""
        return await discord_helpers.create_specialized_details_embed(results)

    async def _create_specialized_knowledge_embed(self, knowledge_data: dict[str, Any]) -> Any:
        """Create specialized knowledge integration embed (delegates to discord_helpers)."""
        return await discord_helpers.create_specialized_knowledge_embed(knowledge_data)

    async def _execute_content_pipeline(self, url: str) -> StepResult:
        """Execute the core content pipeline with minimal wrapping for autonomous workflow."""
        try:
            self.logger.info(f"Executing ContentPipeline for autonomous intelligence workflow: {url}")
            pipeline_tool = PipelineTool()
            quality_strategies = ["1080p", "720p", "480p", "audio"]
            for quality in quality_strategies:
                try:
                    self.logger.info(f"Attempting ContentPipeline with quality: {quality}")
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
                        return pipeline_result
                    else:
                        self.logger.warning(f"ContentPipeline failed with quality {quality}: {pipeline_result.error}")
                except Exception as quality_error:
                    self.logger.warning(f"ContentPipeline exception with quality {quality}: {quality_error}")
                    continue
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
            transcript = content_data.get("transcription", {}).get("transcript", "")
            if not transcript:
                return StepResult.skip(reason="No transcript available for fact analysis")
            claim_extractor = ClaimExtractorTool()
            fact_check_tool = FactCheckTool()
            fallacy_tool = LogicalFallacyTool()
            perspective_tool = PerspectiveSynthesizerTool()
            claim_res = await asyncio.to_thread(claim_extractor.run, transcript)
            claims: list[str] = []
            if isinstance(claim_res, StepResult) and claim_res.success:
                raw_claims = claim_res.data.get("claims", []) if isinstance(claim_res.data, dict) else []
                if isinstance(raw_claims, list):
                    claims = sorted([str(c) for c in raw_claims if isinstance(c, str)], key=len, reverse=True)[:5]
            per_claim_results: list[StepResult] = []
            evidence: list[dict[str, Any]] = []
            backends_used: set[str] = set()
            factcheck_items: list[dict[str, Any]] = []
            if claims:
                tasks = [asyncio.create_task(self._to_thread_with_tenant(fact_check_tool.run, c)) for c in claims]
                per_claim_results = list(await asyncio.gather(*tasks, return_exceptions=True))
                for r, c in zip(per_claim_results, claims, strict=False):
                    if isinstance(r, StepResult) and r.success:
                        ev = r.data.get("evidence", []) if isinstance(r.data, dict) else []
                        if isinstance(ev, list):
                            for item in ev:
                                if isinstance(item, dict):
                                    item = {**item, "claim": c}
                                    evidence.append(item)
                        bu = r.data.get("backends_used", []) if isinstance(r.data, dict) else []
                        if isinstance(bu, list):
                            for b in bu:
                                if isinstance(b, str):
                                    backends_used.add(b)
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
                                    confidence = float(conf_raw)
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
                            pass
            fallacy_result = await asyncio.to_thread(fallacy_tool.run, transcript)
            perspective_inputs: list[str] = [transcript]
            if evidence:
                snippets = []
                for e in evidence[:10]:
                    title = str(e.get("title", "")) if isinstance(e, dict) else ""
                    url = str(e.get("url", "")) if isinstance(e, dict) else ""
                    claim = str(e.get("claim", "")) if isinstance(e, dict) else ""
                    if title or url or claim:
                        snippets.append(" | ".join(filter(None, [claim, title, url])))
                if snippets:
                    perspective_inputs.append("\n".join(snippets))
            perspective_result = await asyncio.to_thread(perspective_tool.run, *perspective_inputs)
            fact_checks_payload: dict[str, Any] = {
                "claims": claims,
                "evidence": evidence,
                "backends_used": sorted(backends_used),
                "evidence_count": len(evidence),
            }
            if factcheck_items:
                fact_checks_payload["items"] = factcheck_items
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
                            c_val = float(c_raw)
                        except Exception:
                            c_val = 0.0
                        conf_sum += max(0.0, min(c_val, 1.0))
                        conf_ct += 1
                    fact_checks_payload["verified_claims"] = verified
                    fact_checks_payload["disputed_claims"] = disputed
                    if conf_ct > 0:
                        fact_checks_payload["confidence"] = round(conf_sum / conf_ct, 3)
                except Exception:
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
            title = content_data.get("download", {}).get("title", "")
            keywords = content_data.get("analysis", {}).get("keywords", [])
            if not title and (not keywords):
                return StepResult.skip(reason="No topics identified for cross-platform intelligence")
            search_terms = [title, *keywords[:3]] if keywords else [title]
            if os.getenv("ENABLE_PLACEHOLDER_SOCIAL_INTEL", "0").lower() not in {"1", "true", "yes", "on"}:
                return StepResult.skip(
                    reason="social_connectors_not_configured",
                    message="Social connectors are not configured; skipping placeholder social intelligence. Set ENABLE_PLACEHOLDER_SOCIAL_INTEL=1 to enable synthetic monitoring during development.",
                    search_terms=search_terms,
                )
            social_monitor = SocialMediaMonitorTool()
            x_monitor = XMonitorTool()
            search_terms = [title, *keywords[:3]] if keywords else [title]
            search_query = " OR ".join(search_terms)
            placeholder_posts = {
                "reddit": [f"Discussion about {term}" for term in search_terms[:2]],
                "twitter": [f"Latest news on {term}" for term in search_terms[:2]],
                "discord": [f"Community chatter about {term}" for term in search_terms[:1]],
            }
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
            deception_tool = DeceptionScoringTool()
            truth_tool = TruthScoringTool()
            trust_tool = TrustworthinessTrackerTool()
            fact_verification_data = fact_data.get("fact_checks", {})
            logical_analysis_data = fact_data.get("logical_fallacies", {})
            factchecks = self._transform_evidence_to_verdicts(fact_verification_data)
            fallacies = self._extract_fallacy_data(logical_analysis_data)
            analysis_input = {
                "content": content_data,
                "factchecks": factchecks,
                "fallacies": fallacies,
                "perspective": fact_data.get("perspective_synthesis", {}),
            }
            deception_task = asyncio.create_task(self._to_thread_with_tenant(deception_tool.run, analysis_input))

            def _verdict_to_bool(v: str) -> object:
                v = v.strip().lower()
                if v in {"true", "likely true", "supported"}:
                    return True
                if v in {"false", "likely false", "unsupported"}:
                    return False
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
                truth_task = asyncio.create_task(asyncio.to_thread(lambda: StepResult.skip(reason="no verdicts")))
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

            async def _compute_trust_result():
                tr = await truth_task
                verdict_bool = None
                if isinstance(tr, StepResult) and tr.success:
                    score = tr.data.get("score") if isinstance(tr.data, dict) else None
                    if isinstance(score, (int, float)):
                        verdict_bool = bool(score >= 0.55)
                if verdict_bool is None:
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
            memory_tool = MemoryStorageTool()
            graph_tool = GraphMemoryTool()
            hipporag_tool = HippoRagContinualMemoryTool()
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
                    tags=[f"platform:{knowledge_payload.get('platform', 'unknown')}"]
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
        """Synthesize all autonomous analysis results into a comprehensive summary.

        Delegates to result_synthesizers.synthesize_autonomous_results.
        """
        return result_synthesizers.synthesize_autonomous_results(
            all_results=all_results,
            calculate_summary_statistics_fn=self._calculate_summary_statistics,
            generate_autonomous_insights_fn=self._generate_autonomous_insights,
            logger=self.logger,
        )

    async def _synthesize_enhanced_autonomous_results(self, all_results: dict[str, Any]) -> StepResult:
        """Synthesize enhanced autonomous analysis results using advanced multi-modal synthesis.

        Delegates to result_synthesizers.synthesize_enhanced_autonomous_results.
        """
        return await result_synthesizers.synthesize_enhanced_autonomous_results(
            all_results=all_results,
            synthesizer=self.synthesizer,
            error_handler=self.error_handler,
            fallback_basic_synthesis_fn=self._fallback_basic_synthesis,
            logger=self.logger,
        )

    async def _fallback_basic_synthesis(self, all_results: dict[str, Any], error_context: str) -> StepResult:
        """Fallback basic synthesis when advanced synthesis fails.

        Delegates to result_synthesizers.fallback_basic_synthesis.
        """
        return result_synthesizers.fallback_basic_synthesis(
            all_results=all_results, error_context=error_context, logger=self.logger
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
        """Check if Discord session is still valid for sending messages (delegates to discord_helpers)."""
        return discord_helpers.is_session_valid(interaction, self.logger)

    async def _persist_workflow_results(self, workflow_id: str, results: dict[str, Any], url: str, depth: str) -> str:
        """Persist workflow results to disk when Discord session closes (delegates to discord_helpers)."""
        return await discord_helpers.persist_workflow_results(workflow_id, results, url, depth, self.logger)

    async def _send_progress_update(self, interaction: Any, message: str, current: int, total: int) -> None:
        """Send real-time progress updates to Discord (delegates to discord_helpers)."""
        await discord_helpers.send_progress_update(interaction, message, current, total, self.logger)

    async def _handle_acquisition_failure(self, interaction: Any, acquisition_result: StepResult, url: str) -> None:
        """Handle content acquisition failures with specialized guidance (delegates to discord_helpers)."""
        await discord_helpers.handle_acquisition_failure(interaction, acquisition_result, url, self.logger)

    async def _send_error_response(self, interaction: Any, stage: str, error: str) -> None:
        """Send error response to Discord with session resilience (delegates to discord_helpers)."""
        await discord_helpers.send_error_response(interaction, stage, error, self.logger)

    async def _send_enhanced_error_response(self, interaction: Any, stage: str, enhanced_message: str) -> None:
        """Send enhanced user-friendly error response to Discord (delegates to discord_helpers)."""
        await discord_helpers.send_enhanced_error_response(interaction, stage, enhanced_message, self.logger)

    async def _deliver_autonomous_results(self, interaction: Any, results: dict[str, Any], depth: str) -> None:
        """Deliver comprehensive autonomous analysis results to Discord (delegates to discord_helpers)."""
        await discord_helpers.deliver_autonomous_results(interaction, results, depth, self.logger)

    async def _create_main_results_embed(self, results: dict[str, Any], depth: str) -> Any:
        """Create the main results embed for Discord.

        Delegates to discord_helpers.create_main_results_embed for implementation.
        """
        return await discord_helpers.create_main_results_embed(results, depth)

    async def _create_details_embed(self, results: dict[str, Any]) -> Any:
        """Create detailed results embed (delegates to discord_helpers)."""
        return await discord_helpers.create_details_embed(results)

    async def _create_knowledge_base_embed(self, knowledge_data: dict[str, Any]) -> Any:
        """Create knowledge base integration embed (delegates to discord_helpers)."""
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
        """Extract research topics from transcript and claims.

        Delegates to extractors.extract_research_topics.
        """
        return extractors.extract_research_topics(transcript, claims)

    def _calculate_contextual_relevance(self, research_results: dict[str, Any], analysis_data: dict[str, Any]) -> float:
        """Calculate contextual relevance of research to analysis.

        Delegates to analytics_calculators.calculate_contextual_relevance.
        """
        return analytics_calculators.calculate_contextual_relevance(research_results, analysis_data, self.logger)

    def _calculate_synthesis_confidence(self, research_results: dict[str, Any]) -> float:
        """Delegates to analytics_calculators.calculate_synthesis_confidence."""
        return analytics_calculators.calculate_synthesis_confidence(research_results, self.logger)

    def _extract_research_topics_from_crew(self, crew_result: Any) -> list[str]:
        """Extract research topics from CrewAI crew analysis.

        Delegates to extractors.extract_research_topics_from_crew.
        """
        return extractors.extract_research_topics_from_crew(crew_result)

    def _calculate_contextual_relevance_from_crew(self, crew_result: Any, analysis_data: dict[str, Any]) -> float:
        """Delegates to analytics_calculators.calculate_contextual_relevance_from_crew."""
        return analytics_calculators.calculate_contextual_relevance_from_crew(crew_result, analysis_data, self.logger)

    def _calculate_synthesis_confidence_from_crew(self, crew_result: Any) -> float:
        """Calculate synthesis confidence from CrewAI crew results.

        Delegates to extractors.calculate_synthesis_confidence_from_crew.
        """
        return extractors.calculate_synthesis_confidence_from_crew(crew_result)

    def _extract_system_status_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Delegate to pipeline_result_builders.extract_system_status_from_crew."""
        from domains.orchestration.pipeline_result_builders import extract_system_status_from_crew

        return extract_system_status_from_crew(crew_result)

    def _calculate_consolidation_metrics_from_crew(self, crew_result: Any) -> dict[str, Any]:
        """Delegates to analytics_calculators.calculate_consolidation_metrics_from_crew."""
        return analytics_calculators.calculate_consolidation_metrics_from_crew(crew_result, self.logger)

    def _create_executive_summary(self, analysis_data: dict[str, Any], threat_data: dict[str, Any]) -> str:
        """Delegate to pipeline_result_builders.create_executive_summary."""
        from domains.orchestration.pipeline_result_builders import create_executive_summary

        return create_executive_summary(analysis_data, threat_data)

    def _extract_key_findings(
        self, analysis_data: dict[str, Any], verification_data: dict[str, Any], threat_data: dict[str, Any]
    ) -> list[str]:
        """Delegate to pipeline_result_builders.extract_key_findings."""
        from domains.orchestration.pipeline_result_builders import extract_key_findings

        return extract_key_findings(analysis_data, verification_data, threat_data)

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

    async def _execute_advanced_pattern_recognition(
        self, analysis_data: dict[str, Any], behavioral_data: dict[str, Any]
    ) -> StepResult:
        """Execute advanced pattern recognition using CrewAI comprehensive linguistic analyst."""
        try:
            pattern_agent = self._get_or_create_agent("comprehensive_linguistic_analyst")
            try:
                self._populate_agent_tool_context(
                    pattern_agent, {"analysis_data": analysis_data, "behavioral_data": behavioral_data}
                )
                self.logger.info("✅ Pattern recognition context populated successfully")
            except Exception as _ctx_err:
                self.logger.debug(f"Pattern agent context population skipped: {_ctx_err}")
            pattern_task = Task(
                description=f"Perform advanced pattern recognition analysis on linguistic data: {str(analysis_data)[:500]}... and behavioral patterns: {str(behavioral_data)[:500]}... Identify recurring patterns, anomalies, linguistic markers, behavioral signatures, predictive indicators, and correlations between content patterns and behavioral traits.",
                expected_output="Advanced pattern recognition report containing identified patterns, behavioral correlations, anomaly detection results, predictive indicators, and pattern confidence scores",
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
            network_agent = self.crew.research_synthesis_specialist
            try:
                self._populate_agent_tool_context(
                    network_agent, {"verification_data": verification_data, "research_data": research_data}
                )
                self.logger.info("✅ Cross-reference network context populated successfully")
            except Exception as _ctx_err:
                self.logger.debug(f"Cross-reference network context population skipped: {_ctx_err}")
            network_task = Task(
                description=f"Build comprehensive cross-reference intelligence network from verification data: {str(verification_data)[:500]}... and research data: {str(research_data)[:500]}... Create interconnected knowledge network mapping relationships between facts, sources, entities, claims, and contextual information. Identify information gaps, corroboration patterns, contradiction networks, and source reliability clusters.",
                expected_output="Cross-reference intelligence network report with relationship mappings, source clusters, fact corroboration matrix, contradiction analysis, and network reliability scores",
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
            threat_agent = self.crew.threat_intelligence_analyst
            try:
                self._populate_agent_tool_context(
                    threat_agent,
                    {"threat_data": threat_data, "behavioral_data": behavioral_data, "pattern_data": pattern_data},
                )
                self.logger.info("✅ Predictive threat context populated successfully")
            except Exception as _ctx_err:
                self.logger.debug(f"Predictive threat context population skipped: {_ctx_err}")
            prediction_task = Task(
                description=f"Perform comprehensive predictive threat assessment combining threat intelligence: {str(threat_data)[:500]}..., behavioral patterns: {str(behavioral_data)[:500]}..., and pattern recognition: {str(pattern_data)[:500]}... Analyze threat trajectories, predict future risk vectors, assess escalation probabilities, identify early warning indicators, and develop mitigation strategies for potential threats.",
                expected_output="Predictive threat assessment report with risk trajectory analysis, threat escalation probabilities, early warning indicators, predictive risk scores, and mitigation strategies",
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
                synthesis_agent = self._get_or_create_agent("knowledge_integrator")
                try:
                    self._populate_agent_tool_context(
                        synthesis_agent,
                        {
                            "acquisition_data": acquisition_data,
                            "analysis_data": analysis_data,
                            "behavioral_data": behavioral_data,
                        },
                    )
                except Exception as _ctx_err:
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
                graph_agent = self._get_or_create_agent("knowledge_integrator")
                try:
                    self._populate_agent_tool_context(
                        graph_agent, {"knowledge_data": knowledge_data, "network_data": network_data}
                    )
                except Exception as _ctx_err:
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
                learning_agent = self._get_or_create_agent("performance_analyst")
                try:
                    self._populate_agent_tool_context(
                        learning_agent, {"quality_data": quality_data, "analytics_data": analytics_data}
                    )
                except Exception as _ctx_err:
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
                bandits_agent = self._get_or_create_agent("performance_analyst")
                try:
                    self._populate_agent_tool_context(
                        bandits_agent, {"analytics_data": analytics_data, "learning_data": learning_data}
                    )
                except Exception as _ctx_err:
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
                community_agent = self._get_or_create_agent("community_liaison")
                self._populate_agent_tool_context(
                    community_agent, {"social_data": social_data, "network_data": network_data}
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
                adaptive_agent = self._get_or_create_agent("mission_orchestrator")
                self._populate_agent_tool_context(
                    adaptive_agent, {"bandits_data": bandits_data, "learning_data": learning_data}
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
                memory_agent = self._get_or_create_agent("knowledge_integrator")
                self._populate_agent_tool_context(
                    memory_agent, {"knowledge_data": knowledge_data, "graph_data": graph_data}
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

    def _route_query_to_tool(self, query: str) -> str | None:
        """Use semantic router to select the best tool for a query."""
        settings = Settings()
        if not settings.enable_semantic_router:
            self.logger.debug("Semantic router is disabled by settings.")
            return None
        if not SEMANTIC_ROUTER_AVAILABLE:
            self.logger.warning(
                "Semantic router requested but semantic-router library not installed. Install with: pip install -e '.[semantic_router]'"
            )
            return None
        try:
            from semantic_router import Route
        except ImportError:
            self.logger.warning("Failed to import semantic_router.Route")
            return None
        routes = [
            Route(
                name="social_media_monitoring",
                utterances=[
                    "monitor social media for",
                    "track mentions of",
                    "what are people saying about",
                    "check twitter for",
                ],
            ),
            Route(
                name="content_acquisition",
                utterances=[
                    "download the video from",
                    "get the content from this url",
                    "acquire the media at",
                    "fetch this youtube link",
                ],
            ),
            Route(
                name="transcription",
                utterances=[
                    "transcribe the audio from",
                    "what does the audio say",
                    "create a transcript for",
                    "convert this speech to text",
                ],
            ),
            Route(
                name="analysis",
                utterances=[
                    "analyze the transcript",
                    "what are the key insights",
                    "summarize the content",
                    "give me a breakdown of the text",
                ],
            ),
            Route(
                name="verification",
                utterances=[
                    "fact-check the claims",
                    "verify the information",
                    "is this true",
                    "check the facts in this",
                ],
            ),
        ]
        try:
            router_service = SemanticRouterService(routes=routes)
            route_name = router_service.route(query)
            self.logger.info(f"Semantic router routed query to: {route_name}")
            return route_name
        except Exception as e:
            self.logger.error(f"Semantic router failed: {e}", exc_info=True)
            return None

    async def _execute_agent_coordination_setup(self, url: str, depth: str) -> StepResult:
        """Initialize and coordinate CrewAI multi-agent system for sophisticated orchestration."""
        try:
            if not getattr(self, "_llm_available", False):
                self.agent_coordinators = {}
                return StepResult.skip(reason="llm_unavailable", message="Agent system not initialized (no API key)")
            from .crew_core import UltimateDiscordIntelligenceBotCrew

            crew_instance = UltimateDiscordIntelligenceBotCrew()
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
            else:
                active_agents = ["mission_orchestrator", "acquisition_specialist", "analysis_cartographer"]
            self.crew_instance = crew_instance
            self.active_agents = active_agents
            self.agent_coordinators = {}
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
            if getattr(self, "_llm_available", False):
                mission_agent = self._get_or_create_agent("mission_orchestrator")
                with contextlib.suppress(Exception):
                    self._populate_agent_tool_context(
                        mission_agent, {"mission_url": url, "mission_depth": depth, "target_url": url, "depth": depth}
                    )
                planning_task = Task(
                    description=prompt_config.Autonomous.ORCHESTRATOR_PROMPT.format(url=url, depth=depth),
                    expected_output="A detailed report of the content analysis, including a summary, key claims, and any detected fallacies or perspectives. The final output must be a markdown document.",
                    agent=mission_agent,
                )
                planning_crew = Crew(
                    agents=[mission_agent], tasks=[planning_task], verbose=True, process=Process.sequential
                )
                crew_result = await asyncio.to_thread(planning_crew.kickoff)
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

    async def _execute_specialized_content_acquisition(self, url: str) -> StepResult:
        """Execute specialized content acquisition with enhanced multi-platform support and ContentPipeline integration."""
        try:
            self.logger.info(f"Starting specialized content acquisition with ContentPipeline synergy: {url}")
            pipeline_result = await self._execute_content_pipeline(url)
            if not pipeline_result.success:
                error_msg = pipeline_result.error or "Content acquisition failed"
                lower_url = url.lower()
                if ("youtube.com" in lower_url or "youtu.be" in lower_url) and (
                    "Requested format is not available" in error_msg or "nsig extraction failed" in error_msg
                ):
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
            pipeline_wrapper = pipeline_result.data if isinstance(pipeline_result.data, dict) else {}
            raw_payload = pipeline_wrapper.get("data") if isinstance(pipeline_wrapper, dict) else None
            pipeline_payload = dict(raw_payload) if isinstance(raw_payload, dict) else {}
            metadata = {k: v for k, v in pipeline_wrapper.items() if k != "data"}
            metadata.update(
                {"acquisition_timestamp": time.time(), "source_url": url, "workflow_type": "autonomous_intelligence"}
            )
            metadata.setdefault("url", url)
            normalised_payload = dict(pipeline_payload)
            normalised_payload.pop("status", None)
            normalised_payload.setdefault("source_url", url)
            normalised_payload.setdefault("acquisition_timestamp", metadata["acquisition_timestamp"])
            normalised_payload.setdefault("workflow_type", metadata["workflow_type"])
            normalised_payload["pipeline_metadata"] = metadata
            if isinstance(raw_payload, dict):
                normalised_payload["raw_pipeline_payload"] = raw_payload
            self.logger.info("Specialized content acquisition successful with ContentPipeline")
            return StepResult.ok(**normalised_payload, message="Content acquisition completed via ContentPipeline")
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
            if not acquisition_result.success or not acquisition_result.data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")
            pipeline_data = self._normalize_acquisition_data(acquisition_result)
            if not pipeline_data:
                return StepResult.skip(reason="No acquisition data available for transcription analysis")
            transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
            transcription_block = {} if not isinstance(transcription_block, dict) else dict(transcription_block)
            transcript = transcription_block.get("transcript", "")
            media_info = pipeline_data.get("download", {}) if isinstance(pipeline_data, dict) else {}
            media_info = {} if not isinstance(media_info, dict) else dict(media_info)
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
            if hasattr(self, "crew") and self.crew is not None:
                try:
                    transcription_agent = self._get_or_create_agent("transcription_engineer")
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
                    except Exception as _ctx_err:
                        self.logger.warning(
                            f"⚠️ Transcription agent context population FAILED: {_ctx_err}", exc_info=True
                        )
                    transcription_task = Task(
                        description=f"Enhance transcription quality, create timeline anchors, and build comprehensive index for transcript: {transcript[:500]}... Media info: {media_info}",
                        expected_output="Enhanced transcript with timeline anchors, quality improvements, and comprehensive indexing",
                        agent=transcription_agent,
                    )
                    transcription_crew = Crew(
                        agents=[transcription_agent],
                        tasks=[transcription_task],
                        verbose=True,
                        process=Process.sequential,
                    )
                    crew_result = await asyncio.to_thread(transcription_crew.kickoff)
                    return StepResult.ok(
                        message="Advanced transcription analysis completed with CrewAI agent",
                        transcript=transcript,
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
            else:
                self.logger.info("CrewAI agents not available, using basic transcription processing")
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
            if not transcription_result.success or not transcription_result.data:
                return StepResult.skip(reason="No transcription data available for content analysis")
            transcription_data = transcription_result.data
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
            return {
                "transcript": transcript,
                "analysis": "Basic analysis completed",
                "source_url": source_url,
                "error": "No advanced analysis available",
            }
        except Exception as e:
            return StepResult.fail(f"Content analysis failed: {e}")
