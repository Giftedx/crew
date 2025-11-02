"""Multimodal Analysis Pipeline for Creator Intelligence.

This module provides the main orchestration pipeline that coordinates all analysis
services for comprehensive content understanding and intelligence generation.

Pipeline Flow:
1. Content Ingestion (MCP tools)
2. ASR Transcription
3. Speaker Diarization
4. Visual Parsing (OCR + Scene Analysis)
5. Topic Segmentation
6. Claim & Quote Extraction
7. Highlight Detection
8. Sentiment & Stance Analysis
9. Safety & Brand Suitability
10. Cross-Platform Deduplication
11. Artifact Publishing

Features:
- End-to-end content analysis orchestration
- Configurable analysis depth and speed
- Error handling and graceful degradation
- Integration with all analysis services
- Publishing of comprehensive reports

Dependencies:
- All analysis services (ASR, speaker, visual, topic, claim, highlight, sentiment, safety)
- Publishing service for report generation
- Vector DB for result storage
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the multimodal analysis pipeline."""

    # Analysis depth settings
    enable_asr: bool = True
    enable_speaker_diarization: bool = True
    enable_visual_parsing: bool = True
    enable_topic_segmentation: bool = True
    enable_claim_extraction: bool = True
    enable_highlight_detection: bool = True
    enable_sentiment_analysis: bool = True
    enable_safety_analysis: bool = True
    enable_deduplication: bool = True
    enable_publishing: bool = True

    # Performance settings
    model_quality: Literal["fast", "balanced", "quality"] = "balanced"
    max_processing_time: int = 300  # seconds
    enable_caching: bool = True

    # Output settings
    publish_reports: bool = True
    store_in_vector_db: bool = True
    generate_summary: bool = True


@dataclass
class PipelineResult:
    """Result of multimodal analysis pipeline execution."""

    success: bool
    total_processing_time: float
    analysis_results: dict[str, Any]
    published_reports: list[str]
    errors: list[str]
    warnings: list[str]
    metadata: dict[str, Any]


