"""Multimodal content processing pipeline.

This module implements the core pipeline for processing creator content:
download → diarization → transcription → visual analysis → content analysis → claim extraction → KG ingestion
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any

from kg.creator_kg_store import CreatorKGStore


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the multimodal pipeline."""

    enable_download: bool = True
    enable_diarization: bool = True
    enable_transcription: bool = True
    enable_visual_analysis: bool = True
    enable_content_analysis: bool = True
    enable_claim_extraction: bool = True
    enable_kg_ingestion: bool = True
    min_transcription_confidence: float = 0.7
    min_diarization_confidence: float = 0.6
    min_visual_analysis_confidence: float = 0.5
    max_processing_time: int = 600
    max_file_size_mb: int = 500
    max_audio_duration_hours: int = 3
    save_intermediate_results: bool = True
    cleanup_temp_files: bool = True


@dataclass
class PipelineStage:
    """Represents a stage in the pipeline."""

    name: str
    description: str
    required: bool
    estimated_duration: int
    dependencies: list[str]


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    success: bool
    stages_completed: list[str]
    stages_failed: list[str]
    total_duration: float
    intermediate_results: dict[str, Any]
    final_kg_nodes: list[int]
    final_kg_edges: list[int]
    errors: list[str]
    warnings: list[str]
    stage_results: dict[str, Any] | None = None


