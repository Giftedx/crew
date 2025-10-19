"""Advanced parallel execution engine for CrewAI task orchestration.

This module provides sophisticated parallel execution capabilities that can
identify independent tasks and execute them concurrently, significantly
improving performance for complex analysis workflows.
"""

import logging
from typing import Any

from crewai import Crew, Task

logger = logging.getLogger(__name__)


class TaskDependencyGraph:
    """Represents task dependencies and enables parallel execution analysis."""

    def __init__(self, tasks: list[Task]):
        """Initialize the dependency graph with tasks.

        Args:
            tasks: List of CrewAI tasks to analyze
        """
        self.tasks = tasks
        self.dependencies: dict[str, set[str]] = {}
        self.dependents: dict[str, set[str]] = {}
        self._build_dependency_graph()

    def _build_dependency_graph(self):
        """Build the dependency graph from task contexts."""
        # Initialize dependency maps
        for task in self.tasks:
            task_id = self._get_task_id(task)
            self.dependencies[task_id] = set()
            self.dependents[task_id] = set()

        # Build dependency relationships
        for task in self.tasks:
            task_id = self._get_task_id(task)
            if hasattr(task, "context") and task.context:
                for context_task in task.context:
                    context_id = self._get_task_id(context_task)
                    self.dependencies[task_id].add(context_id)
                    self.dependents[context_id].add(task_id)

    def _get_task_id(self, task: Task) -> str:
        """Get a unique identifier for a task."""
        # Use agent role + description hash as task ID
        agent_role = getattr(task.agent, "role", "unknown")
        desc_hash = hash(task.description)
        return f"{agent_role}_{desc_hash}"

    def get_execution_levels(self) -> list[list[str]]:
        """Get tasks grouped by execution level (parallel execution groups).

        Returns:
            List of task ID groups that can execute in parallel
        """
        levels = []
        remaining_tasks = set(self.dependencies.keys())
        completed_tasks = set()

        while remaining_tasks:
            # Find tasks with no pending dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                if self.dependencies[task_id].issubset(completed_tasks):
                    ready_tasks.append(task_id)

            if not ready_tasks:
                # Handle circular dependencies by taking the first remaining task
                ready_tasks = [next(iter(remaining_tasks))]
                logger.warning(f"Circular dependency detected, forcing execution of {ready_tasks[0]}")

            levels.append(ready_tasks)
            completed_tasks.update(ready_tasks)
            remaining_tasks -= set(ready_tasks)

        return levels

    def can_execute_parallel(self, task_ids: list[str]) -> bool:
        """Check if a group of tasks can execute in parallel.

        Args:
            task_ids: List of task IDs to check

        Returns:
            True if tasks can execute in parallel
        """
        for task_id in task_ids:
            for other_task_id in task_ids:
                if task_id != other_task_id:
                    # Check if tasks have dependencies on each other
                    if task_id in self.dependencies[other_task_id] or other_task_id in self.dependencies[task_id]:
                        return False
        return True


