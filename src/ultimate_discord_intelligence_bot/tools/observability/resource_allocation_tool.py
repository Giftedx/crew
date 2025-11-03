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
class ResourcePool:
    """Represents a pool of available resources."""

    cpu_units: int
    memory_mb: int
    gpu_hours: float
    storage_gb: int
    network_bandwidth_mbps: int
    reserved_resources: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAllocation:
    """Represents a resource allocation for a specific task or agent."""

    allocation_id: str
    task_id: str
    agent_id: str
    cpu_units: int
    memory_mb: int
    gpu_hours: float
    storage_gb: int
    network_bandwidth_mbps: int
    priority: int
    estimated_duration_hours: float
    allocated_at: float
    status: str = "allocated"


@dataclass
class LoadBalancingMetrics:
    """Metrics for load balancing across agents."""

    agent_id: str
    current_load: float
    cpu_utilization: float
    memory_utilization: float
    active_tasks: int
    queued_tasks: int
    average_task_duration_hours: float


class ResourceAllocationTool(BaseTool):
    """
    Resource allocation tool for dynamic resource management with load balancing.
    Handles CPU, memory, GPU, storage, and network resource allocation across agents
    with intelligent load balancing and priority-based assignment.
    """

    name: str = "resource_allocation_tool"
    description: str = "Manages dynamic resource allocation with intelligent load balancing. Allocates CPU, memory, GPU, storage, and network resources across agents based on task requirements, current load, and priority levels."

    def _run(
        self, plan: dict[str, Any], available_resources: dict[str, Any], tenant: str, workspace: str
    ) -> StepResult:
        """
        Allocate resources based on the strategic plan and available resources.

        Args:
            plan: Strategic plan containing objectives and execution phases
            available_resources: Available resource pool (CPU, memory, GPU, etc.)
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization

        Returns:
            StepResult with resource allocation data
        """
        metrics = get_metrics()
        start_time = time.time()
        try:
            logger.info(f"Allocating resources for tenant '{tenant}', workspace '{workspace}'")
            logger.debug(f"Plan: {plan}")
            logger.debug(f"Available Resources: {available_resources}")
            if not plan or not available_resources:
                return StepResult.fail("Plan and available resources are required")
            if not tenant or not workspace:
                return StepResult.fail("Tenant and workspace are required")
            resource_pool = self._create_resource_pool(available_resources)
            plan_requirements = self._analyze_plan_requirements(plan)
            load_metrics = self._analyze_load_balancing(plan_requirements)
            allocations = self._allocate_resources_with_balancing(plan_requirements, resource_pool, load_metrics)
            allocation_summary = self._calculate_allocation_summary(allocations, resource_pool)
            allocation_report = {
                "allocation_id": f"alloc_{int(time.time())}_{tenant}_{workspace}",
                "plan_id": plan.get("plan_id", "unknown"),
                "allocations": [alloc.__dict__ for alloc in allocations],
                "allocation_summary": allocation_summary,
                "load_balancing_metrics": [metric.__dict__ for metric in load_metrics],
                "resource_utilization": self._calculate_resource_utilization(allocations, resource_pool),
                "created_at": self._get_current_timestamp(),
                "tenant": tenant,
                "workspace": workspace,
                "status": "allocated",
                "version": "1.0",
            }
            logger.info("Resource allocation completed successfully")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "success"})
            return StepResult.success(allocation_report)
        except Exception as e:
            logger.error(f"Resource allocation failed: {e!s}")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "error"})
            return StepResult.fail(f"Resource allocation failed: {e!s}")
        finally:
            metrics.histogram("tool_run_seconds", time.time() - start_time, labels={"tool": self.__class__.__name__})

    def _create_resource_pool(self, available_resources: dict[str, Any]) -> ResourcePool:
        """Create resource pool from available resources."""
        return ResourcePool(
            cpu_units=available_resources.get("cpu_units", 100),
            memory_mb=available_resources.get("memory_mb", 8192),
            gpu_hours=available_resources.get("gpu_hours", 10.0),
            storage_gb=available_resources.get("storage_gb", 1000),
            network_bandwidth_mbps=available_resources.get("network_bandwidth_mbps", 1000),
        )

    def _analyze_plan_requirements(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze plan to determine resource requirements for each objective."""
        requirements = []
        objectives = plan.get("objectives", [])
        plan.get("execution_plan", {})
        for objective in objectives:
            req = self._estimate_objective_requirements(objective)
            requirements.append(req)
        return requirements

    def _estimate_objective_requirements(self, objective: dict[str, Any]) -> dict[str, Any]:
        """Estimate resource requirements for a specific objective."""
        title = objective.get("title", "").lower()
        description = objective.get("description", "").lower()
        cpu_units = 10
        memory_mb = 512
        gpu_hours = 0.0
        storage_gb = 1
        network_bandwidth_mbps = 100
        if "analysis" in title or "analysis" in description:
            cpu_units = 20
            memory_mb = 1024
            gpu_hours = 0.5
        if "real-time" in title or "live" in title or "stream" in title:
            cpu_units = 30
            memory_mb = 2048
            network_bandwidth_mbps = 500
        if "transcription" in title or "audio" in title or "video" in title:
            cpu_units = 25
            memory_mb = 1536
            storage_gb = 5
        if "fact-check" in title or "verification" in title:
            cpu_units = 15
            memory_mb = 768
            network_bandwidth_mbps = 200
        return {
            "objective_id": objective.get("id", "unknown"),
            "title": objective.get("title", ""),
            "cpu_units": cpu_units,
            "memory_mb": memory_mb,
            "gpu_hours": gpu_hours,
            "storage_gb": storage_gb,
            "network_bandwidth_mbps": network_bandwidth_mbps,
            "priority": objective.get("priority", 1),
            "estimated_duration_hours": 1.0,
        }

    def _analyze_load_balancing(self, requirements: list[dict[str, Any]]) -> list[LoadBalancingMetrics]:
        """Analyze current load balancing across agents."""
        agents = ["agent_ingestion", "agent_analysis", "agent_verification", "agent_reporting"]
        metrics = []
        for i, agent_id in enumerate(agents):
            base_load = 0.2 + i * 0.1
            metrics.append(
                LoadBalancingMetrics(
                    agent_id=agent_id,
                    current_load=min(base_load, 0.9),
                    cpu_utilization=base_load * 0.8,
                    memory_utilization=base_load * 0.7,
                    active_tasks=max(1, int(base_load * 10)),
                    queued_tasks=max(0, int(base_load * 5)),
                    average_task_duration_hours=1.0 + i * 0.2,
                )
            )
        return metrics

    def _allocate_resources_with_balancing(
        self, requirements: list[dict[str, Any]], resource_pool: ResourcePool, load_metrics: list[LoadBalancingMetrics]
    ) -> list[ResourceAllocation]:
        """Allocate resources with intelligent load balancing."""
        allocations = []
        current_timestamp = self._get_current_timestamp()
        sorted_requirements = sorted(requirements, key=lambda x: x["priority"], reverse=True)
        for req in sorted_requirements:
            best_agent = self._select_best_agent(req, load_metrics)
            if self._check_resource_availability(req, resource_pool):
                allocation = ResourceAllocation(
                    allocation_id=f"alloc_{req['objective_id']}_{int(current_timestamp)}",
                    task_id=req["objective_id"],
                    agent_id=best_agent,
                    cpu_units=req["cpu_units"],
                    memory_mb=req["memory_mb"],
                    gpu_hours=req["gpu_hours"],
                    storage_gb=req["storage_gb"],
                    network_bandwidth_mbps=req["network_bandwidth_mbps"],
                    priority=req["priority"],
                    estimated_duration_hours=req["estimated_duration_hours"],
                    allocated_at=current_timestamp,
                )
                allocations.append(allocation)
                self._update_resource_pool(allocation, resource_pool)
                self._update_load_metrics(allocation, load_metrics)
            else:
                logger.warning(f"Insufficient resources for objective {req['objective_id']}")
        return allocations

    def _select_best_agent(self, requirement: dict[str, Any], load_metrics: list[LoadBalancingMetrics]) -> str:
        """Select the best agent based on load balancing criteria."""
        suitable_agents = [metric for metric in load_metrics if metric.current_load < 0.8]
        if not suitable_agents:
            suitable_agents = load_metrics
        best_agent = min(suitable_agents, key=lambda x: x.current_load)
        return best_agent.agent_id

    def _check_resource_availability(self, requirement: dict[str, Any], resource_pool: ResourcePool) -> bool:
        """Check if required resources are available in the pool."""
        return (
            requirement["cpu_units"] <= resource_pool.cpu_units
            and requirement["memory_mb"] <= resource_pool.memory_mb
            and (requirement["gpu_hours"] <= resource_pool.gpu_hours)
            and (requirement["storage_gb"] <= resource_pool.storage_gb)
            and (requirement["network_bandwidth_mbps"] <= resource_pool.network_bandwidth_mbps)
        )

    def _update_resource_pool(self, allocation: ResourceAllocation, resource_pool: ResourcePool):
        """Update resource pool after allocation."""
        resource_pool.cpu_units -= allocation.cpu_units
        resource_pool.memory_mb -= allocation.memory_mb
        resource_pool.gpu_hours -= allocation.gpu_hours
        resource_pool.storage_gb -= allocation.storage_gb
        resource_pool.network_bandwidth_mbps -= allocation.network_bandwidth_mbps

    def _update_load_metrics(self, allocation: ResourceAllocation, load_metrics: list[LoadBalancingMetrics]):
        """Update load metrics after allocation."""
        for metric in load_metrics:
            if metric.agent_id == allocation.agent_id:
                load_increase = (
                    allocation.cpu_units / 100.0 * 0.3
                    + allocation.memory_mb / 8192.0 * 0.2
                    + allocation.gpu_hours / 10.0 * 0.5
                )
                metric.current_load = min(1.0, metric.current_load + load_increase)
                metric.active_tasks += 1
                break

    def _calculate_allocation_summary(
        self, allocations: list[ResourceAllocation], resource_pool: ResourcePool
    ) -> dict[str, Any]:
        """Calculate summary of resource allocations."""
        total_allocated = {
            "cpu_units": sum(alloc.cpu_units for alloc in allocations),
            "memory_mb": sum(alloc.memory_mb for alloc in allocations),
            "gpu_hours": sum(alloc.gpu_hours for alloc in allocations),
            "storage_gb": sum(alloc.storage_gb for alloc in allocations),
            "network_bandwidth_mbps": sum(alloc.network_bandwidth_mbps for alloc in allocations),
        }
        return {
            "total_allocations": len(allocations),
            "total_allocated_resources": total_allocated,
            "remaining_resources": {
                "cpu_units": resource_pool.cpu_units,
                "memory_mb": resource_pool.memory_mb,
                "gpu_hours": resource_pool.gpu_hours,
                "storage_gb": resource_pool.storage_gb,
                "network_bandwidth_mbps": resource_pool.network_bandwidth_mbps,
            },
            "utilization_percentage": {
                "cpu_units": total_allocated["cpu_units"]
                / (total_allocated["cpu_units"] + resource_pool.cpu_units)
                * 100,
                "memory_mb": total_allocated["memory_mb"]
                / (total_allocated["memory_mb"] + resource_pool.memory_mb)
                * 100,
                "gpu_hours": total_allocated["gpu_hours"]
                / (total_allocated["gpu_hours"] + resource_pool.gpu_hours)
                * 100,
            },
        }

    def _calculate_resource_utilization(
        self, allocations: list[ResourceAllocation], resource_pool: ResourcePool
    ) -> dict[str, Any]:
        """Calculate detailed resource utilization metrics."""
        agent_utilization = {}
        for alloc in allocations:
            if alloc.agent_id not in agent_utilization:
                agent_utilization[alloc.agent_id] = {
                    "cpu_units": 0,
                    "memory_mb": 0,
                    "gpu_hours": 0,
                    "storage_gb": 0,
                    "network_bandwidth_mbps": 0,
                    "task_count": 0,
                }
            agent_utilization[alloc.agent_id]["cpu_units"] += alloc.cpu_units
            agent_utilization[alloc.agent_id]["memory_mb"] += alloc.memory_mb
            agent_utilization[alloc.agent_id]["gpu_hours"] += alloc.gpu_hours
            agent_utilization[alloc.agent_id]["storage_gb"] += alloc.storage_gb
            agent_utilization[alloc.agent_id]["network_bandwidth_mbps"] += alloc.network_bandwidth_mbps
            agent_utilization[alloc.agent_id]["task_count"] += 1
        return {
            "by_agent": agent_utilization,
            "overall_efficiency": self._calculate_overall_efficiency(allocations),
            "load_distribution": self._calculate_load_distribution(allocations),
        }

    def _calculate_overall_efficiency(self, allocations: list[ResourceAllocation]) -> float:
        """Calculate overall resource allocation efficiency."""
        if not allocations:
            return 0.0
        high_priority_count = sum(1 for alloc in allocations if alloc.priority >= 3)
        total_count = len(allocations)
        return high_priority_count / total_count if total_count > 0 else 0.0

    def _calculate_load_distribution(self, allocations: list[ResourceAllocation]) -> dict[str, Any]:
        """Calculate load distribution across agents."""
        agent_loads = {}
        for alloc in allocations:
            if alloc.agent_id not in agent_loads:
                agent_loads[alloc.agent_id] = 0
            agent_loads[alloc.agent_id] += 1
        if not agent_loads:
            return {"balance_score": 1.0, "distribution": {}}
        loads = list(agent_loads.values())
        max_load = max(loads)
        min_load = min(loads)
        balance_score = 1.0 - (max_load - min_load) / max_load if max_load > 0 else 1.0
        return {"balance_score": balance_score, "distribution": agent_loads, "max_load": max_load, "min_load": min_load}

    def _get_current_timestamp(self) -> float:
        """Returns the current UTC timestamp."""
        return time.time()
