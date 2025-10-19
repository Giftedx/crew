"""Task completion callback utilities for CrewAI orchestration.

This module provides the task completion callback functionality for extracting
and propagating structured data between crew tasks.

Extracted from crew_builders.py to improve maintainability and organization.
"""

import logging
from typing import Any

# Module-level logger
logger = logging.getLogger(__name__)


def task_completion_callback(
    task_output: Any,
    populate_agent_context_callback: Any | None = None,
    detect_placeholder_callback: Any | None = None,
    repair_json_callback: Any | None = None,
    extract_key_values_callback: Any | None = None,
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
    agent_coordinators: dict[str, Any] | None = None,
) -> None:
    """Callback executed after each task to extract and propagate structured data.

    CRITICAL FIX: CrewAI task context passes TEXT to LLM prompts, NOT structured
    data to tools. This callback extracts tool results and updates global crew
    context so subsequent tasks can access the data.

    Now includes Pydantic validation to prevent invalid data propagation.

    Args:
        task_output: TaskOutput object from completed task
        populate_agent_context_callback: Optional callback to populate agent tool context
        detect_placeholder_callback: Optional callback to detect placeholder responses
        repair_json_callback: Optional callback to repair malformed JSON
        extract_key_values_callback: Optional callback to extract key-value pairs from text
        logger_instance: Optional logger instance
        metrics_instance: Optional metrics instance
        agent_coordinators: Optional dict of cached agents to update
    """
    _logger = logger_instance or logger

    # Import here to avoid circular dependency
    try:
        from pydantic import ValidationError

        from ..schemas.task_outputs import TASK_OUTPUT_SCHEMAS
    except ImportError:
        _logger.warning("Task output schemas not available - validation disabled")
        TASK_OUTPUT_SCHEMAS = {}
        ValidationError = Exception

    try:
        # Extract structured data from task output
        output_data = {}
        task_name = "unknown"

        # Try to get task name for schema lookup
        if hasattr(task_output, "task") and hasattr(task_output.task, "description"):
            desc = str(task_output.task.description).lower()
            # Infer task type from description keywords
            if "download" in desc or "acquire" in desc:
                task_name = "acquisition"
            elif "transcript" in desc or "audio" in desc:
                task_name = "transcription"
            elif "analysis" in desc or "linguistic" in desc:
                task_name = "analysis"
            elif "fact" in desc or "verify" in desc:
                task_name = "fact_checking"
            elif "bias" in desc or "manipulation" in desc:
                task_name = "bias_analysis"
            elif "synthesis" in desc or "integration" in desc:
                task_name = "knowledge_integration"

        # Extract raw output text
        raw_output = ""
        if hasattr(task_output, "raw") and task_output.raw:
            raw_output = str(task_output.raw)
        elif hasattr(task_output, "output") and task_output.output:
            raw_output = str(task_output.output)

        if not raw_output:
            _logger.warning(f"⚠️  No output data found for task: {task_name}")
            return

        _logger.info(f"📋 Processing task completion for: {task_name}")

        # Check for placeholder responses
        if detect_placeholder_callback:
            if detect_placeholder_callback(raw_output):
                _logger.error(f"❌ PLACEHOLDER RESPONSE DETECTED in {task_name} task")
                return

        # Try to extract JSON data
        json_data = None
        if repair_json_callback:
            json_data = repair_json_callback(raw_output)
        elif extract_key_values_callback:
            json_data = extract_key_values_callback(raw_output)

        # If we got structured data, validate it
        if json_data and task_name in TASK_OUTPUT_SCHEMAS:
            try:
                validated_data = TASK_OUTPUT_SCHEMAS[task_name](**json_data)
                output_data = validated_data.model_dump()
                _logger.info(f"✅ Validated {task_name} output with schema")
            except ValidationError as e:
                _logger.warning(f"⚠️  Schema validation failed for {task_name}: {e}")
                output_data = json_data
        elif json_data:
            output_data = json_data
        else:
            # Fallback: treat raw output as text data
            output_data = {"raw_text": raw_output}

        # Update agent context with extracted data
        if populate_agent_context_callback and agent_coordinators:
            for agent_name, agent in agent_coordinators.items():
                try:
                    populate_agent_context_callback(agent, output_data, _logger, metrics_instance)
                except Exception as e:
                    _logger.warning(f"⚠️  Failed to update context for agent {agent_name}: {e}")

        # Track metrics
        if metrics_instance:
            try:
                metrics_instance.counter(
                    "autointel_task_completed",
                    labels={
                        "task_name": task_name,
                        "has_structured_data": bool(json_data),
                        "output_size": len(raw_output),
                    },
                ).inc()
            except Exception:
                pass

        _logger.info(f"✅ Task completion processed for {task_name}")

    except Exception as e:
        _logger.exception(f"❌ Error in task completion callback: {e}")


def create_task_callback_with_dependencies(
    populate_agent_context_callback: Any | None = None,
    detect_placeholder_callback: Any | None = None,
    repair_json_callback: Any | None = None,
    extract_key_values_callback: Any | None = None,
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
    agent_coordinators: dict[str, Any] | None = None,
) -> Any:
    """Create a task completion callback with pre-configured dependencies.

    Args:
        populate_agent_context_callback: Callback to populate agent tool context
        detect_placeholder_callback: Callback to detect placeholder responses
        repair_json_callback: Callback to repair malformed JSON
        extract_key_values_callback: Callback to extract key-value pairs from text
        logger_instance: Optional logger instance
        metrics_instance: Optional metrics instance
        agent_coordinators: Optional dict of cached agents to update

    Returns:
        Configured task completion callback function
    """

    def callback(task_output: Any) -> None:
        task_completion_callback(
            task_output=task_output,
            populate_agent_context_callback=populate_agent_context_callback,
            detect_placeholder_callback=detect_placeholder_callback,
            repair_json_callback=repair_json_callback,
            extract_key_values_callback=extract_key_values_callback,
            logger_instance=logger_instance,
            metrics_instance=metrics_instance,
            agent_coordinators=agent_coordinators,
        )

    return callback
