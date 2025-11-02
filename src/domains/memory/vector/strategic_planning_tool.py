from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import Any

from crewai.tools import BaseTool


logger = logging.getLogger(__name__)


@dataclass
class StrategicObjective:
    """Represents a strategic objective in the mission plan."""

    id: str
    title: str
    description: str
    priority: int
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    assigned_to: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Risk assessment for strategic objectives."""

    risk_id: str
    objective_id: str
    risk_type: str
    severity: str
    probability: float
    impact: str
    mitigation_strategy: str
    contingency_plan: str


class StrategicPlanningTool(BaseTool):
    """
    Strategic planning tool for creating comprehensive mission plans with execution phases,
    risk assessment, and success metrics for intelligence operations.
    """

    name: str = "strategic_planning_tool"
    description: str = "Creates strategic plans for intelligence missions with execution phases, risk assessment, and success metrics. Handles complex multi-objective planning with dependency management and resource allocation."

    def _run(self, mission_context: str, objectives: list[dict[str, Any]], tenant: str, workspace: str) -> StepResult:
        """
        Create a strategic plan for intelligence operations.

        Args:
            mission_context: High-level description of the mission
            objectives: List of objective dictionaries with id, title, description, priority, dependencies
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization

        Returns:
            StepResult with strategic plan data
        """
        metrics = get_metrics()
        start_time = time.time()
        try:
            logger.info(f"Creating strategic plan for tenant '{tenant}', workspace '{workspace}'")
            logger.debug(f"Mission Context: {mission_context}")
            logger.debug(f"Objectives: {objectives}")
            if not mission_context or not objectives:
                return StepResult.fail("Mission context and objectives are required")
            if not tenant or not workspace:
                return StepResult.fail("Tenant and workspace are required")
            strategic_objectives = self._create_strategic_objectives(objectives)
            execution_plan = self._create_execution_plan(strategic_objectives)
            risk_assessment = self._assess_risks(strategic_objectives)
            success_metrics = self._define_success_metrics(strategic_objectives)
            strategic_plan = {
                "mission_context": mission_context,
                "objectives": [obj.__dict__ for obj in strategic_objectives],
                "execution_plan": execution_plan,
                "risk_assessment": [risk.__dict__ for risk in risk_assessment],
                "success_metrics": success_metrics,
                "created_at": self._get_current_timestamp(),
                "tenant": tenant,
                "workspace": workspace,
                "status": "draft",
                "version": "1.0",
                "plan_id": f"plan_{int(time.time())}_{tenant}_{workspace}",
            }
            logger.info("Strategic plan created successfully")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "success"})
            return StepResult.success(strategic_plan)
        except Exception as e:
            logger.error(f"Strategic planning failed: {e!s}")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "error"})
            return StepResult.fail(f"Strategic planning failed: {e!s}")
        finally:
            metrics.histogram("tool_run_seconds", time.time() - start_time, labels={"tool": self.__class__.__name__})

    def _create_strategic_objectives(self, objectives_data: list[dict[str, Any]]) -> list[StrategicObjective]:
        """Create strategic objectives from input data."""
        strategic_objectives = []
        for obj_data in objectives_data:
            objective = StrategicObjective(
                id=obj_data.get("id", f"obj_{len(strategic_objectives)}"),
                title=obj_data.get("title", "Untitled Objective"),
                description=obj_data.get("description", ""),
                priority=obj_data.get("priority", 1),
                dependencies=obj_data.get("dependencies", []),
            )
            strategic_objectives.append(objective)
        return strategic_objectives

    def _create_execution_plan(self, objectives: list[StrategicObjective]) -> dict[str, Any]:
        """Create execution plan with phases based on dependencies."""
        execution_phases = []
        current_phase = []
        completed_deps: set[str] = set()
        sorted_objectives = sorted(objectives, key=lambda x: x.priority)
        for objective in sorted_objectives:
            if all(dep in completed_deps for dep in objective.dependencies):
                current_phase.append(objective)
            else:
                if current_phase:
                    execution_phases.append(current_phase)
                    completed_deps.update(obj.id for obj in current_phase)
                current_phase = [objective]
        if current_phase:
            execution_phases.append(current_phase)
            completed_deps.update(obj.id for obj in current_phase)
        return {
            "phases": [[obj.__dict__ for obj in phase] for phase in execution_phases],
            "total_phases": len(execution_phases),
            "estimated_duration_hours": len(execution_phases) * 2,
            "status": "planned",
            "created_at": self._get_current_timestamp(),
        }

    def _assess_risks(self, objectives: list[StrategicObjective]) -> list[RiskAssessment]:
        """Assess risks for strategic objectives."""
        risks = []
        for objective in objectives:
            if "analysis" in objective.title.lower():
                risks.append(
                    RiskAssessment(
                        risk_id=f"risk_{objective.id}_data_quality",
                        objective_id=objective.id,
                        risk_type="data_quality",
                        severity="medium",
                        probability=0.3,
                        impact="Analysis accuracy may be compromised",
                        mitigation_strategy="Implement data validation and quality checks",
                        contingency_plan="Fallback to alternative data sources",
                    )
                )
            if "real-time" in objective.title.lower() or "live" in objective.title.lower():
                risks.append(
                    RiskAssessment(
                        risk_id=f"risk_{objective.id}_latency",
                        objective_id=objective.id,
                        risk_type="performance",
                        severity="high",
                        probability=0.4,
                        impact="Real-time processing may exceed latency requirements",
                        mitigation_strategy="Implement caching and optimization",
                        contingency_plan="Switch to batch processing mode",
                    )
                )
            if len(objective.dependencies) > 2:
                risks.append(
                    RiskAssessment(
                        risk_id=f"risk_{objective.id}_dependencies",
                        objective_id=objective.id,
                        risk_type="dependency",
                        severity="medium",
                        probability=0.5,
                        impact="Complex dependencies may cause delays",
                        mitigation_strategy="Monitor dependency completion closely",
                        contingency_plan="Parallel execution where possible",
                    )
                )
        return risks

    def _define_success_metrics(self, objectives: list[StrategicObjective]) -> dict[str, Any]:
        """Define success metrics based on strategic objectives."""
        metrics = {
            "overall_success_rate": 0.95,
            "average_completion_time_hours": 0,
            "cost_efficiency_score": 0.9,
            "quality_score": 0.92,
        }
        for obj in objectives:
            metrics[f"{obj.id}_completion_rate"] = 1.0
            metrics[f"{obj.id}_time_to_completion_hours"] = 1.0
            metrics[f"{obj.id}_cost_usd"] = 0.1
            metrics[f"{obj.id}_quality_score"] = 0.9
        return metrics

    def _get_current_timestamp(self) -> float:
        """Returns the current UTC timestamp."""
        return time.time()
