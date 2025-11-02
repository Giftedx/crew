"""
Advanced AI integration module for the Ultimate Discord Intelligence Bot.

Provides sophisticated AI capabilities including:
- DSPy optimization framework for prompt engineering
- Advanced agent planning patterns for multi-agent coordination
- Integrated AI workflows with adaptive execution strategies
- Performance monitoring and optimization
"""

from .agent_planner import (
    Agent,
    AgentCapability,
    AgentPlanner,
    CoordinationPattern,
    ExecutionPlan,
    PlanningContext,
    PlanningStrategy,
    Task,
    TaskPriority,
    TaskStatus,
)
from .ai_integration import (
    AICapability,
    AIIntegration,
    AIResource,
    AIWorkflow,
    IntegrationMode,
    WorkflowResult,
)
from .dspy_optimizer import (
    DSPyOptimizer,
    EvaluationDataset,
    OptimizationConfig,
    OptimizationMetric,
    OptimizationResult,
    OptimizationStrategy,
    PromptTemplate,
    PromptType,
)


__all__ = [
    "AICapability",
    # AI Integration
    "AIIntegration",
    "AIResource",
    "AIWorkflow",
    "Agent",
    "AgentCapability",
    # Agent Planning
    "AgentPlanner",
    "CoordinationPattern",
    # DSPy Optimization
    "DSPyOptimizer",
    "EvaluationDataset",
    "ExecutionPlan",
    "IntegrationMode",
    "OptimizationConfig",
    "OptimizationMetric",
    "OptimizationResult",
    "OptimizationStrategy",
    "PlanningContext",
    "PlanningStrategy",
    "PromptTemplate",
    "PromptType",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "WorkflowResult",
]
