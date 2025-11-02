"""Crew executor for modular crew organization."""

from __future__ import annotations
import json
import os
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from ultimate_discord_intelligence_bot.settings import get_settings

if TYPE_CHECKING:
    from crewai import Crew


class CrewExecutor:
    """Executor for managing crew execution with modular organization."""

    def __init__(self, agent_registry, task_registry, tool_registry):
        self.agent_registry = agent_registry
        self.task_registry = task_registry
        self.tool_registry = tool_registry
        self.settings = get_settings()

    def create_crew(self) -> Crew:
        """Create and configure the crew."""
        from crewai import Crew, Process

        embedder_config = {"provider": os.getenv("CREW_EMBEDDER_PROVIDER", "openai")}
        embedder_json = os.getenv("CREW_EMBEDDER_CONFIG_JSON")
        if embedder_json:
            try:
                additional_config = json.loads(embedder_json)
                embedder_config.update(additional_config)
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in CREW_EMBEDDER_CONFIG_JSON: {embedder_json}")
        if os.getenv("ENABLE_CREW_CONFIG_VALIDATION", "0").lower() in {"1", "true", "yes"}:
            required_fields = {"date_format"}
            missing = {
                name: sorted(required_fields - set((cfg or {}).keys()))
                for name, cfg in (getattr(self, "agents_config", {}) or {}).items()
                if not required_fields.issubset((cfg or {}).keys())
            }
            if missing:
                raise ValueError(f"missing required fields: {missing}")
        crew = Crew(
            agents=[
                self.agent_registry.mission_orchestrator(),
                self.agent_registry.executive_supervisor(),
                self.agent_registry.workflow_manager(),
                self.agent_registry.acquisition_specialist(),
                self.agent_registry.transcription_engineer(),
                self.agent_registry.analysis_cartographer(),
                self.agent_registry.verification_director(),
                self.agent_registry.risk_intelligence_analyst(),
                self.agent_registry.persona_archivist(),
                self.agent_registry.knowledge_integrator(),
                self.agent_registry.signal_recon_specialist(),
                self.agent_registry.trend_intelligence_scout(),
                self.agent_registry.research_synthesist(),
                self.agent_registry.intelligence_briefing_curator(),
                self.agent_registry.argument_strategist(),
                self.agent_registry.system_reliability_officer(),
                self.agent_registry.community_liaison(),
                self.agent_registry.autonomous_mission_coordinator(),
                self.agent_registry.multi_platform_acquisition_specialist(),
                self.agent_registry.advanced_transcription_engineer(),
                self.agent_registry.comprehensive_linguistic_analyst(),
                self.agent_registry.information_verification_director(),
                self.agent_registry.threat_intelligence_analyst(),
                self.agent_registry.behavioral_profiling_specialist(),
                self.agent_registry.knowledge_integration_architect(),
                self.agent_registry.social_intelligence_coordinator(),
                self.agent_registry.trend_analysis_scout(),
                self.agent_registry.research_synthesis_specialist(),
                self.agent_registry.intelligence_briefing_director(),
                self.agent_registry.strategic_argument_analyst(),
                self.agent_registry.system_operations_manager(),
                self.agent_registry.community_engagement_coordinator(),
                self.agent_registry.personality_synthesis_manager(),
                self.agent_registry.visual_intelligence_specialist(),
                self.agent_registry.audio_intelligence_specialist(),
                self.agent_registry.trend_intelligence_specialist(),
                self.agent_registry.content_generation_specialist(),
                self.agent_registry.cross_platform_intelligence_specialist(),
            ],
            tasks=[
                self.task_registry.plan_autonomy_mission(),
                self.task_registry.capture_source_media(),
                self.task_registry.transcribe_and_index_media(),
                self.task_registry.map_transcript_insights(),
                self.task_registry.verify_priority_claims(),
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
            max_rpm=10,
            embedder=embedder_config,
        )
        return crew

    def execute_crew(self, inputs: dict[str, Any]) -> Any:
        """Execute the crew with given inputs."""
        crew = self.create_crew()
        return crew.kickoff(inputs=inputs)

    def run_langgraph_if_enabled(self, url: str, quality: str = "1080p") -> dict:
        """Optional LangGraph execution path controlled by feature flag."""
        if not getattr(self.settings, "ENABLE_LANGGRAPH_PIPELINE", False):
            return {}
        try:
            from ultimate_discord_intelligence_bot import langgraph_pipeline as _lg

            app = _lg.compile_mission_graph()
            config = {"configurable": {"thread_id": f"mission_{int(time.time())}"}}
            inputs = {"request_url": url, "quality": quality}
            last_event = None
            try:
                for ev in app.stream(inputs, config=config):
                    last_event = ev
            except Exception:
                return {}
            return {"langgraph": True, "last_event": str(last_event) if last_event else None}
        except Exception:
            return {}

    def get_crew_info(self) -> dict[str, Any]:
        """Get information about the crew configuration."""
        return {
            "agent_count": len(self.agent_registry.__dict__),
            "task_count": len(self.task_registry.__dict__),
            "tool_count": self.tool_registry.get_tool_count(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
