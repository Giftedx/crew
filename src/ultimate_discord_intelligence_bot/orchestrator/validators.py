"""Input/output validation utilities for autonomous orchestration.

This module contains validation functions that ensure data integrity
and system prerequisites are met before executing workflows.

Extracted from autonomous_orchestrator.py to improve maintainability.
"""

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def validate_stage_data(stage_name: str, required_keys: list[str], data: dict[str, Any]) -> None:
    """Validate that stage data contains all required keys.

    Args:
        stage_name: Name of the stage being validated
        required_keys: List of keys that must be present in data
        data: Data dictionary to validate

    Raises:
        ValueError: If any required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Stage '{stage_name}' missing required keys: {missing_keys}")


def validate_system_prerequisites() -> dict[str, Any]:
    """Validate that all system prerequisites are met.

    Returns:
        Dictionary with validation results for each component
    """
    results = {
        "yt_dlp": check_ytdlp_available(),
        "llm_api": check_llm_api_available(),
        "discord": check_discord_available(),
    }

    # Overall status
    results["all_valid"] = all(results.values())

    return results


def check_ytdlp_available() -> bool:
    """Check if yt-dlp is available in the system.

    Returns:
        True if yt-dlp is available, False otherwise
    """
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("yt-dlp not found in system PATH")
        return False


def check_llm_api_available() -> bool:
    """Check if LLM API is configured.

    Returns:
        True if API keys are configured, False otherwise
    """
    import os

    # Check for various LLM API keys
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "TOGETHER_API_KEY"]

    return any(os.environ.get(key) for key in api_keys)


def check_discord_available() -> bool:
    """Check if Discord webhook is configured.

    Returns:
        True if Discord webhook is configured, False otherwise
    """
    import os

    return bool(os.environ.get("DISCORD_WEBHOOK"))


def detect_placeholder_responses(task_name: str, output_data: dict[str, Any]) -> None:
    """Detect and warn about placeholder responses from agents.

    Args:
        task_name: Name of the task that generated the output
        output_data: Output data to check for placeholder content
    """
    placeholder_phrases = ["placeholder", "to be determined", "tbd", "coming soon", "not available", "n/a"]

    output_str = str(output_data).lower()

    for phrase in placeholder_phrases:
        if phrase in output_str:
            logger.warning(f"Task '{task_name}' may have returned placeholder content: '{phrase}' detected")
            break


def validate_depth_parameter(depth: str) -> str:
    """Validate and normalize the depth parameter.

    Args:
        depth: Raw depth parameter from user input

    Returns:
        Normalized depth value

    Raises:
        ValueError: If depth is invalid
    """
    valid_depths = ["standard", "deep", "comprehensive", "experimental"]

    normalized = depth.lower().strip()

    if normalized not in valid_depths:
        raise ValueError(f"Invalid depth '{depth}'. Valid options: {', '.join(valid_depths)}")

    return normalized
