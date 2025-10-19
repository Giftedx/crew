"""Quality validation functions for content analysis.

This module provides validation functions for detecting placeholder responses
and validating stage data integrity in the analysis pipeline.
"""

import logging
from typing import Any

# Module-level logger
logger = logging.getLogger(__name__)


def detect_placeholder_responses(
    task_name: str,
    output_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
) -> None:
    """Detect when agents generate placeholder/mock responses instead of calling tools.

    Critical validation for ensuring LLMs call tools properly, not generate mock data.

    Args:
        task_name: Name of the task being validated (e.g., "transcription")
        output_data: Dictionary of output data from the task
        logger_instance: Optional logger instance (uses module logger if None)
        metrics_instance: Optional metrics instance for tracking
    """
    _logger = logger_instance or logger
    placeholder_patterns = [
        "your transcribed text goes here",
        "goes here",
        "<extracted_insights>",
        "placeholder",
        "mock data",
        "example content",
        "sample text",
        "[insert",
        "TODO:",
        "FIXME:",
        "dummy data",
        "test content",
        "<insert",
        "replace with",
        "fill in",
        "[placeholder",
    ]

    # Validate transcription task
    if task_name == "transcription" and "transcript" in output_data:
        transcript = str(output_data["transcript"])

        # Check transcript length
        if len(transcript) < 100:
            _logger.error(
                "❌ TOOL EXECUTION FAILURE: Transcript too short (%d chars). "
                "Agent likely generated placeholder text instead of calling transcription tool.",
                len(transcript),
            )
            if metrics_instance:
                metrics_instance.counter(
                    "autointel_placeholder_detected",
                    labels={"task": task_name, "reason": "short_transcript"},
                ).inc()

        # Check for placeholder patterns
        transcript_lower = transcript.lower()
        for pattern in placeholder_patterns:
            if pattern.lower() in transcript_lower:
                _logger.error(
                    "❌ TOOL EXECUTION FAILURE: Placeholder pattern '%s' found in transcript. "
                    "Agent generated mock data instead of calling tool.",
                    pattern,
                )
                if metrics_instance:
                    metrics_instance.counter(
                        "autointel_placeholder_detected",
                        labels={"task": task_name, "reason": "placeholder_pattern"},
                    ).inc()
                break

    # Validate analysis task
    elif task_name == "analysis":
        insights = output_data.get("insights", "")
        themes = output_data.get("themes", [])
        fallacies = output_data.get("fallacies", {})
        _ = output_data.get("perspectives", {})  # Reserved for future use

        # Check insights
        if insights:
            insights_lower = str(insights).lower()
            for pattern in placeholder_patterns:
                if pattern.lower() in insights_lower:
                    _logger.error(
                        "❌ TOOL EXECUTION FAILURE: Placeholder pattern '%s' found in insights. "
                        "Agent generated mock insights.",
                        pattern,
                    )
                    if metrics_instance:
                        metrics_instance.counter(
                            "autointel_placeholder_detected",
                            labels={"task": task_name, "reason": "placeholder_insights"},
                        ).inc()
                    break

        # Check themes
        if isinstance(themes, list):
            for theme in themes:
                theme_str = str(theme).lower()
                for pattern in placeholder_patterns:
                    if pattern.lower() in theme_str:
                        _logger.error(
                            "❌ TOOL EXECUTION FAILURE: Placeholder pattern '%s' found in themes.",
                            pattern,
                        )
                        if metrics_instance:
                            metrics_instance.counter(
                                "autointel_placeholder_detected",
                                labels={"task": task_name, "reason": "placeholder_themes"},
                            ).inc()
                        break

        # Check fallacies
        if isinstance(fallacies, dict):
            for key, value in fallacies.items():
                value_str = str(value).lower()
                for pattern in placeholder_patterns:
                    if pattern.lower() in value_str:
                        _logger.warning(
                            "⚠️ POTENTIAL PLACEHOLDER: Pattern '%s' in fallacy '%s'",
                            pattern,
                            key,
                        )
                        if metrics_instance:
                            metrics_instance.counter(
                                "autointel_placeholder_detected",
                                labels={"task": task_name, "reason": "placeholder_fallacies"},
                            ).inc()
                        break

    # Validate verification task
    elif task_name == "verification":
        verified_claims = output_data.get("verified_claims", [])
        fact_check_results = output_data.get("fact_check_results", {})

        if not verified_claims and not fact_check_results:
            _logger.error(
                "❌ TOOL EXECUTION FAILURE: Verification task returned empty claims and results. "
                "Agent likely skipped tool execution."
            )
            if metrics_instance:
                metrics_instance.counter(
                    "autointel_placeholder_detected",
                    labels={"task": task_name, "reason": "empty_verification"},
                ).inc()


def validate_stage_data(stage_name: str, required_keys: list[str], data: dict[str, Any]) -> None:
    """Validate that required keys are present in stage data.

    Args:
        stage_name: Name of the pipeline stage
        required_keys: List of required keys that must be present
        data: Data dictionary to validate

    Raises:
        ValueError: If required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Stage '{stage_name}' missing required keys: {missing_keys}")
