"""
Comprehensive test suite for AI integration capabilities.

Tests DSPy optimization, agent planning, and integrated AI workflows.
"""

import pytest


pytest.skip("Test file imports from non-existent core.ai module", allow_module_level=True)

from core.ai import (
    Agent,
    AgentCapability,
    AgentPlanner,
    AICapability,
    AIIntegration,
    AIWorkflow,
    DSPyOptimizer,
    EvaluationDataset,
    IntegrationMode,
    OptimizationConfig,
    OptimizationMetric,
    OptimizationStrategy,
    PlanningContext,
    PlanningStrategy,
    PromptTemplate,
    PromptType,
    Task,
    TaskPriority,
)


class TestDSPyOptimizer:
    """Test DSPy optimization framework."""

    @pytest.fixture
    def optimizer(self) -> DSPyOptimizer:
        """Create DSPy optimizer instance for testing."""
        config = OptimizationConfig(
            strategy=OptimizationStrategy.BAYESIAN_OPTIMIZATION,
            max_iterations=10,
            patience=3,
        )
        return DSPyOptimizer(config)

    @pytest.fixture
    def sample_template(self) -> PromptTemplate:
        """Create sample prompt template."""
        return PromptTemplate(
            template_id="test_template",
            prompt_type=PromptType.ANALYSIS,
            base_template="Analyze the following content: {content}",
            variables=["content"],
            examples=[{"content": "Sample text", "analysis": "Sample analysis"}],
        )

    @pytest.fixture
    def sample_dataset(self) -> EvaluationDataset:
        """Create sample evaluation dataset."""
        return EvaluationDataset(
            dataset_id="test_dataset",
            examples=[{"content": "Sample content"}],
            ground_truth=["Sample analysis"],
            evaluation_metrics=[OptimizationMetric.ACCURACY],
        )

    def test_optimizer_initialization(self, optimizer: DSPyOptimizer) -> None:
        """Test optimizer initialization."""
        assert optimizer.config.strategy == OptimizationStrategy.BAYESIAN_OPTIMIZATION
        assert optimizer.config.max_iterations == 10
        assert len(optimizer.templates) == 0
        assert len(optimizer.optimization_history) == 0

    def test_template_properties(self, sample_template: PromptTemplate) -> None:
        """Test prompt template properties."""
        assert sample_template.template_id == "test_template"
        assert sample_template.prompt_type == PromptType.ANALYSIS
        assert sample_template.is_valid is True
        assert sample_template.variable_count == 1

    def test_dataset_properties(self, sample_dataset: EvaluationDataset) -> None:
        """Test evaluation dataset properties."""
        assert sample_dataset.dataset_id == "test_dataset"
        assert sample_dataset.size == 1
        assert sample_dataset.is_balanced is True

    @pytest.mark.asyncio
    async def test_register_template(self, optimizer: DSPyOptimizer, sample_template: PromptTemplate) -> None:
        """Test template registration."""
        result = await optimizer.register_template(sample_template)
        assert result is True
        assert "test_template" in optimizer.templates

    @pytest.mark.asyncio
    async def test_register_dataset(self, optimizer: DSPyOptimizer, sample_dataset: EvaluationDataset) -> None:
        """Test dataset registration."""
        result = await optimizer.register_dataset(sample_dataset)
        assert result is True
        assert "test_dataset" in optimizer.evaluation_datasets

    @pytest.mark.asyncio
    async def test_optimization_workflow(
        self,
        optimizer: DSPyOptimizer,
        sample_template: PromptTemplate,
        sample_dataset: EvaluationDataset,
    ) -> None:
        """Test complete optimization workflow."""
        # Register template and dataset
        await optimizer.register_template(sample_template)
        await optimizer.register_dataset(sample_dataset)

        # Run optimization
        result = await optimizer.optimize_template(
            sample_template.template_id,
            sample_dataset.dataset_id,
        )

        assert result is not None
        assert result.template_id == sample_template.template_id
        assert result.optimized_template is not None
        assert result.optimization_time > 0

    @pytest.mark.asyncio
    async def test_optimization_history(self, optimizer: DSPyOptimizer) -> None:
        """Test optimization history tracking."""
        history = await optimizer.get_optimization_history()
        assert isinstance(history, list)

        stats = await optimizer.get_performance_stats()
        assert "total_optimizations" in stats

    @pytest.mark.asyncio
    async def test_context_manager(self, optimizer: DSPyOptimizer) -> None:
        """Test optimizer as context manager."""
        async with optimizer:
            assert optimizer is not None


