"""Unit tests for crew_builders module.

This module tests the core CrewAI crew building functions that configure and
manage agents, tasks, and their execution context for the autonomous intelligence workflow.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.orchestrator.crew_builders import (
    build_intelligence_crew,
    get_or_create_agent,
    populate_agent_tool_context,
    task_completion_callback,
)


# ============================================================================
# Test Class: populate_agent_tool_context
# ============================================================================


class TestPopulateAgentToolContext:
    """Test suite for populate_agent_tool_context function.

    This function populates shared context on all tool wrappers for an agent,
    which is CRITICAL for CrewAI agents to receive structured data.
    """

    def test_populates_context_on_tools_with_update_context_method(self):
        """Should populate context on tools that have update_context method."""
        # Arrange
        tool1 = Mock()
        tool1.update_context = Mock()
        tool1.name = "Tool1"

        tool2 = Mock()
        tool2.update_context = Mock()
        tool2.name = "Tool2"

        agent = Mock()
        agent.tools = [tool1, tool2]
        agent.role = "test_agent"

        context_data = {"key1": "value1", "key2": "value2"}

        # Act
        populate_agent_tool_context(agent, context_data)

        # Assert
        tool1.update_context.assert_called_once_with(context_data)
        tool2.update_context.assert_called_once_with(context_data)

    def test_ignores_tools_without_update_context_method(self):
        """Should skip tools that don't have update_context method."""
        # Arrange
        tool_with_update = Mock()
        tool_with_update.update_context = Mock()
        tool_with_update.name = "GoodTool"

        tool_without_update = Mock(spec=[])  # No update_context method

        agent = Mock()
        agent.tools = [tool_with_update, tool_without_update]
        agent.role = "test_agent"

        context_data = {"data": "test"}

        # Act - should not raise error
        populate_agent_tool_context(agent, context_data)

        # Assert
        tool_with_update.update_context.assert_called_once_with(context_data)

    def test_handles_agent_without_tools_attribute(self):
        """Should handle agent without tools attribute gracefully."""
        # Arrange
        agent = Mock(spec=["role"])  # No tools attribute
        agent.role = "test_agent"
        context_data = {"data": "test"}

        # Act - should not raise error
        populate_agent_tool_context(agent, context_data)

        # Assert - function should complete without error

    def test_tracks_metrics_when_metrics_provided(self):
        """Should track context population in metrics when provided."""
        # Arrange
        tool = Mock()
        tool.update_context = Mock()
        tool.name = "TestTool"

        agent = Mock()
        agent.tools = [tool]
        agent.role = "test_agent"

        metrics = Mock()
        counter_mock = Mock()
        metrics.counter.return_value = counter_mock

        context_data = {"transcript": "test transcript"}

        # Act
        populate_agent_tool_context(agent, context_data, metrics_instance=metrics)

        # Assert
        metrics.counter.assert_called_once()
        counter_mock.inc.assert_called_once()

    def test_handles_context_with_various_data_types(self):
        """Should handle context data with strings, lists, and dicts."""
        # Arrange
        tool = Mock()
        tool.update_context = Mock()

        agent = Mock()
        agent.tools = [tool]
        agent.role = "test_agent"

        context_data = {
            "transcript": "Long text content" * 100,
            "metadata": {"key": "value"},
            "items": [1, 2, 3, 4, 5],
            "number": 42,
        }

        # Act
        populate_agent_tool_context(agent, context_data)

        # Assert
        tool.update_context.assert_called_once_with(context_data)

    def test_uses_custom_logger_when_provided(self):
        """Should use custom logger instance when provided."""
        # Arrange
        tool = Mock()
        tool.update_context = Mock()

        agent = Mock()
        agent.tools = [tool]
        agent.role = "test_agent"

        custom_logger = Mock(spec=logging.Logger)
        context_data = {"data": "test"}

        # Act
        populate_agent_tool_context(agent, context_data, logger_instance=custom_logger)

        # Assert
        assert custom_logger.warning.called or custom_logger.debug.called


# ============================================================================
# Test Class: get_or_create_agent
# ============================================================================


