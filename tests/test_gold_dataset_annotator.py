from datetime import datetime

from src.ultimate_discord_intelligence_bot.services.gold_dataset_annotator import (
    GoldDatasetAnnotator,
    GoldEpisodeAnnotation,
    InterAnnotatorAgreement,
)


class TestGoldEpisodeAnnotation:
    """Test the GoldEpisodeAnnotation dataclass."""

    def test_annotation_creation(self):
        """Test creating a GoldEpisodeAnnotation."""
        annotation = GoldEpisodeAnnotation(
            episode_id="test_episode",
            platform="youtube",
            creator="h3podcast",
            title="Test Episode",
            duration_seconds=3600,
            upload_date=datetime.now(),
            url="https://youtube.com/watch?v=test",
            transcript_segments=[
                {
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "text": "Test transcript",
                    "speaker": "Ethan",
                    "confidence": 0.95,
                }
            ],
            speaker_segments=[
                {
                    "start_time": 0.0,
                    "end_time": 180.0,
                    "speaker": "Ethan",
                    "confidence": 0.95,
                }
            ],
            topics=[
                {
                    "topic": "test",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "confidence": 0.90,
                }
            ],
            claims=[
                {
                    "claim_id": "claim_001",
                    "text": "Test claim",
                    "speaker": "Ethan",
                    "confidence": 0.85,
                }
            ],
            highlights=[
                {
                    "highlight_id": "highlight_001",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "type": "key_statement",
                    "confidence": 0.80,
                }
            ],
        )

        assert annotation.episode_id == "test_episode"
        assert annotation.platform == "youtube"
        assert annotation.creator == "h3podcast"
        assert annotation.title == "Test Episode"
        assert annotation.duration_seconds == 3600
        assert len(annotation.transcript_segments) == 1
        assert len(annotation.speaker_segments) == 1
        assert len(annotation.topics) == 1
        assert len(annotation.claims) == 1
        assert len(annotation.highlights) == 1


class TestInterAnnotatorAgreement:
    """Test the InterAnnotatorAgreement dataclass."""

    def test_agreement_creation(self):
        """Test creating an InterAnnotatorAgreement."""
        agreement = InterAnnotatorAgreement(
            cohens_kappa=0.75,
            fleiss_kappa=0.73,
            pairwise_agreement={"ann1_ann2": 0.78, "ann1_ann3": 0.74},
            category_agreements={"speakers": 0.82, "topics": 0.76},
            overall_agreement=0.78,
            sample_size=30,
            annotation_categories=["speakers", "topics", "claims"],
        )

        assert agreement.cohens_kappa == 0.75
        assert agreement.fleiss_kappa == 0.73
        assert agreement.overall_agreement == 0.78
        assert agreement.sample_size == 30
        assert len(agreement.annotation_categories) == 3


