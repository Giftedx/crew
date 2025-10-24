"""Tests for parallel execution engine module."""

from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.orchestrator.parallel_execution_engine import (
    ParallelExecutionEngine,
    TaskDependencyGraph,
    create_enhanced_parallel_analysis_tasks,
    optimize_crew_for_parallel_execution,
)


class TestTaskDependencyGraph:
    """Test cases for TaskDependencyGraph class."""

    def test_build_dependency_graph_no_dependencies(self):
        """Test building dependency graph with no dependencies."""
        # Create mock tasks without dependencies
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        tasks = [task1, task2]
        graph = TaskDependencyGraph(tasks)

        assert len(graph.dependencies) == 2
        assert len(graph.dependents) == 2
        for task_id in graph.dependencies:
            assert len(graph.dependencies[task_id]) == 0
            assert len(graph.dependents[task_id]) == 0

    def test_build_dependency_graph_with_dependencies(self):
        """Test building dependency graph with dependencies."""
        # Create mock tasks with dependencies
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]
        graph = TaskDependencyGraph(tasks)

        task1_id = graph._get_task_id(task1)
        task2_id = graph._get_task_id(task2)

        assert task1_id in graph.dependencies[task2_id]
        assert task2_id in graph.dependents[task1_id]
        assert len(graph.dependencies[task1_id]) == 0
        assert len(graph.dependents[task2_id]) == 0

    def test_get_execution_levels_simple_dependencies(self):
        """Test getting execution levels for simple dependencies."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]
        graph = TaskDependencyGraph(tasks)
        levels = graph.get_execution_levels()

        assert len(levels) == 2
        assert len(levels[0]) == 1  # task1 can run first
        assert len(levels[1]) == 1  # task2 can run after task1

    def test_get_execution_levels_parallel_tasks(self):
        """Test getting execution levels for parallel tasks."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        task3 = Mock()
        task3.agent.role = "agent3"
        task3.description = "task3"
        task3.context = [task1, task2]

        tasks = [task1, task2, task3]
        graph = TaskDependencyGraph(tasks)
        levels = graph.get_execution_levels()

        assert len(levels) == 2
        assert len(levels[0]) == 2  # task1 and task2 can run in parallel
        assert len(levels[1]) == 1  # task3 runs after both

    def test_can_execute_parallel_no_dependencies(self):
        """Test parallel execution check for tasks with no dependencies."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        tasks = [task1, task2]
        graph = TaskDependencyGraph(tasks)

        task1_id = graph._get_task_id(task1)
        task2_id = graph._get_task_id(task2)

        assert graph.can_execute_parallel([task1_id, task2_id]) is True

    def test_can_execute_parallel_with_dependencies(self):
        """Test parallel execution check for tasks with dependencies."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]
        graph = TaskDependencyGraph(tasks)

        task1_id = graph._get_task_id(task1)
        task2_id = graph._get_task_id(task2)

        assert graph.can_execute_parallel([task1_id, task2_id]) is False


class TestParallelExecutionEngine:
    """Test cases for ParallelExecutionEngine class."""

    def test_analyze_parallelization_potential_no_parallelization(self):
        """Test parallelization analysis with no parallelization potential."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]
        engine = ParallelExecutionEngine()
        analysis = engine.analyze_parallelization_potential(tasks)

        assert analysis["total_tasks"] == 2
        assert analysis["execution_levels"] == 2
        assert analysis["max_parallel_tasks"] == 1
        assert analysis["parallelization_feasible"] is False
        assert analysis["estimated_time_savings_percent"] == 0.0

    def test_analyze_parallelization_potential_high_parallelization(self):
        """Test parallelization analysis with high parallelization potential."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        task3 = Mock()
        task3.agent.role = "agent3"
        task3.description = "task3"
        task3.context = None

        task4 = Mock()
        task4.agent.role = "agent4"
        task4.description = "task4"
        task4.context = [task1, task2, task3]

        tasks = [task1, task2, task3, task4]
        engine = ParallelExecutionEngine()
        analysis = engine.analyze_parallelization_potential(tasks)

        assert analysis["total_tasks"] == 4
        assert analysis["execution_levels"] == 2
        assert analysis["max_parallel_tasks"] == 3
        assert analysis["parallelization_feasible"] is True
        assert analysis["estimated_time_savings_percent"] > 0

    def test_optimize_task_execution_order(self):
        """Test task execution order optimization."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        task3 = Mock()
        task3.agent.role = "agent3"
        task3.description = "task3"
        task3.context = [task1]

        tasks = [task1, task2, task3]
        engine = ParallelExecutionEngine()
        optimized = engine.optimize_task_execution_order(tasks)

        # Should maintain dependency order
        assert len(optimized) == 3
        assert optimized[0] == task1  # First task should be first

    def test_create_parallel_crew_configuration_sequential(self):
        """Test crew configuration for sequential execution."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]
        engine = ParallelExecutionEngine()

        base_config = {
            "process": "sequential",
            "max_execution_time": 300,
            "max_rpm": 10,
        }

        config = engine.create_parallel_crew_configuration(tasks, base_config)

        assert config["process"] == "sequential"
        assert config["max_execution_time"] == 300
        assert config["max_rpm"] == 10

    def test_create_parallel_crew_configuration_parallel(self):
        """Test crew configuration for parallel execution."""
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        task3 = Mock()
        task3.agent.role = "agent3"
        task3.description = "task3"
        task3.context = [task1, task2]

        tasks = [task1, task2, task3]
        engine = ParallelExecutionEngine()

        base_config = {
            "process": "sequential",
            "max_execution_time": 300,
            "max_rpm": 10,
        }

        config = engine.create_parallel_crew_configuration(tasks, base_config)

        assert config["process"] == "hierarchical"
        assert config["max_execution_time"] > 300  # Should be increased
        assert config["max_rpm"] > 10  # Should be increased


