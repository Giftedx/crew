"""
Multi-modal analysis capabilities for the Ultimate Discord Intelligence Bot.

This module provides comprehensive multi-modal content analysis including:
- Image analysis (object detection, scene classification, OCR, face analysis)
- Audio analysis (emotion detection, speaker identification, quality analysis)
- Video analysis (scene detection, motion analysis, object tracking)
- Cross-modal correlation (intelligent correlation between modalities)
"""

from .audio_analyzer import (
    AcousticFeatures,
    AudioAnalysisResult,
    AudioAnalysisType,
    AudioAnalyzer,
    AudioQuality,
    AudioQualityMetrics,
    BackgroundNoiseAnalysis,
    EmotionAnalysis,
    EmotionType,
    SilenceDetection,
    SpeakerProfile,
    SpeechRateAnalysis,
    analyze_audio,
    analyze_audio_from_file,
    get_global_audio_analyzer,
    set_global_audio_analyzer,
)
from .cross_modal_correlator import (
    ConsistencyLevel,
    ContentVerification,
    CorrelationStrength,
    CorrelationType,
    CrossModalAnalysisResult,
    CrossModalCorrelation,
    CrossModalCorrelator,
    ModalityData,
    MultimodalInsight,
    analyze_cross_modal,
    get_global_cross_modal_correlator,
    set_global_cross_modal_correlator,
)
from .image_analyzer import (
    ConfidenceLevel,
    ContentModerationResult,
    DetectedObject,
    ExtractedText,
    FaceAnalysis,
    ImageAnalysisResult,
    ImageAnalysisType,
    ImageAnalyzer,
    SceneClassification,
    analyze_image,
    analyze_image_from_file,
    analyze_image_from_url,
    get_global_image_analyzer,
    set_global_image_analyzer,
)
from .video_analyzer import (
    ActivityRecognition as VideoActivityRecognition,
)
from .video_analyzer import (
    ActivityType as VideoActivityType,
)
from .video_analyzer import (
    CameraMovement,
    MotionAnalysis,
    MotionType,
    ObjectTrack,
    SceneSegment,
    SceneType,
    ShotBoundary,
    TemporalFeatures,
    VideoAnalysisResult,
    VideoAnalysisType,
    VideoAnalyzer,
    VisualClassification,
    analyze_video,
    analyze_video_from_file,
    get_global_video_analyzer,
    set_global_video_analyzer,
)

__all__ = [
    # Image analysis
    "ImageAnalyzer",
    "ImageAnalysisResult",
    "ImageAnalysisType",
    "DetectedObject",
    "SceneClassification",
    "ExtractedText",
    "FaceAnalysis",
    "ContentModerationResult",
    "ConfidenceLevel",
    "analyze_image",
    "analyze_image_from_file",
    "analyze_image_from_url",
    "get_global_image_analyzer",
    "set_global_image_analyzer",
    # Audio analysis
    "AudioAnalyzer",
    "AudioAnalysisResult",
    "AudioAnalysisType",
    "EmotionAnalysis",
    "EmotionType",
    "SpeakerProfile",
    "AudioQualityMetrics",
    "AudioQuality",
    "AcousticFeatures",
    "BackgroundNoiseAnalysis",
    "SpeechRateAnalysis",
    "SilenceDetection",
    "analyze_audio",
    "analyze_audio_from_file",
    "get_global_audio_analyzer",
    "set_global_audio_analyzer",
    # Video analysis
    "VideoAnalyzer",
    "VideoAnalysisResult",
    "VideoAnalysisType",
    "SceneSegment",
    "SceneType",
    "MotionAnalysis",
    "MotionType",
    "ObjectTrack",
    "VisualClassification",
    "TemporalFeatures",
    "VideoActivityRecognition",
    "VideoActivityType",
    "ShotBoundary",
    "CameraMovement",
    "analyze_video",
    "analyze_video_from_file",
    "get_global_video_analyzer",
    "set_global_video_analyzer",
    # Cross-modal correlation
    "CrossModalCorrelator",
    "CrossModalAnalysisResult",
    "CrossModalCorrelation",
    "CorrelationType",
    "CorrelationStrength",
    "ConsistencyLevel",
    "ModalityData",
    "MultimodalInsight",
    "ContentVerification",
    "analyze_cross_modal",
    "get_global_cross_modal_correlator",
    "set_global_cross_modal_correlator",
]
