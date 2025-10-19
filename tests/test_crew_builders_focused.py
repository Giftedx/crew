"""Unit tests for focused crew builders module."""

from unittest.mock import Mock, patch

from crewai import Task

from src.ultimate_discord_intelligence_bot.orchestrator import crew_builders_focused


class TestCrewBuildersFocused:
    """Test suite for focused crew building functions."""

    def test_create_acquisition_task(self):
        """Test acquisition task creation."""
        # Arrange
        agent = Mock()
        callback = Mock()

        # Act
        task = crew_builders_focused.create_acquisition_task(agent, callback)

        # Assert
        assert isinstance(task, Task)
        assert task.agent == agent
        assert task.callback == callback
        assert "Download and acquire media content" in task.description
        assert "JSON with url, video_id, file_path" in task.expected_output

    def test_create_transcription_task(self):
        """Test transcription task creation."""
        # Arrange
        agent = Mock()
        acquisition_task = Mock()
        callback = Mock()

        # Act
        task = crew_builders_focused.create_transcription_task(agent, acquisition_task, callback)

        # Assert
        assert isinstance(task, Task)
        assert task.agent == agent
        assert task.callback == callback
        assert task.context == [acquisition_task]
        assert "AudioTranscriptionTool" in task.description
        assert "transcript" in task.expected_output

    def test_create_analysis_tasks_parallel(self):
        """Test parallel analysis tasks creation."""
        # Arrange
        agents = {"analysis_cartographer": Mock(), "verification_director": Mock()}
        transcription_task = Mock()
        depth = "deep"
        callback = Mock()

        # Act
        tasks = crew_builders_focused.create_analysis_tasks(
            agents, transcription_task, depth, enable_parallel=True, callback=callback
        )

        # Assert
        assert len(tasks) == 3  # text_analysis, fact_checking, bias_analysis
        assert all(isinstance(task, Task) for task in tasks)
        assert all(task.callback == callback for task in tasks)
        assert all(task.context == [transcription_task] for task in tasks)

    def test_create_analysis_tasks_sequential(self):
        """Test sequential analysis tasks creation."""
        # Arrange
        agents = {"analysis_cartographer": Mock(), "verification_director": Mock()}
        transcription_task = Mock()
        depth = "standard"
        callback = Mock()

        # Act
        tasks = crew_builders_focused.create_analysis_tasks(
            agents, transcription_task, depth, enable_parallel=False, callback=callback
        )

        # Assert
        assert len(tasks) == 1  # single comprehensive analysis task
        assert isinstance(tasks[0], Task)
        assert tasks[0].callback == callback
        assert tasks[0].context == [transcription_task]

    def test_create_knowledge_integration_task(self):
        """Test knowledge integration task creation."""
        # Arrange
        agent = Mock()
        previous_tasks = [Mock(), Mock()]
        depth = "comprehensive"
        callback = Mock()

        # Act
        task = crew_builders_focused.create_knowledge_integration_task(agent, previous_tasks, depth, callback)

        # Assert
        assert isinstance(task, Task)
        assert task.agent == agent
        assert task.callback == callback
        assert task.context == previous_tasks
        assert "synthesis" in task.description.lower()
        assert "integration" in task.description.lower()

    def test_build_crew_with_tasks_sequential(self):
        """Test crew building with sequential process."""
        # Arrange
        tasks = [Mock(), Mock()]
        process_type = "sequential"  # Use string instead of Process.sequential

        # Act
        crew = crew_builders_focused.build_crew_with_tasks(tasks, process_type)

        # Assert
        assert crew.tasks == tasks
        assert crew.process == "sequential"

    def test_build_crew_with_tasks_hierarchical(self):
        """Test crew building with hierarchical process."""
        # Arrange
        tasks = [Mock(), Mock()]
        process_type = "hierarchical"  # Use string instead of Process.hierarchical

        # Act
        crew = crew_builders_focused.build_crew_with_tasks(tasks, process_type)

        # Assert
        assert crew.tasks == tasks
        assert crew.process == "hierarchical"

    @patch("src.ultimate_discord_intelligence_bot.orchestrator.crew_builders_focused.get_settings")
    def test_build_crew_with_tasks_default_process(self, mock_get_settings):
        """Test crew building with default process."""
        # Arrange
        tasks = [Mock()]

        # Mock settings to avoid attribute errors
        settings = Mock()
        settings.enable_graph_memory = True
        settings.enable_crew_planning = True
        settings.enable_crew_cache = True
        settings.crew_max_rpm = 10
        settings.crew_max_execution_time = 300
        settings.crew_verbose = True
        mock_get_settings.return_value = settings

        # Act
        crew = crew_builders_focused.build_crew_with_tasks(tasks)

        # Assert
        assert crew.tasks == tasks
        assert crew.process == "sequential"  # default

    def test_create_analysis_tasks_with_logger(self):
        """Test analysis tasks creation with custom logger."""
        # Arrange
        agents = {"analysis_cartographer": Mock(), "verification_director": Mock()}
        transcription_task = Mock()
        depth = "standard"
        callback = Mock()
        custom_logger = Mock()

        # Act
        tasks = crew_builders_focused.create_analysis_tasks(
            agents, transcription_task, depth, enable_parallel=True, callback=callback, logger_instance=custom_logger
        )

        # Assert
        assert len(tasks) == 3
        custom_logger.info.assert_called()

    def test_create_analysis_tasks_depth_in_description(self):
        """Test that depth level is included in task descriptions."""
        # Arrange
        agents = {"analysis_cartographer": Mock()}
        transcription_task = Mock()
        depth = "experimental"
        callback = Mock()

        # Act
        tasks = crew_builders_focused.create_analysis_tasks(
            agents, transcription_task, depth, enable_parallel=False, callback=callback
        )

        # Assert
        assert len(tasks) == 1
        assert depth in tasks[0].description

    def test_create_knowledge_integration_task_depth_in_description(self):
        """Test that depth level is included in knowledge integration task."""
        # Arrange
        agent = Mock()
        previous_tasks = [Mock()]
        depth = "deep"
        callback = Mock()

        # Act
        task = crew_builders_focused.create_knowledge_integration_task(agent, previous_tasks, depth, callback)

        # Assert
        assert depth in task.description

    def test_create_transcription_task_expected_output(self):
        """Test transcription task expected output format."""
        # Arrange
        agent = Mock()
        acquisition_task = Mock()
        callback = Mock()

        # Act
        task = crew_builders_focused.create_transcription_task(agent, acquisition_task, callback)

        # Assert
        assert "REJECT" in task.expected_output
        assert "ACCEPT" in task.expected_output
        assert "transcript_length" in task.expected_output

    def test_create_acquisition_task_json_format(self):
        """Test acquisition task JSON format requirements."""
        # Arrange
        agent = Mock()
        callback = Mock()

        # Act
        task = crew_builders_focused.create_acquisition_task(agent, callback)

        # Assert
        assert "JSON" in task.description
        assert "url, video_id, file_path" in task.description
        assert "```json```" in task.description