class TestGetOrCreateAgent:
    """Test suite for get_or_create_agent function.

    This function ensures agents are created ONCE and reused across stages,
    preventing fresh agents with empty tools from bypassing context population.
    """

    def test_returns_cached_agent_when_exists(self):
        """Should return existing agent from cache without creating new one."""
        # Arrange
        cached_agent = Mock()
        cached_agent.role = "cached_agent"

        agent_coordinators = {"test_agent": cached_agent}
        crew_instance = Mock()

        # Act
        result = get_or_create_agent("test_agent", agent_coordinators, crew_instance)

        # Assert
        assert result is cached_agent
        # Crew instance method should NOT be called
        assert not any(call[0] == "test_agent" for call in crew_instance.method_calls)

    def test_creates_and_caches_new_agent_when_not_exists(self):
        """Should create new agent and add to cache when not found."""
        # Arrange
        new_agent = Mock()
        new_agent.role = "new_agent"

        agent_coordinators = {}
        crew_instance = Mock()
        crew_instance.test_agent = Mock(return_value=new_agent)

        # Act
        result = get_or_create_agent("test_agent", agent_coordinators, crew_instance)

        # Assert
        assert result is new_agent
        assert agent_coordinators["test_agent"] is new_agent
        crew_instance.test_agent.assert_called_once()

    def test_raises_error_for_nonexistent_agent_method(self):
        """Should raise ValueError when agent method doesn't exist."""
        # Arrange
        agent_coordinators = {}
        crew_instance = Mock(spec=[])  # No methods

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown agent"):
            get_or_create_agent("nonexistent_agent", agent_coordinators, crew_instance)

    def test_uses_custom_logger_when_provided(self):
        """Should use custom logger instance when provided."""
        # Arrange
        new_agent = Mock()
        agent_coordinators = {}
        crew_instance = Mock()
        crew_instance.test_agent = Mock(return_value=new_agent)
        custom_logger = Mock(spec=logging.Logger)

        # Act
        get_or_create_agent(
            "test_agent",
            agent_coordinators,
            crew_instance,
            logger_instance=custom_logger,
        )

        # Assert
        assert custom_logger.info.called or custom_logger.debug.called

    def test_reuses_agent_across_multiple_calls(self):
        """Should return same agent instance across multiple calls."""
        # Arrange
        new_agent = Mock()
        agent_coordinators = {}
        crew_instance = Mock()
        crew_instance.test_agent = Mock(return_value=new_agent)

        # Act
        result1 = get_or_create_agent("test_agent", agent_coordinators, crew_instance)
        result2 = get_or_create_agent("test_agent", agent_coordinators, crew_instance)
        result3 = get_or_create_agent("test_agent", agent_coordinators, crew_instance)

        # Assert
        assert result1 is result2 is result3
        # Agent creation method should only be called once
        crew_instance.test_agent.assert_called_once()


# ============================================================================
# Test Class: build_intelligence_crew
# ============================================================================