class TestGoldDatasetAnnotator:
    """Test the GoldDatasetAnnotator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.annotator = GoldDatasetAnnotator()

    def test_initialization(self):
        """Test annotator initialization."""
        assert len(self.annotator.episodes_data) == 10
        assert len(self.annotator.annotators) == 3

    def test_create_single_annotation(self):
        """Test creating a single annotation."""
        episode_id = "h3_podcast_123"
        episode_info = self.annotator.episodes_data[episode_id]
        annotator_id = "annotator_1"

        annotation = self.annotator._create_single_annotation(episode_id, episode_info, annotator_id)

        assert annotation.episode_id == episode_id
        assert annotation.annotator_id == annotator_id
        assert len(annotation.transcript_segments) > 0
        assert len(annotation.speaker_segments) > 0
        assert len(annotation.topics) > 0
        assert len(annotation.claims) > 0
        assert len(annotation.highlights) > 0

    def test_generate_transcript_segments(self):
        """Test transcript segment generation."""
        segments = self.annotator._generate_transcript_segments("test_episode", "annotator_1")

        assert len(segments) > 0
        for segment in segments:
            assert "start_time" in segment
            assert "end_time" in segment
            assert "text" in segment
            assert "speaker" in segment
            assert "confidence" in segment
            assert 0.0 <= segment["confidence"] <= 1.0

    def test_generate_speaker_segments(self):
        """Test speaker segment generation."""
        segments = self.annotator._generate_speaker_segments("test_episode", "annotator_1")

        assert len(segments) > 0
        for segment in segments:
            assert "start_time" in segment
            assert "end_time" in segment
            assert "speaker" in segment
            assert "confidence" in segment

    def test_generate_topics(self):
        """Test topic generation."""
        topics = self.annotator._generate_topics("test_episode", "annotator_1")

        assert len(topics) > 0
        for topic in topics:
            assert "topic" in topic
            assert "start_time" in topic
            assert "end_time" in topic
            assert "confidence" in topic
            assert "keywords" in topic

    def test_generate_claims(self):
        """Test claim generation."""
        claims = self.annotator._generate_claims("test_episode", "annotator_1")

        assert len(claims) > 0
        for claim in claims:
            assert "claim_id" in claim
            assert "text" in claim
            assert "speaker" in claim
            assert "confidence" in claim

    def test_generate_highlights(self):
        """Test highlight generation."""
        highlights = self.annotator._generate_highlights("test_episode", "annotator_1")

        assert len(highlights) > 0
        for highlight in highlights:
            assert "highlight_id" in highlight
            assert "start_time" in highlight
            assert "end_time" in highlight
            assert "type" in highlight
            assert "confidence" in highlight

    def test_calculate_confidence_scores(self):
        """Test confidence score calculation."""
        annotation = GoldEpisodeAnnotation(
            episode_id="test_episode",
            platform="youtube",
            creator="h3podcast",
            title="Test Episode",
            duration_seconds=3600,
            upload_date=datetime.now(),
            url="https://youtube.com/watch?v=test",
            transcript_segments=[
                {
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "text": "Test transcript",
                    "speaker": "Ethan",
                    "confidence": 0.95,
                }
            ],
            speaker_segments=[
                {
                    "start_time": 0.0,
                    "end_time": 180.0,
                    "speaker": "Ethan",
                    "confidence": 0.95,
                }
            ],
            topics=[
                {
                    "topic": "test",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "confidence": 0.90,
                }
            ],
            claims=[
                {
                    "claim_id": "claim_001",
                    "text": "Test claim",
                    "speaker": "Ethan",
                    "confidence": 0.85,
                }
            ],
            highlights=[
                {
                    "highlight_id": "highlight_001",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "type": "key_statement",
                    "confidence": 0.80,
                }
            ],
        )

        scores = self.annotator._calculate_confidence_scores(annotation)

        assert "transcript" in scores
        assert "speakers" in scores
        assert "topics" in scores
        assert "claims" in scores
        assert "highlights" in scores

        # All scores should be in 0-1 range
        for category, score in scores.items():
            assert 0.0 <= score <= 1.0

    def test_calculate_inter_annotator_agreement(self):
        """Test inter-annotator agreement calculation."""
        # Create mock annotations for testing
        annotations = []
        for i in range(3):  # 3 annotators
            annotation = self.annotator._create_single_annotation(
                "test_episode", self.annotator.episodes_data["h3_podcast_123"], f"annotator_{i + 1}"
            )
            annotations.append(annotation)

        agreement = self.annotator._calculate_inter_annotator_agreement(annotations)

        assert agreement.cohens_kappa >= 0.0
        assert agreement.overall_agreement >= 0.0
        assert agreement.sample_size == 3
        assert len(agreement.annotation_categories) > 0

    def test_select_gold_annotation(self):
        """Test gold annotation selection."""
        annotations = []
        for i in range(3):
            annotation = self.annotator._create_single_annotation(
                "test_episode", self.annotator.episodes_data["h3_podcast_123"], f"annotator_{i + 1}"
            )
            annotations.append(annotation)

        agreement = self.annotator._calculate_inter_annotator_agreement(annotations)
        gold_annotation = self.annotator._select_gold_annotation(annotations, agreement)

        assert isinstance(gold_annotation, GoldEpisodeAnnotation)
        assert gold_annotation.episode_id == "test_episode"

    def test_create_gold_annotations(self):
        """Test creating gold annotations for all episodes."""
        gold_annotations = self.annotator.create_gold_annotations()

        assert len(gold_annotations) == 10  # Should have 10 episodes

        for annotation in gold_annotations:
            assert isinstance(annotation, GoldEpisodeAnnotation)
            assert annotation.episode_id in self.annotator.episodes_data
            assert len(annotation.transcript_segments) > 0
            assert len(annotation.speaker_segments) > 0
            assert len(annotation.topics) > 0
            assert len(annotation.claims) > 0
            assert len(annotation.highlights) > 0

    def test_save_gold_dataset(self):
        """Test saving gold dataset to file."""
        gold_annotations = self.annotator.create_gold_annotations()

        result = self.annotator.save_gold_dataset(gold_annotations, "test_gold_dataset.json")

        assert result.success
        assert "data" in result.data
        assert result.data["data"]["episodes_annotated"] == 10
        assert result.data["data"]["output_path"] == "test_gold_dataset.json"

        # Verify file was created and can be loaded
        loaded_annotations = self.annotator.load_gold_dataset("test_gold_dataset.json")
        assert len(loaded_annotations) == 10

    def test_load_gold_dataset(self):
        """Test loading gold dataset from file."""
        # First save a dataset
        gold_annotations = self.annotator.create_gold_annotations()
        self.annotator.save_gold_dataset(gold_annotations, "test_load_gold_dataset.json")

        # Then load it back
        loaded_annotations = self.annotator.load_gold_dataset("test_load_gold_dataset.json")

        assert len(loaded_annotations) == 10

        for annotation in loaded_annotations:
            assert isinstance(annotation, GoldEpisodeAnnotation)
            assert annotation.episode_id in self.annotator.episodes_data

    def test_validate_gold_dataset(self):
        """Test gold dataset validation."""
        gold_annotations = self.annotator.create_gold_annotations()

        result = self.annotator.validate_gold_dataset(gold_annotations)

        assert result.success
        assert "data" in result.data
        assert result.data["data"]["total_episodes"] == 10
        assert result.data["data"]["validation_passed"] is True

    def test_generate_annotation_report(self):
        """Test annotation report generation."""
        report = self.annotator.generate_annotation_report()

        assert "dataset_summary" in report
        assert "inter_annotator_agreement" in report
        assert "validation_results" in report
        assert "episode_details" in report

        # Check inter-annotator agreement
        agreement = report["inter_annotator_agreement"]
        assert "cohens_kappa" in agreement
        assert "target_met" in agreement

        # Check episode details
        episode_details = report["episode_details"]
        assert len(episode_details) == 10

        for episode in episode_details:
            assert "episode_id" in episode
            assert "transcript_segments" in episode
            assert "speaker_segments" in episode
            assert "topics" in episode
            assert "claims" in episode
            assert "highlights" in episode

    def test_calculate_agreement_metrics(self):
        """Test agreement metrics calculation."""
        agreement = self.annotator.calculate_agreement_metrics()

        assert isinstance(agreement, InterAnnotatorAgreement)
        assert agreement.cohens_kappa >= 0.0
        assert agreement.sample_size > 0
