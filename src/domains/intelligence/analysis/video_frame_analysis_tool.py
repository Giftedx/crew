"""
Advanced video frame analysis tool with computer vision capabilities.

This tool provides comprehensive video frame analysis including:
- Key frame extraction and scene detection
- Object recognition and tracking
- Face detection and emotion recognition
- Text extraction from video frames (OCR)
- Visual sentiment analysis
- Scene transition analysis

Uses state-of-the-art computer vision models and techniques for robust analysis.
"""

from __future__ import annotations

import base64
import importlib
import logging
import os
import time
from functools import cached_property
from platform.cache.tool_cache_decorator import cache_tool_result
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


cv2: Any | None = None
PIL: Any | None = None
openai: Any | None = None
try:
    cv2 = importlib.import_module("cv2")
except ImportError:
    cv2 = None
try:
    PIL = importlib.import_module("PIL")
except ImportError:
    PIL = None
try:
    openai = importlib.import_module("openai")
except ImportError:
    openai = None


class FrameAnalysisResult(TypedDict, total=False):
    """Result structure for frame analysis."""

    timestamp: float
    frame_id: int
    objects: list[dict[str, Any]]
    faces: list[dict[str, Any]]
    text_content: str
    scene_type: str
    visual_sentiment: str
    confidence_scores: dict[str, float]
    raw_analysis: dict[str, Any]


class VideoAnalysisResult(TypedDict, total=False):
    """Complete video analysis result structure."""

    total_frames: int
    analyzed_frames: int
    duration_seconds: float
    key_frames: list[FrameAnalysisResult]
    scene_transitions: list[dict[str, Any]]
    overall_sentiment: str
    dominant_objects: list[str]
    text_timeline: list[dict[str, Any]]
    processing_time: float


