from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from core.typing_utils import (
    typed,  # typing aid: keep precise signatures after framework decorators
)

try:
    from .agent_training.performance_monitor import AgentPerformanceMonitor

    _PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    _PERFORMANCE_MONITOR_AVAILABLE = False
    AgentPerformanceMonitor = None

try:
    from eval.trajectory_evaluator import EnhancedCrewEvaluator

    _TRAJECTORY_EVALUATOR_AVAILABLE = True
except ImportError:
    _TRAJECTORY_EVALUATOR_AVAILABLE = False
    EnhancedCrewEvaluator = None

from .config_types import AgentConfig, TaskConfig
from .settings import DISCORD_PRIVATE_WEBHOOK
from .tools.advanced_performance_analytics_tool import AdvancedPerformanceAnalyticsTool
from .tools.character_profile_tool import CharacterProfileTool
from .tools.debate_command_tool import DebateCommandTool
from .tools.discord_download_tool import DiscordDownloadTool
from .tools.discord_monitor_tool import DiscordMonitorTool
from .tools.discord_private_alert_tool import DiscordPrivateAlertTool
from .tools.discord_qa_tool import DiscordQATool
from .tools.fact_check_tool import FactCheckTool
from .tools.leaderboard_tool import LeaderboardTool
from .tools.logical_fallacy_tool import LogicalFallacyTool
from .tools.multi_platform_monitor_tool import MultiPlatformMonitorTool
from .tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from .tools.pipeline_tool import PipelineTool
from .tools.social_media_monitor_tool import SocialMediaMonitorTool
from .tools.steelman_argument_tool import SteelmanArgumentTool
from .tools.system_status_tool import SystemStatusTool
from .tools.text_analysis_tool import TextAnalysisTool
from .tools.timeline_tool import TimelineTool
from .tools.transcript_index_tool import TranscriptIndexTool
from .tools.trustworthiness_tracker_tool import TrustworthinessTrackerTool
from .tools.truth_scoring_tool import TruthScoringTool
from .tools.x_monitor_tool import XMonitorTool
from .tools.yt_dlp_download_tool import (
    InstagramDownloadTool,
    KickDownloadTool,
    RedditDownloadTool,
    TikTokDownloadTool,
    TwitchDownloadTool,
    TwitterDownloadTool,
    YouTubeDownloadTool,
)

_CREWAI_AVAILABLE = False
if TYPE_CHECKING:  # Provide real symbols for type checking when installed
    from crewai import Agent, Crew, Process, Task  # noqa: F401
    from crewai.agents.agent_builder.base_agent import BaseAgent  # noqa: F401
    from crewai.project import CrewBase, agent, crew, task  # noqa: F401

    _CREWAI_AVAILABLE = True
else:  # Runtime: attempt import but allow graceful degradation
    try:  # pragma: no cover - import side effects external
        from crewai import Agent, Crew, Process, Task  # type: ignore
        from crewai.agents.agent_builder.base_agent import BaseAgent  # type: ignore
        from crewai.project import CrewBase, agent, crew, task  # type: ignore

        _CREWAI_AVAILABLE = True
    except Exception:  # pragma: no cover - fallback placeholders
        from typing import Any as Agent  # type: ignore
        from typing import Any as Crew  # type: ignore
        from typing import Any as Process  # type: ignore
        from typing import Any as Task  # type: ignore

        class BaseAgent:  # minimal placeholder
            ...

        def CrewBase(cls):  # type: ignore
            return cls

        def agent(func):  # type: ignore
            return func

        def crew(func):  # type: ignore
            return func

        def task(func):  # type: ignore
            return func


