"""Modular crew orchestrator with organized agent and task modules.

This module defines the UltimateDiscordIntelligenceBotCrew using the new
modular structure with domain-specific agent and task modules for improved
maintainability and organization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


# Optional compatibility: import crewai dynamically to avoid type-stub issues
if TYPE_CHECKING:  # pragma: no cover - avoid importing third-party without stubs
    # Provide minimal type placeholders to satisfy type checkers without importing crewai
    class Agent:  # type: ignore[too-many-ancestors]
        ...

    class Task:  # type: ignore[too-many-ancestors]
        ...

    class Crew:  # type: ignore[too-many-ancestors]
        ...

    class Process:  # type: ignore[too-many-ancestors]
        sequential: str

    def agent(fn): ...

    def task(fn): ...

    def crew(fn): ...
else:
    try:  # pragma: no cover - friendly import
        import importlib as _importlib

        _crewai = _importlib.import_module("crewai")
        _project = _importlib.import_module("crewai.project")
        Agent = _crewai.Agent
        Crew = _crewai.Crew
        Process = _crewai.Process
        Task = _crewai.Task
        agent = _project.agent
        crew = _project.crew
        task = _project.task
    except ImportError:  # pragma: no cover - graceful degradation
        # Fallback for environments without crewai
        class Agent:  # type: ignore[too-many-ancestors]
            def __init__(self, **kwargs): ...

        class Task:  # type: ignore[too-many-ancestors]
            def __init__(self, **kwargs): ...

        class Crew:  # type: ignore[too-many-ancestors]
            def __init__(self, **kwargs): ...

        class Process:  # type: ignore[too-many-ancestors]
            sequential = "sequential"

        def agent(fn):
            return fn

        def task(fn):
            return fn

        def crew(fn):
            return fn


# Import modular components (optional in minimal environments)
try:  # pragma: no cover - optional dependency structure
    from ultimate_discord_intelligence_bot.agents import (
        AcquisitionAgents,
        AnalysisAgents,
        IntelligenceAgents,
        ObservabilityAgents,
        VerificationAgents,
    )

    _HAS_AGENT_MODULES = True
except Exception:  # minimal fallback without agent modules
    _HAS_AGENT_MODULES = False

# Import feature flags
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


# Import task modules (optional)
try:  # pragma: no cover
    from ultimate_discord_intelligence_bot.tasks import (
        ContentProcessingTasks,
        QualityAssuranceTasks,
    )

    _HAS_TASK_MODULES = True
except Exception:
    _HAS_TASK_MODULES = False

# Import tools for wrapping
from ultimate_discord_intelligence_bot.tools import (
    AdvancedPerformanceAnalyticsTool,
    CheckpointManagementTool,
    ContentGenerationTool,
    CostTrackingTool,
    MCPCallTool,
    Mem0MemoryTool,
    MultimodalAnalysisTool,
    OrchestrationStatusTool,
    PerspectiveSynthesizerTool,
    PipelineTool,
    RouterStatusTool,
    SystemStatusTool,
    TimelineTool,
    UnifiedCacheTool,
    UnifiedContextTool,
    UnifiedMemoryStoreTool,
    UnifiedMemoryTool,
    UnifiedMetricsTool,
    UnifiedRouterTool,
)


# Initialize feature flags
_flags = FeatureFlags.from_env()

# Feature flags for conditional tool inclusion
ENABLE_UNIFIED_KNOWLEDGE = _flags.is_enabled("ENABLE_UNIFIED_KNOWLEDGE")
ENABLE_UNIFIED_ROUTER = _flags.is_enabled("ENABLE_UNIFIED_ROUTER")
ENABLE_UNIFIED_CACHE = _flags.is_enabled("ENABLE_UNIFIED_CACHE")
ENABLE_ALERTS = _flags.is_enabled("ENABLE_ALERTS")
ENABLE_METRICS = _flags.is_enabled("ENABLE_METRICS")


def wrap_tool_for_crewai(tool_instance: Any) -> Any:
    """Wrap tool instance for CrewAI compatibility."""
    # This function provides compatibility between our tools and CrewAI
    # In a real implementation, this would handle the wrapping logic
    return tool_instance


class UltimateDiscordIntelligenceBotCrew:
    """Modular crew orchestrator with organized agent and task modules."""

    def __init__(self):
        """Initialize the modular crew."""
        # Initialize agent modules (or minimal placeholders)
        if _HAS_AGENT_MODULES:
            self.acquisition_agents = AcquisitionAgents()
            self.analysis_agents = AnalysisAgents()
            self.verification_agents = VerificationAgents()
            self.intelligence_agents = IntelligenceAgents()
            self.observability_agents = ObservabilityAgents()
        else:
            # Lightweight placeholders to satisfy attribute access in fast tests
            class _Placeholder:
                pass

            self.acquisition_agents = _Placeholder()
            self.analysis_agents = _Placeholder()
            self.verification_agents = _Placeholder()
            self.intelligence_agents = _Placeholder()
            self.observability_agents = _Placeholder()

        # Initialize task modules (or placeholders)
        if _HAS_TASK_MODULES:
            self.content_processing_tasks = ContentProcessingTasks()
            self.quality_assurance_tasks = QualityAssuranceTasks()
        else:

            class _PT:
                def plan_autonomy_mission(self):
                    return Task(description="Plan mission", expected_output="ok", agent=lambda: Agent(role="planner"))

                def capture_source_media(self):
                    return Task(description="Capture", expected_output="ok", agent=lambda: Agent(role="acq"))

                def transcribe_and_index_media(self):
                    return Task(description="Transcribe", expected_output="ok", agent=lambda: Agent(role="ts"))

                def map_transcript_insights(self):
                    return Task(description="Analyze", expected_output="ok", agent=lambda: Agent(role="ana"))

                def verify_priority_claims(self):
                    return Task(description="Verify", expected_output="ok", agent=lambda: Agent(role="ver"))

                def synthesize_intelligence(self):
                    return Task(description="Synthesize", expected_output="ok", agent=lambda: Agent(role="intel"))

                def store_memory_and_context(self):
                    return Task(description="Store", expected_output="ok", agent=lambda: Agent(role="mem"))

            class _QT:
                def assess_content_quality(self):
                    return Task(description="Assess", expected_output="ok", agent=lambda: Agent(role="qa"))

                def validate_fact_checking_results(self):
                    return Task(description="Validate", expected_output="ok", agent=lambda: Agent(role="qa"))

                def monitor_system_performance(self):
                    return Task(description="Monitor", expected_output="ok", agent=lambda: Agent(role="obs"))

                def optimize_resource_usage(self):
                    return Task(description="Optimize", expected_output="ok", agent=lambda: Agent(role="ops"))

                def ensure_output_consistency(self):
                    return Task(description="Consistency", expected_output="ok", agent=lambda: Agent(role="qa"))

                def track_quality_metrics(self):
                    return Task(description="Track", expected_output="ok", agent=lambda: Agent(role="obs"))

            self.content_processing_tasks = _PT()
            self.quality_assurance_tasks = _QT()

    # Mission Orchestrator
    @agent
    def mission_orchestrator(self) -> Agent:
        """Mission orchestrator with comprehensive tool set."""
        return Agent(
            role="Autonomy Mission Orchestrator",
            goal="Coordinate end-to-end missions, sequencing depth, specialists, and budgets.",
            backstory="Mission orchestration and strategic control with multimodal planning capabilities.",
            tools=[
                # Core orchestration tools
                wrap_tool_for_crewai(PipelineTool()),
                wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()),
                wrap_tool_for_crewai(TimelineTool()),
                wrap_tool_for_crewai(PerspectiveSynthesizerTool()),
                wrap_tool_for_crewai(MCPCallTool()),
                # Enhanced capabilities
                wrap_tool_for_crewai(MultimodalAnalysisTool()),
                wrap_tool_for_crewai(ContentGenerationTool()),
                wrap_tool_for_crewai(Mem0MemoryTool()),
                wrap_tool_for_crewai(CheckpointManagementTool()),
                # Conditional tools based on feature flags
                *(
                    [
                        wrap_tool_for_crewai(UnifiedMemoryTool()),
                        wrap_tool_for_crewai(UnifiedMemoryStoreTool()),
                        wrap_tool_for_crewai(UnifiedContextTool()),
                    ]
                    if ENABLE_UNIFIED_KNOWLEDGE
                    else []
                ),
                *(
                    [
                        wrap_tool_for_crewai(UnifiedRouterTool()),
                        wrap_tool_for_crewai(CostTrackingTool()),
                        wrap_tool_for_crewai(RouterStatusTool()),
                    ]
                    if ENABLE_UNIFIED_ROUTER
                    else []
                ),
                *(
                    [
                        wrap_tool_for_crewai(UnifiedCacheTool()),
                    ]
                    if ENABLE_UNIFIED_CACHE
                    else []
                ),
                *(
                    [
                        wrap_tool_for_crewai(UnifiedMetricsTool()),
                        wrap_tool_for_crewai(SystemStatusTool()),
                        wrap_tool_for_crewai(OrchestrationStatusTool()),
                    ]
                    if ENABLE_METRICS
                    else []
                ),
            ],
            verbose=True,
            allow_delegation=True,
        )

    # Content Processing Tasks
    @task
    def plan_autonomy_mission(self) -> Task:
        """Plan and execute autonomous intelligence mission."""
        return self.content_processing_tasks.plan_autonomy_mission()

    @task
    def capture_source_media(self) -> Task:
        """Capture and download source media content."""
        return self.content_processing_tasks.capture_source_media()

    @task
    def transcribe_and_index_media(self) -> Task:
        """Transcribe and index media content."""
        return self.content_processing_tasks.transcribe_and_index_media()

    @task
    def map_transcript_insights(self) -> Task:
        """Map insights from transcript content."""
        return self.content_processing_tasks.map_transcript_insights()

    @task
    def verify_priority_claims(self) -> Task:
        """Verify priority claims from content."""
        return self.content_processing_tasks.verify_priority_claims()

    @task
    def synthesize_intelligence(self) -> Task:
        """Synthesize intelligence from multiple sources."""
        return self.content_processing_tasks.synthesize_intelligence()

    @task
    def store_memory_and_context(self) -> Task:
        """Store results in memory and context systems."""
        return self.content_processing_tasks.store_memory_and_context()

    # Quality Assurance Tasks
    @task
    def assess_content_quality(self) -> Task:
        """Assess content quality and accuracy."""
        return self.quality_assurance_tasks.assess_content_quality()

    @task
    def validate_fact_checking_results(self) -> Task:
        """Validate fact-checking results and accuracy."""
        return self.quality_assurance_tasks.validate_fact_checking_results()

    @task
    def monitor_system_performance(self) -> Task:
        """Monitor system performance and health."""
        return self.quality_assurance_tasks.monitor_system_performance()

    @task
    def optimize_resource_usage(self) -> Task:
        """Optimize resource usage and allocation."""
        return self.quality_assurance_tasks.optimize_resource_usage()

    @task
    def ensure_output_consistency(self) -> Task:
        """Ensure output consistency and reliability."""
        return self.quality_assurance_tasks.ensure_output_consistency()

    @task
    def track_quality_metrics(self) -> Task:
        """Track quality metrics and performance indicators."""
        return self.quality_assurance_tasks.track_quality_metrics()

    @crew
    def crew(self) -> Crew:
        """Create the modular crew with organized agents and tasks."""
        if _HAS_AGENT_MODULES and _HAS_TASK_MODULES:
            return Crew(
                agents=[
                    self.mission_orchestrator(),
                    # Acquisition agents
                    self.acquisition_agents.acquisition_specialist(),
                    self.acquisition_agents.transcription_engineer(),
                    self.acquisition_agents.content_ingestion_specialist(),
                    self.acquisition_agents.enhanced_download_specialist(),
                    # Analysis agents
                    self.analysis_agents.analysis_cartographer(),
                    self.analysis_agents.political_analysis_specialist(),
                    self.analysis_agents.sentiment_analysis_specialist(),
                    self.analysis_agents.claim_extraction_specialist(),
                    self.analysis_agents.trend_analysis_specialist(),
                    self.analysis_agents.multimodal_analysis_specialist(),
                    self.analysis_agents.social_graph_analysis_specialist(),
                    self.analysis_agents.live_stream_analysis_specialist(),
                    # Verification agents
                    self.verification_agents.verification_director(),
                    self.verification_agents.fact_checking_specialist(),
                    self.verification_agents.claim_verification_specialist(),
                    self.verification_agents.context_verification_specialist(),
                    self.verification_agents.deception_detection_specialist(),
                    self.verification_agents.logical_fallacy_specialist(),
                    self.verification_agents.steelman_argument_specialist(),
                    self.verification_agents.perspective_synthesis_specialist(),
                    # Intelligence agents
                    self.intelligence_agents.research_specialist(),
                    self.intelligence_agents.intelligence_synthesis_specialist(),
                    self.intelligence_agents.knowledge_management_specialist(),
                    self.intelligence_agents.strategic_intelligence_specialist(),
                    self.intelligence_agents.narrative_tracking_specialist(),
                    self.intelligence_agents.collective_intelligence_specialist(),
                    self.intelligence_agents.memory_management_specialist(),
                    # Observability agents
                    self.observability_agents.system_monitoring_specialist(),
                    self.observability_agents.performance_analytics_specialist(),
                    self.observability_agents.alert_management_specialist(),
                    self.observability_agents.quality_assurance_specialist(),
                    self.observability_agents.resource_optimization_specialist(),
                    self.observability_agents.orchestration_monitoring_specialist(),
                    self.observability_agents.cost_optimization_specialist(),
                ],
                tasks=[
                    self.plan_autonomy_mission(),
                    self.capture_source_media(),
                    self.transcribe_and_index_media(),
                    self.map_transcript_insights(),
                    self.verify_priority_claims(),
                    self.synthesize_intelligence(),
                    self.store_memory_and_context(),
                    self.assess_content_quality(),
                    self.validate_fact_checking_results(),
                    self.monitor_system_performance(),
                    self.optimize_resource_usage(),
                    self.ensure_output_consistency(),
                    self.track_quality_metrics(),
                ],
                process=Process.sequential,
                verbose=True,
                memory=True,
                planning=True,
                cache=True,
                max_rpm=10,
            )
        # Minimal crew for environments without full modules
        return Crew(
            agents=[self.mission_orchestrator()],
            tasks=[self.content_processing_tasks.plan_autonomy_mission()],
            process=Process.sequential,
            verbose=True,
            memory=False,
            planning=False,
            cache=False,
            max_rpm=5,
        )

    def get_crew_info(self) -> dict[str, Any]:
        """Get information about the modular crew structure."""
        return {
            "crew_type": "modular",
            "agent_modules": [
                "acquisition",
                "analysis",
                "verification",
                "intelligence",
                "observability",
            ],
            "task_modules": [
                "content_processing",
                "quality_assurance",
            ],
            "feature_flags": {
                "unified_knowledge": ENABLE_UNIFIED_KNOWLEDGE,
                "unified_router": ENABLE_UNIFIED_ROUTER,
                "unified_cache": ENABLE_UNIFIED_CACHE,
                "alerts": ENABLE_ALERTS,
                "metrics": ENABLE_METRICS,
            },
            "total_agents": 35,  # Approximate count
            "total_tasks": 13,  # Approximate count
        }
