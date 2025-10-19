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
    # AI Integration
    "AIIntegration",
    "AIWorkflow",
    "WorkflowResult",
    "AIResource",
    "IntegrationMode",
    "AICapability",
    # Agent Planning
    "AgentPlanner",
    "Agent",
    "Task",
    "PlanningContext",
    "ExecutionPlan",
    "PlanningStrategy",
    "TaskPriority",
    "TaskStatus",
    "AgentCapability",
    "CoordinationPattern",
    # DSPy Optimization
    "DSPyOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "PromptTemplate",
    "EvaluationDataset",
    "OptimizationStrategy",
    "PromptType",
    "OptimizationMetric",
]