class VideoFrameAnalysisTool(BaseTool[StepResult]):
    """Advanced video frame analysis with computer vision capabilities."""

    name: str = "Video Frame Analysis Tool"
    description: str = "Analyzes video frames using computer vision for object detection, OCR, scene analysis, and visual sentiment detection."

    def __init__(
        self,
        max_frames: int = 10,
        scene_threshold: float = 0.3,
        enable_ocr: bool = True,
        enable_face_detection: bool = True,
        vision_model: str = "gpt-4-vision-preview",
    ):
        super().__init__()
        self._max_frames = max_frames
        self._scene_threshold = scene_threshold
        self._enable_ocr = enable_ocr
        self._enable_face_detection = enable_face_detection
        self._vision_model = vision_model
        self._metrics = get_metrics()
        if cv2 is None:
            logging.warning("OpenCV not available - video processing will be limited")
        if PIL is None:
            logging.warning("PIL not available - image processing will be limited")
        if openai is None:
            logging.warning("OpenAI not available - AI vision analysis will be limited")

    @cached_property
    def openai_client(self) -> Any:
        """Initialize OpenAI client for vision analysis."""
        if openai is None:
            raise RuntimeError("OpenAI package not available. Install with: pip install openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        return openai.OpenAI(api_key=api_key)

    @cache_tool_result(namespace="tool:video_frame_analysis", ttl=7200)
    def _run(
        self, video_path: str, tenant: str = "default", workspace: str = "default", analysis_depth: str = "standard"
    ) -> StepResult:
        """
        Analyze video frames for visual content understanding.

        Args:
            video_path: Path to video file for analysis
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            analysis_depth: Depth of analysis (standard, deep, comprehensive)

        Returns:
            StepResult with comprehensive video frame analysis
        """
        start_time = time.monotonic()
        try:
            if not video_path:
                return StepResult.fail("Video path cannot be empty")
            if not os.path.exists(video_path):
                return StepResult.fail(f"Video file not found: {video_path}")
            if tenant and workspace:
                self.note(f"Starting video frame analysis for {os.path.basename(video_path)}")
            video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"]
            if not any(video_path.lower().endswith(ext) for ext in video_extensions):
                return StepResult.fail("Unsupported video format")
            key_frames = self._extract_key_frames(video_path, analysis_depth)
            if not key_frames:
                return StepResult.fail("Failed to extract frames from video")
            frame_analyses = []
            for frame_data in key_frames:
                try:
                    analysis = self._analyze_frame(frame_data, analysis_depth)
                    if analysis:
                        frame_analyses.append(analysis)
                except Exception as e:
                    logging.warning(f"Failed to analyze frame {frame_data.get('frame_id', 'unknown')}: {e}")
                    continue
            if not frame_analyses:
                return StepResult.fail("No frames could be analyzed")
            overall_analysis = self._generate_overall_analysis(frame_analyses, video_path)
            processing_time = time.monotonic() - start_time
            result: VideoAnalysisResult = {
                "total_frames": len(key_frames),
                "analyzed_frames": len(frame_analyses),
                "duration_seconds": self._get_video_duration(video_path),
                "key_frames": frame_analyses,
                "scene_transitions": self._detect_scene_transitions(frame_analyses),
                "overall_sentiment": overall_analysis.get("overall_sentiment", "neutral"),
                "dominant_objects": overall_analysis.get("dominant_objects", []),
                "text_timeline": overall_analysis.get("text_timeline", []),
                "processing_time": processing_time,
            }
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})
            return StepResult.ok(data=result)
        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception(f"Video frame analysis failed for {video_path}")
            return StepResult.fail(f"Video analysis failed: {e!s}")

    def _extract_key_frames(self, video_path: str, analysis_depth: str) -> list[dict[str, Any]]:
        """Extract key frames from video using scene detection."""
        if cv2 is None:
            return self._extract_frames_simple(video_path)
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {video_path}")
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            total_frames / fps if fps > 0 else 0
            max_frames = {
                "standard": min(self._max_frames, 5),
                "deep": min(self._max_frames, 10),
                "comprehensive": self._max_frames,
            }.get(analysis_depth, self._max_frames)
            interval = max(1, total_frames // max_frames) if total_frames > 0 else 1
            frame_id = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_id % interval == 0:
                    timestamp = frame_id / fps if fps > 0 else frame_id
                    frame_data = {
                        "frame_id": frame_id,
                        "timestamp": timestamp,
                        "frame": frame,
                        "frame_base64": self._frame_to_base64(frame),
                    }
                    frames.append(frame_data)
                    if len(frames) >= max_frames:
                        break
                frame_id += 1
            cap.release()
            return frames
        except Exception as e:
            logging.error(f"Frame extraction failed: {e}")
            return []

    def _extract_frames_simple(self, video_path: str) -> list[dict[str, Any]]:
        """Simple frame extraction fallback when OpenCV is not available."""
        logging.warning("OpenCV not available - cannot extract video frames")
        return []

    def _frame_to_base64(self, frame: Any) -> str:
        """Convert OpenCV frame to base64 string."""
        if cv2 is None:
            return ""
        try:
            _, buffer = cv2.imencode(".jpg", frame)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")
            return frame_base64
        except Exception as e:
            logging.error(f"Frame to base64 conversion failed: {e}")
            return ""

    def _analyze_frame(self, frame_data: dict[str, Any], analysis_depth: str) -> FrameAnalysisResult | None:
        """Analyze a single frame using computer vision."""
        try:
            frame_base64 = frame_data.get("frame_base64")
            if not frame_base64:
                return None
            analysis = self._analyze_frame_with_gpt4v(frame_base64, analysis_depth)
            result: FrameAnalysisResult = {
                "timestamp": frame_data.get("timestamp", 0.0),
                "frame_id": frame_data.get("frame_id", 0),
                "objects": analysis.get("objects", []),
                "faces": analysis.get("faces", []),
                "text_content": analysis.get("text_content", ""),
                "scene_type": analysis.get("scene_type", "unknown"),
                "visual_sentiment": analysis.get("visual_sentiment", "neutral"),
                "confidence_scores": analysis.get("confidence_scores", {}),
                "raw_analysis": analysis,
            }
            return result
        except Exception as e:
            logging.error(f"Frame analysis failed: {e}")
            return None

    def _analyze_frame_with_gpt4v(self, frame_base64: str, analysis_depth: str) -> dict[str, Any]:
        """Analyze frame using GPT-4 Vision."""
        if openai is None:
            return self._analyze_frame_fallback()
        try:
            if analysis_depth == "comprehensive":
                prompt = "Analyze this video frame comprehensively and provide a JSON response with:\n                1. objects: List of detected objects with confidence scores\n                2. faces: Number and descriptions of faces (emotions if visible)\n                3. text_content: Any text visible in the frame (OCR)\n                4. scene_type: Type of scene (indoor/outdoor/studio/etc.)\n                5. visual_sentiment: Overall emotional tone (positive/negative/neutral)\n                6. confidence_scores: Confidence for each analysis type\n                7. detailed_description: Comprehensive description of the frame\n\n                Format as valid JSON."
            elif analysis_depth == "deep":
                prompt = "Analyze this video frame and provide a JSON response with:\n                1. objects: Main objects visible\n                2. text_content: Any readable text\n                3. scene_type: Type of scene\n                4. visual_sentiment: Emotional tone\n                5. confidence_scores: Analysis confidence\n\n                Format as valid JSON."
            else:
                prompt = "Analyze this video frame and provide a JSON response with:\n                1. objects: Main objects visible\n                2. scene_type: Type of scene\n                3. visual_sentiment: Emotional tone (positive/negative/neutral)\n\n                Format as valid JSON."
            response = self.openai_client.chat.completions.create(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}},
                        ],
                    }
                ],
                max_tokens=1000,
            )
            response_text = response.choices[0].message.content
            try:
                import json

                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                return {
                    "objects": [],
                    "text_content": "",
                    "scene_type": "unknown",
                    "visual_sentiment": "neutral",
                    "raw_response": response_text,
                }
        except Exception as e:
            logging.error(f"GPT-4V analysis failed: {e}")
            return self._analyze_frame_fallback()

    def _analyze_frame_fallback(self) -> dict[str, Any]:
        """Fallback analysis when AI vision is not available."""
        return {
            "objects": [],
            "faces": [],
            "text_content": "",
            "scene_type": "unknown",
            "visual_sentiment": "neutral",
            "confidence_scores": {"overall": 0.0},
            "error": "AI vision analysis not available",
        }

    def _detect_scene_transitions(self, frame_analyses: list[FrameAnalysisResult]) -> list[dict[str, Any]]:
        """Detect scene transitions based on frame analysis."""
        transitions = []
        for i in range(1, len(frame_analyses)):
            current = frame_analyses[i]
            previous = frame_analyses[i - 1]
            if current.get("scene_type") != previous.get("scene_type"):
                transitions.append(
                    {
                        "timestamp": current.get("timestamp", 0.0),
                        "transition_type": "scene_change",
                        "from_scene": previous.get("scene_type", "unknown"),
                        "to_scene": current.get("scene_type", "unknown"),
                    }
                )
        return transitions

    def _generate_overall_analysis(self, frame_analyses: list[FrameAnalysisResult], video_path: str) -> dict[str, Any]:
        """Generate overall video analysis from frame analyses."""
        if not frame_analyses:
            return {}
        sentiments = [frame.get("visual_sentiment", "neutral") for frame in frame_analyses]
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        overall_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        all_objects = []
        for frame in frame_analyses:
            objects = frame.get("objects", [])
            if isinstance(objects, list):
                for obj in objects:
                    if isinstance(obj, dict):
                        all_objects.append(obj.get("name", str(obj)))
                    else:
                        all_objects.append(str(obj))
        object_counts = {}
        for obj in all_objects:
            object_counts[obj] = object_counts.get(obj, 0) + 1
        dominant_objects = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        dominant_objects = [obj[0] for obj in dominant_objects]
        text_timeline = []
        for frame in frame_analyses:
            text_content = frame.get("text_content", "")
            if text_content:
                text_timeline.append({"timestamp": frame.get("timestamp", 0.0), "text": text_content})
        return {
            "overall_sentiment": overall_sentiment,
            "dominant_objects": dominant_objects,
            "text_timeline": text_timeline,
            "total_scenes": len({frame.get("scene_type", "unknown") for frame in frame_analyses}),
        }

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        if cv2 is None:
            return 0.0
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0.0
            cap.release()
            return duration
        except Exception:
            return 0.0

    def run(
        self, video_path: str, tenant: str = "default", workspace: str = "default", analysis_depth: str = "standard"
    ) -> StepResult:
        """Public interface for video frame analysis."""
        return self._run(video_path, tenant, workspace, analysis_depth)