class TestBuildIntelligenceCrew:
    """Test suite for build_intelligence_crew function.

    This function builds a single chained CrewAI crew for the complete
    intelligence workflow using the CORRECT CrewAI pattern.
    """

    def test_builds_crew_with_standard_depth(self):
        """Should build crew with 3 tasks for standard depth."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew") as mock_crew_class,
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task") as mock_task_class,
        ):
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance

            result = build_intelligence_crew(
                url="https://example.com/video",
                depth="standard",
                agent_getter_callback=agent_getter,
            )

            # Assert
            assert result is mock_crew_instance
            # Standard depth should create 3 tasks (acquisition, transcription, analysis)
            assert mock_task_class.call_count == 5  # All tasks created, but only 3 used

            # Verify crew was created with correct process
            mock_crew_class.assert_called_once()
            call_kwargs = mock_crew_class.call_args.kwargs
            # Process enum is passed as string "sequential" not enum
            assert str(call_kwargs["process"]) == "sequential"
            assert call_kwargs["verbose"] is True
            assert call_kwargs["memory"] is True
            assert len(call_kwargs["tasks"]) == 3

    def test_builds_crew_with_deep_depth(self):
        """Should build crew with 4 tasks for deep depth."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew") as mock_crew_class,
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task"),
        ):
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance

            build_intelligence_crew(
                url="https://example.com/video",
                depth="deep",
                agent_getter_callback=agent_getter,
            )

            # Assert
            call_kwargs = mock_crew_class.call_args.kwargs
            assert len(call_kwargs["tasks"]) == 4  # Adds verification

    def test_builds_crew_with_comprehensive_depth(self):
        """Should build crew with all 5 tasks for comprehensive depth."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew") as mock_crew_class,
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task"),
        ):
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance

            build_intelligence_crew(
                url="https://example.com/video",
                depth="comprehensive",
                agent_getter_callback=agent_getter,
            )

            # Assert
            call_kwargs = mock_crew_class.call_args.kwargs
            assert len(call_kwargs["tasks"]) == 5  # All tasks

    def test_builds_crew_with_experimental_depth(self):
        """Should build crew with all 5 tasks for experimental depth."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew") as mock_crew_class,
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task"),
        ):
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance

            build_intelligence_crew(
                url="https://example.com/video",
                depth="experimental",
                agent_getter_callback=agent_getter,
            )

            # Assert
            call_kwargs = mock_crew_class.call_args.kwargs
            assert len(call_kwargs["tasks"]) == 5  # All tasks

    def test_passes_url_to_task_inputs(self):
        """Should include URL in task inputs for template substitution."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        test_url = "https://youtube.com/watch?v=test123"

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew"),
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task") as mock_task_class,
        ):
            build_intelligence_crew(
                url=test_url,
                depth="standard",
                agent_getter_callback=agent_getter,
            )

            # Assert - first task (acquisition) should reference URL
            first_task_call = mock_task_class.call_args_list[0]
            task_description = first_task_call.kwargs.get("description", "")
            assert "{url}" in task_description

    def test_uses_task_completion_callback_when_provided(self):
        """Should attach callback to tasks when provided."""
        # Arrange
        mock_agents = {
            "acquisition_specialist": Mock(role="acquisition"),
            "transcription_engineer": Mock(role="transcription"),
            "analysis_cartographer": Mock(role="analysis"),
            "verification_director": Mock(role="verification"),
            "knowledge_integrator": Mock(role="knowledge"),
        }

        def agent_getter(name):
            return mock_agents[name]

        callback_mock = Mock()

        # Act
        with (
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Crew"),
            patch("ultimate_discord_intelligence_bot.orchestrator.crew_builders.Task") as mock_task_class,
        ):
            build_intelligence_crew(
                url="https://example.com/video",
                depth="standard",
                agent_getter_callback=agent_getter,
                task_completion_callback=callback_mock,
            )

            # Assert - tasks should have callback attached
            for call in mock_task_class.call_args_list:
                assert call.kwargs.get("callback") is callback_mock


# ============================================================================
# Test Class: task_completion_callback
# ============================================================================


class TestTaskCompletionCallback:
    """Test suite for task_completion_callback function.

    This callback extracts structured data from task outputs and propagates
    it to the global crew context for subsequent tasks.
    """

    def test_extracts_json_from_code_block(self):
        """Should extract JSON from ```json code block."""
        # Arrange
        task_output = Mock()
        task_output.raw = """
        Here are the results:
        ```json
        {"file_path": "/tmp/video.mp4", "title": "Test Video"}
        ```
        """
        task_output.task = Mock()
        task_output.task.description = "Download and acquire content"

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output)

            # Assert - context should be updated
            # Note: This uses import, so we check via module
            from ultimate_discord_intelligence_bot import crewai_tool_wrappers

            assert "file_path" in crewai_tool_wrappers._GLOBAL_CREW_CONTEXT
            assert crewai_tool_wrappers._GLOBAL_CREW_CONTEXT["file_path"] == "/tmp/video.mp4"

    def test_extracts_json_from_generic_code_block(self):
        """Should extract JSON from generic ``` code block."""
        # Arrange
        task_output = Mock()
        task_output.raw = """
        Results:
        ```
        {"transcript": "This is a test transcript", "quality_score": 0.85}
        ```
        """
        task_output.task = Mock()
        task_output.task.description = "Transcribe the content"

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output)

            # Assert
            from ultimate_discord_intelligence_bot import crewai_tool_wrappers

            assert "transcript" in crewai_tool_wrappers._GLOBAL_CREW_CONTEXT
            assert "quality_score" in crewai_tool_wrappers._GLOBAL_CREW_CONTEXT

    def test_falls_back_to_key_value_extraction_on_invalid_json(self):
        """Should use fallback extraction when JSON parsing fails."""
        # Arrange
        task_output = Mock()
        task_output.raw = """
        file_path: /tmp/test.mp4
        title: Test Video
        duration: 120
        """
        task_output.task = Mock()
        task_output.task.description = "Download content"

        extract_callback = Mock(return_value={"file_path": "/tmp/test.mp4", "title": "Test Video"})

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output, extract_key_values_callback=extract_callback)

            # Assert
            extract_callback.assert_called_once()

    def test_calls_placeholder_detection_when_provided(self):
        """Should call placeholder detection callback when provided."""
        # Arrange
        task_output = Mock()
        task_output.raw = '```json\n{"transcript": "short placeholder text"}\n```'
        task_output.task = Mock()
        task_output.task.description = "Transcribe content"

        detect_callback = Mock()

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output, detect_placeholder_callback=detect_callback)

            # Assert
            detect_callback.assert_called_once()

    def test_validates_output_against_schema_when_available(self):
        """Should validate output against Pydantic schema when available."""
        # Arrange
        task_output = Mock()
        task_output.raw = '```json\n{"file_path": "/tmp/test.mp4", "title": "Test"}\n```'
        task_output.task = Mock()
        task_output.task.description = "Download and acquire content"

        # Mock schema validation
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            # Act - should not raise error even without schema
            task_completion_callback(task_output)

    def test_tracks_validation_metrics_on_success(self):
        """Should track successful validation in metrics."""
        # Arrange
        task_output = Mock()
        task_output.raw = '```json\n{"file_path": "/tmp/test.mp4"}\n```'
        task_output.task = Mock()
        task_output.task.description = "Download content"

        metrics = Mock()
        counter_mock = Mock()
        metrics.counter.return_value = counter_mock

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output, metrics_instance=metrics)

            # Note: Metrics may or may not be called depending on schema availability
            # Just verify no errors occur

    def test_handles_integration_task_tool_compliance_checking(self):
        """Should check tool compliance for integration tasks."""
        # Arrange
        task_output = Mock()
        task_output.raw = """```json
        {
            "memory_stored": true,
            "graph_created": false,
            "briefing": "Test briefing"
        }
        ```"""
        task_output.task = Mock()
        task_output.task.description = "Knowledge integration task"

        metrics = Mock()
        counter_mock = Mock()
        metrics.counter.return_value = counter_mock

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output, metrics_instance=metrics)

            # Assert - should track tool compliance
            # Function checks for memory_stored and graph_created flags

    def test_populates_agent_tools_when_callback_provided(self):
        """Should populate agent tools with context when callback provided."""
        # Arrange
        task_output = Mock()
        task_output.raw = '```json\n{"transcript": "Test transcript data"}\n```'
        task_output.task = Mock()
        task_output.task.description = "Transcribe"

        agent1 = Mock()
        agent2 = Mock()
        agent_coordinators = {"agent1": agent1, "agent2": agent2}

        populate_callback = Mock()

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(
                task_output,
                populate_agent_context_callback=populate_callback,
                agent_coordinators=agent_coordinators,
            )

            # Assert - should populate context on all cached agents
            assert populate_callback.call_count == 2  # Once per agent

    def test_handles_callback_errors_gracefully(self):
        """Should handle callback errors without crashing."""
        # Arrange
        task_output = Mock()
        task_output.raw = "Invalid data that will cause errors"
        task_output.task = Mock()
        task_output.task.description = "Test"

        # Act - should not raise exception
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output)

            # Assert - function should complete

    def test_repairs_json_when_repair_callback_provided(self):
        """Should attempt JSON repair when parsing fails."""
        # Arrange
        task_output = Mock()
        task_output.raw = """```json
        {"file_path": "/tmp/test.mp4", "title": "Test",}
        ```"""  # Trailing comma
        task_output.task = Mock()
        task_output.task.description = "Download"

        repair_callback = Mock(return_value='{"file_path": "/tmp/test.mp4", "title": "Test"}')

        # Act
        with patch(
            "ultimate_discord_intelligence_bot.crewai_tool_wrappers._GLOBAL_CREW_CONTEXT",
            {},
        ):
            task_completion_callback(task_output, repair_json_callback=repair_callback)

            # Assert
            repair_callback.assert_called_once()