class MultimodalAnalysisPipeline:
    """Main orchestration pipeline for creator intelligence analysis.

    Usage:
        pipeline = MultimodalAnalysisPipeline()
        result = pipeline.analyze_content(content_url, config)
        reports = result.data["published_reports"]
    """

    def __init__(self):
        """Initialize the multimodal pipeline."""
        self._services_initialized = False
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all required analysis services."""
        try:
            # Import all services (lazy initialization)
            self._asr_service = None
            self._speaker_service = None
            self._visual_service = None
            self._topic_service = None
            self._claim_service = None
            self._highlight_service = None
            self._sentiment_service = None
            self._safety_service = None
            self._deduplication_service = None
            self._publishing_service = None

            self._services_initialized = True
            logger.info("All analysis services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize analysis services: {e}")
            self._services_initialized = False

    def analyze_content(
        self,
        content_url: str,
        platform: str = "youtube",
        config: PipelineConfig | None = None,
    ) -> StepResult:
        """Analyze content through the complete multimodal pipeline.

        Args:
            content_url: URL or path to content to analyze
            platform: Platform type (youtube, twitch, etc.)
            config: Pipeline configuration

        Returns:
            StepResult with complete analysis results
        """
        if config is None:
            config = PipelineConfig()

        if not self._services_initialized:
            return StepResult.fail("Pipeline services not initialized", status="internal_error")

        start_time = time.time()
        analysis_results = {}
        published_reports = []
        errors = []
        warnings = []

        try:
            logger.info(f"Starting multimodal analysis for {content_url} on {platform}")

            # Step 1: Content Ingestion (MCP-based)
            logger.info("Step 1: Content Ingestion")
            ingestion_result = self._ingest_content(content_url, platform)
            if not ingestion_result.success:
                errors.append(f"Content ingestion failed: {ingestion_result.error}")
            else:
                analysis_results["ingestion"] = ingestion_result.data
                logger.info("✅ Content ingestion completed")

            # Step 2: ASR Transcription
            if config.enable_asr and ingestion_result.success:
                logger.info("Step 2: ASR Transcription")
                transcript_result = self._perform_asr_analysis(
                    ingestion_result.data, config.model_quality, config.enable_caching
                )
                if transcript_result.success:
                    analysis_results["asr"] = transcript_result.data
                    logger.info("✅ ASR transcription completed")
                else:
                    errors.append(f"ASR analysis failed: {transcript_result.error}")
                    warnings.append("ASR transcription failed, continuing with other analysis")

            # Step 3: Speaker Diarization
            if config.enable_speaker_diarization and "asr" in analysis_results:
                logger.info("Step 3: Speaker Diarization")
                speaker_result = self._perform_speaker_analysis(
                    analysis_results["asr"], config.model_quality, config.enable_caching
                )
                if speaker_result.success:
                    analysis_results["speaker_diarization"] = speaker_result.data
                    logger.info("✅ Speaker diarization completed")
                else:
                    warnings.append(f"Speaker diarization failed: {speaker_result.error}")

            # Step 4: Visual Parsing
            if config.enable_visual_parsing and ingestion_result.success:
                logger.info("Step 4: Visual Parsing")
                visual_result = self._perform_visual_analysis(
                    ingestion_result.data, config.model_quality, config.enable_caching
                )
                if visual_result.success:
                    analysis_results["visual_parsing"] = visual_result.data
                    logger.info("✅ Visual parsing completed")
                else:
                    warnings.append(f"Visual parsing failed: {visual_result.error}")

            # Step 5: Topic Segmentation
            if config.enable_topic_segmentation and "asr" in analysis_results:
                logger.info("Step 5: Topic Segmentation")
                topic_result = self._perform_topic_analysis(
                    analysis_results["asr"], config.model_quality, config.enable_caching
                )
                if topic_result.success:
                    analysis_results["topic_segmentation"] = topic_result.data
                    logger.info("✅ Topic segmentation completed")
                else:
                    warnings.append(f"Topic segmentation failed: {topic_result.error}")

            # Step 6: Claim & Quote Extraction
            if config.enable_claim_extraction and "speaker_diarization" in analysis_results:
                logger.info("Step 6: Claim & Quote Extraction")
                claim_result = self._perform_claim_extraction(
                    analysis_results["speaker_diarization"],
                    config.model_quality,
                    config.enable_caching,
                )
                if claim_result.success:
                    analysis_results["claim_extraction"] = claim_result.data
                    logger.info("✅ Claim extraction completed")
                else:
                    warnings.append(f"Claim extraction failed: {claim_result.error}")

            # Step 7: Highlight Detection
            if config.enable_highlight_detection and "asr" in analysis_results:
                logger.info("Step 7: Highlight Detection")
                highlight_result = self._perform_highlight_detection(
                    analysis_results["asr"], config.model_quality, config.enable_caching
                )
                if highlight_result.success:
                    analysis_results["highlight_detection"] = highlight_result.data
                    logger.info("✅ Highlight detection completed")
                else:
                    warnings.append(f"Highlight detection failed: {highlight_result.error}")

            # Step 8: Sentiment & Stance Analysis
            if config.enable_sentiment_analysis and "asr" in analysis_results:
                logger.info("Step 8: Sentiment & Stance Analysis")
                sentiment_result = self._perform_sentiment_analysis(
                    analysis_results["asr"], config.model_quality, config.enable_caching
                )
                if sentiment_result.success:
                    analysis_results["sentiment_analysis"] = sentiment_result.data
                    logger.info("✅ Sentiment analysis completed")
                else:
                    warnings.append(f"Sentiment analysis failed: {sentiment_result.error}")

            # Step 9: Safety & Brand Suitability
            if config.enable_safety_analysis and "asr" in analysis_results:
                logger.info("Step 9: Safety & Brand Suitability Analysis")
                safety_result = self._perform_safety_analysis(
                    analysis_results["asr"], config.model_quality, config.enable_caching
                )
                if safety_result.success:
                    analysis_results["safety_analysis"] = safety_result.data
                    logger.info("✅ Safety analysis completed")
                else:
                    warnings.append(f"Safety analysis failed: {safety_result.error}")

            # Step 10: Cross-Platform Deduplication
            if config.enable_deduplication:
                logger.info("Step 10: Cross-Platform Deduplication")
                dedup_result = self._perform_deduplication_analysis(
                    analysis_results, config.model_quality, config.enable_caching
                )
                if dedup_result.success:
                    analysis_results["deduplication"] = dedup_result.data
                    logger.info("✅ Deduplication analysis completed")
                else:
                    warnings.append(f"Deduplication analysis failed: {dedup_result.error}")

            # Step 11: Artifact Publishing
            if config.enable_publishing:
                logger.info("Step 11: Artifact Publishing")
                publishing_result = self._publish_analysis_results(analysis_results, platform, config.model_quality)
                if publishing_result.success:
                    published_reports.extend(publishing_result.data.get("report_ids", []))
                    logger.info("✅ Artifact publishing completed")
                else:
                    warnings.append(f"Artifact publishing failed: {publishing_result.error}")

            total_time = time.time() - start_time

            # Check if we exceeded max processing time
            if total_time > config.max_processing_time:
                errors.append(f"Pipeline exceeded max processing time ({config.max_processing_time}s)")

            success = len(errors) == 0

            return StepResult.ok(
                data={
                    "success": success,
                    "total_processing_time": total_time,
                    "analysis_results": analysis_results,
                    "published_reports": published_reports,
                    "errors": errors,
                    "warnings": warnings,
                    "metadata": {
                        "content_url": content_url,
                        "platform": platform,
                        "config": config.__dict__,
                        "pipeline_version": "1.0.0",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return StepResult.fail(f"Pipeline execution failed: {e!s}", status="internal_error")

    def _ingest_content(self, content_url: str, platform: str) -> StepResult:
        """Ingest content from platform (placeholder for MCP integration).

        Args:
            content_url: Content URL or path
            platform: Platform type

        Returns:
            StepResult with ingestion data
        """
        # Placeholder for MCP-based content ingestion
        # In production, this would use the creator intelligence ingestion tools

        # Simulate content metadata
        ingestion_data = {
            "content_url": content_url,
            "platform": platform,
            "title": f"Content from {platform}",
            "duration": 3600.0,  # 1 hour placeholder
            "thumbnail_url": f"https://example.com/thumb/{platform}.jpg",
            "ingested_at": time.time(),
        }

        return StepResult.ok(data=ingestion_data)

    def _perform_asr_analysis(self, ingestion_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform ASR transcription analysis."""
        try:
            from analysis.transcription.asr_service import get_asr_service

            asr_service = get_asr_service()

            # Use ingestion data to determine audio path
            # In production, this would extract audio from video
            audio_path = ingestion_data.get("audio_path", "placeholder_audio.wav")

            result = asr_service.transcribe_audio(
                audio_path=audio_path,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"ASR analysis failed: {e}")
            return StepResult.fail(f"ASR analysis failed: {e!s}")

    def _perform_speaker_analysis(self, asr_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform speaker diarization analysis."""
        try:
            from analysis.transcription.speaker_diarization_service import (
                get_diarization_service,
            )

            diarization_service = get_diarization_service()

            # Use ASR segments for speaker analysis
            transcript_segments = asr_data.get("segments", [])

            if not transcript_segments:
                # Fallback: analyze entire transcript
                result = diarization_service.diarize_audio(
                    audio_path="placeholder_audio.wav",  # Would use actual audio
                    model=model,
                    use_cache=use_cache,
                )
            else:
                # Align with transcript segments
                result = diarization_service.diarize_with_transcript(
                    audio_path="placeholder_audio.wav",
                    transcript_path=None,
                    asr_service=None,  # Would pass actual ASR service
                    model=model,
                    use_cache=use_cache,
                )

            return result

        except Exception as e:
            logger.error(f"Speaker analysis failed: {e}")
            return StepResult.fail(f"Speaker analysis failed: {e!s}")

    def _perform_visual_analysis(self, ingestion_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform visual parsing analysis."""
        try:
            from analysis.vision.visual_parsing_service import (
                get_visual_parsing_service,
            )

            visual_service = get_visual_parsing_service()

            # Use thumbnail or video for visual analysis
            ingestion_data.get("thumbnail_url", "placeholder_image.jpg")

            result = visual_service.analyze_video(
                video_path="placeholder_video.mp4",  # Would use actual video
                model=model,
                extract_keyframes=True,
                perform_ocr=True,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Visual analysis failed: {e}")
            return StepResult.fail(f"Visual analysis failed: {e!s}")

    def _perform_topic_analysis(self, asr_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform topic segmentation analysis."""
        try:
            from analysis.topic.topic_segmentation_service import (
                get_topic_segmentation_service,
            )

            topic_service = get_topic_segmentation_service()

            # Use ASR transcript for topic analysis
            transcript_text = asr_data.get("text", "")

            result = topic_service.segment_text(
                text=transcript_text,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Topic analysis failed: {e}")
            return StepResult.fail(f"Topic analysis failed: {e!s}")

    def _perform_claim_extraction(self, speaker_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform claim and quote extraction analysis."""
        try:
            from analysis.nlp.claim_quote_extraction_service import (
                get_claim_quote_extraction_service,
            )

            extraction_service = get_claim_quote_extraction_service()

            # Use speaker segments for claim extraction
            speaker_segments = speaker_data.get("segments", [])

            result = extraction_service.extract_from_segments(
                segments=speaker_segments,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return StepResult.fail(f"Claim extraction failed: {e!s}")

    def _perform_highlight_detection(self, asr_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform highlight detection analysis."""
        try:
            from analysis.highlight.highlight_detection_service import (
                get_highlight_detection_service,
            )

            highlight_service = get_highlight_detection_service()

            # Use ASR data for highlight detection
            transcript_segments = asr_data.get("segments", [])

            result = highlight_service.detect_highlights(
                transcript_segments=transcript_segments,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Highlight detection failed: {e}")
            return StepResult.fail(f"Highlight detection failed: {e!s}")

    def _perform_sentiment_analysis(self, asr_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform sentiment and stance analysis."""
        try:
            from analysis.sentiment.sentiment_stance_analysis_service import (
                get_sentiment_stance_analysis_service,
            )

            sentiment_service = get_sentiment_stance_analysis_service()

            # Use ASR segments for sentiment analysis
            transcript_segments = asr_data.get("segments", [])

            result = sentiment_service.analyze_segments(
                segments=transcript_segments,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return StepResult.fail(f"Sentiment analysis failed: {e!s}")

    def _perform_safety_analysis(self, asr_data: dict[str, Any], model: str, use_cache: bool) -> StepResult:
        """Perform safety and brand suitability analysis."""
        try:
            from analysis.safety.safety_brand_suitability_service import (
                get_safety_brand_suitability_service,
            )

            safety_service = get_safety_brand_suitability_service()

            # Use ASR segments for safety analysis
            transcript_segments = asr_data.get("segments", [])

            result = safety_service.analyze_segments(
                segments=transcript_segments,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Safety analysis failed: {e}")
            return StepResult.fail(f"Safety analysis failed: {e!s}")

    def _perform_deduplication_analysis(
        self, analysis_results: dict[str, Any], model: str, use_cache: bool
    ) -> StepResult:
        """Perform cross-platform deduplication analysis."""
        try:
            from analysis.deduplication.cross_platform_deduplication_service import (
                get_cross_platform_deduplication_service,
            )

            deduplication_service = get_cross_platform_deduplication_service()

            # Collect text items for deduplication
            text_items = []
            for analysis_type, result_data in analysis_results.items():
                if analysis_type == "asr":
                    # Add transcript segments
                    segments = result_data.get("segments", [])
                    for segment in segments:
                        text_items.append(
                            {
                                "id": f"transcript_{segment.get('start_time', 0)}",
                                "text": segment.get("text", ""),
                                "platform": "transcript",
                            }
                        )

            result = deduplication_service.find_duplicates(
                text_items=text_items,
                similarity_threshold=0.8,
                model=model,
                use_cache=use_cache,
            )

            return result

        except Exception as e:
            logger.error(f"Deduplication analysis failed: {e}")
            return StepResult.fail(f"Deduplication analysis failed: {e!s}")

    def _publish_analysis_results(self, analysis_results: dict[str, Any], platform: str, model: str) -> StepResult:
        """Publish analysis results to configured platforms."""
        try:
            from publishing.artifact_publishing_service import (
                get_artifact_publishing_service,
            )

            publishing_service = get_artifact_publishing_service()
            published_reports = []

            # Publish highlight summary if available
            if "highlight_detection" in analysis_results:
                highlight_data = analysis_results["highlight_detection"]
                highlights = highlight_data.get("highlights", [])

                if highlights:
                    result = publishing_service.publish_highlight_summary(
                        highlights=highlights,
                        episode_info={"platform": platform},
                    )
                    if result.success:
                        published_reports.append(f"highlight_summary_{result.data['artifact_id']}")

            # Publish claim summary if available
            if "claim_extraction" in analysis_results:
                claim_data = analysis_results["claim_extraction"]
                claims = claim_data.get("claims", [])
                quotes = claim_data.get("quotes", [])

                if claims or quotes:
                    result = publishing_service.publish_claim_summary(
                        claims=claims,
                        quotes=quotes,
                        episode_info={"platform": platform},
                    )
                    if result.success:
                        published_reports.append(f"claim_summary_{result.data['artifact_id']}")

            # Publish comprehensive analysis report
            result = publishing_service.publish_report(
                report_data={
                    "platform": platform,
                    "analysis_types": list(analysis_results.keys()),
                    "model_quality": model,
                },
                report_type="comprehensive",
            )
            if result.success:
                published_reports.append(f"comprehensive_report_{result.data['artifact_id']}")

            return StepResult.ok(data={"report_ids": published_reports})

        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            return StepResult.fail(f"Publishing failed: {e!s}")

    def get_pipeline_status(self) -> StepResult:
        """Get the current status of the pipeline and all services.

        Returns:
            StepResult with pipeline status information
        """
        try:
            status_info = {
                "services_initialized": self._services_initialized,
                "available_services": [],
                "service_health": {},
            }

            # Check each service availability
            service_checks = [
                ("ASR", "analysis.transcription.asr_service"),
                (
                    "Speaker Diarization",
                    "analysis.transcription.speaker_diarization_service",
                ),
                ("Visual Parsing", "analysis.vision.visual_parsing_service"),
                ("Topic Segmentation", "analysis.topic.topic_segmentation_service"),
                ("Claim Extraction", "analysis.nlp.claim_quote_extraction_service"),
                (
                    "Highlight Detection",
                    "analysis.highlight.highlight_detection_service",
                ),
                (
                    "Sentiment Analysis",
                    "analysis.sentiment.sentiment_stance_analysis_service",
                ),
                ("Safety Analysis", "analysis.safety.safety_brand_suitability_service"),
                (
                    "Deduplication",
                    "analysis.deduplication.cross_platform_deduplication_service",
                ),
                ("Publishing", "publishing.artifact_publishing_service"),
            ]

            for service_name, module_path in service_checks:
                try:
                    __import__(module_path)
                    status_info["available_services"].append(service_name)
                    status_info["service_health"][service_name] = "available"
                except ImportError:
                    status_info["service_health"][service_name] = "unavailable"
                except Exception as e:
                    status_info["service_health"][service_name] = f"error: {e!s}"

            return StepResult.ok(data=status_info)

        except Exception as e:
            logger.error(f"Pipeline status check failed: {e}")
            return StepResult.fail(f"Pipeline status check failed: {e!s}")


# Singleton instance
_pipeline: MultimodalAnalysisPipeline | None = None


def get_multimodal_analysis_pipeline() -> MultimodalAnalysisPipeline:
    """Get singleton pipeline instance.

    Returns:
        Initialized MultimodalAnalysisPipeline instance
    """
    global _pipeline

    if _pipeline is None:
        _pipeline = MultimodalAnalysisPipeline()

    return _pipeline