class TestEnhancedParallelAnalysisTasks:
    """Test cases for enhanced parallel analysis task creation."""

    def test_create_enhanced_parallel_analysis_tasks_parallel_enabled(self):
        """Test creating enhanced parallel analysis tasks when parallel is enabled."""
        # Mock agents
        agents = {
            "analysis_cartographer": Mock(),
            "verification_director": Mock(),
        }

        # Mock transcription task
        transcription_task = Mock()
        transcription_task.description = "transcription task"

        tasks = create_enhanced_parallel_analysis_tasks(
            agents=agents,
            transcription_task=transcription_task,
            depth="standard",
            enable_parallel=True,
            callback=None,
            logger_instance=None,
        )

        assert len(tasks) == 3  # text_analysis, fact_checking, bias_analysis

        # Check that all tasks have the transcription task as context
        for task in tasks:
            assert transcription_task in task.context

    def test_create_enhanced_parallel_analysis_tasks_comprehensive_depth(self):
        """Test creating enhanced parallel analysis tasks for comprehensive depth."""
        agents = {
            "analysis_cartographer": Mock(),
            "verification_director": Mock(),
        }

        transcription_task = Mock()
        transcription_task.description = "transcription task"

        tasks = create_enhanced_parallel_analysis_tasks(
            agents=agents,
            transcription_task=transcription_task,
            depth="comprehensive",
            enable_parallel=True,
            callback=None,
            logger_instance=None,
        )

        assert len(tasks) == 5  # 3 base + 2 advanced tasks

        # Check that all tasks have the transcription task as context
        for task in tasks:
            assert transcription_task in task.context

    def test_create_enhanced_parallel_analysis_tasks_parallel_disabled(self):
        """Test creating enhanced parallel analysis tasks when parallel is disabled."""
        agents = {
            "analysis_cartographer": Mock(),
            "verification_director": Mock(),
        }

        transcription_task = Mock()
        transcription_task.description = "transcription task"

        with patch(
            "ultimate_discord_intelligence_bot.orchestrator.crew_builders_focused.create_analysis_tasks"
        ) as mock_create:
            mock_create.return_value = [Mock(), Mock()]

            tasks = create_enhanced_parallel_analysis_tasks(
                agents=agents,
                transcription_task=transcription_task,
                depth="standard",
                enable_parallel=False,
                callback=None,
                logger_instance=None,
            )

            mock_create.assert_called_once()
            assert len(tasks) == 2


class TestOptimizeCrewForParallelExecution:
    """Test cases for crew optimization."""

    def test_optimize_crew_for_parallel_execution_feasible(self):
        """Test crew optimization when parallelization is feasible."""
        # Create tasks with parallelization potential
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = None

        task3 = Mock()
        task3.agent.role = "agent3"
        task3.description = "task3"
        task3.context = [task1, task2]

        tasks = [task1, task2, task3]

        # Mock crew
        crew = Mock()
        crew.tasks = tasks

        with patch(
            "ultimate_discord_intelligence_bot.orchestrator.crew_builders_focused.build_crew_with_tasks"
        ) as mock_build:
            mock_build.return_value = Mock()

            optimized_crew = optimize_crew_for_parallel_execution(crew, tasks)

            mock_build.assert_called_once()
            assert optimized_crew is not None

    def test_optimize_crew_for_parallel_execution_not_feasible(self):
        """Test crew optimization when parallelization is not feasible."""
        # Create tasks with no parallelization potential
        task1 = Mock()
        task1.agent.role = "agent1"
        task1.description = "task1"
        task1.context = None

        task2 = Mock()
        task2.agent.role = "agent2"
        task2.description = "task2"
        task2.context = [task1]

        tasks = [task1, task2]

        # Mock crew
        crew = Mock()
        crew.tasks = tasks

        optimized_crew = optimize_crew_for_parallel_execution(crew, tasks)

        # Should return original crew unchanged
        assert optimized_crew == crew
