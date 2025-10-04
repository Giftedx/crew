"""Quality assessment functions for content analysis.

This module provides functions for assessing quality, coherence, accuracy,
credibility, bias, and other quality metrics across analysis outputs.

All functions accept optional logger and metrics parameters for dependency injection.
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


def assess_content_coherence(
    analysis_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
) -> float:
    """Assess the coherence of analyzed content based on transcript structure and logical flow.

    Args:
        analysis_data: Dictionary containing analysis results
        logger_instance: Optional logger instance

    Returns:
        Coherence score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        # Extract transcript and analysis data
        transcript = analysis_data.get("transcript", "")
        linguistic_patterns = analysis_data.get("linguistic_patterns", {})
        sentiment_analysis = analysis_data.get("sentiment_analysis", {})
        content_metadata = analysis_data.get("content_metadata", {})

        coherence_score = 0.5  # Base neutral score

        # Factor 1: Transcript length and structure
        if transcript:
            word_count = len(transcript.split())
            if word_count > 100:
                coherence_score += 0.1
            elif word_count < 20:
                coherence_score -= 0.2

            # Check for structured content (paragraphs, sentences)
            sentences = transcript.split(".")
            if len(sentences) > 3:
                coherence_score += 0.1

        # Factor 2: Linguistic patterns consistency
        if linguistic_patterns and isinstance(linguistic_patterns, dict):
            coherence_score += 0.1

        # Factor 3: Sentiment consistency
        if sentiment_analysis and isinstance(sentiment_analysis, dict):
            coherence_score += 0.05

        # Factor 4: Content metadata completeness
        metadata_completeness = sum(
            1 for key in ["title", "platform", "word_count", "quality_score"] if content_metadata.get(key) is not None
        )
        metadata_bonus = (metadata_completeness / 4) * 0.1
        coherence_score += metadata_bonus

        # Ensure score is within valid range
        return max(0.0, min(1.0, coherence_score))

    except Exception as exc:
        _logger.debug("Content coherence assessment failed: %s", exc)
        return 0.5


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


