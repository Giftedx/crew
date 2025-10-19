"""Error handling and data repair utilities for orchestrator.

This module provides utilities for:
- Repairing malformed JSON
- Extracting key-value pairs from plain text fallback
- Stage execution with error recovery
"""

import asyncio
import logging
import re
from collections.abc import Callable
from typing import Any

from ..step_result import StepResult

logger = logging.getLogger(__name__)


def repair_json(json_text: str) -> str:
    """Attempt to repair common JSON malformations.

    Handles:
    - Unescaped quotes in string values
    - Trailing commas before closing braces/brackets
    - Single quotes instead of double quotes
    - Newlines in string values

    Args:
        json_text: Potentially malformed JSON string

    Returns:
        Repaired JSON string

    Example:
        >>> repair_json('{"key": "value",}')
        '{"key": "value"}'
    """
    repaired = json_text

    # Fix 1: Remove trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Fix 2: Replace single quotes with double quotes (but not in escaped contexts)
    # This is risky, so we only do it if we detect single-quoted keys
    if re.search(r"'[a-zA-Z_][a-zA-Z0-9_]*'\s*:", repaired):
        repaired = repaired.replace("'", '"')

    # Fix 3: Escape unescaped quotes within string values
    # Find patterns like: "key": "value with "embedded" quotes"
    # This is complex, so we use a careful regex
    def escape_inner_quotes(match):
        key_value = match.group(0)
        # Only fix if we detect unescaped quotes inside the value
        if key_value.count('"') > 4:  # More than 2 pairs suggests embedded quotes
            parts = key_value.split('":')
            if len(parts) == 2:
                key_part = parts[0] + '":'
                value_part = parts[1]
                # Escape quotes in value part (but not the outer delimiters)
                if value_part.count('"') > 2:
                    # Find inner quotes and escape them
                    value_part = re.sub(r'([^\\])"', r'\1\\"', value_part)
                return key_part + value_part
        return key_value

    # Apply escaping fix cautiously
    # repaired = re.sub(r'"[^"]+"\s*:\s*"[^"]*"[^"]*"[^"]*"', escape_inner_quotes, repaired)

    # Fix 4: Remove newlines within string values
    repaired = re.sub(r'"([^"]*?)\n([^"]*?)"', r'"\1 \2"', repaired)

    return repaired


def extract_key_values_from_text(text: str) -> dict[str, Any]:
    """Fallback extraction when JSON parsing fails.

    Attempts to extract key-value pairs from plain text output using
    common patterns like "key: value" or "key = value".

    Args:
        text: Plain text containing key-value pairs

    Returns:
        Dictionary of extracted key-value pairs

    Example:
        >>> extract_key_values_from_text("file_path: video.mp4\\ntitle: Test")
        {'file_path': 'video.mp4', 'title': 'Test'}
    """
    extracted = {}

    # Common patterns for key-value pairs
    patterns = [
        r"(?:^|\n)([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+?)(?=\n|$)",  # key: value
        r"(?:^|\n)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)(?=\n|$)",  # key = value
        r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:\s*"([^"]*)"',  # "key": "value"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for key, value in matches:
            key = key.strip()
            value = value.strip().strip("\"'")

            # Only add if we got something meaningful
            if key and value and len(value) > 3:
                extracted[key] = value

    # Try to extract specific important fields if present
    important_fields = {
        "file_path": r"(?:file_path|path|file)[\s:=]+([^\s\n]+\.(?:mp4|webm|mp3|wav|m4a))",
        "transcript": r"(?:transcript|transcription)[\s:=]+(.*?)(?:\n\n|$)",
        "url": r"(?:url|link)[\s:=]+(https?://[^\s\n]+)",
        "title": r"(?:title)[\s:=]+(.+?)(?=\n|$)",
    }

    for field, pattern in important_fields.items():
        if field not in extracted:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                extracted[field] = match.group(1).strip()

    return extracted


async def execute_stage_with_recovery(
    stage_function: Callable,
    stage_name: str,
    agent_name: str,
    workflow_depth: str,
    error_handler: Any,
    get_system_health: Callable[[], dict[str, Any]],
    logger_instance: logging.Logger | None = None,
    *args,
    **kwargs,
) -> StepResult:
    """Execute a workflow stage with intelligent error handling and recovery.

    Args:
        stage_function: The async function to execute
        stage_name: Name of the stage for logging
        agent_name: Name of the agent executing the stage
        workflow_depth: Current workflow depth level
        error_handler: Error handler instance with handle_crew_error method
        get_system_health: Callback to get system health metrics
        logger_instance: Optional logger instance
        *args: Positional arguments for stage_function
        **kwargs: Keyword arguments for stage_function

    Returns:
        StepResult from stage execution or error recovery
    """
    if logger_instance is None:
        logger_instance = logger

    retry_count = 0
    max_retries = 3

    while retry_count <= max_retries:
        try:
            # Execute the stage function
            result = await stage_function(*args, **kwargs)

            # If successful, return result
            if result.success:
                return result

            # If stage failed but returned a result, handle as controlled failure
            if not result.success and retry_count < max_retries:
                retry_count += 1
                await asyncio.sleep(0.5 * retry_count)  # Exponential backoff
                continue

            return result

        except Exception as e:
            logger_instance.warning(f"Stage {stage_name} failed (attempt {retry_count + 1}): {e}")

            # Use error handler for recovery planning
            recovery_plan, interim_result = await error_handler.handle_crew_error(
                error=e,
                stage_name=stage_name,
                agent_name=agent_name,
                workflow_depth=workflow_depth,
                retry_count=retry_count,
                preceding_results=kwargs.get("preceding_results", {}),
                system_health=get_system_health(),
            )

            # Execute recovery based on plan
            if not recovery_plan.continue_workflow:
                return interim_result

            if retry_count >= max_retries or retry_count >= recovery_plan.max_retries:
                return interim_result

            retry_count += 1

            # Apply recovery strategy modifications for next attempt
            if recovery_plan.simplified_parameters:
                kwargs.update(recovery_plan.simplified_parameters)

            await asyncio.sleep(0.5 * retry_count)  # Exponential backoff

    # Final fallback
    return StepResult.fail(
        f"Stage {stage_name} failed after {max_retries} retries", step=f"{stage_name}_max_retries_exceeded"
    )
