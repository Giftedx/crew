from __future__ import annotations
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any
from crewai.tools import BaseTool
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""
    task_id: str
    depends_on: list[str]
    dependency_type: str = 'hard'
    priority: int = 1
    estimated_delay_minutes: int = 0

@dataclass
class ExecutionPhase:
    """Represents a phase of execution with parallel tasks."""
    phase_id: str
    phase_number: int
    tasks: list[str]
    estimated_duration_minutes: int
    can_parallelize: bool = True
    critical_path: bool = False

@dataclass
class DependencyResolution:
    """Result of dependency resolution with execution plan."""
    execution_order: list[str]
    execution_phases: list[ExecutionPhase]
    circular_dependencies: list[list[str]]
    missing_dependencies: list[str]
    critical_path: list[str]
    estimated_total_duration_minutes: int
    parallelization_opportunities: list[list[str]]

class DependencyResolverTool(BaseTool):
    """
    Dependency resolver tool for managing inter-agent dependencies with topological sort.
    Resolves task dependencies, detects circular dependencies, creates execution phases,
    and identifies parallelization opportunities for optimal workflow execution.
    """
    name: str = 'dependency_resolver_tool'
    description: str = 'Resolves task dependencies with topological sort and circular dependency detection. Creates execution phases, identifies parallelization opportunities, and generates optimal execution order for complex workflows.'

    def _run(self, workflow_plan: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """
        Resolve dependencies and establish execution order for workflow tasks.

        Args:
            workflow_plan: Workflow plan containing tasks and their dependencies
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization

        Returns:
            StepResult with dependency resolution data
        """
        metrics = get_metrics()
        start_time = time.time()
        try:
            logger.info(f"Resolving dependencies for tenant '{tenant}', workspace '{workspace}'")
            logger.debug(f'Workflow Plan: {workflow_plan}')
            if not workflow_plan:
                return StepResult.fail('Workflow plan is required')
            if not tenant or not workspace:
                return StepResult.fail('Tenant and workspace are required')
            tasks = self._parse_workflow_tasks(workflow_plan)
            dependencies = self._extract_dependencies(tasks)
            dependency_graph = self._build_dependency_graph(dependencies)
            circular_deps = self._detect_circular_dependencies(dependency_graph)
            execution_order = self._topological_sort(dependency_graph)
            execution_phases = self._create_execution_phases(execution_order, dependencies)
            critical_path = self._identify_critical_path(execution_phases, tasks)
            parallelization_opportunities = self._find_parallelization_opportunities(execution_phases)
            total_duration = self._calculate_total_duration(execution_phases)
            resolution = DependencyResolution(execution_order=execution_order, execution_phases=[phase.__dict__ for phase in execution_phases], circular_dependencies=circular_deps, missing_dependencies=self._find_missing_dependencies(dependencies, tasks), critical_path=critical_path, estimated_total_duration_minutes=total_duration, parallelization_opportunities=parallelization_opportunities)
            resolution_report = {'resolution_id': f'resolution_{int(time.time())}_{tenant}_{workspace}', 'workflow_id': workflow_plan.get('id', 'unknown'), 'resolution': resolution.__dict__, 'dependency_graph': self._serialize_dependency_graph(dependency_graph), 'resolution_metrics': self._calculate_resolution_metrics(resolution), 'created_at': self._get_current_timestamp(), 'tenant': tenant, 'workspace': workspace, 'status': 'resolved' if not circular_deps else 'partial', 'version': '1.0'}
            logger.info('Dependency resolution completed successfully')
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'success'})
            return StepResult.success(resolution_report)
        except Exception as e:
            logger.error(f'Dependency resolution failed: {e!s}')
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'error'})
            return StepResult.fail(f'Dependency resolution failed: {e!s}')
        finally:
            metrics.histogram('tool_run_seconds', time.time() - start_time, labels={'tool': self.__class__.__name__})

    def _parse_workflow_tasks(self, workflow_plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse workflow plan to extract task information."""
        return workflow_plan.get('tasks', [])

    def _extract_dependencies(self, tasks: list[dict[str, Any]]) -> list[TaskDependency]:
        """Extract dependency information from tasks."""
        dependencies = []
        for task in tasks:
            task_id = task.get('id', f'task_{len(dependencies)}')
            depends_on = task.get('dependencies', [])
            dependency_type = task.get('dependency_type', 'hard')
            priority = task.get('priority', 1)
            estimated_delay = task.get('estimated_delay_minutes', 0)
            dependency = TaskDependency(task_id=task_id, depends_on=depends_on, dependency_type=dependency_type, priority=priority, estimated_delay_minutes=estimated_delay)
            dependencies.append(dependency)
        return dependencies

    def _build_dependency_graph(self, dependencies: list[TaskDependency]) -> dict[str, set[str]]:
        """Build dependency graph from task dependencies."""
        graph = defaultdict(set)
        for dep in dependencies:
            task_id = dep.task_id
            for dependent_task in dep.depends_on:
                graph[dependent_task].add(task_id)
        return dict(graph)

    def _detect_circular_dependencies(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        circular_deps = []

        def dfs(node: str, path: list[str]) -> None:
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = [*path[cycle_start:], node]
                circular_deps.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, set()):
                dfs(neighbor, path.copy())
            rec_stack.remove(node)
        for node in graph:
            if node not in visited:
                dfs(node, [])
        return circular_deps

    def _topological_sort(self, graph: dict[str, set[str]]) -> list[str]:
        """Perform topological sort to determine execution order."""
        in_degree = defaultdict(int)
        all_nodes = set()
        for node in graph:
            all_nodes.add(node)
            for neighbor in graph[node]:
                all_nodes.add(neighbor)
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(result) != len(all_nodes):
            logger.warning('Graph contains cycles, topological sort incomplete')
            remaining = all_nodes - set(result)
            result.extend(remaining)
        return result

    def _create_execution_phases(self, execution_order: list[str], dependencies: list[TaskDependency]) -> list[ExecutionPhase]:
        """Create execution phases based on dependency resolution."""
        phases = []
        current_phase = []
        completed_tasks: set[str] = set()
        phase_number = 1
        dep_map = {dep.task_id: set(dep.depends_on) for dep in dependencies}
        for task_id in execution_order:
            task_deps = dep_map.get(task_id, set())
            if task_deps.issubset(completed_tasks):
                current_phase.append(task_id)
            elif current_phase:
                phase = ExecutionPhase(phase_id=f'phase_{phase_number}', phase_number=phase_number, tasks=current_phase, estimated_duration_minutes=self._estimate_phase_duration(current_phase, dependencies), can_parallelize=len(current_phase) > 1)
                phases.append(phase)
                completed_tasks.update(current_phase)
                phase_number += 1
                current_phase = [task_id]
            else:
                current_phase = [task_id]
        if current_phase:
            phase = ExecutionPhase(phase_id=f'phase_{phase_number}', phase_number=phase_number, tasks=current_phase, estimated_duration_minutes=self._estimate_phase_duration(current_phase, dependencies), can_parallelize=len(current_phase) > 1)
            phases.append(phase)
            completed_tasks.update(current_phase)
        return phases

    def _estimate_phase_duration(self, tasks: list[str], dependencies: list[TaskDependency]) -> int:
        """Estimate duration for a phase based on its tasks."""
        base_duration = len(tasks) * 60
        if len(tasks) > 1:
            base_duration = int(base_duration * 0.5)
        return base_duration

    def _identify_critical_path(self, phases: list[ExecutionPhase], tasks: list[dict[str, Any]]) -> list[str]:
        """Identify critical path through the execution phases."""
        critical_path = []
        for phase in phases:
            if phase.critical_path or len(phase.tasks) == 1:
                critical_path.extend(phase.tasks)
            else:
                phase_tasks = [task for task in tasks if task.get('id') in phase.tasks]
                if phase_tasks:
                    highest_priority_task = max(phase_tasks, key=lambda t: t.get('priority', 1))
                    critical_path.append(highest_priority_task.get('id'))
        return critical_path

    def _find_parallelization_opportunities(self, phases: list[ExecutionPhase]) -> list[list[str]]:
        """Find opportunities for parallel execution."""
        opportunities = []
        for phase in phases:
            if phase.can_parallelize and len(phase.tasks) > 1:
                opportunities.append(phase.tasks)
        return opportunities

    def _calculate_total_duration(self, phases: list[ExecutionPhase]) -> int:
        """Calculate total estimated duration for the workflow."""
        return sum((phase.estimated_duration_minutes for phase in phases))

    def _find_missing_dependencies(self, dependencies: list[TaskDependency], tasks: list[dict[str, Any]]) -> list[str]:
        """Find dependencies that reference non-existent tasks."""
        task_ids = {task.get('id') for task in tasks}
        missing_deps = []
        for dep in dependencies:
            for dependent_task in dep.depends_on:
                if dependent_task not in task_ids:
                    missing_deps.append(f'{dep.task_id} -> {dependent_task}')
        return missing_deps

    def _serialize_dependency_graph(self, graph: dict[str, set[str]]) -> dict[str, list[str]]:
        """Serialize dependency graph for JSON output."""
        return {node: list(dependencies) for node, dependencies in graph.items()}

    def _calculate_resolution_metrics(self, resolution: DependencyResolution) -> dict[str, Any]:
        """Calculate metrics for the dependency resolution."""
        total_tasks = len(resolution.execution_order)
        total_phases = len(resolution.execution_phases)
        parallel_phases = sum((1 for phase in resolution.execution_phases if phase.get('can_parallelize', False)))
        return {'total_tasks': total_tasks, 'total_phases': total_phases, 'parallel_phases': parallel_phases, 'parallelization_ratio': parallel_phases / total_phases if total_phases > 0 else 0.0, 'circular_dependencies_count': len(resolution.circular_dependencies), 'missing_dependencies_count': len(resolution.missing_dependencies), 'critical_path_length': len(resolution.critical_path), 'estimated_efficiency': self._calculate_efficiency_metric(resolution)}

    def _calculate_efficiency_metric(self, resolution: DependencyResolution) -> float:
        """Calculate efficiency metric for the resolution."""
        if not resolution.execution_phases:
            return 0.0
        parallelization_score = len(resolution.parallelization_opportunities) / len(resolution.execution_phases)
        critical_path_score = 1.0 - len(resolution.critical_path) / len(resolution.execution_order)
        penalty = 0.0
        if resolution.circular_dependencies:
            penalty += 0.3
        if resolution.missing_dependencies:
            penalty += 0.2
        efficiency = parallelization_score * 0.6 + critical_path_score * 0.4 - penalty
        return max(0.0, min(1.0, efficiency))

    def _get_current_timestamp(self) -> float:
        """Returns the current UTC timestamp."""
        return time.time()