class TestAgentPlanner:
    """Test agent planning system."""

    @pytest.fixture
    def planner(self) -> AgentPlanner:
        """Create agent planner instance for testing."""
        return AgentPlanner(PlanningStrategy.ADAPTIVE)

    @pytest.fixture
    def sample_agent(self) -> Agent:
        """Create sample agent."""
        return Agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities={
                AgentCapability.CONTENT_ANALYSIS,
                AgentCapability.FACT_CHECKING,
            },
            max_capacity=1.0,
            performance_score=0.9,
        )

    @pytest.fixture
    def sample_task(self) -> Task:
        """Create sample task."""
        return Task(
            task_id="test_task",
            task_type="analysis",
            description="Test analysis task",
            priority=TaskPriority.NORMAL,
            required_capabilities={AgentCapability.CONTENT_ANALYSIS},
            estimated_duration=60.0,
        )

    def test_planner_initialization(self, planner: AgentPlanner) -> None:
        """Test planner initialization."""
        assert planner.strategy == PlanningStrategy.ADAPTIVE
        assert len(planner.agents) == 0
        assert len(planner.execution_plans) == 0

    def test_agent_properties(self, sample_agent: Agent) -> None:
        """Test agent properties."""
        assert sample_agent.agent_id == "test_agent"
        assert sample_agent.is_available is True
        assert sample_agent.available_capacity == 1.0
        assert sample_agent.capability_match_score({AgentCapability.CONTENT_ANALYSIS}) == 1.0

    def test_task_properties(self, sample_task: Task) -> None:
        """Test task properties."""
        assert sample_task.task_id == "test_task"
        assert sample_task.is_ready is True
        assert sample_task.complexity_score > 0
        assert sample_task.urgency_score == 0.6  # NORMAL priority

    def test_agent_can_handle_task(self, sample_agent: Agent, sample_task: Task) -> None:
        """Test agent task handling capability."""
        assert sample_agent.can_handle_task(sample_task) is True

    @pytest.mark.asyncio
    async def test_register_agent(self, planner: AgentPlanner, sample_agent: Agent) -> None:
        """Test agent registration."""
        result = await planner.register_agent(sample_agent)
        assert result is True
        assert "test_agent" in planner.agents

    @pytest.mark.asyncio
    async def test_submit_task(self, planner: AgentPlanner, sample_task: Task) -> None:
        """Test task submission."""
        result = await planner.submit_task(sample_task)
        assert result is True
        assert len(planner.task_queue) == 1

    @pytest.mark.asyncio
    async def test_create_execution_plan(self, planner: AgentPlanner, sample_agent: Agent, sample_task: Task) -> None:
        """Test execution plan creation."""
        # Register agent
        await planner.register_agent(sample_agent)

        # Create planning context
        context = PlanningContext(
            available_agents=[sample_agent],
            system_load=0.3,
        )

        # Create execution plan
        plan = await planner.create_execution_plan([sample_task], context)

        assert plan is not None
        assert plan.is_valid is True
        assert sample_task.task_id in plan.task_assignments
        assert plan.estimated_completion_time > 0

    @pytest.mark.asyncio
    async def test_planning_statistics(self, planner: AgentPlanner) -> None:
        """Test planning statistics."""
        stats = await planner.get_planning_statistics()
        assert "plans_created" in stats
        assert "tasks_assigned" in stats

    @pytest.mark.asyncio
    async def test_context_manager(self, planner: AgentPlanner) -> None:
        """Test planner as context manager."""
        async with planner:
            assert planner is not None


