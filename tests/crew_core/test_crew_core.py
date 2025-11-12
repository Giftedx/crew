"""Unit tests for crew_core components."""

from __future__ import annotations

import pytest

from domains.orchestration.crew import (
    CrewConfig,
    CrewErrorHandler,
    CrewExecutionResult,
    CrewInsightGenerator,
    CrewTask,
    DefaultCrewFactory,
    UnifiedCrewExecutor,
    get_crew_factory,
)
from domains.orchestration.crew.interfaces import CrewExecutionMode, CrewPriority
from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult


class TestCrewConfig:
    """Test CrewConfig dataclass."""

    def test_crew_config_defaults(self) -> None:
        """Test default values are set correctly."""
        config = CrewConfig(tenant_id="test-tenant")
        assert config.tenant_id == "test-tenant"
        assert config.enable_cache is True
        assert config.enable_telemetry is True
        assert config.timeout_seconds == 300
        assert config.max_retries == 3
        assert config.quality_threshold == 0.7
        assert config.execution_mode == CrewExecutionMode.SEQUENTIAL
        assert config.enable_early_exit is True
        assert config.enable_fallback is True
        assert config.metadata == {}

    def test_crew_config_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CrewConfig(
            tenant_id="custom-tenant",
            enable_cache=False,
            timeout_seconds=600,
            max_retries=5,
            quality_threshold=0.9,
            execution_mode=CrewExecutionMode.PARALLEL,
            metadata={"key": "value"},
        )
        assert config.tenant_id == "custom-tenant"
        assert config.enable_cache is False
        assert config.timeout_seconds == 600
        assert config.max_retries == 5
        assert config.quality_threshold == 0.9
        assert config.execution_mode == CrewExecutionMode.PARALLEL
        assert config.metadata == {"key": "value"}


class TestCrewTask:
    """Test CrewTask dataclass."""

    def test_crew_task_valid(self) -> None:
        """Test valid task creation."""
        task = CrewTask(
            task_id="task-123",
            task_type="analysis",
            description="Analyze content",
            inputs={"content": "test"},
            agent_requirements=["analyzer"],
            tool_requirements=["search"],
            priority=CrewPriority.HIGH,
        )
        assert task.task_id == "task-123"
        assert task.task_type == "analysis"
        assert task.description == "Analyze content"
        assert task.inputs == {"content": "test"}
        assert task.agent_requirements == ["analyzer"]
        assert task.tool_requirements == ["search"]
        assert task.priority == CrewPriority.HIGH

    def test_crew_task_validation_empty_id(self) -> None:
        """Test task validation fails with empty ID."""
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            CrewTask(task_id="", task_type="analysis", description="Test", inputs={})

    def test_crew_task_validation_empty_type(self) -> None:
        """Test task validation fails with empty type."""
        with pytest.raises(ValueError, match="task_type cannot be empty"):
            CrewTask(task_id="task-123", task_type="", description="Test", inputs={})

    def test_crew_task_validation_empty_description(self) -> None:
        """Test task validation fails with empty description."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            CrewTask(task_id="task-123", task_type="analysis", description="", inputs={})


class TestUnifiedCrewExecutor:
    """Test UnifiedCrewExecutor."""

    @pytest.mark.asyncio
    async def test_executor_initialization(self) -> None:
        """Test executor initializes correctly."""
        config = CrewConfig(tenant_id="test-tenant")
        executor = UnifiedCrewExecutor(config)
        assert executor.config == config
        assert executor.metrics is not None

    @pytest.mark.asyncio
    async def test_validate_task_success(self) -> None:
        """Test task validation succeeds for valid task."""
        config = CrewConfig(tenant_id="test-tenant")
        executor = UnifiedCrewExecutor(config)
        task = CrewTask(task_id="task-123", task_type="analysis", description="Test task", inputs={"data": "test"})
        result = await executor.validate_task(task)
        assert result.success is True
        assert result.data == {"validated": True}

    @pytest.mark.asyncio
    async def test_validate_task_empty_id(self) -> None:
        """Test task validation fails with empty ID."""
        config = CrewConfig(tenant_id="test-tenant")
        executor = UnifiedCrewExecutor(config)
        task = object.__new__(CrewTask)
        task.task_id = ""
        task.task_type = "analysis"
        task.description = "Test"
        task.inputs = {}
        result = await executor.validate_task(task)
        assert result.success is False
        assert result.error_category == ErrorCategory.VALIDATION

    @pytest.mark.asyncio
    async def test_execute_task_returns_summary(self) -> None:
        """Test task execution returns structured mission summary."""
        config = CrewConfig(tenant_id="test-tenant")
        executor = UnifiedCrewExecutor(config)
        task = CrewTask(task_id="task-123", task_type="analysis", description="Test task", inputs={"data": "test"})
        result = await executor.execute(task, config)
        assert isinstance(result, CrewExecutionResult)
        assert result.task_id == "task-123"
        assert result.step_result.success is True
        assert result.execution_time_seconds > 0
        payload = result.step_result.data
        assert payload["status"] == "success"
        assert payload["message"].startswith("Mission outcome")
        assert "pending_migration" not in payload["message"].lower()
        metadata = result.step_result.metadata
        assert isinstance(metadata["agents_used"], list)
        assert metadata["cache_hits"] == 0

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test cleanup doesn't raise errors."""
        config = CrewConfig(tenant_id="test-tenant")
        executor = UnifiedCrewExecutor(config)
        await executor.cleanup()


