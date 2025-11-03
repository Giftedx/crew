"""Accuracy assessment functions for content analysis.

This module provides functions for assessing factual accuracy and source credibility
in the analysis pipeline.
"""

import logging
from typing import Any


# Module-level logger
logger = logging.getLogger(__name__)


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp helper to keep quality metrics within expected bounds.

    Args:
        value: Value to clamp
        minimum: Minimum allowed value
        maximum: Maximum allowed value

    Returns:
        Clamped value between minimum and maximum
    """
    try:
        return max(minimum, min(maximum, float(value)))
    except Exception:
        return minimum


def assess_factual_accuracy(
    verification_data: dict[str, Any] | None,
    fact_data: dict[str, Any] | None = None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Derive a factual accuracy score from verification and fact analysis outputs.

    Args:
        verification_data: Verification analysis results
        fact_data: Optional fact-checking results
        logger_instance: Optional logger instance

    Returns:
        Accuracy score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    score = 0.5
    try:
        total_verified = 0
        total_disputed = 0
        evidence_count = 0
        sources: list[dict[str, Any]] = []

        if isinstance(verification_data, dict):
            for key in ("fact_checks", "fact_verification"):
                candidate = verification_data.get(key)
                if isinstance(candidate, dict):
                    sources.append(candidate)
        if isinstance(fact_data, dict):
            candidate = fact_data.get("fact_checks")
            if isinstance(candidate, dict):
                sources.append(candidate)

        for candidate in sources:
            verified = candidate.get("verified_claims")
            disputed = candidate.get("disputed_claims")
            evidence = candidate.get("evidence")

            if isinstance(verified, int):
                total_verified += verified
            elif isinstance(verified, list):
                total_verified += len(verified)

            if isinstance(disputed, int):
                total_disputed += disputed
            elif isinstance(disputed, list):
                total_disputed += len(disputed)

            if isinstance(evidence, list):
                evidence_count += len(evidence)

        total_claims = total_verified + total_disputed
        if total_claims > 0:
            verification_ratio = total_verified / total_claims
            score = 0.3 + (verification_ratio * 0.5)

        if evidence_count > 0:
            score = min(1.0, score + (min(evidence_count, 5) * 0.04))

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Factual accuracy assessment failed: %s", exc)
        return 0.5


def assess_source_credibility(
    knowledge_data: dict[str, Any] | None,
    verification_data: dict[str, Any] | None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Estimate source credibility using knowledge payload and verification metadata.

    Args:
        knowledge_data: Knowledge graph or content metadata
        verification_data: Verification analysis results
        logger_instance: Optional logger instance

    Returns:
        Credibility score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    score = 0.5
    try:
        if isinstance(verification_data, dict):
            validation = verification_data.get("source_validation")
            if isinstance(validation, dict):
                if validation.get("validated") is True:
                    score = 0.85
                elif validation.get("validated") is False:
                    score = 0.35

        if isinstance(knowledge_data, dict):
            fact_results = knowledge_data.get("fact_check_results")
            if isinstance(fact_results, dict):
                reliability = fact_results.get("source_reliability")
                if isinstance(reliability, (int, float)):
                    score = (score * 0.5) + (clamp_score(float(reliability)) * 0.5)
                elif isinstance(reliability, str):
                    mapping = {"high": 0.85, "medium": 0.6, "low": 0.3}
                    score = (score * 0.5) + (mapping.get(reliability.lower(), 0.5) * 0.5)

            metadata = knowledge_data.get("content_metadata")
            if isinstance(metadata, dict):
                if metadata.get("source_url"):
                    score = min(1.0, score + 0.05)
                if metadata.get("platform"):
                    score = min(1.0, score + 0.05)

        credibility = None
        if isinstance(verification_data, dict):
            credibility = verification_data.get("credibility_assessment")
        if isinstance(credibility, dict):
            cred_score = credibility.get("score") or credibility.get("overall")
            if isinstance(cred_score, (int, float)):
                score = (score * 0.5) + (clamp_score(float(cred_score)) * 0.5)

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Source credibility assessment fallback due to error: %s", exc)
        return 0.5
