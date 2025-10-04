"""Pipeline result builder utilities for ContentPipeline orchestration.

This module provides functions to synthesize ContentPipeline stage outputs into
structured analysis results. These builders handle data extraction, transformation,
and graceful degradation when inputs are incomplete.
"""

from __future__ import annotations

import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


def merge_threat_payload(
    threat_payload: dict[str, Any],
    verification_data: dict[str, Any] | None,
    fact_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """Augment a plain threat payload dict with relevant verification/fact data.

    This helper is used when we have already-materialized dict payloads rather than StepResult objects.
    It attaches deception_score, logical fallacies, and fact checks if present, without overriding
    existing values.

    Args:
        threat_payload: Base threat detection payload dict
        verification_data: Optional verification results with deception metrics
        fact_data: Optional fact analysis results with fact checks

    Returns:
        Merged threat payload with verification and fact data incorporated
    """
    merged = dict(threat_payload) if isinstance(threat_payload, dict) else {}

    # From verification results
    if isinstance(verification_data, dict):
        if "deception_metrics" in verification_data and "deception_metrics" not in merged:
            merged["deception_metrics"] = verification_data.get("deception_metrics")
        if "credibility_assessment" in verification_data and "credibility_assessment" not in merged:
            merged["credibility_assessment"] = verification_data.get("credibility_assessment")
        # Deception score may live under various keys; don't clobber if already present
        for k in ("deception_score",):
            if k not in merged and isinstance(verification_data.get(k), (int, float)):
                merged[k] = verification_data.get(k)
        if "logical_analysis" in verification_data and "logical_fallacies" not in merged:
            merged["logical_fallacies"] = verification_data.get("logical_analysis")

    # From fact analysis data
    if isinstance(fact_data, dict):
        if "fact_checks" in fact_data and "fact_checks" not in merged:
            merged["fact_checks"] = fact_data.get("fact_checks")
        if "logical_fallacies" in fact_data and "logical_fallacies" not in merged:
            merged["logical_fallacies"] = fact_data.get("logical_fallacies")
        if "perspective_synthesis" in fact_data and "perspective" not in merged:
            merged["perspective"] = fact_data.get("perspective_synthesis")

    return merged


def build_pipeline_content_analysis_result(
    *,
    transcript: str,
    transcription_data: dict[str, Any],
    pipeline_analysis: dict[str, Any],
    media_info: dict[str, Any],
    pipeline_fallacy: dict[str, Any] | None,
    pipeline_perspective: dict[str, Any] | None,
    pipeline_metadata: dict[str, Any] | None,
    source_url: str | None,
    logger: Any = None,
) -> StepResult:
    """Synthesize content analysis directly from ContentPipeline outputs.

    When the pipeline already produced rich analysis artifacts, prefer them over
    launching additional agent workloads. This consolidates sentiment,
    perspective, and fallacy insights into the step result expected by
    downstream stages.

    Args:
        transcript: Raw transcript text from transcription stage
        transcription_data: Metadata from transcription (quality, anchors, index)
        pipeline_analysis: Analysis results from ContentPipeline
        media_info: Media metadata (title, platform, duration, etc.)
        pipeline_fallacy: Optional fallacy analysis from pipeline
        pipeline_perspective: Optional perspective analysis from pipeline
        pipeline_metadata: Optional pipeline execution metadata
        source_url: Optional source URL for the content
        logger: Optional logger instance for warnings

    Returns:
        StepResult with synthesized analysis data or degraded fallback
    """
    try:
        # Extract keywords from analysis
        keywords: list[str] = []
        if isinstance(pipeline_analysis.get("keywords"), list):
            keywords = [str(kw) for kw in pipeline_analysis.get("keywords", [])]
        elif isinstance(pipeline_analysis.get("key_phrases"), list):
            keywords = [str(kw) for kw in pipeline_analysis.get("key_phrases", [])]

        # Extract structured data
        structured = pipeline_analysis.get("structured")
        if not isinstance(structured, dict):
            structured = {}

        # Build sentiment payload
        sentiment_details = pipeline_analysis.get("sentiment_details")
        sentiment_payload: dict[str, Any] = {}
        if isinstance(sentiment_details, dict):
            sentiment_payload = dict(sentiment_details)
        sentiment_label = pipeline_analysis.get("sentiment")
        sentiment_score = pipeline_analysis.get("sentiment_score")
        if sentiment_label and "label" not in sentiment_payload:
            sentiment_payload["label"] = sentiment_label
        if sentiment_score is not None and "score" not in sentiment_payload:
            sentiment_payload["score"] = sentiment_score
        sentiment_payload.setdefault("label", sentiment_label or "neutral")

        # Calculate word count
        word_count = None
        if isinstance(structured.get("word_count"), int):
            word_count = structured["word_count"]
        elif isinstance(pipeline_analysis.get("word_count"), int):
            word_count = pipeline_analysis["word_count"]
        if word_count is None:
            word_count = len(transcript.split())

        # Extract summary
        summary = pipeline_analysis.get("summary")
        if not summary and isinstance(pipeline_perspective, dict):
            summary = pipeline_perspective.get("summary")

        # Build content metadata
        content_metadata: dict[str, Any] = {
            "word_count": word_count,
            "quality_score": transcription_data.get("quality_score", 0.5),
            "analysis_timestamp": time.time(),
            "analysis_method": pipeline_analysis.get("analysis_method", "content_pipeline_analysis"),
            "analysis_source": "content_pipeline",
        }

        # Merge media info into metadata
        if isinstance(media_info, dict):
            for key in ("title", "platform", "duration", "uploader", "video_id"):
                if key in media_info and media_info[key] is not None:
                    content_metadata.setdefault(key, media_info[key])
            if not source_url and media_info.get("source_url"):
                source_url = media_info.get("source_url")

        # Merge pipeline metadata
        if isinstance(pipeline_metadata, dict):
            for key in ("source_url", "workflow_type", "acquisition_timestamp"):
                if key in pipeline_metadata and pipeline_metadata[key] is not None:
                    content_metadata.setdefault(key, pipeline_metadata[key])
            if not source_url and pipeline_metadata.get("source_url"):
                source_url = str(pipeline_metadata.get("source_url"))

        # Build thematic insights from keywords and perspectives
        thematic_insights = list(keywords)
        if isinstance(pipeline_perspective, dict):
            additional_perspectives = pipeline_perspective.get("perspectives")
            if isinstance(additional_perspectives, list):
                for item in additional_perspectives:
                    if isinstance(item, str) and item not in thematic_insights:
                        thematic_insights.append(item)

        # Construct final analysis results
        analysis_results = {
            "message": "Content analysis derived from ContentPipeline output",
            "transcript": transcript,
            "crew_analysis": pipeline_analysis,
            "keywords": keywords,
            "sentiment": sentiment_payload.get("label"),
            "sentiment_score": sentiment_payload.get("score"),
            "linguistic_patterns": {"keywords": keywords, "key_phrases": keywords},
            "sentiment_analysis": sentiment_payload,
            "thematic_insights": thematic_insights,
            "content_metadata": content_metadata,
            "timeline_anchors": transcription_data.get("timeline_anchors", []),
            "transcript_index": transcription_data.get("transcript_index", {}),
            "summary": summary,
            "source_url": source_url,
            "pipeline_analysis": pipeline_analysis,
            "pipeline_fallacy": pipeline_fallacy,
            "pipeline_perspective": pipeline_perspective,
            "pipeline_metadata": pipeline_metadata,
            "media_info": media_info,
        }

        # Add optional analysis components
        if pipeline_fallacy is not None:
            analysis_results.setdefault("fallacy_analysis", pipeline_fallacy)
        if pipeline_perspective is not None:
            analysis_results.setdefault("perspective_analysis", pipeline_perspective)

        return StepResult.ok(**analysis_results)

    except Exception as exc:  # pragma: no cover - defensive
        if logger:
            logger.warning("Failed to construct pipeline-derived analysis payload: %s", exc)

        # Calculate safe word count for degraded mode
        safe_word_count = 0
        if transcript and isinstance(transcript, str):
            safe_word_count = len(transcript.split())

        # Return degraded result with minimal data
        return StepResult.ok(
            message="ContentPipeline analysis extraction degraded",
            transcript=transcript or "",
            linguistic_patterns={"keywords": []},
            sentiment_analysis={"label": "neutral"},
            thematic_insights=[],
            content_metadata={
                "word_count": safe_word_count,
                "analysis_timestamp": time.time(),
                "analysis_method": "content_pipeline_analysis_degraded",
            },
            timeline_anchors=transcription_data.get("timeline_anchors", []),
            transcript_index=transcription_data.get("transcript_index", {}),
            source_url=source_url,
            pipeline_analysis=pipeline_analysis,
            pipeline_fallacy=pipeline_fallacy,
            pipeline_perspective=pipeline_perspective,
            pipeline_metadata=pipeline_metadata,
            media_info=media_info,
        )