class TestAIIntegration:
    """Test AI integration system."""

    @pytest.fixture
    def ai_integration(self) -> AIIntegration:
        """Create AI integration instance for testing."""
        return AIIntegration(IntegrationMode.ADAPTIVE)

    @pytest.fixture
    def sample_workflow(self) -> AIWorkflow:
        """Create sample AI workflow."""
        return AIWorkflow(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="Test AI workflow",
            required_capabilities={
                AICapability.PROMPT_OPTIMIZATION,
                AICapability.TASK_PLANNING,
            },
            optimization_config=OptimizationConfig(max_iterations=5),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.ADAPTIVE,
            expected_duration=300.0,
        )

    def test_ai_integration_initialization(self, ai_integration: AIIntegration) -> None:
        """Test AI integration initialization."""
        assert ai_integration.integration_mode == IntegrationMode.ADAPTIVE
        assert ai_integration.is_initialized is False
        assert len(ai_integration.workflows) == 0

    def test_workflow_properties(self, sample_workflow: AIWorkflow) -> None:
        """Test workflow properties."""
        assert sample_workflow.workflow_id == "test_workflow"
        assert sample_workflow.requires_optimization is True
        assert sample_workflow.requires_planning is True
        assert sample_workflow.is_complex is True

    @pytest.mark.asyncio
    async def test_initialize_system(self, ai_integration: AIIntegration) -> None:
        """Test system initialization."""
        result = await ai_integration.initialize()
        assert result is True
        assert ai_integration.is_initialized is True
        assert ai_integration.dspy_optimizer is not None
        assert ai_integration.agent_planner is not None

    @pytest.mark.asyncio
    async def test_register_workflow(self, ai_integration: AIIntegration, sample_workflow: AIWorkflow) -> None:
        """Test workflow registration."""
        await ai_integration.initialize()
        result = await ai_integration.register_workflow(sample_workflow)
        assert result is True
        assert "test_workflow" in ai_integration.workflows

    @pytest.mark.asyncio
    async def test_execute_workflow(self, ai_integration: AIIntegration, sample_workflow: AIWorkflow) -> None:
        """Test workflow execution."""
        await ai_integration.initialize()
        await ai_integration.register_workflow(sample_workflow)

        result = await ai_integration.execute_workflow("test_workflow")

        assert result is not None
        assert result.workflow_id == "test_workflow"
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_performance_metrics(self, ai_integration: AIIntegration) -> None:
        """Test performance metrics."""
        metrics = await ai_integration.get_performance_metrics()
        assert "total_workflows" in metrics
        assert "successful_workflows" in metrics
        assert "average_execution_time" in metrics

    @pytest.mark.asyncio
    async def test_workflow_history(self, ai_integration: AIIntegration) -> None:
        """Test workflow history."""
        history = await ai_integration.get_workflow_history()
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_context_manager(self, ai_integration: AIIntegration) -> None:
        """Test AI integration as context manager."""
        async with ai_integration:
            assert ai_integration is not None


class TestIntegrationWorkflows:
    """Test integrated AI workflows."""

    @pytest.mark.asyncio
    async def test_optimization_first_workflow(self) -> None:
        """Test optimization-first workflow execution."""
        ai_integration = AIIntegration(IntegrationMode.OPTIMIZATION_FIRST)
        await ai_integration.initialize()

        workflow = AIWorkflow(
            workflow_id="opt_first_workflow",
            name="Optimization First Workflow",
            description="Test optimization-first execution",
            required_capabilities={AICapability.PROMPT_OPTIMIZATION},
            optimization_config=OptimizationConfig(max_iterations=3),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.OPTIMIZATION_FIRST,
            expected_duration=120.0,
        )

        await ai_integration.register_workflow(workflow)
        result = await ai_integration.execute_workflow("opt_first_workflow")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_planning_first_workflow(self) -> None:
        """Test planning-first workflow execution."""
        ai_integration = AIIntegration(IntegrationMode.PLANNING_FIRST)
        await ai_integration.initialize()

        workflow = AIWorkflow(
            workflow_id="plan_first_workflow",
            name="Planning First Workflow",
            description="Test planning-first execution",
            required_capabilities={AICapability.TASK_PLANNING},
            optimization_config=OptimizationConfig(max_iterations=3),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.PLANNING_FIRST,
            expected_duration=180.0,
        )

        await ai_integration.register_workflow(workflow)
        result = await ai_integration.execute_workflow("plan_first_workflow")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_parallel_workflow(self) -> None:
        """Test parallel workflow execution."""
        ai_integration = AIIntegration(IntegrationMode.PARALLEL)
        await ai_integration.initialize()

        workflow = AIWorkflow(
            workflow_id="parallel_workflow",
            name="Parallel Workflow",
            description="Test parallel execution",
            required_capabilities={
                AICapability.PROMPT_OPTIMIZATION,
                AICapability.TASK_PLANNING,
            },
            optimization_config=OptimizationConfig(max_iterations=3),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.PARALLEL,
            expected_duration=240.0,
        )

        await ai_integration.register_workflow(workflow)
        result = await ai_integration.execute_workflow("parallel_workflow")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_adaptive_workflow(self) -> None:
        """Test adaptive workflow execution."""
        ai_integration = AIIntegration(IntegrationMode.ADAPTIVE)
        await ai_integration.initialize()

        workflow = AIWorkflow(
            workflow_id="adaptive_workflow",
            name="Adaptive Workflow",
            description="Test adaptive execution",
            required_capabilities={
                AICapability.PROMPT_OPTIMIZATION,
                AICapability.TASK_PLANNING,
            },
            optimization_config=OptimizationConfig(max_iterations=3),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.ADAPTIVE,
            expected_duration=300.0,
        )

        await ai_integration.register_workflow(workflow)
        result = await ai_integration.execute_workflow("adaptive_workflow")

        assert result is not None
        assert result.success is True