def assess_bias_levels(
    analysis_data: dict[str, Any] | None,
    verification_data: dict[str, Any] | None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Score how balanced the content is based on bias indicators and sentiment spread.

    Args:
        analysis_data: Content analysis results
        verification_data: Verification analysis results
        logger_instance: Optional logger instance

    Returns:
        Bias score between 0.0 (highly biased) and 1.0 (balanced)
    """
    _logger = logger_instance or logger
    try:
        base_score = 0.7
        bias_signals = []

        if isinstance(verification_data, dict):
            indicators = verification_data.get("bias_indicators")
            if isinstance(indicators, list):
                bias_signals = indicators
            elif isinstance(indicators, dict):
                extracted = indicators.get("signals")
                if isinstance(extracted, list):
                    bias_signals = extracted

        bias_penalty = min(0.5, len(bias_signals) * 0.1)

        sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
        if isinstance(sentiment, dict):
            positive = sentiment.get("positive") or sentiment.get("positives")
            negative = sentiment.get("negative") or sentiment.get("negatives")
            if isinstance(positive, (int, float)) and isinstance(negative, (int, float)):
                total = positive + negative
                if total:
                    swing = abs(positive - negative) / total
                    bias_penalty += min(0.3, swing * 0.3)
            if sentiment.get("overall_sentiment") == "neutral":
                bias_penalty = max(0.0, bias_penalty - 0.05)

        score = base_score - bias_penalty
        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Bias assessment fallback due to error: %s", exc)
        return 0.5


def assess_emotional_manipulation(
    analysis_data: dict[str, Any] | None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Estimate the level of emotional manipulation present in the content.

    Args:
        analysis_data: Content analysis results
        logger_instance: Optional logger instance

    Returns:
        Manipulation resistance score between 0.0 (high manipulation) and 1.0 (low manipulation)
    """
    _logger = logger_instance or logger
    try:
        sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
        if not isinstance(sentiment, dict) or not sentiment:
            return 0.6

        intensity = sentiment.get("intensity")
        if isinstance(intensity, (int, float)):
            score = 1.0 - min(0.8, float(intensity) * 0.5)
        else:
            positive = sentiment.get("positive") or sentiment.get("positives") or 0.0
            negative = sentiment.get("negative") or sentiment.get("negatives") or 0.0
            if not isinstance(positive, (int, float)):
                positive = 0.0
            if not isinstance(negative, (int, float)):
                negative = 0.0

            total = positive + negative
            if total > 0:
                swing = abs(positive - negative) / total
                score = 1.0 - min(0.8, swing * 0.5)
            else:
                score = 0.7

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Emotional manipulation assessment failed: %s", exc)
        return 0.6


def assess_logical_consistency(
    verification_data: dict[str, Any] | None,
    logical_analysis: dict[str, Any] | None = None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Evaluate logical consistency based on verification and logical analysis.

    Args:
        verification_data: Verification analysis results
        logical_analysis: Optional logical analysis results
        logger_instance: Optional logger instance

    Returns:
        Logical consistency score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        score = 0.6  # Base score

        # Check logical analysis
        if isinstance(logical_analysis, dict):
            fallacies = logical_analysis.get("fallacies", [])
            if isinstance(fallacies, list):
                # More fallacies = lower consistency
                fallacy_penalty = min(0.4, len(fallacies) * 0.1)
                score -= fallacy_penalty

            reasoning_quality = logical_analysis.get("reasoning_quality")
            if isinstance(reasoning_quality, (int, float)):
                score = (score * 0.5) + (clamp_score(float(reasoning_quality)) * 0.5)

        # Check verification data
        if isinstance(verification_data, dict):
            logical_check = verification_data.get("logical_consistency")
            if isinstance(logical_check, dict):
                consistency_score = logical_check.get("score")
                if isinstance(consistency_score, (int, float)):
                    score = (score * 0.5) + (clamp_score(float(consistency_score)) * 0.5)

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Logical consistency assessment failed: %s", exc)
        return 0.6


def assess_quality_trend(ai_quality_score: float) -> str:
    """Assess the quality trend based on AI quality score.

    Args:
        ai_quality_score: Quality score from 0.0 to 1.0

    Returns:
        Trend description ("improving", "stable", "declining")
    """
    try:
        if ai_quality_score >= 0.75:
            return "improving"
        elif ai_quality_score >= 0.5:
            return "stable"
        else:
            return "declining"
    except Exception:
        return "stable"


def calculate_overall_confidence(
    *data_sources,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Calculate overall confidence across all data sources.

    Args:
        *data_sources: Variable number of data dictionaries
        logger_instance: Optional logger instance

    Returns:
        Confidence score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        valid_sources = sum(1 for source in data_sources if source and isinstance(source, dict))
        return min(valid_sources * 0.15, 0.9)
    except Exception as exc:
        _logger.debug("Overall confidence calculation failed: %s", exc)
        return 0.5


def assess_transcript_quality(
    transcript: str,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Assess the quality of a transcript based on various metrics.

    Args:
        transcript: Transcript text to assess
        logger_instance: Optional logger instance

    Returns:
        Quality score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        if not transcript:
            return 0.0

        # Basic quality metrics
        word_count = len(transcript.split())
        char_count = len(transcript)

        # Quality factors
        quality_score = 0.0

        # Length factor (longer transcripts are generally better)
        if word_count > 100:
            quality_score += 0.3
        elif word_count > 50:
            quality_score += 0.2
        elif word_count > 10:
            quality_score += 0.1

        # Character density (reasonable character to word ratio)
        if word_count > 0:
            char_per_word = char_count / word_count
            if 4 <= char_per_word <= 8:  # Reasonable range
                quality_score += 0.2

        # Sentence structure (presence of punctuation)
        punctuation_count = sum(1 for char in transcript if char in ".!?")
        if punctuation_count > word_count / 20:  # At least one sentence marker per 20 words
            quality_score += 0.2

        # Capitalization (proper nouns, sentence starts)
        capital_count = sum(1 for char in transcript if char.isupper())
        if capital_count > word_count / 30:  # Some capitals expected
            quality_score += 0.1

        # Coherence factor (not too many repeated words)
        words = transcript.lower().split()
        unique_words = set(words)
        if len(words) > 0:
            uniqueness_ratio = len(unique_words) / len(words)
            if uniqueness_ratio > 0.3:  # At least 30% unique words
                quality_score += 0.2

        return min(quality_score, 1.0)  # Cap at 1.0
    except Exception as exc:
        _logger.debug("Transcript quality assessment failed: %s", exc)
        return 0.5  # Default moderate quality if assessment fails


def identify_learning_opportunities(
    analysis_data: dict[str, Any],
    verification_data: dict[str, Any],
    fact_data: dict[str, Any] | None = None,
) -> list[str]:
    """Highlight opportunities for future workflow improvements.

    Args:
        analysis_data: Analysis data containing transcript index, timeline anchors
        verification_data: Verification data with fact checks and bias indicators
        fact_data: Optional fact checking data (fallback source for fact_checks)

    Returns:
        List of actionable improvement opportunities
    """
    opportunities: list[str] = []

    transcript_index = analysis_data.get("transcript_index") if isinstance(analysis_data, dict) else {}
    if not transcript_index:
        opportunities.append("Generate a transcript index to accelerate follow-up investigations.")

    if isinstance(analysis_data, dict) and not analysis_data.get("timeline_anchors"):
        opportunities.append("Add timeline anchors to support multi-agent temporal reasoning.")

    fact_checks = None
    if isinstance(verification_data, dict):
        fact_checks = verification_data.get("fact_checks")
    if fact_checks is None and isinstance(fact_data, dict):
        fact_checks = fact_data.get("fact_checks")
    if not fact_checks:
        opportunities.append("Expand fact-check coverage to strengthen factual accuracy metrics.")

    bias_indicators = verification_data.get("bias_indicators") if isinstance(verification_data, dict) else None
    if bias_indicators:
        opportunities.append("Review detected bias indicators and adjust sourcing diversity.")

    if not opportunities:
        opportunities.append("Capture analyst retrospectives to preserve implicit learnings.")

    return opportunities


def generate_enhancement_suggestions(
    quality_dimensions: dict[str, float],
    analysis_data: dict[str, Any],
    verification_data: dict[str, Any],
) -> dict[str, Any]:
    """Convert dimension scores into actionable follow-up items.

    Args:
        quality_dimensions: Quality dimension scores (0.0-1.0)
        analysis_data: Analysis data with content metadata
        verification_data: Verification data with source validation

    Returns:
        Dictionary with priority_actions, watch_items, and context
    """
    priority_actions: list[str] = []
    watch_items: list[str] = []

    for dimension, value in quality_dimensions.items():
        if not isinstance(value, (int, float)):
            continue
        label = dimension.replace("_", " ").title()
        if value < 0.4:
            priority_actions.append(f"{label}: urgent remediation required (score {value:.2f}).")
        elif value < 0.6:
            watch_items.append(f"{label}: monitor for drift (score {value:.2f}).")

    if not priority_actions and not watch_items and quality_dimensions:
        priority_actions.append("All quality metrics above targets – maintain current strategy.")

    metadata = analysis_data.get("content_metadata", {}) if isinstance(analysis_data, dict) else {}
    source_validation = verification_data.get("source_validation", {}) if isinstance(verification_data, dict) else {}

    return {
        "priority_actions": priority_actions,
        "watch_items": watch_items,
        "context": {
            "title": metadata.get("title") if metadata else None,
            "platform": metadata.get("platform") if metadata else None,
            "validated_sources": bool(source_validation),
        },
    }
