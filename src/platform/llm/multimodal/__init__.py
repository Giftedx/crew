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
    "AcousticFeatures",
    "AudioAnalysisResult",
    "AudioAnalysisType",
    # Audio analysis
    "AudioAnalyzer",
    "AudioQuality",
    "AudioQualityMetrics",
    "BackgroundNoiseAnalysis",
    "CameraMovement",
    "ConfidenceLevel",
    "ConsistencyLevel",
    "ContentModerationResult",
    "ContentVerification",
    "CorrelationStrength",
    "CorrelationType",
    "CrossModalAnalysisResult",
    "CrossModalCorrelation",
    # Cross-modal correlation
    "CrossModalCorrelator",
    "DetectedObject",
    "EmotionAnalysis",
    "EmotionType",
    "ExtractedText",
    "FaceAnalysis",
    "ImageAnalysisResult",
    "ImageAnalysisType",
    # Image analysis
    "ImageAnalyzer",
    "ModalityData",
    "MotionAnalysis",
    "MotionType",
    "MultimodalInsight",
    "ObjectTrack",
    "SceneClassification",
    "SceneSegment",
    "SceneType",
    "ShotBoundary",
    "SilenceDetection",
    "SpeakerProfile",
    "SpeechRateAnalysis",
    "TemporalFeatures",
    "VideoActivityRecognition",
    "VideoActivityType",
    "VideoAnalysisResult",
    "VideoAnalysisType",
    # Video analysis
    "VideoAnalyzer",
    "VisualClassification",
    "analyze_audio",
    "analyze_audio_from_file",
    "analyze_cross_modal",
    "analyze_image",
    "analyze_image_from_file",
    "analyze_image_from_url",
    "analyze_video",
    "analyze_video_from_file",
    "get_global_audio_analyzer",
    "get_global_cross_modal_correlator",
    "get_global_image_analyzer",
    "get_global_video_analyzer",
    "set_global_audio_analyzer",
    "set_global_cross_modal_correlator",
    "set_global_image_analyzer",
    "set_global_video_analyzer",
]
