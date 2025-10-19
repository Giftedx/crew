"""Visual Parsing Service for Creator Intelligence.

This module provides visual content analysis capabilities including:
- OCR (Optical Character Recognition) for on-screen text
- Scene segmentation for visual content structure
- Thumbnail and keyframe analysis

Features:
- EasyOCR integration for multilingual text recognition
- OpenCV-based scene segmentation
- Keyframe extraction for video analysis
- Text overlay detection and extraction
- Integration with multimodal understanding pipeline

Dependencies:
- opencv-python: For image processing and scene segmentation
- easyocr: For optical character recognition
- PIL: For image manipulation
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)

# Try to import OpenCV (optional dependency)
try:
    import cv2
    import numpy as np
    from PIL import Image

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV/PIL not available, visual parsing disabled")

# Try to import EasyOCR (optional dependency)
try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available, OCR functionality disabled")


@dataclass
class OCRResult:
    """Result of OCR text extraction."""

    text: str
    confidence: float
    bounding_box: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    language: str | None = None


@dataclass
class SceneSegment:
    """A segment of visual content."""

    start_frame: int
    end_frame: int
    scene_type: str  # intro, discussion, interview, outro, etc.
    keyframes: list[str]  # Paths to keyframe images
    text_overlays: list[OCRResult]
    confidence: float = 1.0


@dataclass
class VisualAnalysisResult:
    """Result of visual content analysis."""

    scene_segments: list[SceneSegment]
    keyframes: list[str]  # Paths to extracted keyframes
    ocr_results: list[OCRResult]
    total_frames: int
    duration_seconds: float
    model: str
    confidence: float = 1.0
    processing_time_ms: float = 0.0


class VisualParsingService:
    """Visual content parsing service for video analysis.

    Usage:
        service = VisualParsingService()
        result = service.analyze_video("video.mp4")
        keyframes = result.data["keyframes"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize visual parsing service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._analysis_cache: dict[str, VisualAnalysisResult] = {}

        # Load OCR reader lazily
        self._ocr_reader: Any = None

    def analyze_video(
        self,
        video_path: str | Path,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        extract_keyframes: bool = True,
        perform_ocr: bool = True,
        use_cache: bool = True,
    ) -> StepResult:
        """Analyze video for visual content structure and text.

        Args:
            video_path: Path to video file
            model: Model selection (fast, balanced, quality)
            extract_keyframes: Whether to extract keyframe images
            perform_ocr: Whether to perform OCR on frames
            use_cache: Whether to use analysis cache

        Returns:
            StepResult with visual analysis data
        """
        try:
            import time

            start_time = time.time()
            video_path = Path(video_path)

            # Validate input
            if not video_path.exists():
                return StepResult.fail(f"Video file not found: {video_path}", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(video_path, model)
                if cache_result:
                    logger.info(f"Visual analysis cache hit for {video_path}")
                    return StepResult.ok(
                        data={
                            "scene_segments": [s.__dict__ for s in cache_result.scene_segments],
                            "keyframes": cache_result.keyframes,
                            "ocr_results": [r.__dict__ for r in cache_result.ocr_results],
                            "total_frames": cache_result.total_frames,
                            "duration_seconds": cache_result.duration_seconds,
                            "model": cache_result.model,
                            "confidence": cache_result.confidence,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform visual analysis
            model_name = self._select_model(model)
            analysis_result = self._analyze_video(video_path, model_name, extract_keyframes, perform_ocr)

            if analysis_result:
                # Cache result
                if use_cache:
                    self._cache_result(video_path, model, analysis_result)

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "scene_segments": [s.__dict__ for s in analysis_result.scene_segments],
                        "keyframes": analysis_result.keyframes,
                        "ocr_results": [r.__dict__ for r in analysis_result.ocr_results],
                        "total_frames": analysis_result.total_frames,
                        "duration_seconds": analysis_result.duration_seconds,
                        "model": analysis_result.model,
                        "confidence": analysis_result.confidence,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Visual analysis failed", status="retryable")

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return StepResult.fail(f"Visual analysis failed: {str(e)}", status="retryable")

    def extract_keyframes(
        self,
        video_path: str | Path,
        interval_seconds: int = 30,
        output_dir: str | Path | None = None,
    ) -> StepResult:
        """Extract keyframes from video at regular intervals.

        Args:
            video_path: Path to video file
            interval_seconds: Interval between keyframes in seconds
            output_dir: Directory to save keyframes (auto-generated if None)

        Returns:
            StepResult with keyframe information
        """
        try:
            if not OPENCV_AVAILABLE:
                return StepResult.fail("OpenCV not available for keyframe extraction")

            video_path = Path(video_path)
            if not video_path.exists():
                return StepResult.fail(f"Video file not found: {video_path}", status="bad_request")

            # Create output directory
            if output_dir is None:
                output_dir = Path(tempfile.mkdtemp()) / "keyframes"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            # Open video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return StepResult.fail("Failed to open video file", status="bad_request")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            if duration == 0:
                cap.release()
                return StepResult.fail("Could not determine video duration", status="bad_request")

            keyframes = []
            frame_interval = int(fps * interval_seconds)

            for frame_num in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    # Save keyframe
                    timestamp = frame_num / fps
                    keyframe_path = output_dir / f"keyframe_{timestamp:.1f}s.jpg"

                    # Convert BGR to RGB for PIL
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)

                    # Save with reasonable quality
                    pil_image.save(keyframe_path, quality=85)

                    keyframes.append(str(keyframe_path))

            cap.release()

            return StepResult.ok(
                data={
                    "keyframes": keyframes,
                    "total_frames": total_frames,
                    "duration_seconds": duration,
                    "interval_seconds": interval_seconds,
                    "output_dir": str(output_dir),
                }
            )

        except Exception as e:
            logger.error(f"Keyframe extraction failed: {e}")
            return StepResult.fail(f"Keyframe extraction failed: {str(e)}", status="retryable")

    def perform_ocr_on_image(
        self,
        image_path: str | Path,
        languages: list[str] | None = None,
    ) -> StepResult:
        """Perform OCR on a single image.

        Args:
            image_path: Path to image file
            languages: List of language codes (e.g., ["en", "es"])

        Returns:
            StepResult with OCR results
        """
        try:
            if not EASYOCR_AVAILABLE:
                return StepResult.fail("EasyOCR not available for OCR", status="not_implemented")

            image_path = Path(image_path)
            if not image_path.exists():
                return StepResult.fail(f"Image file not found: {image_path}", status="bad_request")

            # Load OCR reader lazily
            if self._ocr_reader is None:
                logger.info("Loading EasyOCR reader")
                self._ocr_reader = easyocr.Reader(languages or ["en"])

            # Perform OCR
            results = self._ocr_reader.readtext(str(image_path))

            # Convert to our format
            ocr_results = []
            full_text = ""

            for bbox, text, confidence in results:
                # Convert bbox to our format (x1, y1, x2, y2)
                x1, y1 = bbox[0]
                x2, y2 = bbox[2]

                ocr_result = OCRResult(
                    text=text,
                    confidence=confidence,
                    bounding_box=(int(x1), int(y1), int(x2), int(y2)),
                )
                ocr_results.append(ocr_result)
                full_text += text + " "

            return StepResult.ok(
                data={
                    "text": full_text.strip(),
                    "ocr_results": [r.__dict__ for r in ocr_results],
                    "num_detections": len(ocr_results),
                    "avg_confidence": sum(r.confidence for r in ocr_results) / len(ocr_results) if ocr_results else 0.0,
                }
            )

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return StepResult.fail(f"OCR failed: {str(e)}", status="retryable")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_analysis",
            "balanced": "balanced_analysis",
            "quality": "quality_analysis",
        }

        return model_configs.get(model_alias, "balanced_analysis")

    def _analyze_video(
        self,
        video_path: Path,
        model_name: str,
        extract_keyframes: bool,
        perform_ocr: bool,
    ) -> VisualAnalysisResult | None:
        """Analyze video for visual content structure.

        Args:
            video_path: Path to video file
            model_name: Model configuration
            extract_keyframes: Whether to extract keyframes
            perform_ocr: Whether to perform OCR

        Returns:
            VisualAnalysisResult or None if analysis fails
        """
        try:
            if not OPENCV_AVAILABLE:
                logger.warning("OpenCV not available, using fallback analysis")
                return self._analyze_fallback(video_path, model_name)

            # Open video and get basic info
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # Scene segmentation (simplified approach)
            scene_segments = self._detect_scenes(cap, fps, total_frames)

            # Extract keyframes if requested
            keyframes = []
            if extract_keyframes:
                keyframes = self._extract_keyframes_from_segments(cap, scene_segments)

            # Perform OCR if requested
            ocr_results = []
            if perform_ocr and keyframes:
                ocr_results = self._perform_ocr_on_keyframes(keyframes)

            cap.release()

            return VisualAnalysisResult(
                scene_segments=scene_segments,
                keyframes=keyframes,
                ocr_results=ocr_results,
                total_frames=total_frames,
                duration_seconds=duration,
                model=model_name,
                confidence=0.8,  # Overall confidence estimate
            )

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return None

    def _detect_scenes(self, cap: Any, fps: float, total_frames: int) -> list[SceneSegment]:
        """Detect scene changes in video.

        Args:
            cap: OpenCV video capture object
            fps: Video FPS
            total_frames: Total number of frames

        Returns:
            List of scene segments
        """
        # Simplified scene detection based on frame differences
        # In production, use more sophisticated algorithms

        prev_frame = None
        scene_segments = []
        current_start = 0

        for frame_num in range(0, total_frames, max(1, int(fps))):  # Sample every second
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if not ret:
                break

            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (64, 64))  # Reduce size for faster comparison

            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(gray, prev_frame)
                diff_score = np.mean(diff)

                # Scene change threshold (adjust based on testing)
                if diff_score > 15:  # Threshold for scene change
                    if frame_num - current_start > fps * 5:  # Minimum 5 seconds per scene
                        # End previous scene
                        scene_segments.append(
                            SceneSegment(
                                start_frame=current_start,
                                end_frame=frame_num,
                                scene_type=self._classify_scene_type(current_start / fps),
                                keyframes=[],  # Will be populated later
                                text_overlays=[],
                                confidence=0.7,
                            )
                        )
                        current_start = frame_num

            prev_frame = gray

        # Add final scene
        if current_start < total_frames:
            scene_segments.append(
                SceneSegment(
                    start_frame=current_start,
                    end_frame=total_frames,
                    scene_type=self._classify_scene_type(current_start / fps),
                    keyframes=[],
                    text_overlays=[],
                    confidence=0.7,
                )
            )

        return scene_segments

    def _classify_scene_type(self, start_time_seconds: float) -> str:
        """Classify scene type based on timing and heuristics.

        Args:
            start_time_seconds: Start time of scene in seconds

        Returns:
            Scene type classification
        """
        # Simple heuristics for scene classification
        if start_time_seconds < 60:  # First minute
            return "intro"
        elif start_time_seconds > 3600:  # After 1 hour
            return "outro"
        else:
            return "discussion"  # Default scene type

    def _extract_keyframes_from_segments(self, cap: Any, scene_segments: list[SceneSegment]) -> list[str]:
        """Extract keyframes from identified scene segments.

        Args:
            cap: OpenCV video capture object
            scene_segments: List of scene segments

        Returns:
            List of keyframe image paths
        """
        keyframes = []

        for segment in scene_segments:
            # Extract keyframe from middle of segment
            mid_frame = (segment.start_frame + segment.end_frame) // 2

            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()

            if ret:
                # Save keyframe
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    cv2.imwrite(f.name, frame)
                    keyframes.append(f.name)

        return keyframes

    def _perform_ocr_on_keyframes(self, keyframe_paths: list[str]) -> list[OCRResult]:
        """Perform OCR on keyframe images.

        Args:
            keyframe_paths: List of keyframe image paths

        Returns:
            List of OCR results
        """
        if not EASYOCR_AVAILABLE or not keyframe_paths:
            return []

        ocr_results = []

        for keyframe_path in keyframe_paths:
            ocr_result_step = self.perform_ocr_on_image(keyframe_path)

            if ocr_result_step.success:
                # Convert to OCRResult format
                ocr_data = ocr_result_step.data
                for ocr_item in ocr_data.get("ocr_results", []):
                    ocr_result = OCRResult(
                        text=ocr_item["text"],
                        confidence=ocr_item["confidence"],
                        bounding_box=ocr_item["bounding_box"],
                    )
                    ocr_results.append(ocr_result)

        return ocr_results

    def _analyze_fallback(self, video_path: Path, model_name: str) -> VisualAnalysisResult:
        """Fallback visual analysis when OpenCV unavailable.

        Args:
            video_path: Path to video file
            model_name: Model configuration

        Returns:
            VisualAnalysisResult with fallback data
        """
        # Simple fallback: assume single scene for entire video
        fallback_segments = [
            SceneSegment(
                start_frame=0,
                end_frame=1,  # Placeholder
                scene_type="unknown",
                keyframes=[],
                text_overlays=[],
                confidence=0.5,
            )
        ]

        return VisualAnalysisResult(
            scene_segments=fallback_segments,
            keyframes=[],
            ocr_results=[],
            total_frames=1,
            duration_seconds=0.0,
            model=f"fallback-{model_name}",
            confidence=0.5,
        )

    def _check_cache(self, video_path: Path, model: str) -> VisualAnalysisResult | None:
        """Check if visual analysis exists in cache.

        Args:
            video_path: Path to video file
            model: Model alias

        Returns:
            Cached VisualAnalysisResult or None
        """
        import hashlib

        # Use file path and modification time for cache key
        file_stat = video_path.stat()
        combined = f"{video_path}:{file_stat.st_mtime}:{file_stat.st_size}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        return None

    def _cache_result(self, video_path: Path, model: str, result: VisualAnalysisResult) -> None:
        """Cache visual analysis result.

        Args:
            video_path: Path to video file
            model: Model alias
            result: VisualAnalysisResult to cache
        """
        import hashlib
        import time

        # Use file path and modification time for cache key
        file_stat = video_path.stat()
        combined = f"{video_path}:{file_stat.st_mtime}:{file_stat.st_size}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()

        # Add processing timestamp
        result.processing_time_ms = time.time() * 1000

        # Evict old entries if cache is full
        if len(self._analysis_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._analysis_cache))
            del self._analysis_cache[first_key]

        self._analysis_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear visual analysis cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._analysis_cache)
        self._analysis_cache.clear()

        logger.info(f"Cleared {cache_size} cached visual analyses")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get visual analysis cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._analysis_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._analysis_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }

            # Count entries per model
            for result in self._analysis_cache.values():
                model = result.model
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {str(e)}")


# Singleton instance
_visual_service: VisualParsingService | None = None


def get_visual_parsing_service() -> VisualParsingService:
    """Get singleton visual parsing service instance.

    Returns:
        Initialized VisualParsingService instance
    """
    global _visual_service

    if _visual_service is None:
        _visual_service = VisualParsingService()

    return _visual_service