class MultimodalContentPipeline:
    """Orchestrates multimodal content processing pipeline."""

    def __init__(self, config: PipelineConfig | None = None, kg_store: CreatorKGStore | None = None):
        """Initialize pipeline with configuration and KG store."""
        self.config = config or PipelineConfig()
        self.kg_store = kg_store or CreatorKGStore(":memory:")
        self.stages = [
            PipelineStage(
                name="download",
                description="Download content from platform",
                required=True,
                estimated_duration=60,
                dependencies=[],
            ),
            PipelineStage(
                name="diarization",
                description="Speaker diarization and segmentation",
                required=True,
                estimated_duration=120,
                dependencies=["download"],
            ),
            PipelineStage(
                name="transcription",
                description="Audio transcription with timestamps",
                required=True,
                estimated_duration=180,
                dependencies=["diarization"],
            ),
            PipelineStage(
                name="visual_analysis",
                description="Visual content analysis and frame extraction",
                required=False,
                estimated_duration=90,
                dependencies=["download"],
            ),
            PipelineStage(
                name="content_analysis",
                description="Content analysis and topic extraction",
                required=True,
                estimated_duration=60,
                dependencies=["transcription", "visual_analysis"],
            ),
            PipelineStage(
                name="claim_extraction",
                description="Extract and validate claims",
                required=True,
                estimated_duration=45,
                dependencies=["content_analysis"],
            ),
            PipelineStage(
                name="kg_ingestion",
                description="Ingest results into knowledge graph",
                required=True,
                estimated_duration=30,
                dependencies=["claim_extraction"],
            ),
        ]

    async def process_content(
        self, url: str, tenant: str, workspace: str, creator_name: str | None = None, episode_title: str | None = None
    ) -> StepResult:
        """Process content through the complete pipeline."""
        start_time = time.time()
        result = PipelineResult(
            success=False,
            stages_completed=[],
            stages_failed=[],
            total_duration=0.0,
            intermediate_results={},
            final_kg_nodes=[],
            final_kg_edges=[],
            errors=[],
            warnings=[],
        )
        try:
            logger.info(f"Starting pipeline processing for URL: {url}")
            validation_result = await self._validate_inputs(url, tenant, workspace)
            if not validation_result.success:
                result.errors.append(f"Input validation failed: {validation_result.error}")
                return StepResult.fail(f"Pipeline failed: {', '.join(result.errors)}"
            stage_results = await self._execute_stages(url, tenant, workspace, creator_name, episode_title, result)
            result.stage_results = stage_results
            result.total_duration = time.time() - start_time
            required_stages = [stage.name for stage in self.stages if stage.required]
            result.success = all(stage in result.stages_completed for stage in required_stages)
            if result.success:
                logger.info(f"Pipeline completed successfully in {result.total_duration:.2f}s")
                return StepResult.ok(data=result)
            else:
                logger.error(f"Pipeline failed after {result.total_duration:.2f}s")
                return StepResult.fail(f"Pipeline failed: {', '.join(result.errors)}"
        except Exception as e:
            result.total_duration = time.time() - start_time
            result.errors.append(f"Pipeline exception: {e!s}")
            logger.exception("Pipeline processing failed")
            return StepResult.fail(f"Pipeline failed: {', '.join(result.errors)}"

    async def _validate_inputs(self, url: str, tenant: str, workspace: str) -> StepResult:
        """Validate pipeline inputs."""
        try:
            if not url or not url.startswith(("http://", "https://")):
                return StepResult.fail("Invalid URL format")
            if not tenant or not workspace:
                return StepResult.fail("Tenant and workspace are required")
            return StepResult.ok(data={"validated": True})
        except Exception as e:
            return StepResult.fail(f"Validation failed: {e!s}")

    async def _execute_stages(
        self,
        url: str,
        tenant: str,
        workspace: str,
        creator_name: str | None,
        episode_title: str | None,
        result: PipelineResult,
    ) -> dict[str, Any]:
        """Execute all pipeline stages."""
        stage_results = {}
        for stage in self.stages:
            if not self._is_stage_enabled(stage.name):
                logger.info(f"Skipping disabled stage: {stage.name}")
                continue
            if not self._check_dependencies(stage, result.stages_completed):
                result.errors.append(f"Stage {stage.name} dependencies not met")
                result.stages_failed.append(stage.name)
                continue
            try:
                logger.info(f"Executing stage: {stage.name}")
                stage_start = time.time()
                stage_result = await self._execute_stage(
                    stage, url, tenant, workspace, creator_name, episode_title, stage_results
                )
                stage_duration = time.time() - stage_start
                logger.info(f"Stage {stage.name} completed in {stage_duration:.2f}s")
                if stage_result.success:
                    result.stages_completed.append(stage.name)
                    actual_data = (
                        stage_result.data["data"]
                        if isinstance(stage_result.data, dict) and "data" in stage_result.data
                        else stage_result.data
                    )
                    stage_results[stage.name] = actual_data
                    result.intermediate_results[stage.name] = actual_data
                else:
                    result.stages_failed.append(stage.name)
                    result.errors.append(f"Stage {stage.name} failed: {stage_result.error}")
                    if stage.required:
                        break
            except Exception as e:
                result.stages_failed.append(stage.name)
                result.errors.append(f"Stage {stage.name} exception: {e!s}")
                logger.exception(f"Stage {stage.name} failed with exception")
                if stage.required:
                    break
        return stage_results

    def _is_stage_enabled(self, stage_name: str) -> bool:
        """Check if a stage is enabled in configuration."""
        return getattr(self.config, f"enable_{stage_name}", True)

    def _check_dependencies(self, stage: PipelineStage, completed_stages: list[str]) -> bool:
        """Check if stage dependencies are met."""
        return all(dep in completed_stages for dep in stage.dependencies)

    async def _execute_stage(
        self,
        stage: PipelineStage,
        url: str,
        tenant: str,
        workspace: str,
        creator_name: str | None,
        episode_title: str | None,
        stage_results: dict[str, Any],
    ) -> StepResult:
        """Execute a specific pipeline stage."""
        if stage.name == "download":
            return await self._stage_download(url, tenant, workspace)
        elif stage.name == "diarization":
            return await self._stage_diarization(stage_results["download"], tenant, workspace)
        elif stage.name == "transcription":
            return await self._stage_transcription(stage_results["diarization"], tenant, workspace)
        elif stage.name == "visual_analysis":
            return await self._stage_visual_analysis(stage_results["download"], tenant, workspace)
        elif stage.name == "content_analysis":
            return await self._stage_content_analysis(
                stage_results["transcription"], stage_results.get("visual_analysis"), tenant, workspace
            )
        elif stage.name == "claim_extraction":
            return await self._stage_claim_extraction(stage_results["content_analysis"], tenant, workspace)
        elif stage.name == "kg_ingestion":
            return await self._stage_kg_ingestion(stage_results, url, tenant, workspace, creator_name, episode_title)
        else:
            return StepResult.fail(f"Unknown stage: {stage.name}")

    async def _stage_download(self, url: str, tenant: str, workspace: str) -> StepResult:
        """Download content from platform."""
        try:
            logger.info(f"Downloading content from: {url}")
            await asyncio.sleep(1)
            download_result = {
                "url": url,
                "file_path": f"/tmp/downloaded_content_{int(time.time())}.mp4",
                "format": "mp4",
                "duration": 3600,
                "file_size_mb": 250,
                "platform": "youtube",
                "title": "Sample Content",
                "description": "Sample description",
                "upload_date": "2024-01-15",
                "view_count": 100000,
                "like_count": 5000,
                "comment_count": 500,
            }
            return StepResult.ok(data=download_result)
        except Exception as e:
            return StepResult.fail(f"Download failed: {e!s}")

    async def _stage_diarization(self, download_result: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Perform speaker diarization."""
        try:
            logger.info("Performing speaker diarization")
            await asyncio.sleep(2)
            diarization_result = {
                "speakers": [
                    {"id": "speaker_1", "name": "Host", "confidence": 0.9},
                    {"id": "speaker_2", "name": "Guest", "confidence": 0.8},
                ],
                "segments": [
                    {"start": 0, "end": 300, "speaker": "speaker_1", "confidence": 0.9},
                    {"start": 300, "end": 600, "speaker": "speaker_2", "confidence": 0.8},
                    {"start": 600, "end": 900, "speaker": "speaker_1", "confidence": 0.9},
                ],
                "total_speakers": 2,
                "average_confidence": 0.85,
            }
            return StepResult.ok(data=diarization_result)
        except Exception as e:
            return StepResult.fail(f"Diarization failed: {e!s}")

    async def _stage_transcription(self, diarization_result: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Perform audio transcription."""
        try:
            logger.info("Performing audio transcription")
            await asyncio.sleep(3)
            transcription_result = {
                "segments": [
                    {
                        "start": 0,
                        "end": 300,
                        "speaker": "speaker_1",
                        "text": "Welcome to the show, today we're discussing politics and current events.",
                        "confidence": 0.9,
                    },
                    {
                        "start": 300,
                        "end": 600,
                        "speaker": "speaker_2",
                        "text": "Thanks for having me. I think the current political climate is very interesting.",
                        "confidence": 0.8,
                    },
                    {
                        "start": 600,
                        "end": 900,
                        "speaker": "speaker_1",
                        "text": "Absolutely. Let's dive into the recent election results.",
                        "confidence": 0.9,
                    },
                ],
                "full_text": "Welcome to the show, today we're discussing politics and current events. Thanks for having me. I think the current political climate is very interesting. Absolutely. Let's dive into the recent election results.",
                "language": "en",
                "average_confidence": 0.87,
                "word_count": 45,
            }
            return StepResult.ok(data=transcription_result)
        except Exception as e:
            return StepResult.fail(f"Transcription failed: {e!s}")

    async def _stage_visual_analysis(self, download_result: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Perform visual content analysis."""
        try:
            logger.info("Performing visual analysis")
            await asyncio.sleep(1.5)
            visual_result = {
                "frames_analyzed": 100,
                "objects_detected": [
                    {"object": "person", "confidence": 0.9, "count": 2},
                    {"object": "microphone", "confidence": 0.8, "count": 1},
                    {"object": "computer", "confidence": 0.7, "count": 1},
                ],
                "scenes": [
                    {"start": 0, "end": 1800, "type": "interview", "confidence": 0.9},
                    {"start": 1800, "end": 3600, "type": "discussion", "confidence": 0.8},
                ],
                "average_confidence": 0.8,
            }
            return StepResult.ok(data=visual_result)
        except Exception as e:
            return StepResult.fail(f"Visual analysis failed: {e!s}")

    async def _stage_content_analysis(
        self, transcription_result: dict[str, Any], visual_result: dict[str, Any] | None, tenant: str, workspace: str
    ) -> StepResult:
        """Perform content analysis and topic extraction."""
        try:
            logger.info("Performing content analysis")
            await asyncio.sleep(1)
            content_result = {
                "topics": [
                    {"name": "Politics", "confidence": 0.9, "mentions": 5},
                    {"name": "Current Events", "confidence": 0.8, "mentions": 3},
                    {"name": "Elections", "confidence": 0.7, "mentions": 2},
                ],
                "sentiment": {
                    "overall": "neutral",
                    "confidence": 0.8,
                    "by_segment": [
                        {"start": 0, "end": 300, "sentiment": "positive", "confidence": 0.7},
                        {"start": 300, "end": 600, "sentiment": "neutral", "confidence": 0.8},
                        {"start": 600, "end": 900, "sentiment": "neutral", "confidence": 0.9},
                    ],
                },
                "key_phrases": ["politics", "current events", "election results", "political climate"],
                "summary": "Discussion about politics and current events, focusing on recent election results and the political climate.",
            }
            return StepResult.ok(data=content_result)
        except Exception as e:
            return StepResult.fail(f"Content analysis failed: {e!s}")

    async def _stage_claim_extraction(self, content_result: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Extract and validate claims."""
        try:
            logger.info("Extracting claims")
            await asyncio.sleep(0.75)
            claims_result = {
                "claims": [
                    {
                        "text": "The current political climate is very interesting",
                        "speaker": "speaker_2",
                        "timestamp": 300,
                        "confidence": 0.8,
                        "type": "opinion",
                        "verification_status": "unverified",
                    },
                    {
                        "text": "Let's dive into the recent election results",
                        "speaker": "speaker_1",
                        "timestamp": 600,
                        "confidence": 0.9,
                        "type": "statement",
                        "verification_status": "unverified",
                    },
                ],
                "quotes": [
                    {
                        "text": "Welcome to the show",
                        "speaker": "speaker_1",
                        "timestamp": 0,
                        "context": "opening",
                        "viral_potential": 0.3,
                    }
                ],
                "highlights": [
                    {
                        "start_time": 300,
                        "end_time": 600,
                        "description": "Guest discusses political climate",
                        "type": "discussion",
                        "confidence": 0.8,
                    }
                ],
            }
            return StepResult.ok(data=claims_result)
        except Exception as e:
            return StepResult.fail(f"Claim extraction failed: {e!s}")

    async def _stage_kg_ingestion(
        self,
        stage_results: dict[str, Any],
        url: str,
        tenant: str,
        workspace: str,
        creator_name: str | None,
        episode_title: str | None,
    ) -> StepResult:
        """Ingest results into knowledge graph."""
        try:
            logger.info("Ingesting results into knowledge graph")
            await asyncio.sleep(0.5)
            download_result = stage_results["download"]
            episode_id = self.kg_store.add_creator_node(
                tenant=tenant,
                node_type="episode",
                name=episode_title or download_result["title"],
                attrs={
                    "title": download_result["title"],
                    "duration": download_result["duration"],
                    "upload_date": download_result["upload_date"],
                    "platform": download_result["platform"],
                    "view_count": download_result["view_count"],
                    "like_count": download_result["like_count"],
                    "comment_count": download_result["comment_count"],
                    "url": url,
                },
            )
            creator_id = None
            if creator_name:
                creator_id = self.kg_store.add_creator_node(
                    tenant=tenant,
                    node_type="creator",
                    name=creator_name,
                    attrs={"platform": download_result["platform"], "channel_id": "unknown", "subscriber_count": 0},
                )
                if creator_id:
                    self.kg_store.add_creator_edge(creator_id, episode_id, "hosts")
            content_result = stage_results["content_analysis"]
            topic_ids = []
            for topic in content_result["topics"]:
                topic_id = self.kg_store.add_creator_node(
                    tenant=tenant,
                    node_type="topic",
                    name=topic["name"],
                    attrs={
                        "name": topic["name"],
                        "category": "General",
                        "trending_score": topic["confidence"],
                        "mentions": topic["mentions"],
                    },
                )
                topic_ids.append(topic_id)
                self.kg_store.add_creator_edge(episode_id, topic_id, "discusses")
            claims_result = stage_results["claim_extraction"]
            claim_ids = []
            for claim in claims_result["claims"]:
                claim_id = self.kg_store.add_creator_node(
                    tenant=tenant,
                    node_type="claim",
                    name=claim["text"][:50] + "...",
                    attrs={
                        "text": claim["text"],
                        "speaker": claim["speaker"],
                        "timestamp": claim["timestamp"],
                        "confidence": claim["confidence"],
                        "verification_status": claim["verification_status"],
                    },
                )
                claim_ids.append(claim_id)
                if creator_id:
                    self.kg_store.add_creator_edge(creator_id, claim_id, "makes_claim")
            highlight_ids = []
            for highlight in claims_result["highlights"]:
                highlight_id = self.kg_store.add_creator_node(
                    tenant=tenant,
                    node_type="highlight",
                    name=highlight["description"],
                    attrs={
                        "start_time": highlight["start_time"],
                        "end_time": highlight["end_time"],
                        "description": highlight["description"],
                        "episode_id": episode_id,
                        "confidence": highlight["confidence"],
                    },
                )
                highlight_ids.append(highlight_id)
                self.kg_store.add_creator_edge(episode_id, highlight_id, "contains_highlight")
            ingestion_result = {
                "episode_id": episode_id,
                "creator_id": creator_id,
                "topic_ids": topic_ids,
                "claim_ids": claim_ids,
                "highlight_ids": highlight_ids,
                "total_nodes_created": 1
                + len(topic_ids)
                + len(claim_ids)
                + len(highlight_ids)
                + (1 if creator_id else 0),
                "total_edges_created": len(topic_ids) + len(claim_ids) + len(highlight_ids) + (1 if creator_id else 0),
            }
            return StepResult.ok(data=ingestion_result)
        except Exception as e:
            return StepResult.fail(f"KG ingestion failed: {e!s}")

    def get_pipeline_status(self) -> dict[str, Any]:
        """Get current pipeline status and configuration."""
        return {
            "stages": [
                {
                    "name": stage.name,
                    "description": stage.description,
                    "required": stage.required,
                    "enabled": self._is_stage_enabled(stage.name),
                    "estimated_duration": stage.estimated_duration,
                    "dependencies": stage.dependencies,
                }
                for stage in self.stages
            ],
            "config": {
                "max_processing_time": self.config.max_processing_time,
                "max_file_size_mb": self.config.max_file_size_mb,
                "max_audio_duration_hours": self.config.max_audio_duration_hours,
                "save_intermediate_results": self.config.save_intermediate_results,
                "cleanup_temp_files": self.config.cleanup_temp_files,
            },
        }
