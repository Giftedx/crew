"""
Executive Supervisor Agent - Strategic Intelligence Command Center

This agent serves as the top-level strategic commander of the intelligence platform,
responsible for mission planning, resource allocation, and system-wide optimization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from crewai import Agent

from ..step_result import StepResult
from ..tools._base import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class StrategicObjective:
    """Strategic objective with priority and success criteria."""

    id: str
    title: str
    description: str
    priority: int  # 1-10, higher is more important
    success_criteria: List[str]
    resource_requirements: Dict[str, Any]
    timeline: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, failed
    progress: float = 0.0


@dataclass
class ResourceAllocation:
    """Resource allocation for agents and tasks."""

    agent_id: str
    cpu_cores: int
    memory_gb: float
    gpu_units: int
    network_bandwidth_mbps: int
    storage_gb: int
    priority_level: int
    allocated_at: str
    expires_at: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-wide performance and health metrics."""

    total_agents: int
    active_agents: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_response_time_ms: float
    system_load_percent: float
    memory_usage_percent: float
    error_rate_percent: float
    cost_per_hour_usd: float


class StrategicPlanningTool(BaseTool):
    """Tool for strategic mission planning and objective management."""

    def _run(
        self,
        mission_context: str,
        objectives: List[Dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """
        Create and manage strategic objectives for the intelligence platform.

        Args:
            mission_context: High-level mission description
            objectives: List of objective definitions
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with strategic plan
        """
        try:
            if not mission_context or not objectives:
                return StepResult.fail("Mission context and objectives are required")

            strategic_plan = self._create_strategic_plan(
                mission_context, objectives, tenant, workspace
            )

            return StepResult.ok(
                data={
                    "strategic_plan": strategic_plan,
                    "objectives_count": len(objectives),
                    "mission_context": mission_context,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Strategic planning failed: {str(e)}")
            return StepResult.fail(f"Strategic planning failed: {str(e)}")

    def _create_strategic_plan(
        self,
        mission_context: str,
        objectives: List[Dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> Dict[str, Any]:
        """Create comprehensive strategic plan."""
        strategic_objectives: List[StrategicObjective] = []

        for obj_data in objectives:
            objective = StrategicObjective(
                id=obj_data.get("id", f"obj_{len(strategic_objectives)}"),
                title=obj_data.get("title", "Untitled Objective"),
                description=obj_data.get("description", ""),
                priority=obj_data.get("priority", 5),
                success_criteria=obj_data.get("success_criteria", []),
                resource_requirements=obj_data.get("resource_requirements", {}),
                timeline=obj_data.get("timeline", "TBD"),
                dependencies=obj_data.get("dependencies", []),
            )
            strategic_objectives.append(objective)

        # Sort by priority
        strategic_objectives.sort(key=lambda x: x.priority, reverse=True)

        return {
            "mission_context": mission_context,
            "objectives": [
                {
                    "id": obj.id,
                    "title": obj.title,
                    "description": obj.description,
                    "priority": obj.priority,
                    "success_criteria": obj.success_criteria,
                    "resource_requirements": obj.resource_requirements,
                    "timeline": obj.timeline,
                    "dependencies": obj.dependencies,
                    "status": obj.status,
                    "progress": obj.progress,
                }
                for obj in strategic_objectives
            ],
            "execution_plan": self._create_execution_plan(strategic_objectives),
            "risk_assessment": self._assess_risks(strategic_objectives),
            "success_metrics": self._define_success_metrics(strategic_objectives),
        }

    def _create_execution_plan(
        self, objectives: List[StrategicObjective]
    ) -> Dict[str, Any]:
        """Create detailed execution plan with dependencies."""
        execution_phases = []
        current_phase = []
        completed_deps: Set[str] = set()

        for objective in objectives:
            if all(dep in completed_deps for dep in objective.dependencies):
                current_phase.append(objective)
            else:
                # Start new phase
                if current_phase:
                    execution_phases.append(current_phase)
                current_phase = [objective]

        if current_phase:
            execution_phases.append(current_phase)

        return {
            "phases": [
                {
                    "phase_id": f"phase_{i + 1}",
                    "objectives": [obj.id for obj in phase],
                    "estimated_duration": self._estimate_phase_duration(phase),
                    "critical_path": self._identify_critical_path(phase),
                }
                for i, phase in enumerate(execution_phases)
            ],
            "total_estimated_duration": sum(
                self._estimate_phase_duration(phase) for phase in execution_phases
            ),
        }

    def _estimate_phase_duration(self, objectives: List[StrategicObjective]) -> str:
        """Estimate phase duration based on objectives."""
        # Simple estimation logic - can be enhanced with ML
        base_days = len(objectives) * 2
        complexity_multiplier = (
            sum(obj.priority for obj in objectives) / len(objectives) / 10
        )
        estimated_days = int(base_days * (1 + complexity_multiplier))
        return f"{estimated_days} days"

    def _identify_critical_path(
        self, objectives: List[StrategicObjective]
    ) -> List[str]:
        """Identify critical path objectives."""
        return [obj.id for obj in objectives if obj.priority >= 8]

    def _assess_risks(self, objectives: List[StrategicObjective]) -> Dict[str, Any]:
        """Assess risks for strategic objectives."""
        high_priority_count = sum(1 for obj in objectives if obj.priority >= 8)
        dependency_count = sum(len(obj.dependencies) for obj in objectives)

        risk_level = "low"
        if high_priority_count > 3 or dependency_count > 5:
            risk_level = "high"
        elif high_priority_count > 1 or dependency_count > 2:
            risk_level = "medium"

        return {
            "overall_risk_level": risk_level,
            "high_priority_objectives": high_priority_count,
            "dependency_complexity": dependency_count,
            "mitigation_strategies": [
                "Implement parallel execution where possible",
                "Create fallback plans for critical objectives",
                "Monitor progress continuously",
                "Maintain resource buffers",
            ],
        }

    def _define_success_metrics(
        self, objectives: List[StrategicObjective]
    ) -> Dict[str, Any]:
        """Define success metrics for the strategic plan."""
        return {
            "completion_rate_target": 0.95,
            "timeline_adherence_target": 0.90,
            "resource_efficiency_target": 0.85,
            "quality_score_target": 0.92,
            "stakeholder_satisfaction_target": 0.88,
        }


class ResourceAllocationTool(BaseTool):
    """Tool for dynamic resource allocation and management."""

    def _run(
        self, allocation_requests: List[Dict[str, Any]], tenant: str, workspace: str
    ) -> StepResult:
        """
        Allocate resources to agents and tasks based on priority and availability.

        Args:
            allocation_requests: List of resource allocation requests
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with allocation results
        """
        try:
            if not allocation_requests:
                return StepResult.fail("Allocation requests are required")

            allocations = self._process_allocation_requests(
                allocation_requests, tenant, workspace
            )

            return StepResult.ok(
                data={
                    "allocations": allocations,
                    "total_allocated": len(allocations),
                    "resource_utilization": self._calculate_resource_utilization(
                        allocations
                    ),
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Resource allocation failed: {str(e)}")
            return StepResult.fail(f"Resource allocation failed: {str(e)}")

    def _process_allocation_requests(
        self, requests: List[Dict[str, Any]], tenant: str, workspace: str
    ) -> List[Dict[str, Any]]:
        """Process resource allocation requests."""
        allocations = []

        for request in requests:
            allocation = ResourceAllocation(
                agent_id=request.get("agent_id", "unknown"),
                cpu_cores=request.get("cpu_cores", 1),
                memory_gb=request.get("memory_gb", 1.0),
                gpu_units=request.get("gpu_units", 0),
                network_bandwidth_mbps=request.get("network_bandwidth_mbps", 100),
                storage_gb=request.get("storage_gb", 10),
                priority_level=request.get("priority_level", 5),
                allocated_at=self._get_current_timestamp(),
                expires_at=request.get("expires_at"),
            )

            allocations.append(
                {
                    "agent_id": allocation.agent_id,
                    "cpu_cores": allocation.cpu_cores,
                    "memory_gb": allocation.memory_gb,
                    "gpu_units": allocation.gpu_units,
                    "network_bandwidth_mbps": allocation.network_bandwidth_mbps,
                    "storage_gb": allocation.storage_gb,
                    "priority_level": allocation.priority_level,
                    "allocated_at": allocation.allocated_at,
                    "expires_at": allocation.expires_at,
                    "status": "allocated",
                }
            )

        return allocations

    def _calculate_resource_utilization(
        self, allocations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate resource utilization metrics."""
        total_cpu = sum(alloc.get("cpu_cores", 0) for alloc in allocations)
        total_memory = sum(alloc.get("memory_gb", 0) for alloc in allocations)
        total_gpu = sum(alloc.get("gpu_units", 0) for alloc in allocations)

        return {
            "total_cpu_cores": total_cpu,
            "total_memory_gb": total_memory,
            "total_gpu_units": total_gpu,
            "allocation_count": len(allocations),
            "average_priority": sum(
                alloc.get("priority_level", 0) for alloc in allocations
            )
            / len(allocations)
            if allocations
            else 0,
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat()


class EscalationManagementTool(BaseTool):
    """Tool for handling escalations and complex scenarios."""

    def _run(
        self,
        escalation_context: str,
        severity: str,
        affected_components: List[str],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """
        Handle escalations and complex scenarios with appropriate responses.

        Args:
            escalation_context: Description of the escalation
            severity: Severity level (low, medium, high, critical)
            affected_components: List of affected system components
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with escalation response
        """
        try:
            if not escalation_context or not severity:
                return StepResult.fail("Escalation context and severity are required")

            response = self._process_escalation(
                escalation_context, severity, affected_components, tenant, workspace
            )

            return StepResult.ok(
                data={
                    "escalation_response": response,
                    "severity": severity,
                    "affected_components": affected_components,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Escalation management failed: {str(e)}")
            return StepResult.fail(f"Escalation management failed: {str(e)}")

    def _process_escalation(
        self,
        context: str,
        severity: str,
        components: List[str],
        tenant: str,
        workspace: str,
    ) -> Dict[str, Any]:
        """Process escalation and determine response."""
        response_actions = []

        if severity == "critical":
            response_actions = [
                "Immediate system isolation",
                "Emergency resource allocation",
                "Stakeholder notification",
                "Incident response team activation",
            ]
        elif severity == "high":
            response_actions = [
                "Priority resource allocation",
                "Enhanced monitoring",
                "Team lead notification",
                "Contingency plan activation",
            ]
        elif severity == "medium":
            response_actions = [
                "Standard escalation procedures",
                "Additional monitoring",
                "Team notification",
                "Documentation update",
            ]
        else:  # low
            response_actions = [
                "Standard monitoring",
                "Log documentation",
                "Routine follow-up",
            ]

        return {
            "escalation_id": f"esc_{self._generate_escalation_id()}",
            "severity": severity,
            "context": context,
            "affected_components": components,
            "response_actions": response_actions,
            "estimated_resolution_time": self._estimate_resolution_time(severity),
            "escalation_timestamp": self._get_current_timestamp(),
            "assigned_team": self._assign_escalation_team(severity),
            "monitoring_requirements": self._define_monitoring_requirements(severity),
        }

    def _generate_escalation_id(self) -> str:
        """Generate unique escalation ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    def _estimate_resolution_time(self, severity: str) -> str:
        """Estimate resolution time based on severity."""
        time_estimates = {
            "critical": "15 minutes",
            "high": "1 hour",
            "medium": "4 hours",
            "low": "24 hours",
        }
        return time_estimates.get(severity, "TBD")

    def _assign_escalation_team(self, severity: str) -> str:
        """Assign appropriate team based on severity."""
        team_assignments = {
            "critical": "Emergency Response Team",
            "high": "Senior Operations Team",
            "medium": "Operations Team",
            "low": "Support Team",
        }
        return team_assignments.get(severity, "General Team")

    def _define_monitoring_requirements(self, severity: str) -> List[str]:
        """Define monitoring requirements based on severity."""
        if severity in ["critical", "high"]:
            return [
                "Real-time monitoring",
                "Automated alerts",
                "Performance metrics tracking",
                "Resource utilization monitoring",
            ]
        else:
            return ["Standard monitoring", "Periodic status checks"]

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat()


class ExecutiveSupervisorAgent:
    """Executive Supervisor Agent for strategic intelligence operations."""

    def __init__(self):
        """Initialize the Executive Supervisor Agent."""
        self.strategic_planning_tool = StrategicPlanningTool()
        self.resource_allocation_tool = ResourceAllocationTool()
        self.escalation_management_tool = EscalationManagementTool()

        # Note: CrewAI Agent initialization would go here in a real implementation
        # For now, we'll use the tools directly without CrewAI integration
        self.agent = None

    async def execute_strategic_planning(
        self,
        mission_context: str,
        objectives: List[Dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """Execute strategic planning for intelligence operations."""
        return self.strategic_planning_tool._run(
            mission_context, objectives, tenant, workspace
        )

    async def allocate_resources(
        self, allocation_requests: List[Dict[str, Any]], tenant: str, workspace: str
    ) -> StepResult:
        """Allocate resources to agents and tasks."""
        return self.resource_allocation_tool._run(
            allocation_requests, tenant, workspace
        )

    async def handle_escalation(
        self,
        escalation_context: str,
        severity: str,
        affected_components: List[str],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """Handle escalations and complex scenarios."""
        return self.escalation_management_tool._run(
            escalation_context, severity, affected_components, tenant, workspace
        )

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        return self.agent
