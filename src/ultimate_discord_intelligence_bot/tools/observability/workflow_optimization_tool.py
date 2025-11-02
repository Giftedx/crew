from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Any
from crewai.tools import BaseTool
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

@dataclass
class OptimizationRecommendation:
    """Represents an optimization recommendation for workflow improvement."""
    recommendation_id: str
    type: str
    title: str
    description: str
    impact_score: float
    effort_score: float
    estimated_improvement_percent: float
    affected_tasks: list[str]
    implementation_steps: list[str]
    priority: int

@dataclass
class BottleneckAnalysis:
    """Analysis of workflow bottlenecks and constraints."""
    bottleneck_id: str
    task_id: str
    bottleneck_type: str
    severity: str
    impact_description: str
    current_throughput: float
    potential_throughput: float
    improvement_opportunity: float
    recommended_actions: list[str]

@dataclass
class PerformanceMetrics:
    """Performance metrics for workflow optimization."""
    current_execution_time_minutes: float
    optimized_execution_time_minutes: float
    current_cost_usd: float
    optimized_cost_usd: float
    current_resource_utilization: float
    optimized_resource_utilization: float
    parallelization_efficiency: float
    bottleneck_count: int
    optimization_score: float

class WorkflowOptimizationTool(BaseTool):
    """
    Workflow optimization tool for finding parallelization opportunities and identifying bottlenecks.
    Analyzes workflow execution paths, identifies optimization opportunities, and provides
    actionable recommendations for improving efficiency, reducing costs, and enhancing performance.
    """
    name: str = 'workflow_optimization_tool'
    description: str = 'Optimizes workflow execution paths for efficiency and performance. Identifies parallelization opportunities, bottlenecks, and provides actionable recommendations for workflow improvement.'

    def _run(self, workflow_execution: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """
        Optimize workflow execution paths for efficiency and performance.

        Args:
            workflow_execution: Workflow execution data with tasks, assignments, and performance metrics
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization

        Returns:
            StepResult with workflow optimization data
        """
        metrics = get_metrics()
        start_time = time.time()
        try:
            logger.info(f"Optimizing workflow for tenant '{tenant}', workspace '{workspace}'")
            logger.debug(f'Workflow Execution: {workflow_execution}')
            if not workflow_execution:
                return StepResult.fail('Workflow execution data is required')
            if not tenant or not workspace:
                return StepResult.fail('Tenant and workspace are required')
            current_metrics = self._analyze_current_performance(workflow_execution)
            bottlenecks = self._identify_bottlenecks(workflow_execution)
            parallelization_opportunities = self._find_parallelization_opportunities(workflow_execution)
            recommendations = self._generate_optimization_recommendations(workflow_execution, bottlenecks, parallelization_opportunities)
            optimized_metrics = self._calculate_optimized_metrics(current_metrics, recommendations, bottlenecks)
            optimization_plan = self._create_optimization_plan(recommendations, bottlenecks)
            optimization_report = {'optimization_id': f'optimization_{int(time.time())}_{tenant}_{workspace}', 'workflow_id': workflow_execution.get('id', 'unknown'), 'current_metrics': current_metrics.__dict__, 'optimized_metrics': optimized_metrics.__dict__, 'bottlenecks': [bottleneck.__dict__ for bottleneck in bottlenecks], 'parallelization_opportunities': parallelization_opportunities, 'recommendations': [rec.__dict__ for rec in recommendations], 'optimization_plan': optimization_plan, 'created_at': self._get_current_timestamp(), 'tenant': tenant, 'workspace': workspace, 'status': 'optimized', 'version': '1.0'}
            logger.info('Workflow optimization completed successfully')
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'success'})
            return StepResult.success(optimization_report)
        except Exception as e:
            logger.error(f'Workflow optimization failed: {e!s}')
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'error'})
            return StepResult.fail(f'Workflow optimization failed: {e!s}')
        finally:
            metrics.histogram('tool_run_seconds', time.time() - start_time, labels={'tool': self.__class__.__name__})

    def _analyze_current_performance(self, workflow_execution: dict[str, Any]) -> PerformanceMetrics:
        """Analyze current workflow performance metrics."""
        tasks = workflow_execution.get('tasks', [])
        assignments = workflow_execution.get('assignments', [])
        current_execution_time = sum((task.get('estimated_duration_minutes', 60) for task in tasks))
        current_cost = sum((assignment.get('cost_usd', 0.1) for assignment in assignments))
        total_resources = len(assignments)
        utilized_resources = len([a for a in assignments if a.get('status') != 'pending'])
        current_resource_utilization = utilized_resources / total_resources if total_resources > 0 else 0.0
        parallel_tasks = len([t for t in tasks if t.get('can_parallelize', False)])
        total_tasks = len(tasks)
        parallelization_efficiency = parallel_tasks / total_tasks if total_tasks > 0 else 0.0
        return PerformanceMetrics(current_execution_time_minutes=current_execution_time, optimized_execution_time_minutes=current_execution_time, current_cost_usd=current_cost, optimized_cost_usd=current_cost, current_resource_utilization=current_resource_utilization, optimized_resource_utilization=current_resource_utilization, parallelization_efficiency=parallelization_efficiency, bottleneck_count=0, optimization_score=0.0)

    def _identify_bottlenecks(self, workflow_execution: dict[str, Any]) -> list[BottleneckAnalysis]:
        """Identify bottlenecks in the workflow execution."""
        bottlenecks = []
        tasks = workflow_execution.get('tasks', [])
        assignments = workflow_execution.get('assignments', [])
        for task in tasks:
            task_id = task.get('id', '')
            dependencies = task.get('dependencies', [])
            if len(dependencies) > 2:
                bottlenecks.append(BottleneckAnalysis(bottleneck_id=f'bottleneck_deps_{task_id}', task_id=task_id, bottleneck_type='dependency', severity='medium', impact_description=f'Task {task_id} has {len(dependencies)} dependencies causing delays', current_throughput=1.0 / len(dependencies), potential_throughput=1.0, improvement_opportunity=1.0 - 1.0 / len(dependencies), recommended_actions=['Review dependency structure', 'Consider parallel execution where possible', 'Optimize task sequencing']))
        agent_assignments = {}
        for assignment in assignments:
            agent_id = assignment.get('agent_id', 'unknown')
            if agent_id not in agent_assignments:
                agent_assignments[agent_id] = []
            agent_assignments[agent_id].append(assignment)
        for agent_id, agent_tasks in agent_assignments.items():
            if len(agent_tasks) > 3:
                bottlenecks.append(BottleneckAnalysis(bottleneck_id=f'bottleneck_resource_{agent_id}', task_id=agent_id, bottleneck_type='resource', severity='high', impact_description=f'Agent {agent_id} is overloaded with {len(agent_tasks)} tasks', current_throughput=1.0 / len(agent_tasks), potential_throughput=1.0, improvement_opportunity=1.0 - 1.0 / len(agent_tasks), recommended_actions=['Redistribute tasks to other agents', 'Scale up agent capacity', 'Implement load balancing']))
        for task in tasks:
            duration = task.get('estimated_duration_minutes', 60)
            if duration > 120:
                bottlenecks.append(BottleneckAnalysis(bottleneck_id=f'bottleneck_perf_{task.get('id', '')}', task_id=task.get('id', ''), bottleneck_type='performance', severity='medium', impact_description=f'Task {task.get('id', '')} takes {duration} minutes to complete', current_throughput=60.0 / duration, potential_throughput=1.0, improvement_opportunity=1.0 - 60.0 / duration, recommended_actions=['Optimize task implementation', 'Consider task splitting', 'Implement caching strategies']))
        return bottlenecks

    def _find_parallelization_opportunities(self, workflow_execution: dict[str, Any]) -> list[list[str]]:
        """Find opportunities for parallel execution."""
        opportunities = []
        tasks = workflow_execution.get('tasks', [])
        execution_order = workflow_execution.get('execution_order', [])
        current_phase = []
        completed_deps = set()
        for task_id in execution_order:
            task = next((t for t in tasks if t.get('id') == task_id), None)
            if not task:
                continue
            dependencies = set(task.get('dependencies', []))
            if dependencies.issubset(completed_deps):
                current_phase.append(task_id)
            else:
                if len(current_phase) > 1:
                    opportunities.append(current_phase)
                current_phase = [task_id]
        if len(current_phase) > 1:
            opportunities.append(current_phase)
        return opportunities

    def _generate_optimization_recommendations(self, workflow_execution: dict[str, Any], bottlenecks: list[BottleneckAnalysis], parallelization_opportunities: list[list[str]]) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        for i, opportunity in enumerate(parallelization_opportunities):
            if len(opportunity) > 1:
                recommendations.append(OptimizationRecommendation(recommendation_id=f'rec_parallel_{i}', type='parallelization', title=f'Parallelize {len(opportunity)} tasks', description=f'Execute tasks {', '.join(opportunity)} in parallel to reduce execution time', impact_score=0.8, effort_score=0.3, estimated_improvement_percent=50.0, affected_tasks=opportunity, implementation_steps=['Identify shared resources', 'Implement parallel execution logic', 'Add synchronization mechanisms', 'Test parallel execution'], priority=3))
        for bottleneck in bottlenecks:
            if bottleneck.severity in ['high', 'critical']:
                recommendations.append(OptimizationRecommendation(recommendation_id=f'rec_bottleneck_{bottleneck.bottleneck_id}', type='bottleneck_removal', title=f'Remove {bottleneck.bottleneck_type} bottleneck', description=bottleneck.impact_description, impact_score=0.9 if bottleneck.severity == 'critical' else 0.7, effort_score=0.6, estimated_improvement_percent=bottleneck.improvement_opportunity * 100, affected_tasks=[bottleneck.task_id], implementation_steps=bottleneck.recommended_actions, priority=4 if bottleneck.severity == 'critical' else 3))
        assignments = workflow_execution.get('assignments', [])
        agent_utilization = {}
        for assignment in assignments:
            agent_id = assignment.get('agent_id', 'unknown')
            agent_utilization[agent_id] = agent_utilization.get(agent_id, 0) + 1
        for agent_id, task_count in agent_utilization.items():
            if task_count > 2:
                recommendations.append(OptimizationRecommendation(recommendation_id=f'rec_resource_{agent_id}', type='resource_optimization', title=f'Optimize resource allocation for {agent_id}', description=f'Agent {agent_id} is handling {task_count} tasks, consider load balancing', impact_score=0.6, effort_score=0.4, estimated_improvement_percent=30.0, affected_tasks=[a.get('task_id') for a in assignments if a.get('agent_id') == agent_id], implementation_steps=['Analyze agent capacity', 'Redistribute tasks', 'Implement dynamic load balancing', 'Monitor performance improvements'], priority=2))
        total_cost = sum((a.get('cost_usd', 0.1) for a in assignments))
        if total_cost > 1.0:
            recommendations.append(OptimizationRecommendation(recommendation_id='rec_cost_reduction', type='cost_reduction', title='Implement cost optimization strategies', description=f'Current workflow cost is ${total_cost:.2f}, implement cost reduction measures', impact_score=0.7, effort_score=0.5, estimated_improvement_percent=25.0, affected_tasks=[a.get('task_id') for a in assignments], implementation_steps=['Review task resource requirements', 'Implement cost-effective alternatives', 'Optimize agent selection', 'Monitor cost metrics'], priority=2))
        return recommendations

    def _calculate_optimized_metrics(self, current_metrics: PerformanceMetrics, recommendations: list[OptimizationRecommendation], bottlenecks: list[BottleneckAnalysis]) -> PerformanceMetrics:
        """Calculate optimized performance metrics based on recommendations."""
        parallelization_improvement = 0.0
        for rec in recommendations:
            if rec.type == 'parallelization':
                parallelization_improvement += rec.estimated_improvement_percent
        bottleneck_improvement = 0.0
        for bottleneck in bottlenecks:
            if bottleneck.severity in ['high', 'critical']:
                bottleneck_improvement += bottleneck.improvement_opportunity * 100
        cost_improvement = 0.0
        for rec in recommendations:
            if rec.type == 'cost_reduction':
                cost_improvement += rec.estimated_improvement_percent
        optimized_execution_time = current_metrics.current_execution_time_minutes * (1 - parallelization_improvement / 100)
        optimized_cost = current_metrics.current_cost_usd * (1 - cost_improvement / 100)
        optimized_resource_utilization = min(1.0, current_metrics.current_resource_utilization * 1.2)
        time_improvement = (current_metrics.current_execution_time_minutes - optimized_execution_time) / current_metrics.current_execution_time_minutes
        cost_improvement_ratio = (current_metrics.current_cost_usd - optimized_cost) / current_metrics.current_cost_usd
        resource_improvement = (optimized_resource_utilization - current_metrics.current_resource_utilization) / current_metrics.current_resource_utilization
        optimization_score = time_improvement * 0.4 + cost_improvement_ratio * 0.3 + resource_improvement * 0.3
        return PerformanceMetrics(current_execution_time_minutes=current_metrics.current_execution_time_minutes, optimized_execution_time_minutes=optimized_execution_time, current_cost_usd=current_metrics.current_cost_usd, optimized_cost_usd=optimized_cost, current_resource_utilization=current_metrics.current_resource_utilization, optimized_resource_utilization=optimized_resource_utilization, parallelization_efficiency=min(1.0, current_metrics.parallelization_efficiency + 0.3), bottleneck_count=len(bottlenecks), optimization_score=optimization_score)

    def _create_optimization_plan(self, recommendations: list[OptimizationRecommendation], bottlenecks: list[BottleneckAnalysis]) -> dict[str, Any]:
        """Create an implementation plan for optimizations."""
        sorted_recommendations = sorted(recommendations, key=lambda r: (r.priority, r.impact_score), reverse=True)
        immediate_actions = [r for r in sorted_recommendations if r.priority >= 4]
        short_term_actions = [r for r in sorted_recommendations if r.priority == 3]
        long_term_actions = [r for r in sorted_recommendations if r.priority <= 2]
        return {'implementation_phases': {'immediate': {'actions': [r.__dict__ for r in immediate_actions], 'estimated_effort_hours': sum((r.effort_score * 8 for r in immediate_actions)), 'expected_impact': sum((r.impact_score for r in immediate_actions)) / len(immediate_actions) if immediate_actions else 0.0}, 'short_term': {'actions': [r.__dict__ for r in short_term_actions], 'estimated_effort_hours': sum((r.effort_score * 16 for r in short_term_actions)), 'expected_impact': sum((r.impact_score for r in short_term_actions)) / len(short_term_actions) if short_term_actions else 0.0}, 'long_term': {'actions': [r.__dict__ for r in long_term_actions], 'estimated_effort_hours': sum((r.effort_score * 32 for r in long_term_actions)), 'expected_impact': sum((r.impact_score for r in long_term_actions)) / len(long_term_actions) if long_term_actions else 0.0}}, 'critical_bottlenecks': [b.__dict__ for b in bottlenecks if b.severity in ['high', 'critical']], 'success_metrics': {'target_execution_time_reduction': 30.0, 'target_cost_reduction': 25.0, 'target_resource_utilization': 0.85, 'target_optimization_score': 0.8}, 'monitoring_plan': ['Track execution time improvements', 'Monitor cost reduction metrics', 'Measure resource utilization', 'Validate optimization effectiveness']}

    def _get_current_timestamp(self) -> float:
        """Returns the current UTC timestamp."""
        return time.time()