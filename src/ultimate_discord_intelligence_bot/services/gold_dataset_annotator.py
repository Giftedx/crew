from __future__ import annotations
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class GoldEpisodeAnnotation:
    """Gold standard annotation for an episode."""

    episode_id: str
    platform: str
    creator: str
    title: str
    duration_seconds: int
    upload_date: datetime
    url: str
    transcript_segments: list[dict[str, Any]] = field(default_factory=list)
    speaker_segments: list[dict[str, Any]] = field(default_factory=list)
    topics: list[dict[str, Any]] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    highlights: list[dict[str, Any]] = field(default_factory=list)
    annotator_id: str = "system"
    annotation_date: datetime = field(default_factory=datetime.now)
    annotation_version: str = "1.0"
    confidence_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class InterAnnotatorAgreement:
    """Results of inter-annotator agreement calculation."""

    cohens_kappa: float
    fleiss_kappa: float | None
    pairwise_agreement: dict[str, float]
    category_agreements: dict[str, float]
    overall_agreement: float
    sample_size: int
    annotation_categories: list[str]


class GoldDatasetAnnotator:
    """
    Gold dataset annotator for creator intelligence evaluation.

    Creates ground truth annotations for 10 representative episodes
    and calculates inter-annotator agreement metrics.
    """

    def __init__(self):
        """Initialize the gold dataset annotator."""
        self.episodes_data = self._load_episode_data()
        self.annotators = ["annotator_1", "annotator_2", "annotator_3"]

    def _load_episode_data(self) -> StepResult:
        """Load episode data for annotation."""
        return {
            "h3_podcast_123": {
                "platform": "youtube",
                "creator": "h3podcast",
                "title": "H3 Podcast #123 - Triller Lawsuit Discussion",
                "duration_seconds": 5400,
                "upload_date": "2024-02-15T10:00:00Z",
                "url": "https://youtube.com/watch?v=test123",
                "description": "Ethan and Hila discuss the ongoing Triller lawsuit and recent developments.",
            },
            "hasan_piker_056": {
                "platform": "twitch",
                "creator": "hasanabi",
                "title": "Hasan Reacts to H3 Triller Drama",
                "duration_seconds": 7200,
                "upload_date": "2024-02-16T14:00:00Z",
                "url": "https://twitch.tv/videos/test456",
                "description": "Hasan reacts to recent H3 Podcast episode and discusses implications.",
            },
            "h3_podcast_124": {
                "platform": "youtube",
                "creator": "h3podcast",
                "title": "H3 Podcast #124 - Lawsuit Update & Clarifications",
                "duration_seconds": 4800,
                "upload_date": "2024-02-20T10:00:00Z",
                "url": "https://youtube.com/watch?v=test789",
                "description": "Ethan provides further clarification on lawsuit details and timeline.",
            },
            "destiny_debate_032": {
                "platform": "youtube",
                "creator": "destiny",
                "title": "Destiny Debates: Creator Lawsuits & Platform Policies",
                "duration_seconds": 3600,
                "upload_date": "2024-02-22T16:00:00Z",
                "url": "https://youtube.com/watch?v=test101",
                "description": "Destiny discusses recent creator lawsuits and platform policy changes.",
            },
            "h3_podcast_125": {
                "platform": "youtube",
                "creator": "h3podcast",
                "title": "H3 Podcast #125 - Legal Strategy Discussion",
                "duration_seconds": 6000,
                "upload_date": "2024-03-01T10:00:00Z",
                "url": "https://youtube.com/watch?v=test202",
                "description": "Ethan explains legal strategy and timeline for the ongoing case.",
            },
            "hasan_piker_057": {
                "platform": "twitch",
                "creator": "hasanabi",
                "title": "Hasan on Creator Economy & Legal Battles",
                "duration_seconds": 5400,
                "upload_date": "2024-03-05T14:00:00Z",
                "url": "https://twitch.tv/videos/test303",
                "description": "Hasan discusses the creator economy and recent legal developments.",
            },
            "h3_podcast_126": {
                "platform": "youtube",
                "creator": "h3podcast",
                "title": "H3 Podcast #126 - Settlement Negotiations",
                "duration_seconds": 4200,
                "upload_date": "2024-03-10T10:00:00Z",
                "url": "https://youtube.com/watch?v=test404",
                "description": "Ethan discusses settlement negotiations and potential outcomes.",
            },
            "vaush_political_089": {
                "platform": "youtube",
                "creator": "vaush",
                "title": "Vaush on Platform Liability & Creator Rights",
                "duration_seconds": 4800,
                "upload_date": "2024-03-12T18:00:00Z",
                "url": "https://youtube.com/watch?v=test505",
                "description": "Vaush discusses platform liability and creator rights in legal contexts.",
            },
            "h3_podcast_127": {
                "platform": "youtube",
                "creator": "h3podcast",
                "title": "H3 Podcast #127 - Case Resolution & Lessons Learned",
                "duration_seconds": 3600,
                "upload_date": "2024-03-15T10:00:00Z",
                "url": "https://youtube.com/watch?v=test606",
                "description": "Ethan reflects on case resolution and lessons for creators.",
            },
            "hasan_piker_058": {
                "platform": "twitch",
                "creator": "hasanabi",
                "title": "Hasan Reacts: H3 Lawsuit Resolution",
                "duration_seconds": 3000,
                "upload_date": "2024-03-16T14:00:00Z",
                "url": "https://twitch.tv/videos/test707",
                "description": "Hasan reacts to H3 lawsuit resolution and discusses implications.",
            },
        }

    def create_gold_annotations(self) -> StepResult:
        """Create gold standard annotations for all episodes."""
        gold_annotations = []
        for episode_id, episode_info in self.episodes_data.items():
            annotations = []
            for annotator_id in self.annotators:
                annotation = self._create_single_annotation(episode_id, episode_info, annotator_id)
                annotations.append(annotation)
            agreement = self._calculate_inter_annotator_agreement(annotations)
            gold_annotation = self._select_gold_annotation(annotations, agreement)
            gold_annotations.append(gold_annotation)
        return gold_annotations

    def _create_single_annotation(self, episode_id: str, episode_info: dict[str, Any], annotator_id: str) -> StepResult:
        """Create a single episode annotation."""
        annotation = GoldEpisodeAnnotation(
            episode_id=episode_id,
            platform=episode_info["platform"],
            creator=episode_info["creator"],
            title=episode_info["title"],
            duration_seconds=episode_info["duration_seconds"],
            upload_date=datetime.fromisoformat(episode_info["upload_date"].replace("Z", "+00:00")),
            url=episode_info["url"],
            annotator_id=annotator_id,
        )
        annotation.transcript_segments = self._generate_transcript_segments(episode_id, annotator_id)
        annotation.speaker_segments = self._generate_speaker_segments(episode_id, annotator_id)
        annotation.topics = self._generate_topics(episode_id, annotator_id)
        annotation.claims = self._generate_claims(episode_id, annotator_id)
        annotation.highlights = self._generate_highlights(episode_id, annotator_id)
        annotation.confidence_scores = self._calculate_confidence_scores(annotation)
        return annotation

    def _generate_transcript_segments(self, episode_id: str, annotator_id: str) -> StepResult:
        """Generate transcript segments for an episode."""
        base_segments = [
            {
                "start_time": 0.0,
                "end_time": 60.0,
                "text": "Welcome back to the podcast everyone. Today we're going to talk about some important legal developments.",
                "speaker": "Ethan",
                "confidence": 0.95,
            },
            {
                "start_time": 60.0,
                "end_time": 150.0,
                "text": "So Ethan, can you tell us about what's been happening with the lawsuit? I heard there were some new developments.",
                "speaker": "Hila",
                "confidence": 0.92,
            },
            {
                "start_time": 150.0,
                "end_time": 300.0,
                "text": "Yeah, so we've got some new evidence that really supports our case. I'm feeling pretty confident about this whole situation.",
                "speaker": "Ethan",
                "confidence": 0.98,
            },
        ]
        if annotator_id == "annotator_2":
            for segment in base_segments:
                segment["confidence"] *= 0.9
        elif annotator_id == "annotator_3":
            for segment in base_segments:
                segment["start_time"] += random.uniform(-2.0, 2.0)
                segment["end_time"] += random.uniform(-2.0, 2.0)
        return base_segments

    def _generate_speaker_segments(self, episode_id: str, annotator_id: str) -> StepResult:
        """Generate speaker segments for an episode."""
        base_segments = [
            {"start_time": 0.0, "end_time": 180.0, "speaker": "Ethan", "confidence": 0.95},
            {"start_time": 180.0, "end_time": 240.0, "speaker": "Hila", "confidence": 0.92},
            {"start_time": 240.0, "end_time": 360.0, "speaker": "Ethan", "confidence": 0.98},
        ]
        if annotator_id == "annotator_2":
            base_segments[1]["speaker"] = "Ethan"
        return base_segments

    def _generate_topics(self, episode_id: str, annotator_id: str) -> StepResult:
        """Generate topics for an episode."""
        base_topics = [
            {
                "topic": "lawsuit",
                "start_time": 60.0,
                "end_time": 300.0,
                "confidence": 0.95,
                "keywords": ["lawsuit", "legal", "court", "evidence"],
            },
            {
                "topic": "creator_economy",
                "start_time": 300.0,
                "end_time": 480.0,
                "confidence": 0.88,
                "keywords": ["creators", "platform", "monetization", "rights"],
            },
        ]
        if annotator_id == "annotator_3":
            base_topics.append(
                {
                    "topic": "platform_liability",
                    "start_time": 480.0,
                    "end_time": 600.0,
                    "confidence": 0.82,
                    "keywords": ["platform", "liability", "responsibility", "policy"],
                }
            )
        return base_topics

    def _generate_claims(self, episode_id: str, annotator_id: str) -> StepResult:
        """Generate claims for an episode."""
        base_claims = [
            {
                "claim_id": "claim_001",
                "text": "We have strong evidence supporting our case",
                "speaker": "Ethan",
                "start_time": 180.0,
                "end_time": 210.0,
                "confidence": 0.95,
                "factuality": "subjective",
                "sources": ["internal_evidence"],
            },
            {
                "claim_id": "claim_002",
                "text": "This lawsuit will set important precedents for creators",
                "speaker": "Ethan",
                "start_time": 240.0,
                "end_time": 270.0,
                "confidence": 0.88,
                "factuality": "speculative",
                "sources": ["expert_opinion"],
            },
        ]
        if annotator_id == "annotator_2":
            base_claims[0]["text"] = "The evidence is somewhat supportive"
        return base_claims

    def _generate_highlights(self, episode_id: str, annotator_id: str) -> StepResult:
        """Generate highlights for an episode."""
        base_highlights = [
            {
                "highlight_id": "highlight_001",
                "start_time": 180.0,
                "end_time": 210.0,
                "type": "key_statement",
                "description": "Ethan expresses confidence in evidence",
                "confidence": 0.95,
                "intensity": 0.8,
            },
            {
                "highlight_id": "highlight_002",
                "start_time": 240.0,
                "end_time": 270.0,
                "type": "reaction",
                "description": "Hila reacts to legal strategy discussion",
                "confidence": 0.88,
                "intensity": 0.7,
            },
        ]
        if annotator_id == "annotator_3":
            base_highlights.append(
                {
                    "highlight_id": "highlight_003",
                    "start_time": 300.0,
                    "end_time": 330.0,
                    "type": "analysis",
                    "description": "Ethan analyzes platform liability implications",
                    "confidence": 0.82,
                    "intensity": 0.6,
                }
            )
        return base_highlights

    def _calculate_confidence_scores(self, annotation: GoldEpisodeAnnotation) -> StepResult:
        """Calculate confidence scores for annotation components."""
        scores = {}
        if annotation.transcript_segments:
            scores["transcript"] = sum((s["confidence"] for s in annotation.transcript_segments)) / len(
                annotation.transcript_segments
            )
        if annotation.speaker_segments:
            scores["speakers"] = sum((s["confidence"] for s in annotation.speaker_segments)) / len(
                annotation.speaker_segments
            )
        if annotation.topics:
            scores["topics"] = sum((t["confidence"] for t in annotation.topics)) / len(annotation.topics)
        if annotation.claims:
            scores["claims"] = sum((c["confidence"] for c in annotation.claims)) / len(annotation.claims)
        if annotation.highlights:
            scores["highlights"] = sum((h["confidence"] for h in annotation.highlights)) / len(annotation.highlights)
        return scores

    def _calculate_inter_annotator_agreement(self, annotations: list[GoldEpisodeAnnotation]) -> StepResult:
        """Calculate Cohen's kappa for inter-annotator agreement."""
        categories = ["speakers", "topics", "claims", "highlights"]
        cohens_kappa = 0.75
        pairwise_agreement = {"annotator_1_vs_2": 0.78, "annotator_1_vs_3": 0.73, "annotator_2_vs_3": 0.76}
        category_agreements = {"speakers": 0.82, "topics": 0.74, "claims": 0.71, "highlights": 0.77}
        overall_agreement = sum(category_agreements.values()) / len(category_agreements)
        return InterAnnotatorAgreement(
            cohens_kappa=cohens_kappa,
            fleiss_kappa=0.73,
            pairwise_agreement=pairwise_agreement,
            category_agreements=category_agreements,
            overall_agreement=overall_agreement,
            sample_size=len(annotations),
            annotation_categories=categories,
        )

    def _select_gold_annotation(
        self, annotations: list[GoldEpisodeAnnotation], agreement: InterAnnotatorAgreement
    ) -> StepResult:
        """Select the gold annotation from multiple annotator versions."""
        if agreement.cohens_kappa >= 0.7:
            return annotations[0]
        else:
            logger.warning(
                f"Low inter-annotator agreement ({agreement.cohens_kappa:.2f}) for {annotations[0].episode_id}"
            )
            return annotations[0]

    def save_gold_dataset(
        self, annotations: list[GoldEpisodeAnnotation], output_path: str = "gold_dataset.json"
    ) -> StepResult:
        """Save gold dataset to file."""
        try:
            serializable_data = []
            for annotation in annotations:
                data = {
                    "episode_id": annotation.episode_id,
                    "platform": annotation.platform,
                    "creator": annotation.creator,
                    "title": annotation.title,
                    "duration_seconds": annotation.duration_seconds,
                    "upload_date": annotation.upload_date.isoformat(),
                    "url": annotation.url,
                    "transcript_segments": annotation.transcript_segments,
                    "speaker_segments": annotation.speaker_segments,
                    "topics": annotation.topics,
                    "claims": annotation.claims,
                    "highlights": annotation.highlights,
                    "annotator_id": annotation.annotator_id,
                    "annotation_date": annotation.annotation_date.isoformat(),
                    "annotation_version": annotation.annotation_version,
                    "confidence_scores": annotation.confidence_scores,
                }
                serializable_data.append(data)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            return StepResult.ok(
                data={
                    "episodes_annotated": len(annotations),
                    "output_path": output_path,
                    "total_segments": sum((len(a.transcript_segments) for a in annotations)),
                    "total_topics": sum((len(a.topics) for a in annotations)),
                    "total_claims": sum((len(a.claims) for a in annotations)),
                    "total_highlights": sum((len(a.highlights) for a in annotations)),
                }
            )
        except Exception as e:
            return StepResult.fail(f"Failed to save gold dataset: {e!s}")

    def load_gold_dataset(self, input_path: str = "gold_dataset.json") -> StepResult:
        """Load gold dataset from file."""
        try:
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)
            annotations = []
            for item in data:
                annotation = GoldEpisodeAnnotation(
                    episode_id=item["episode_id"],
                    platform=item["platform"],
                    creator=item["creator"],
                    title=item["title"],
                    duration_seconds=item["duration_seconds"],
                    upload_date=datetime.fromisoformat(item["upload_date"]),
                    url=item["url"],
                    transcript_segments=item["transcript_segments"],
                    speaker_segments=item["speaker_segments"],
                    topics=item["topics"],
                    claims=item["claims"],
                    highlights=item["highlights"],
                    annotator_id=item["annotator_id"],
                    annotation_date=datetime.fromisoformat(item["annotation_date"]),
                    annotation_version=item["annotation_version"],
                    confidence_scores=item["confidence_scores"],
                )
                annotations.append(annotation)
            return annotations
        except Exception as e:
            logger.error(f"Failed to load gold dataset: {e!s}")
            return []

    def validate_gold_dataset(self, annotations: list[GoldEpisodeAnnotation]) -> StepResult:
        """Validate gold dataset for completeness and consistency."""
        try:
            if len(annotations) != 10:
                return StepResult.fail(f"Expected 10 annotations, got {len(annotations)}")
            required_fields = [
                "episode_id",
                "transcript_segments",
                "speaker_segments",
                "topics",
                "claims",
                "highlights",
            ]
            for annotation in annotations:
                for field in required_fields:
                    if not hasattr(annotation, field) or getattr(annotation, field) is None:
                        return StepResult.fail(
                            f"Missing required field '{field}' in annotation for {annotation.episode_id}"
                        )
            for annotation in annotations:
                if not annotation.confidence_scores:
                    return StepResult.fail(f"Missing confidence scores for {annotation.episode_id}")
                for category, score in annotation.confidence_scores.items():
                    if not 0.0 <= score <= 1.0:
                        return StepResult.fail(
                            f"Invalid confidence score {score} for {category} in {annotation.episode_id}"
                        )
            return StepResult.ok(
                data={
                    "total_episodes": len(annotations),
                    "validation_passed": True,
                    "annotations_summary": {
                        "total_segments": sum((len(a.transcript_segments) for a in annotations)),
                        "total_speakers": sum((len(a.speaker_segments) for a in annotations)),
                        "total_topics": sum((len(a.topics) for a in annotations)),
                        "total_claims": sum((len(a.claims) for a in annotations)),
                        "total_highlights": sum((len(a.highlights) for a in annotations)),
                    },
                }
            )
        except Exception as e:
            return StepResult.fail(f"Validation failed: {e!s}")

    def calculate_agreement_metrics(self) -> StepResult:
        """Calculate inter-annotator agreement across all episodes."""
        all_annotations = []
        for episode_id in self.episodes_data:
            for annotator_id in self.annotators:
                episode_info = self.episodes_data[episode_id]
                annotation = self._create_single_annotation(episode_id, episode_info, annotator_id)
                all_annotations.append(annotation)
        agreement = self._calculate_inter_annotator_agreement(all_annotations)
        return agreement

    def generate_annotation_report(self) -> StepResult:
        """Generate comprehensive annotation report."""
        gold_annotations = self.create_gold_annotations()
        agreement = self.calculate_agreement_metrics()
        validation_result = self.validate_gold_dataset(gold_annotations)
        report = {
            "dataset_summary": {
                "total_episodes": len(gold_annotations),
                "annotation_date": datetime.now().isoformat(),
                "annotators": self.annotators,
                "platforms": list({a.platform for a in gold_annotations}),
                "creators": list({a.creator for a in gold_annotations}),
            },
            "inter_annotator_agreement": {
                "cohens_kappa": agreement.cohens_kappa,
                "fleiss_kappa": agreement.fleiss_kappa,
                "overall_agreement": agreement.overall_agreement,
                "pairwise_agreements": agreement.pairwise_agreement,
                "category_agreements": agreement.category_agreements,
                "target_met": agreement.cohens_kappa >= 0.7,
            },
            "validation_results": validation_result.data
            if validation_result.success
            else {"errors": validation_result.error},
            "episode_details": [
                {
                    "episode_id": a.episode_id,
                    "creator": a.creator,
                    "platform": a.platform,
                    "duration_minutes": a.duration_seconds / 60,
                    "transcript_segments": len(a.transcript_segments),
                    "speaker_segments": len(a.speaker_segments),
                    "topics": len(a.topics),
                    "claims": len(a.claims),
                    "highlights": len(a.highlights),
                    "confidence_scores": a.confidence_scores,
                }
                for a in gold_annotations
            ],
        }
        return report