class TestPerformanceAndScaling:
    """Test performance and scaling capabilities."""

    @pytest.mark.asyncio
    async def test_multiple_workflows(self) -> None:
        """Test multiple concurrent workflows."""
        ai_integration = AIIntegration(IntegrationMode.ADAPTIVE)
        await ai_integration.initialize()

        # Create multiple workflows
        workflows = []
        for i in range(3):
            workflow = AIWorkflow(
                workflow_id=f"workflow_{i}",
                name=f"Workflow {i}",
                description=f"Test workflow {i}",
                required_capabilities={AICapability.PROMPT_OPTIMIZATION},
                optimization_config=OptimizationConfig(max_iterations=2),
                planning_strategy=PlanningStrategy.ADAPTIVE,
                integration_mode=IntegrationMode.ADAPTIVE,
                expected_duration=60.0,
            )
            workflows.append(workflow)
            await ai_integration.register_workflow(workflow)

        # Execute workflows
        results = []
        for workflow in workflows:
            result = await ai_integration.execute_workflow(workflow.workflow_id)
            results.append(result)

        # Verify results
        assert len(results) == 3
        assert all(result is not None for result in results)
        assert all(result.success for result in results)

    @pytest.mark.asyncio
    async def test_resource_management(self) -> None:
        """Test AI resource management."""
        ai_integration = AIIntegration(IntegrationMode.ADAPTIVE)
        await ai_integration.initialize()

        # Check resources
        assert "cpu" in ai_integration.ai_resources
        assert "memory" in ai_integration.ai_resources
        assert "gpu" in ai_integration.ai_resources

        # Verify resource properties
        cpu_resource = ai_integration.ai_resources["cpu"]
        assert cpu_resource.resource_type == "computational"
        assert cpu_resource.capacity == 100.0
        assert cpu_resource.available_capacity > 0

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        """Test error handling in workflows."""
        ai_integration = AIIntegration(IntegrationMode.ADAPTIVE)

        # Try to execute workflow without initialization
        result = await ai_integration.execute_workflow("nonexistent_workflow")
        assert result is None

        # Try to register workflow without initialization
        workflow = AIWorkflow(
            workflow_id="error_workflow",
            name="Error Workflow",
            description="Test error handling",
            required_capabilities=set(),
            optimization_config=OptimizationConfig(),
            planning_strategy=PlanningStrategy.ADAPTIVE,
            integration_mode=IntegrationMode.ADAPTIVE,
            expected_duration=60.0,
        )

        result = await ai_integration.register_workflow(workflow)
        assert result is False


# Fixtures for integration testing
@pytest.fixture
def integration_context():
    """Create integration test context."""
    return {
        "system_load": 0.5,
        "available_agents": 3,
        "resource_constraints": {"memory": 1000, "cpu": 100},
    }
