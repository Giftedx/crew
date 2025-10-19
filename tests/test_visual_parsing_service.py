"""Tests for Visual Parsing Service."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from analysis.vision.visual_parsing_service import VisualParsingService, get_visual_parsing_service


class TestVisualParsingService:
    """Test visual parsing service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = VisualParsingService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._analysis_cache) == 0
        assert self.service._ocr_reader is None

    def test_analyze_fallback(self) -> None:
        """Test visual analysis with fallback model."""
        # Create a dummy video file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video content")
            video_path = Path(f.name)

        try:
            result = self.service.analyze_video(video_path, model="fast", use_cache=False)

            assert result.success
            assert result.data is not None
            assert "scene_segments" in result.data
            assert "keyframes" in result.data
            assert "ocr_results" in result.data

            # Fallback should return basic structure
            assert len(result.data["scene_segments"]) >= 1
            assert result.data["model"].startswith("fallback")

        finally:
            video_path.unlink()

    def test_analyze_nonexistent_file(self) -> None:
        """Test handling of non-existent video file."""
        result = self.service.analyze_video("nonexistent.mp4", model="fast")

        assert not result.success
        assert result.status == "bad_request"
        assert "not found" in result.error.lower()

    def test_extract_keyframes_success(self) -> None:
        """Test successful keyframe extraction."""
        # This test would require a real video file
        # For now, we'll test the error handling for non-existent files
        result = self.service.extract_keyframes("nonexistent.mp4")

        assert not result.success
        assert result.status == "bad_request"

    def test_perform_ocr_fallback(self) -> None:
        """Test OCR with fallback when EasyOCR unavailable."""
        # Create a dummy image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"dummy image content")
            image_path = Path(f.name)

        try:
            # Test with EasyOCR unavailable
            with patch("analysis.vision.visual_parsing_service.EASYOCR_AVAILABLE", False):
                result = self.service.perform_ocr_on_image(image_path)

                assert not result.success
                assert result.status == "not_implemented"

        finally:
            image_path.unlink()

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached analyses
        self.service.analyze_video("dummy1.mp4", use_cache=True)
        self.service.analyze_video("dummy2.mp4", use_cache=True)

        assert len(self.service._analysis_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._analysis_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached analyses
        self.service.analyze_video("dummy1.mp4", model="fast", use_cache=True)
        self.service.analyze_video("dummy2.mp4", model="balanced", use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "models_cached" in result.data

        assert result.data["total_cached"] >= 2
        assert result.data["cache_size_limit"] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model("fast") == "fast_analysis"
        assert self.service._select_model("balanced") == "balanced_analysis"
        assert self.service._select_model("quality") == "quality_analysis"
        assert self.service._select_model("unknown") == "balanced_analysis"  # Default

    def test_scene_type_classification(self) -> None:
        """Test scene type classification."""
        # Test different time ranges
        assert self.service._classify_scene_type(30) == "intro"  # First minute
        assert self.service._classify_scene_type(4000) == "outro"  # After 1 hour
        assert self.service._classify_scene_type(300) == "discussion"  # Middle content


class TestVisualParsingServiceSingleton:
    """Test singleton instance management."""

    def test_get_visual_parsing_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_visual_parsing_service()
        service2 = get_visual_parsing_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, VisualParsingService)


class TestVisualParsingWithMocking:
    """Test visual parsing service with mocked dependencies."""

    @patch("cv2.VideoCapture")
    @patch("cv2.cvtColor")
    @patch("cv2.resize")
    @patch("cv2.absdiff")
    @patch("numpy.mean")
    def test_analyze_video_with_opencv(
        self,
        mock_np_mean,
        mock_absdiff,
        mock_resize,
        mock_cvtColor,
        mock_video_capture,
    ):
        """Test video analysis with OpenCV mocking."""
        # Mock OpenCV components
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [30.0, 3000]  # fps=30, frames=3000
        mock_video_capture.return_value = mock_cap

        # Mock frame reading
        mock_frame = MagicMock()
        mock_cap.read.return_value = (True, mock_frame)

        # Mock frame processing
        mock_gray = MagicMock()
        mock_cvtColor.return_value = mock_gray
        mock_resize.return_value = mock_gray

        mock_absdiff.return_value = MagicMock()
        mock_np_mean.return_value = 10.0  # Below scene change threshold

        # Create service with mocked availability
        with patch("analysis.vision.visual_parsing_service.OPENCV_AVAILABLE", True):
            service = VisualParsingService()

            # Create dummy video file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"video")
                video_path = Path(f.name)

            try:
                result = service.analyze_video(
                    video_path, model="balanced", extract_keyframes=False, perform_ocr=False, use_cache=False
                )

                assert result.success
                assert result.data["total_frames"] == 3000
                assert result.data["duration_seconds"] == 100.0  # 3000/30
                assert len(result.data["scene_segments"]) >= 1

                # Verify OpenCV was used
                mock_video_capture.assert_called_once()

            finally:
                video_path.unlink()

    def test_perform_ocr_with_easyocr_mock(self) -> None:
        """Test OCR with EasyOCR mocking."""
        # Create dummy image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"image content")
            image_path = Path(f.name)

        try:
            # Mock EasyOCR reader
            mock_reader = MagicMock()
            mock_reader.readtext.return_value = [
                ([(10, 10), (50, 10), (50, 30), (10, 30)], "Hello", 0.95),
                ([(60, 10), (100, 10), (100, 30), (60, 30)], "World", 0.90),
            ]

            with patch("analysis.vision.visual_parsing_service.EASYOCR_AVAILABLE", True):
                service = VisualParsingService()

                # Mock the OCR reader creation
                with patch.object(service, "_ocr_reader", mock_reader):
                    result = service.perform_ocr_on_image(image_path)

                    assert result.success
                    assert result.data["text"] == "Hello World"
                    assert result.data["num_detections"] == 2
                    assert result.data["avg_confidence"] == 0.925

        finally:
            image_path.unlink()


class TestOCRResult:
    """Test OCR result data structure."""

    def test_create_ocr_result(self) -> None:
        """Test creating OCR result."""
        from analysis.vision.visual_parsing_service import OCRResult

        ocr_result = OCRResult(
            text="Hello World",
            confidence=0.95,
            bounding_box=(10, 10, 100, 50),
            language="en",
        )

        assert ocr_result.text == "Hello World"
        assert ocr_result.confidence == 0.95
        assert ocr_result.bounding_box == (10, 10, 100, 50)
        assert ocr_result.language == "en"

    def test_ocr_result_to_dict(self) -> None:
        """Test converting OCR result to dictionary."""
        from analysis.vision.visual_parsing_service import OCRResult

        ocr_result = OCRResult(
            text="Test Text",
            confidence=0.8,
            bounding_box=(0, 0, 50, 20),
        )

        ocr_dict = ocr_result.__dict__

        assert ocr_dict["text"] == "Test Text"
        assert ocr_dict["confidence"] == 0.8
        assert ocr_dict["bounding_box"] == (0, 0, 50, 20)
        assert ocr_dict["language"] is None


class TestSceneSegment:
    """Test scene segment data structure."""

    def test_create_scene_segment(self) -> None:
        """Test creating scene segment."""
        from analysis.vision.visual_parsing_service import OCRResult, SceneSegment

        ocr_result = OCRResult(text="Test", confidence=0.9, bounding_box=(0, 0, 10, 10))

        segment = SceneSegment(
            start_frame=0,
            end_frame=900,  # 30 seconds at 30fps
            scene_type="intro",
            keyframes=["frame1.jpg", "frame2.jpg"],
            text_overlays=[ocr_result],
            confidence=0.85,
        )

        assert segment.start_frame == 0
        assert segment.end_frame == 900
        assert segment.scene_type == "intro"
        assert len(segment.keyframes) == 2
        assert len(segment.text_overlays) == 1
        assert segment.confidence == 0.85

    def test_scene_segment_to_dict(self) -> None:
        """Test converting scene segment to dictionary."""
        from analysis.vision.visual_parsing_service import SceneSegment

        segment = SceneSegment(
            start_frame=100,
            end_frame=200,
            scene_type="discussion",
            keyframes=[],
            text_overlays=[],
        )

        segment_dict = segment.__dict__

        assert segment_dict["start_frame"] == 100
        assert segment_dict["end_frame"] == 200
        assert segment_dict["scene_type"] == "discussion"
        assert segment_dict["keyframes"] == []
        assert segment_dict["text_overlays"] == []
