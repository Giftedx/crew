"""Compatibility adapter for legacy crew.py API.

This module provides backward compatibility for code using the old
UltimateDiscordIntelligenceBotCrew class by wrapping the new crew_core
async executor with a synchronous, decorator-based interface.

Migration Path:
    1. Code imports UltimateDiscordIntelligenceBotCrewAdapter from here
    2. Adapter provides same API as old crew.py
    3. Internally delegates to UnifiedCrewExecutor
    4. Later, code can migrate to direct crew_core usage

Example:
    # Old code (still works):
    from ultimate_discord_intelligence_bot.crew_core.compat import (
        UltimateDiscordIntelligenceBotCrewAdapter as UltimateDiscordIntelligenceBotCrew
    )

    crew = UltimateDiscordIntelligenceBotCrew()
    crew_instance = crew.crew()
    result = crew_instance.kickoff(inputs={"url": "..."})

    # New code (direct):
    from ultimate_discord_intelligence_bot.crew_core import (
        UnifiedCrewExecutor, CrewConfig, CrewTask
    )

    config = CrewConfig(tenant_id="default")
    task = CrewTask(task_id="...", ...)
    executor = UnifiedCrewExecutor(config)
    result = await executor.execute(task, config)
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any
import structlog
from domains.orchestration.crew.executor import UnifiedCrewExecutor
from domains.orchestration.crew.interfaces import CrewConfig, CrewExecutionMode, CrewTask
if TYPE_CHECKING:
    from crewai import Agent, Task
logger = structlog.get_logger(__name__)

class CrewAdapter:
    """Adapter that makes UnifiedCrewExecutor behave like CrewAI Crew.

    This provides a .kickoff() method that matches the CrewAI Crew interface
    while internally using the async UnifiedCrewExecutor.
    """

    def __init__(self, executor: UnifiedCrewExecutor, config: CrewConfig, agents: list[Agent], tasks: list[Task]):
        """Initialize crew adapter.

        Args:
            executor: The underlying crew executor
            config: Execution configuration
            agents: List of agent definitions
            tasks: List of task definitions
        """
        self.executor = executor
        self.config = config
        self.agents = agents
        self.tasks = tasks
        self._logger = logging.getLogger(__name__)

    def kickoff(self, inputs: dict[str, Any] | None=None) -> Any:
        """Execute crew with sync interface (matches CrewAI Crew.kickoff()).

        This wraps the async executor.execute() in asyncio.run() to provide
        synchronous execution matching the old crew.py pattern.

        Args:
            inputs: Input parameters for the crew execution

        Returns:
            Crew execution output (extracted from StepResult)
        """
        inputs = inputs or {}
        task = CrewTask(task_id=inputs.get('task_id', 'crew_execution'), task_type=inputs.get('task_type', 'autonomous_intelligence'), description=inputs.get('description', 'Execute crew workflow'), inputs=inputs, agent_requirements=[agent.role for agent in self.agents])
        try:
            result = asyncio.run(self.executor.execute(task, self.config))
            if result.step_result.success:
                return self._extract_crew_output(result)
            else:
                error_msg = result.step_result.error or 'Unknown error'
                self._logger.error(f'Crew execution failed: {error_msg}')
                return {'error': error_msg, 'success': False}
        except Exception as e:
            self._logger.exception('Crew execution exception')
            return {'error': str(e), 'success': False}

    def _extract_crew_output(self, result: Any) -> Any:
        """Extract crew output from CrewExecutionResult.

        Args:
            result: CrewExecutionResult from executor

        Returns:
            Output in format expected by legacy callers
        """
        if hasattr(result, 'step_result') and hasattr(result.step_result, 'data'):
            data = result.step_result.data
            if isinstance(data, dict) and 'result' in data:
                return data['result']
            return data
        return result

class UltimateDiscordIntelligenceBotCrewAdapter:
    """Compatibility adapter providing old crew.py API using new crew_core.

    This class mimics the interface of the old UltimateDiscordIntelligenceBotCrew
    while internally delegating to the new UnifiedCrewExecutor system.

    Usage:
        # Drop-in replacement for old crew.py:
        from ultimate_discord_intelligence_bot.crew_core.compat import (
            UltimateDiscordIntelligenceBotCrewAdapter as UltimateDiscordIntelligenceBotCrew
        )

        crew = UltimateDiscordIntelligenceBotCrew()
        crew_obj = crew.crew()
        result = crew_obj.kickoff(inputs={...})
    """

    def __init__(self):
        """Initialize the crew adapter with default configuration."""
        self.config = CrewConfig(tenant_id=os.getenv('TENANT_ID', 'default'), enable_cache=True, enable_telemetry=True, timeout_seconds=int(os.getenv('CREW_TIMEOUT_SECONDS', '300')), max_retries=int(os.getenv('CREW_MAX_RETRIES', '3')), quality_threshold=float(os.getenv('CREW_QUALITY_THRESHOLD', '0.7')), execution_mode=CrewExecutionMode.SEQUENTIAL, enable_early_exit=True, enable_fallback=True)
        self.executor = UnifiedCrewExecutor(self.config)
        self._agents: list[Agent] = []
        self._tasks: list[Task] = []
        logger.info('crew_adapter_initialized', tenant_id=self.config.tenant_id, execution_mode=self.config.execution_mode.value)

    def setup_discord_integration(self, bot_token: str | None=None, artifact_channel_id: int | None=None) -> None:
        """Set up Discord integration (legacy method - now a no-op).

        This method exists for compatibility but doesn't do anything in the
        new architecture. Discord integration is handled separately.

        Args:
            bot_token: Discord bot token (ignored)
            artifact_channel_id: Channel ID for artifacts (ignored)
        """
        logger.warning('setup_discord_integration_deprecated', message='This method is deprecated and has no effect. Discord integration is handled separately in the new architecture.')

    def run_langgraph_if_enabled(self, inputs: dict[str, Any]) -> Any:
        """Run LangGraph workflow if enabled (legacy method - not implemented).

        This method exists for compatibility but is not implemented in the adapter.
        LangGraph integration should be handled separately.

        Args:
            inputs: Workflow inputs

        Returns:
            None (not implemented)
        """
        logger.warning('run_langgraph_deprecated', message='LangGraph integration should be handled separately, not through crew adapter.')
        return None

    def mission_orchestrator(self) -> Agent:
        """Create mission orchestrator agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Mission Orchestrator', goal='Coordinate autonomous intelligence missions', backstory='Strategic coordinator for complex intelligence operations', verbose=True, allow_delegation=True)

    def acquisition_specialist(self) -> Agent:
        """Create acquisition specialist agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Acquisition Specialist', goal='Acquire and download media content from various sources', backstory='Expert in multi-platform content acquisition', verbose=True, allow_delegation=False)

    def transcription_engineer(self) -> Agent:
        """Create transcription engineer agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Transcription Engineer', goal='Transcribe and process audio/video content', backstory='Specialist in speech-to-text and content indexing', verbose=True, allow_delegation=False)

    def analysis_cartographer(self) -> Agent:
        """Create analysis cartographer agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Analysis Cartographer', goal='Map insights and patterns from transcribed content', backstory='Expert in content analysis and insight extraction', verbose=True, allow_delegation=False)

    def verification_director(self) -> Agent:
        """Create verification director agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Verification Director', goal='Verify claims and assess priority', backstory='Specialist in fact-checking and priority assessment', verbose=True, allow_delegation=False)

    def knowledge_integrator(self) -> Agent:
        """Create knowledge integrator agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Knowledge Integrator', goal='Integrate findings into knowledge base', backstory='Expert in knowledge management and integration', verbose=True, allow_delegation=False)

    def system_reliability_officer(self) -> Agent:
        """Create system reliability officer agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='System Reliability Officer', goal='Monitor and maintain system reliability', backstory='Specialist in system health and reliability engineering', verbose=True, allow_delegation=False)

    def community_liaison(self) -> Agent:
        """Create community liaison agent."""
        try:
            from crewai import Agent
        except ImportError:
            logger.error('CrewAI not installed - cannot create agent')
            raise
        return Agent(role='Community Liaison', goal='Communicate findings to community', backstory='Expert in community engagement and communication', verbose=True, allow_delegation=False)

    def plan_autonomy_mission(self) -> Task:
        """Create mission planning task."""
        try:
            from crewai import Task
        except ImportError:
            logger.error('CrewAI not installed - cannot create task')
            raise
        return Task(description='Plan and coordinate autonomous intelligence mission', expected_output='Mission plan with objectives and coordination strategy', agent=self.mission_orchestrator)

    def capture_source_media(self) -> Task:
        """Create media capture task."""
        try:
            from crewai import Task
        except ImportError:
            logger.error('CrewAI not installed - cannot create task')
            raise
        return Task(description='Acquire and download source media content', expected_output='Downloaded media files with metadata', agent=self.acquisition_specialist)

    def transcribe_and_index_media(self) -> Task:
        """Create transcription task."""
        try:
            from crewai import Task
        except ImportError:
            logger.error('CrewAI not installed - cannot create task')
            raise
        return Task(description='Transcribe audio/video and index content', expected_output='Transcribed text with timestamps and index', agent=self.transcription_engineer)

    def map_transcript_insights(self) -> Task:
        """Create insight mapping task."""
        try:
            from crewai import Task
        except ImportError:
            logger.error('CrewAI not installed - cannot create task')
            raise
        return Task(description='Analyze transcript and extract insights', expected_output='Structured insights and patterns from content', agent=self.analysis_cartographer)

    def verify_priority_claims(self) -> Task:
        """Create verification task."""
        try:
            from crewai import Task
        except ImportError:
            logger.error('CrewAI not installed - cannot create task')
            raise
        return Task(description='Verify claims and assess priority', expected_output='Verified claims with priority ratings', agent=self.verification_director)

    def crew(self) -> CrewAdapter:
        """Return configured crew (adapter that mimics CrewAI Crew).

        This method builds the agent and task lists, then returns a
        CrewAdapter that provides the .kickoff() interface.

        Returns:
            CrewAdapter with .kickoff() method
        """
        if not self._agents:
            self._agents = [self.mission_orchestrator(), self.acquisition_specialist(), self.transcription_engineer(), self.analysis_cartographer(), self.verification_director(), self.knowledge_integrator(), self.system_reliability_officer(), self.community_liaison()]
        if not self._tasks:
            self._tasks = [self.plan_autonomy_mission(), self.capture_source_media(), self.transcribe_and_index_media(), self.map_transcript_insights(), self.verify_priority_claims()]
        return CrewAdapter(executor=self.executor, config=self.config, agents=self._agents, tasks=self._tasks)
UltimateDiscordIntelligenceBotCrew = UltimateDiscordIntelligenceBotCrewAdapter
__all__ = ['CrewAdapter', 'UltimateDiscordIntelligenceBotCrew', 'UltimateDiscordIntelligenceBotCrewAdapter']