RAW_SNIPPET_MAX_LEN = 160  # truncate raw output logging for verbose step mode


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    # Explicit attribute declarations to satisfy static type checking. These
    # are populated by the CrewAI framework decorators at runtime. We provide
    # conservative placeholder types so mypy recognizes them.
    agents_config: dict[str, AgentConfig]  # loaded agent configurations
    tasks_config: dict[str, TaskConfig]  # loaded task configurations
    agents: Sequence[BaseAgent]
    tasks: Sequence[Task]

    @typed  # outermost: preserves signature after crewai decorator
    @agent
    def content_manager(self) -> Agent:
        # Runtime path uses helper; the unreachable Agent() block below is for static AST tests.
        if False:  # pragma: no cover - test extraction aid
            Agent(  # type: ignore
                role="placeholder",
                goal="placeholder",
                backstory="placeholder",
                tools=[
                    PipelineTool(),
                    DebateCommandTool(),
                    TranscriptIndexTool(),
                    TimelineTool(),
                ],
            )
        return self._agent_from_config(
            "content_manager",
            tools=[PipelineTool(), DebateCommandTool(), TranscriptIndexTool(), TimelineTool()],
        )

    @typed
    @agent
    def content_downloader(self) -> Agent:
        if False:  # pragma: no cover - static tool enumeration aid
            Agent(  # type: ignore
                role="placeholder",
                goal="placeholder",
                backstory="placeholder",
                tools=[
                    YouTubeDownloadTool(),
                    TwitchDownloadTool(),
                    KickDownloadTool(),
                    TwitterDownloadTool(),
                    InstagramDownloadTool(),
                    TikTokDownloadTool(),
                    RedditDownloadTool(),
                    DiscordDownloadTool(),
                ],
            )
        return self._agent_from_config(
            "content_downloader",
            tools=[
                YouTubeDownloadTool(),
                TwitchDownloadTool(),
                KickDownloadTool(),
                TwitterDownloadTool(),
                InstagramDownloadTool(),
                TikTokDownloadTool(),
                RedditDownloadTool(),
                DiscordDownloadTool(),
            ],
        )

    @typed
    @agent
    def multi_platform_monitor(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[MultiPlatformMonitorTool()])  # type: ignore
        return self._agent_from_config("multi_platform_monitor", tools=[MultiPlatformMonitorTool()])

    @typed
    @agent
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[DiscordPrivateAlertTool("w"), SystemStatusTool(), AdvancedPerformanceAnalyticsTool()],
            )
        return self._agent_from_config(
            "system_alert_manager",
            tools=[DiscordPrivateAlertTool(webhook), SystemStatusTool(), AdvancedPerformanceAnalyticsTool()],
        )

    @typed
    @agent
    def cross_platform_intelligence_gatherer(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
            )
        return self._agent_from_config(
            "cross_platform_intelligence_gatherer",
            tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
        )

    @typed
    @agent
    def enhanced_fact_checker(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
            )
        return self._agent_from_config(
            "enhanced_fact_checker",
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
        )

    @typed
    @agent
    def truth_scoring_specialist(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
            )
        return self._agent_from_config(
            "truth_scoring_specialist",
            tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
        )

    @typed
    @agent
    def steelman_argument_generator(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[SteelmanArgumentTool()])  # type: ignore
        return self._agent_from_config(
            "steelman_argument_generator",
            tools=[SteelmanArgumentTool()],
        )

    @typed
    @agent
    def discord_qa_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[DiscordQATool()])  # type: ignore
        return self._agent_from_config("discord_qa_manager", tools=[DiscordQATool()])

    @typed
    @agent
    def ethan_defender(self) -> Agent:
        return self._agent_from_config("ethan_defender")

    @typed
    @agent
    def hasan_defender(self) -> Agent:
        return self._agent_from_config("hasan_defender")

    @typed
    @agent
    def character_profile_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[CharacterProfileTool()])  # type: ignore
        return self._agent_from_config(
            "character_profile_manager",
            tools=[CharacterProfileTool()],
        )

    @typed
    @agent
    def personality_synthesis_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
            )
        return self._agent_from_config(
            "personality_synthesis_manager",
            tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
        )

    @typed
    @task
    def execute_multi_platform_downloads(self) -> Task:
        return self._task_from_config("execute_multi_platform_downloads")

    @typed
    @task
    def process_video(self) -> Task:
        return self._task_from_config("process_video")

    @typed
    @task
    def monitor_system(self) -> Task:
        return self._task_from_config("monitor_system")

    @typed
    @task
    def identify_new_content(self) -> Task:
        return self._task_from_config("identify_new_content")

    @typed
    @task
    def gather_cross_platform_intelligence(self) -> Task:
        return self._task_from_config("gather_cross_platform_intelligence")

    @typed
    @task
    def get_context(self) -> Task:
        return self._task_from_config("get_context")

    @typed
    @task
    def fact_check_content(self) -> Task:
        return self._task_from_config("fact_check_content")

    @typed
    @task
    def score_truthfulness(self) -> Task:
        return self._task_from_config("score_truthfulness")

    @typed
    @task
    def steelman_argument(self) -> Task:
        return self._task_from_config("steelman_argument")

    @typed
    @task
    def analyze_claim(self) -> Task:
        return self._task_from_config("analyze_claim")

    @typed
    @task
    def fact_check_claim(self) -> Task:
        return self._task_from_config("fact_check_claim")

    @typed
    @task
    def update_leaderboard(self) -> Task:
        return self._task_from_config("update_leaderboard")

    @typed
    @task
    def answer_question(self) -> Task:
        return self._task_from_config("answer_question")

    @typed
    @task
    def get_timeline(self) -> Task:
        return self._task_from_config("get_timeline")

    @typed
    @task
    def get_profile(self) -> Task:
        return self._task_from_config("get_profile")

    @typed
    @task
    def synthesize_personality(self) -> Task:
        return self._task_from_config("synthesize_personality")

    # Advanced Performance Analytics Tasks
    @typed
    @task
    def run_performance_analytics(self) -> Task:
        return self._task_from_config("run_performance_analytics")

    @typed
    @task
    def monitor_performance_alerts(self) -> Task:
        return self._task_from_config("monitor_performance_alerts")

    @typed
    @task
    def send_performance_executive_summary(self) -> Task:
        return self._task_from_config("send_performance_executive_summary")

    @typed
    @task
    def optimize_system_performance(self) -> Task:
        return self._task_from_config("optimize_system_performance")

    @typed
    @task
    def predictive_performance_analysis(self) -> Task:
        return self._task_from_config("predictive_performance_analysis")

    @crew
    def crew(self) -> Crew:
        """Create the project crew with enhanced features.

        Adds optional runtime validation & dynamic embedder configuration.
        """
        if not _CREWAI_AVAILABLE:
            raise ImportError(
                "crewai is not installed. Install project with extras or run 'pip install crewai' to use crew orchestration features."
            )
        if os.getenv("ENABLE_CREW_CONFIG_VALIDATION") == "1":
            self._validate_configs()

        embedder_provider = os.getenv("CREW_EMBEDDER_PROVIDER", "openai")
        embedder_cfg_raw = os.getenv("CREW_EMBEDDER_CONFIG_JSON")
        embedder: dict[str, Any] = {"provider": embedder_provider}
        if embedder_cfg_raw:
            try:  # pragma: no cover - defensive
                extra = json.loads(embedder_cfg_raw)
                if isinstance(extra, dict):
                    embedder.update(extra)
            except Exception as exc:  # pragma: no cover
                logging.getLogger(__name__).warning("Invalid CREW_EMBEDDER_CONFIG_JSON: %s", exc)

        return Crew(
            agents=list(self.agents),  # satisfy expected concrete list type
            tasks=list(self.tasks),  # satisfy expected concrete list type
            process=Process.sequential,
            verbose=True,
            planning=True,
            memory=True,
            cache=True,
            max_rpm=10,
            embedder=embedder,
            step_callback=self._log_step,
        )

    def kickoff_with_performance_tracking(self, inputs: dict[Any, Any] | None = None) -> Any:
        """Execute crew with comprehensive performance tracking and trajectory evaluation."""
        if not _PERFORMANCE_MONITOR_AVAILABLE:
            # Fallback to standard kickoff if performance monitoring unavailable
            return self.crew().kickoff(inputs=inputs or {})

        crew_start_time = time.time()
        session_id = f"crew_{int(crew_start_time)}"

        # Initialize trajectory evaluator if available
        trajectory_evaluator = None
        if _TRAJECTORY_EVALUATOR_AVAILABLE:
            try:
                trajectory_evaluator = EnhancedCrewEvaluator()
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to initialize trajectory evaluator: {e}")

        try:
            # Initialize performance monitor if not exists
            if not hasattr(self, "_performance_monitor"):
                self._performance_monitor = AgentPerformanceMonitor()

            # Execute the crew
            result = self.crew().kickoff(inputs=inputs or {})

            crew_end_time = time.time()
            total_execution_time = crew_end_time - crew_start_time

            # Assess overall crew performance
            crew_quality = self._assess_crew_result_quality(result)

            # Extract tools used from all agents
            all_tools_used = []
            for agent in self.agents:
                agent_tools = getattr(agent, "tools", [])
                all_tools_used.extend([str(tool.__class__.__name__) for tool in agent_tools])

            # Record crew-level performance
            self._performance_monitor.record_agent_interaction(
                agent_name="crew_orchestrator",
                task_type="crew_execution",
                tools_used=list(set(all_tools_used)),  # Unique tools
                tool_sequence=[
                    {
                        "agent": agent.role if hasattr(agent, "role") else str(agent),
                        "tools": [str(tool.__class__.__name__) for tool in getattr(agent, "tools", [])],
                    }
                    for agent in self.agents
                ],
                response_quality=crew_quality,
                response_time=total_execution_time,
                user_feedback={"crew_execution": True, "agent_count": len(self.agents)},
                error_occurred=False,
                error_details={},
            )

            # Trajectory evaluation if available
            if trajectory_evaluator:
                try:
                    # Create execution log for trajectory evaluation
                    execution_log = {
                        "session_id": session_id,
                        "user_input": str(inputs or {}),
                        "start_time": crew_start_time,
                        "total_duration": total_execution_time,
                        "success": True,
                        "final_output": str(result),
                        "steps": self._extract_execution_steps(all_tools_used),
                    }

                    # Evaluate trajectory
                    evaluation_result = trajectory_evaluator.evaluate_crew_execution(execution_log)

                    if evaluation_result.success:
                        logging.getLogger(__name__).info(
                            f"Trajectory evaluation completed: score={evaluation_result.data.get('trajectory_evaluation', {}).get('score', 'unknown')}"
                        )
                    else:
                        logging.getLogger(__name__).warning(f"Trajectory evaluation failed: {evaluation_result.error}")

                except Exception as e:
                    logging.getLogger(__name__).warning(f"Trajectory evaluation error: {e}")

            return result

        except Exception as e:
            crew_end_time = time.time()

            # Record failed execution
            if hasattr(self, "_performance_monitor"):
                self._performance_monitor.record_agent_interaction(
                    agent_name="crew_orchestrator",
                    task_type="crew_execution",
                    tools_used=[],
                    tool_sequence=[],
                    response_quality=0.0,
                    response_time=crew_end_time - crew_start_time,
                    user_feedback={},
                    error_occurred=True,
                    error_details={"error": str(e), "type": type(e).__name__},
                )

            # Failed trajectory evaluation if available
            if trajectory_evaluator:
                try:
                    execution_log = {
                        "session_id": session_id,
                        "user_input": str(inputs or {}),
                        "start_time": crew_start_time,
                        "total_duration": crew_end_time - crew_start_time,
                        "success": False,
                        "final_output": f"Error: {str(e)}",
                        "steps": [],
                    }
                    trajectory_evaluator.evaluate_crew_execution(execution_log)
                except Exception:
                    pass  # Don't let trajectory evaluation errors affect main flow

            raise  # Re-raise the original exception

    def _extract_execution_steps(self, tools_used: list[str]) -> list[dict[str, Any]]:
        """Extract execution steps for trajectory evaluation."""
        steps = []
        for i, tool in enumerate(tools_used):
            steps.append(
                {
                    "timestamp": time.time(),
                    "agent_role": f"agent_{i % len(self.agents)}",
                    "action_type": "tool_call",
                    "content": f"Used tool: {tool}",
                    "tool_name": tool,
                    "tool_args": {},
                    "success": True,
                    "error": None,
                }
            )
        return steps

    def _assess_crew_result_quality(self, result: Any) -> float:
        """Assess the quality of crew execution result."""
        try:
            result_str = str(result)

            # Basic quality assessment
            quality_score = 0.5  # Base score

            # Length and substance
            if len(result_str) > 100:
                quality_score += 0.2

            # Quality indicators
            quality_indicators = [
                "analysis",
                "evidence",
                "conclusion",
                "recommendation",
                "verified",
                "confirmed",
                "research",
                "assessment",
            ]

            indicator_count = sum(1 for indicator in quality_indicators if indicator.lower() in result_str.lower())
            quality_score += min(0.3, indicator_count * 0.1)

            return min(1.0, quality_score)

        except Exception:
            return 0.5  # Default if assessment fails

    @runtime_checkable
    class _StepLike(Protocol):  # protocol to narrow what we access
        agent: Any  # crewai runtime object with a 'role' attribute
        tool: Any | None

    def _log_step(self, step: object) -> None:
        """Log each agent step for observability.

        Accepts a generic object to avoid tight coupling to crewai internals;
        uses duck typing so type checking stays permissive without ``Any``
        leaking into callers.
        """
        if isinstance(step, self._StepLike):
            role = getattr(step.agent, "role", "unknown")
            tool = getattr(step, "tool", None)
            if tool is not None:
                print(f"🤖 Agent {role} using {tool}")
            else:
                print(f"🤖 Agent {role} thinking...")
            if os.getenv("ENABLE_CREW_STEP_VERBOSE") == "1":
                raw = getattr(step, "raw", None) or getattr(getattr(step, "output", None), "raw", None)
                if isinstance(raw, str):
                    snippet = raw.strip().replace("\n", " ")
                    if len(snippet) > RAW_SNIPPET_MAX_LEN:
                        snippet = snippet[: RAW_SNIPPET_MAX_LEN - 3] + "..."
                    print(f"   ↳ raw: {snippet}")

            # Performance tracking integration
            self._track_agent_step_performance(step)

    def _track_agent_step_performance(self, step: object) -> None:
        """Track individual agent step performance for learning."""
        if not _PERFORMANCE_MONITOR_AVAILABLE:
            return

        try:
            # Get or create performance monitor instance
            if not hasattr(self, "_performance_monitor"):
                self._performance_monitor = AgentPerformanceMonitor()

            if isinstance(step, self._StepLike):
                agent_role = getattr(step.agent, "role", "unknown")
                tool_used = getattr(step, "tool", None)
                step_start_time = getattr(step, "start_time", time.time())
                step_end_time = time.time()

                # Extract step output for quality assessment
                raw_output = getattr(step, "raw", None) or getattr(getattr(step, "output", None), "raw", None)

                # Simple quality assessment for this step
                step_quality = 0.7  # Default baseline
                if raw_output and isinstance(raw_output, str):
                    # Basic quality indicators
                    if len(raw_output) > 50:  # Substantial output
                        step_quality += 0.1
                    if any(word in raw_output.lower() for word in ["analysis", "evidence", "because", "therefore"]):
                        step_quality += 0.1
                    if tool_used:  # Tool usage indicates action
                        step_quality += 0.1

                step_quality = min(1.0, step_quality)

                # Record this step as a micro-interaction
                tools_used = [str(tool_used)] if tool_used else []
                tool_sequence = [
                    {
                        "tool": str(tool_used) if tool_used else "reasoning",
                        "action": "step_execution",
                        "timestamp": step_end_time,
                    }
                ]

                # Use a shortened agent name for tracking
                agent_name = agent_role.replace(" ", "_").lower()

                self._performance_monitor.record_agent_interaction(
                    agent_name=agent_name,
                    task_type="crew_step",
                    tools_used=tools_used,
                    tool_sequence=tool_sequence,
                    response_quality=step_quality,
                    response_time=step_end_time - step_start_time,
                    user_feedback={"step_type": "crew_execution"},
                    error_occurred=False,
                    error_details={},
                )

        except Exception as e:
            # Don't let performance tracking break the main workflow
            logging.getLogger(__name__).debug(f"Performance tracking error: {e}")

    # -------------------------------
    # Validation helpers
    # -------------------------------
    def _validate_configs(self) -> None:
        """Validate agent & task configuration structure.

        Raises ValueError on *critical* schema mismatches; prints warnings for
        soft issues to avoid over-strict failures in production.
        """
        required_agent_fields = {
            "role",
            "goal",
            "backstory",
            "allow_delegation",
            "verbose",
            "reasoning",
            "inject_date",
            "date_format",
        }
        for name, cfg in self.agents_config.items():
            missing = required_agent_fields - set(cfg.keys())
            if missing:
                raise ValueError(f"Agent '{name}' missing required fields: {sorted(missing)}")
            # Type sanity checks (best-effort)
            if not isinstance(cfg.get("allow_delegation"), bool):
                raise ValueError(f"Agent '{name}' allow_delegation must be bool")
            if not isinstance(cfg.get("verbose"), bool):
                raise ValueError(f"Agent '{name}' verbose must be bool")
            if not isinstance(cfg.get("reasoning"), bool):
                raise ValueError(f"Agent '{name}' reasoning must be bool")
            if not isinstance(cfg.get("inject_date"), bool):
                raise ValueError(f"Agent '{name}' inject_date must be bool")
            if not isinstance(cfg.get("date_format"), str):
                raise ValueError(f"Agent '{name}' date_format must be str")

        for t_name, t_cfg in self.tasks_config.items():
            for required in ("agent", "description", "expected_output"):
                if required not in t_cfg:
                    raise ValueError(f"Task '{t_name}' missing required field '{required}'")
            # Narrow for type checker
            assert "agent" in t_cfg and "description" in t_cfg and "expected_output" in t_cfg
            agent_ref = t_cfg["agent"]
            if agent_ref not in self.agents_config:
                raise ValueError(f"Task '{t_name}' references unknown agent '{agent_ref}'")
            if "output_file" in t_cfg:
                out_path = Path(t_cfg["output_file"]).expanduser()
                try:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    print(f"Warning: could not create output directory for task '{t_name}' -> {out_path.parent}")

    # -------------------------------
    # Internal construction helpers (typed)
    # -------------------------------
    def _agent_from_config(self, name: str, tools: list[Any] | None = None) -> Agent:
        """Instantiate an Agent from validated config.

        We expand the config explicitly so mypy sees required parameters instead
        of a single opaque ``config=`` argument (which the runtime library
        accepts but its stubs do not model). Unknown forward-compatible keys are
        ignored to keep strict type checking noise low.
        """
        cfg = self.agents_config[name]
        # Narrow required fields for mypy (AgentConfig has them as optional total=False)
        assert "role" in cfg and "goal" in cfg and "backstory" in cfg, f"Agent config '{name}' missing required keys"
        base: dict[str, Any] = {
            "role": cfg["role"],
            "goal": cfg["goal"],
            "backstory": cfg["backstory"],
        }
        # Whitelist optional keys supported by current runtime (avoid spraying **cfg)
        # Manually copy optional known fields (keeps mypy happy about literal keys)
        if "allow_delegation" in cfg:
            base["allow_delegation"] = cfg["allow_delegation"]
        if "verbose" in cfg:
            base["verbose"] = cfg["verbose"]
        if "reasoning" in cfg:
            base["reasoning"] = cfg["reasoning"]
        if "inject_date" in cfg:
            base["inject_date"] = cfg["inject_date"]
        if "date_format" in cfg:
            base["date_format"] = cfg["date_format"]
        if "memory" in cfg:
            base["memory"] = cfg["memory"]
        if "max_reasoning_attempts" in cfg:
            base["max_reasoning_attempts"] = cfg["max_reasoning_attempts"]
        if "respect_context_window" in cfg:
            base["respect_context_window"] = cfg["respect_context_window"]
        if "max_rpm" in cfg:
            base["max_rpm"] = cfg["max_rpm"]
        if tools:
            base["tools"] = tools
        return Agent(**base)

    def _task_from_config(self, name: str) -> Task:
        cfg = self.tasks_config[name]
        assert (
            "description" in cfg and "expected_output" in cfg and "agent" in cfg
        ), f"Task config '{name}' missing required keys"
        base: dict[str, Any] = {
            "description": cfg["description"],
            "expected_output": cfg["expected_output"],
            "agent": cfg["agent"],
        }
        if "human_input" in cfg:
            base["human_input"] = cfg["human_input"]
        if "output_file" in cfg:
            base["output_file"] = cfg["output_file"]
        if "async_execution" in cfg:
            base["async_execution"] = cfg["async_execution"]
        if "context" in cfg:
            base["context"] = cfg["context"]
        return Task(**base)