class TestDefaultCrewFactory:
    """Test DefaultCrewFactory."""

    def test_factory_initialization(self) -> None:
        """Test factory initializes with available executors."""
        factory = DefaultCrewFactory()
        executors = factory.get_available_executors()
        assert "unified" in executors
        assert "default" in executors

    def test_create_unified_executor(self) -> None:
        """Test creating unified executor."""
        factory = DefaultCrewFactory()
        config = CrewConfig(tenant_id="test-tenant")
        executor = factory.create_executor("unified", config)
        assert isinstance(executor, UnifiedCrewExecutor)
        assert executor.config == config

    def test_create_default_executor(self) -> None:
        """Test creating default executor (alias for unified)."""
        factory = DefaultCrewFactory()
        config = CrewConfig(tenant_id="test-tenant")
        executor = factory.create_executor("default", config)
        assert isinstance(executor, UnifiedCrewExecutor)

    def test_create_unknown_executor(self) -> None:
        """Test creating unknown executor raises ValueError."""
        factory = DefaultCrewFactory()
        config = CrewConfig(tenant_id="test-tenant")
        with pytest.raises(ValueError, match="Unknown executor type"):
            factory.create_executor("nonexistent", config)

    def test_get_crew_factory_singleton(self) -> None:
        """Test get_crew_factory returns singleton."""
        factory1 = get_crew_factory()
        factory2 = get_crew_factory()
        assert factory1 is factory2


class TestCrewErrorHandler:
    """Test CrewErrorHandler."""

    @pytest.mark.asyncio
    async def test_handle_execution_error(self) -> None:
        """Test error handling returns appropriate StepResult."""
        handler = CrewErrorHandler(tenant_id="test-tenant")
        task = CrewTask(task_id="task-123", task_type="analysis", description="Test task", inputs={})
        error = ValueError("Test error")
        result = await handler.handle_execution_error(task, error, attempt=0)
        assert result.success is False
        assert result.error_category == ErrorCategory.EXECUTION
        assert "Test error" in result.error_message
        assert result.metadata["error_type"] == "ValueError"
        assert result.metadata["task_id"] == "task-123"

    def test_categorize_timeout_error(self) -> None:
        """Test timeout error categorization."""
        handler = CrewErrorHandler(tenant_id="test-tenant")
        error = TimeoutError("Operation timed out")
        category = handler._categorize_error(error)
        assert category == ErrorCategory.TIMEOUT

    def test_categorize_network_error(self) -> None:
        """Test network error categorization."""
        handler = CrewErrorHandler(tenant_id="test-tenant")
        error = ConnectionError("Network unreachable")
        category = handler._categorize_error(error)
        assert category == ErrorCategory.NETWORK


class TestCrewInsightGenerator:
    """Test CrewInsightGenerator."""

    def test_generate_insights(self) -> None:
        """Test insight generation."""
        generator = CrewInsightGenerator(tenant_id="test-tenant")
        result = CrewExecutionResult(
            step_result=StepResult.ok(result={"data": "test"}),
            task_id="task-123",
            execution_time_seconds=15.5,
            agents_used=["agent1", "agent2"],
            tools_used=["tool1"],
            cache_hits=5,
            retry_count=1,
        )
        insights = generator.generate_insights(result)
        assert insights["task_id"] == "task-123"
        assert insights["success"] is True
        assert insights["execution_time_seconds"] == 15.5
        assert "performance" in insights
        assert "resource_usage" in insights
        assert "recommendations" in insights

    def test_performance_analysis_fast(self) -> None:
        """Test performance analysis for fast execution."""
        generator = CrewInsightGenerator(tenant_id="test-tenant")
        result = CrewExecutionResult(
            step_result=StepResult.ok(result={}),
            task_id="task-123",
            execution_time_seconds=3.0,
            agents_used=[],
            tools_used=[],
        )
        performance = generator._analyze_performance(result)
        assert performance["speed_category"] == "fast"

    def test_performance_analysis_slow(self) -> None:
        """Test performance analysis for slow execution."""
        generator = CrewInsightGenerator(tenant_id="test-tenant")
        result = CrewExecutionResult(
            step_result=StepResult.ok(result={}),
            task_id="task-123",
            execution_time_seconds=45.0,
            agents_used=[],
            tools_used=[],
        )
        performance = generator._analyze_performance(result)
        assert performance["speed_category"] == "slow"

    def test_recommendations_long_execution(self) -> None:
        """Test recommendations for long execution."""
        generator = CrewInsightGenerator(tenant_id="test-tenant")
        result = CrewExecutionResult(
            step_result=StepResult.ok(result={}),
            task_id="task-123",
            execution_time_seconds=150.0,
            agents_used=[],
            tools_used=[],
        )
        recommendations = generator._generate_recommendations(result)
        assert any("smaller sub-tasks" in rec.lower() for rec in recommendations)

    def test_recommendations_high_retries(self) -> None:
        """Test recommendations for high retry count."""
        generator = CrewInsightGenerator(tenant_id="test-tenant")
        result = CrewExecutionResult(
            step_result=StepResult.ok(result={}),
            task_id="task-123",
            execution_time_seconds=10.0,
            agents_used=[],
            tools_used=[],
            retry_count=3,
        )
        recommendations = generator._generate_recommendations(result)
        assert any("retry count" in rec.lower() for rec in recommendations)