class ParallelExecutionEngine:
    """Advanced parallel execution engine for CrewAI workflows."""

    def __init__(self, max_concurrent_tasks: int = 3):
        """Initialize the parallel execution engine.

        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(__name__)

    def analyze_parallelization_potential(self, tasks: list[Task]) -> dict[str, Any]:
        """Analyze the parallelization potential of a task set.

        Args:
            tasks: List of CrewAI tasks to analyze

        Returns:
            Dictionary with parallelization analysis results
        """
        graph = TaskDependencyGraph(tasks)
        execution_levels = graph.get_execution_levels()

        # Calculate metrics
        total_tasks = len(tasks)
        parallel_levels = len(execution_levels)
        max_parallel_tasks = max(len(level) for level in execution_levels) if execution_levels else 0

        # Estimate time savings
        sequential_time = total_tasks  # Assume 1 unit per task
        parallel_time = parallel_levels  # Time = number of levels
        time_savings_percent = ((sequential_time - parallel_time) / sequential_time) * 100 if sequential_time > 0 else 0

        return {
            "total_tasks": total_tasks,
            "execution_levels": parallel_levels,
            "max_parallel_tasks": max_parallel_tasks,
            "estimated_time_savings_percent": time_savings_percent,
            "parallelization_feasible": max_parallel_tasks > 1,
            "execution_level_breakdown": [
                {"level": i, "tasks": len(level), "task_ids": level} for i, level in enumerate(execution_levels)
            ],
        }

    def optimize_task_execution_order(self, tasks: list[Task]) -> list[Task]:
        """Optimize task execution order for maximum parallelization.

        Args:
            tasks: List of CrewAI tasks to optimize

        Returns:
            List of tasks in optimized execution order
        """
        graph = TaskDependencyGraph(tasks)
        execution_levels = graph.get_execution_levels()

        # Reorder tasks by execution level
        optimized_tasks = []
        task_id_to_task = {graph._get_task_id(task): task for task in tasks}

        for level in execution_levels:
            level_tasks = [task_id_to_task[task_id] for task_id in level]
            # Sort by agent type for better resource utilization
            level_tasks.sort(key=lambda t: getattr(t.agent, "role", ""))
            optimized_tasks.extend(level_tasks)

        return optimized_tasks

    def create_parallel_crew_configuration(self, tasks: list[Task], base_crew_config: dict[str, Any]) -> dict[str, Any]:
        """Create optimized crew configuration for parallel execution.

        Args:
            tasks: List of CrewAI tasks
            base_crew_config: Base crew configuration

        Returns:
            Optimized crew configuration
        """
        analysis = self.analyze_parallelization_potential(tasks)

        # Adjust crew settings for parallel execution
        optimized_config = base_crew_config.copy()

        if analysis["parallelization_feasible"]:
            # Use hierarchical process for parallel execution
            optimized_config["process"] = "hierarchical"

            # Increase max execution time for parallel tasks
            current_time = optimized_config.get("max_execution_time", 300)
            optimized_config["max_execution_time"] = current_time + (analysis["execution_levels"] * 60)

            # Adjust max RPM for parallel execution
            current_rpm = optimized_config.get("max_rpm", 10)
            optimized_config["max_rpm"] = current_rpm * min(analysis["max_parallel_tasks"], 3)

            self.logger.info(
                f"⚡ Optimized crew for parallel execution: "
                f"{analysis['max_parallel_tasks']} max concurrent tasks, "
                f"{analysis['estimated_time_savings_percent']:.1f}% time savings"
            )
        else:
            self.logger.info("🔄 Using sequential execution (no parallelization benefit)")

        return optimized_config


def create_enhanced_parallel_analysis_tasks(
    agents: dict[str, Any],
    transcription_task: Task,
    depth: str,
    enable_parallel: bool,
    callback: Any | None = None,
    logger_instance: logging.Logger | None = None,
) -> list[Task]:
    """Create enhanced analysis tasks with advanced parallel execution capabilities.

    This function creates analysis tasks that can execute in parallel when dependencies
    allow, with sophisticated task dependency management.

    Args:
        agents: Dictionary of analysis agents
        transcription_task: Previous transcription task for context
        depth: Analysis depth level
        enable_parallel: Whether to use parallel analysis subtasks
        callback: Optional task completion callback
        logger_instance: Optional logger instance

    Returns:
        List of configured analysis tasks with optimized parallel execution
    """
    _logger = logger_instance or logger

    if enable_parallel:
        _logger.info("⚡ Creating enhanced parallel analysis tasks")

        # Create independent parallel analysis tasks
        tasks = []

        # Task 1: Text Analysis (independent)
        text_analysis_task = Task(
            description=(
                "STEP 1: Extract 'transcript' field from previous task's JSON output. "
                "STEP 2: Perform comprehensive text analysis including: "
                "- Linguistic patterns and readability analysis "
                "- Theme extraction and topic modeling "
                "- Sentiment analysis and emotional indicators "
                "- Keyword extraction and frequency analysis "
                "- Content structure and organization analysis "
                "\n\nCRITICAL: Return your results as JSON with these exact keys: "
                "linguistic_patterns, themes, sentiment_analysis, keywords, content_structure. "
                "Wrap the JSON in ```json``` code blocks."
            ),
            expected_output="JSON with linguistic_patterns, themes, sentiment_analysis, keywords, content_structure",
            agent=agents["analysis_cartographer"],
            context=[transcription_task],
            callback=callback,
        )
        tasks.append(text_analysis_task)

        # Task 2: Fact-Checking Analysis (independent)
        fact_checking_task = Task(
            description=(
                "STEP 1: Extract 'transcript' field from previous task's JSON output. "
                "STEP 2: Perform comprehensive fact-checking analysis including: "
                "- Claim identification and extraction "
                "- Source verification and credibility assessment "
                "- Logical fallacy detection "
                "- Evidence quality evaluation "
                "- Truth assessment and confidence scoring "
                "\n\nCRITICAL: Return your results as JSON with these exact keys: "
                "claims, source_verification, logical_analysis, evidence_quality, truth_assessment. "
                "Wrap the JSON in ```json``` code blocks."
            ),
            expected_output="JSON with claims, source_verification, logical_analysis, evidence_quality, truth_assessment",
            agent=agents["verification_director"],
            context=[transcription_task],
            callback=callback,
        )
        tasks.append(fact_checking_task)

        # Task 3: Bias & Manipulation Detection (independent)
        bias_analysis_task = Task(
            description=(
                "STEP 1: Extract 'transcript' field from previous task's JSON output. "
                "STEP 2: Perform comprehensive bias and manipulation analysis including: "
                "- Bias indicators and type classification "
                "- Deception detection and manipulation techniques "
                "- Narrative integrity assessment "
                "- Psychological threat evaluation "
                "- Trustworthiness scoring "
                "\n\nCRITICAL: Return your results as JSON with these exact keys: "
                "bias_indicators, deception_analysis, narrative_integrity, psychological_threats, trustworthiness. "
                "Wrap the JSON in ```json``` code blocks."
            ),
            expected_output="JSON with bias_indicators, deception_analysis, narrative_integrity, psychological_threats, trustworthiness",
            agent=agents["verification_director"],
            context=[transcription_task],
            callback=callback,
        )
        tasks.append(bias_analysis_task)

        # For deeper analysis, add additional parallel tasks
        if depth in ["comprehensive", "experimental"]:
            # Task 4: Advanced Pattern Recognition (independent)
            pattern_recognition_task = Task(
                description=(
                    "STEP 1: Extract 'transcript' field from previous task's JSON output. "
                    "STEP 2: Perform advanced pattern recognition analysis including: "
                    "- Behavioral pattern identification "
                    "- Communication style analysis "
                    "- Rhetorical device detection "
                    "- Persuasion technique analysis "
                    "- Cognitive bias pattern recognition "
                    "\n\nCRITICAL: Return your results as JSON with these exact keys: "
                    "behavioral_patterns, communication_style, rhetorical_devices, persuasion_techniques, cognitive_biases. "
                    "Wrap the JSON in ```json``` code blocks."
                ),
                expected_output="JSON with behavioral_patterns, communication_style, rhetorical_devices, persuasion_techniques, cognitive_biases",
                agent=agents["analysis_cartographer"],
                context=[transcription_task],
                callback=callback,
            )
            tasks.append(pattern_recognition_task)

            # Task 5: Social Intelligence Analysis (independent)
            social_intelligence_task = Task(
                description=(
                    "STEP 1: Extract 'transcript' field from previous task's JSON output. "
                    "STEP 2: Perform social intelligence analysis including: "
                    "- Social dynamics assessment "
                    "- Influence network analysis "
                    "- Community impact evaluation "
                    "- Cultural context analysis "
                    "- Social engineering detection "
                    "\n\nCRITICAL: Return your results as JSON with these exact keys: "
                    "social_dynamics, influence_network, community_impact, cultural_context, social_engineering. "
                    "Wrap the JSON in ```json``` code blocks."
                ),
                expected_output="JSON with social_dynamics, influence_network, community_impact, cultural_context, social_engineering",
                agent=agents["verification_director"],
                context=[transcription_task],
                callback=callback,
            )
            tasks.append(social_intelligence_task)

        _logger.info(f"✅ Created {len(tasks)} parallel analysis tasks for {depth} depth")
        return tasks

    else:
        # Fall back to sequential analysis
        _logger.info("🔄 Creating sequential analysis task")
        from .crew_builders_focused import create_analysis_tasks

        return create_analysis_tasks(
            agents=agents,
            transcription_task=transcription_task,
            depth=depth,
            enable_parallel=False,
            callback=callback,
            logger_instance=_logger,
        )


def optimize_crew_for_parallel_execution(crew: Crew, tasks: list[Task], max_concurrent_tasks: int = 3) -> Crew:
    """Optimize a crew for parallel execution.

    Args:
        crew: CrewAI crew instance to optimize
        tasks: List of tasks in the crew
        max_concurrent_tasks: Maximum concurrent tasks

    Returns:
        Optimized crew instance
    """
    engine = ParallelExecutionEngine(max_concurrent_tasks)

    # Analyze parallelization potential
    analysis = engine.analyze_parallelization_potential(tasks)

    if analysis["parallelization_feasible"]:
        # Optimize task order
        optimized_tasks = engine.optimize_task_execution_order(tasks)

        # Create optimized crew configuration
        base_config = {
            "process": "hierarchical",
            "memory": True,
            "planning": True,
            "cache": True,
            "max_rpm": 10,
            "max_execution_time": 300,
            "verbose": True,
        }

        optimized_config = engine.create_parallel_crew_configuration(tasks, base_config)

        # Create new optimized crew
        from .crew_builders_focused import build_crew_with_tasks

        optimized_crew = build_crew_with_tasks(
            tasks=optimized_tasks, process_type=optimized_config["process"], logger_instance=logger
        )

        logger.info(
            f"⚡ Crew optimized for parallel execution: "
            f"{analysis['estimated_time_savings_percent']:.1f}% time savings expected"
        )

        return optimized_crew

    return crew
