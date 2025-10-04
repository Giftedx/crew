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


def build_knowledge_payload(
    acquisition_data: dict[str, Any],
    intelligence_data: dict[str, Any],
    verification_data: dict[str, Any],
    threat_data: dict[str, Any],
    fact_data: dict[str, Any],
    behavioral_data: dict[str, Any],
    *,
    fallback_url: str | None = None,
) -> dict[str, Any]:
    """Construct a normalized payload for downstream knowledge storage.

    This function aggregates data from multiple workflow stages (acquisition, intelligence,
    verification, threat, fact, behavioral) into a unified knowledge graph payload suitable
    for persistent storage and retrieval.

    Args:
        acquisition_data: Download and transcription data from acquisition stage
        intelligence_data: Analysis results including content metadata
        verification_data: Verification and fact-checking results
        threat_data: Threat detection and deception analysis
        fact_data: Fact-checking and logical analysis results
        behavioral_data: Behavioral profiling and pattern analysis
        fallback_url: Optional fallback source URL if not found in data

    Returns:
        Normalized knowledge payload with source, metadata, analysis, and assessments
    """
    # Extract acquisition blocks
    download_block = {}
    if isinstance(acquisition_data, dict):
        maybe_download = acquisition_data.get("download")
        if isinstance(maybe_download, dict):
            download_block = maybe_download

    transcription_block = {}
    if isinstance(acquisition_data, dict):
        maybe_transcription = acquisition_data.get("transcription")
        if isinstance(maybe_transcription, dict):
            transcription_block = maybe_transcription

    pipeline_meta = {}
    if isinstance(acquisition_data, dict):
        maybe_pipeline = acquisition_data.get("pipeline_metadata")
        if isinstance(maybe_pipeline, dict):
            pipeline_meta = maybe_pipeline

    content_metadata = {}
    if isinstance(intelligence_data, dict):
        maybe_content = intelligence_data.get("content_metadata")
        if isinstance(maybe_content, dict):
            content_metadata = maybe_content

    # Determine source URL with fallback chain
    source_url = None
    if isinstance(acquisition_data, dict):
        source_url = acquisition_data.get("source_url")
    if not source_url:
        source_url = pipeline_meta.get("url") or fallback_url
    if not source_url and isinstance(download_block, dict):
        source_url = download_block.get("source_url")

    # Extract title from multiple sources
    title = None
    if isinstance(download_block, dict):
        title = download_block.get("title")
    if not title and isinstance(content_metadata, dict):
        title = content_metadata.get("title")
    if not title:
        title = pipeline_meta.get("title")

    # Extract platform from multiple sources
    platform = None
    if isinstance(download_block, dict):
        platform = download_block.get("platform")
    if not platform and isinstance(content_metadata, dict):
        platform = content_metadata.get("platform")
    if not platform:
        platform = pipeline_meta.get("platform") or transcription_block.get("platform")

    # Extract perspective data
    perspective_data: dict[str, Any] = {}
    if isinstance(fact_data, dict):
        maybe_perspective = fact_data.get("perspective_synthesis")
        if isinstance(maybe_perspective, dict):
            perspective_data = maybe_perspective
    if not perspective_data and isinstance(acquisition_data, dict):
        maybe_acquisition_perspective = acquisition_data.get("perspective")
        if isinstance(maybe_acquisition_perspective, dict):
            perspective_data = maybe_acquisition_perspective

    # Build summary with fallback chain
    summary = ""
    if isinstance(perspective_data, dict):
        summary = str(perspective_data.get("summary") or "").strip()
    if not summary and isinstance(content_metadata, dict):
        summary = str(content_metadata.get("summary") or "").strip()
    if not summary and isinstance(intelligence_data, dict):
        transcript = str(intelligence_data.get("enhanced_transcript") or intelligence_data.get("transcript") or "")
        summary = transcript[:400].strip()
    if not summary:
        summary = "Summary unavailable"

    # Extract fact checks from verification or fact data
    fact_checks: dict[str, Any] = {}
    if isinstance(verification_data, dict):
        maybe_fact_checks = verification_data.get("fact_checks")
        if isinstance(maybe_fact_checks, dict):
            fact_checks = maybe_fact_checks
    if not fact_checks and isinstance(fact_data, dict):
        maybe_fact_checks = fact_data.get("fact_checks")
        if isinstance(maybe_fact_checks, dict):
            fact_checks = maybe_fact_checks

    # Extract logical fallacies from verification or fact data
    logical_fallacies: dict[str, Any] = {}
    if isinstance(verification_data, dict):
        maybe_fallacies = verification_data.get("logical_analysis")
        if isinstance(maybe_fallacies, dict):
            logical_fallacies = maybe_fallacies
    if not logical_fallacies and isinstance(fact_data, dict):
        maybe_fallacies = fact_data.get("logical_fallacies")
        if isinstance(maybe_fallacies, dict):
            logical_fallacies = maybe_fallacies

    # Extract deception score from threat data
    deception_score = None
    if isinstance(threat_data, dict):
        deception_score = threat_data.get("deception_score")
        if deception_score is None:
            metrics = threat_data.get("deception_metrics")
            if isinstance(metrics, dict):
                deception_score = metrics.get("deception_score")

    # Extract keywords/thematic insights
    keywords: list[Any] = []
    if isinstance(intelligence_data, dict):
        maybe_keywords = intelligence_data.get("thematic_insights")
        if isinstance(maybe_keywords, list):
            keywords = maybe_keywords

    # Build knowledge payload
    knowledge_payload: dict[str, Any] = {
        "url": source_url,
        "source_url": source_url,
        "title": title,
        "platform": platform,
        "analysis_summary": summary,
        "content_metadata": content_metadata if isinstance(content_metadata, dict) else {},
        "fact_check_results": fact_checks,
        "detected_fallacies": logical_fallacies,
        "verification_results": verification_data,
        "threat_assessment": threat_data,
        "behavioral_profile": behavioral_data,
        "perspective": perspective_data if isinstance(perspective_data, dict) else {},
        "keywords": keywords,
    }

    # Add optional fields if present
    if deception_score is not None:
        knowledge_payload["deception_score"] = deception_score

    transcript_index = intelligence_data.get("transcript_index") if isinstance(intelligence_data, dict) else {}
    if isinstance(transcript_index, dict) and transcript_index:
        knowledge_payload["transcript_index"] = transcript_index

    timeline_anchors = intelligence_data.get("timeline_anchors") if isinstance(intelligence_data, dict) else None
    if isinstance(timeline_anchors, list) and timeline_anchors:
        knowledge_payload["timeline_anchors"] = timeline_anchors

    return knowledge_payload


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
