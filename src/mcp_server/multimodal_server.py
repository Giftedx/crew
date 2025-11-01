"""Multi-modal analysis MCP server for advanced content analysis.

This MCP server extends the existing MCP ecosystem with sophisticated
multi-modal analysis capabilities including:
- Visual sentiment analysis for images
- Video frame-by-frame emotion tracking
- Audio speaker identification and tone analysis
- Cross-modal correlation and synthesis
- Integration with vector database for multi-modal embeddings
"""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.tools.multi_modal_analysis_tool import (
    MultiModalAnalysisTool,
)


logger = logging.getLogger(__name__)


def create_multimodal_server() -> FastMCP:
    """Create the multi-modal analysis MCP server."""

    # Create FastMCP server instance
    mcp = FastMCP(
        "multimodal-analysis",
        description="Advanced multi-modal content analysis server",
        version="1.0.0",
    )

    # Initialize the multi-modal analysis tool
    multimodal_tool = MultiModalAnalysisTool()
    metrics = get_metrics()

    @mcp.tool()
    def analyze_image(image_url: str, tenant: str = "default", workspace: str = "default") -> dict[str, Any]:
        """Analyze image content with advanced visual analysis.

        Args:
            image_url: URL of the image to analyze
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            Comprehensive visual analysis results
        """
        try:
            result = multimodal_tool._run(image_url, "image", tenant, workspace)

            if result.status == "success":
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_image", "outcome": "success"},
                ).inc()
                return {
                    "success": True,
                    "analysis": result.data,
                    "content_type": "image",
                    "dominant_themes": result.data.get("dominant_themes", []),
                    "unified_sentiment": result.data.get("unified_sentiment", "neutral"),
                }
            else:
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_image", "outcome": "error"},
                ).inc()
                return {
                    "success": False,
                    "error": result.error,
                    "content_type": "image",
                }

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            metrics.counter(
                "mcp_tool_calls_total",
                labels={"tool": "analyze_image", "outcome": "error"},
            ).inc()
            return {"success": False, "error": str(e), "content_type": "image"}

    @mcp.tool()
    def analyze_video(video_url: str, tenant: str = "default", workspace: str = "default") -> dict[str, Any]:
        """Analyze video content with frame-by-frame emotion tracking.

        Args:
            video_url: URL of the video to analyze
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            Comprehensive video analysis results
        """
        try:
            result = multimodal_tool._run(video_url, "video", tenant, workspace)

            if result.status == "success":
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_video", "outcome": "success"},
                ).inc()
                return {
                    "success": True,
                    "analysis": result.data,
                    "content_type": "video",
                    "dominant_themes": result.data.get("dominant_themes", []),
                    "unified_sentiment": result.data.get("unified_sentiment", "neutral"),
                }
            else:
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_video", "outcome": "error"},
                ).inc()
                return {
                    "success": False,
                    "error": result.error,
                    "content_type": "video",
                }

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            metrics.counter(
                "mcp_tool_calls_total",
                labels={"tool": "analyze_video", "outcome": "error"},
            ).inc()
            return {"success": False, "error": str(e), "content_type": "video"}

    @mcp.tool()
    def analyze_audio(audio_url: str, tenant: str = "default", workspace: str = "default") -> dict[str, Any]:
        """Analyze audio content with speaker identification and tone detection.

        Args:
            audio_url: URL of the audio to analyze
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            Comprehensive audio analysis results
        """
        try:
            result = multimodal_tool._run(audio_url, "audio", tenant, workspace)

            if result.status == "success":
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_audio", "outcome": "success"},
                ).inc()
                return {
                    "success": True,
                    "analysis": result.data,
                    "content_type": "audio",
                    "dominant_themes": result.data.get("dominant_themes", []),
                    "unified_sentiment": result.data.get("unified_sentiment", "neutral"),
                }
            else:
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_audio", "outcome": "error"},
                ).inc()
                return {
                    "success": False,
                    "error": result.error,
                    "content_type": "audio",
                }

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            metrics.counter(
                "mcp_tool_calls_total",
                labels={"tool": "analyze_audio", "outcome": "error"},
            ).inc()
            return {"success": False, "error": str(e), "content_type": "audio"}

    @mcp.tool()
    def analyze_content_auto(content_url: str, tenant: str = "default", workspace: str = "default") -> dict[str, Any]:
        """Auto-detect content type and perform comprehensive multi-modal analysis.

        Args:
            content_url: URL of the content to analyze
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            Comprehensive multi-modal analysis results
        """
        try:
            result = multimodal_tool._run(content_url, "auto", tenant, workspace)

            if result.status == "success":
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_content_auto", "outcome": "success"},
                ).inc()
                return {
                    "success": True,
                    "analysis": result.data,
                    "content_type": result.data.get("content_type", "unknown"),
                    "dominant_themes": result.data.get("dominant_themes", []),
                    "unified_sentiment": result.data.get("unified_sentiment", "neutral"),
                    "cross_modal_insights": result.data.get("cross_modal_insights", {}),
                }
            else:
                metrics.counter(
                    "mcp_tool_calls_total",
                    labels={"tool": "analyze_content_auto", "outcome": "error"},
                ).inc()
                return {
                    "success": False,
                    "error": result.error,
                    "content_type": "unknown",
                }

        except Exception as e:
            logger.error(f"Auto content analysis failed: {e}")
            metrics.counter(
                "mcp_tool_calls_total",
                labels={"tool": "analyze_content_auto", "outcome": "error"},
            ).inc()
            return {"success": False, "error": str(e), "content_type": "unknown"}

    @mcp.tool()
    def get_visual_sentiment(image_url: str) -> dict[str, Any]:
        """Get visual sentiment analysis for an image.

        Args:
            image_url: URL of the image to analyze

        Returns:
            Visual sentiment and emotion analysis
        """
        try:
            # Use the multi-modal tool for visual analysis
            result = multimodal_tool._run(image_url, "image")

            if result.status == "success":
                visual_analysis = result.data.get("visual_analysis", {})
                return {
                    "success": True,
                    "visual_sentiment": visual_analysis.get("visual_sentiment", "neutral"),
                    "visual_emotions": visual_analysis.get("visual_emotions", {}),
                    "dominant_colors": visual_analysis.get("dominant_colors", []),
                    "scene_type": visual_analysis.get("scene_type", "general"),
                    "composition_score": visual_analysis.get("composition_score", 0.0),
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "visual_sentiment": "neutral",
                    "visual_emotions": {"neutral": 1.0},
                }

        except Exception as e:
            logger.error(f"Visual sentiment analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "visual_sentiment": "neutral",
                "visual_emotions": {"neutral": 1.0},
            }

    @mcp.tool()
    def extract_content_themes(content_url: str, content_type: str = "auto") -> dict[str, Any]:
        """Extract dominant themes and topics from content.

        Args:
            content_url: URL of the content to analyze
            content_type: Type of content (auto, image, video, audio)

        Returns:
            Extracted themes and topic analysis
        """
        try:
            result = multimodal_tool._run(content_url, content_type)

            if result.status == "success":
                return {
                    "success": True,
                    "dominant_themes": result.data.get("dominant_themes", []),
                    "content_type": result.data.get("content_type", "unknown"),
                    "unified_sentiment": result.data.get("unified_sentiment", "neutral"),
                    "cross_modal_insights": result.data.get("cross_modal_insights", {}),
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "dominant_themes": [],
                    "content_type": content_type,
                }

        except Exception as e:
            logger.error(f"Theme extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "dominant_themes": [],
                "content_type": content_type,
            }

    @mcp.resource("analysis://templates")
    def get_analysis_templates() -> str:
        """Get available analysis templates and configurations."""
        return """# Multi-Modal Analysis Templates

## Image Analysis Template
{
  "content_type": "image",
  "analysis_depth": "comprehensive",
  "include_visual_sentiment": true,
  "include_object_detection": true,
  "include_color_analysis": true,
  "include_composition_scoring": true
}

## Video Analysis Template
{
  "content_type": "video",
  "analysis_depth": "comprehensive",
  "include_frame_analysis": true,
  "include_scene_detection": true,
  "include_emotion_tracking": true,
  "include_audio_correlation": true,
  "frame_sampling_rate": 1.0
}

## Audio Analysis Template
{
  "content_type": "audio",
  "analysis_depth": "comprehensive",
  "include_speaker_identification": true,
  "include_tone_analysis": true,
  "include_transcription": true,
  "include_background_noise_detection": true
}

## Cross-Modal Analysis Template
{
  "content_type": "auto",
  "analysis_depth": "comprehensive",
  "include_cross_modal_correlation": true,
  "include_unified_sentiment": true,
  "include_theme_extraction": true,
  "include_enhanced_insights": true
}
"""

    @mcp.resource("analysis://capabilities")
    def get_analysis_capabilities() -> str:
        """Get current multi-modal analysis capabilities."""
        return """# Multi-Modal Analysis Capabilities

## Visual Analysis (Images)
✅ Object Detection: person, building, sky, vehicles, animals
✅ Color Analysis: Dominant color palette extraction (RGB values)
✅ Sentiment Detection: AI-powered visual emotion analysis
✅ Scene Classification: outdoor/indoor, bright/dark, well-composed
✅ Composition Scoring: Visual balance and golden ratio analysis

## Video Analysis (Videos)
✅ Frame Timeline: Structure for analyzing video progression
✅ Scene Change Detection: Identifies narrative transitions
✅ Sentiment Arc: Tracks emotional progression through video
✅ Key Moments: Identifies climactic or important segments
✅ Cross-Referenced Audio: Correlates visual and audio elements

## Audio Analysis (Audio)
✅ Speaker Identification: Multi-speaker conversation analysis
✅ Tone Detection: Emotional analysis of speech patterns
✅ Speech Rate Analysis: Words-per-minute and pacing metrics
✅ Background Noise Detection: Audio quality assessment
✅ Language Identification: Automatic language detection

## Cross-Modal Correlation
✅ Unified Sentiment: Combines sentiment across all modalities
✅ Theme Extraction: Identifies dominant themes across media types
✅ Consistency Analysis: Detects sentiment alignment between modalities
✅ Enhanced Insights: Combines multiple analysis dimensions

## Integration Features
✅ Vector Database Storage: Multi-modal embeddings for RAG
✅ Discord Integration: Rich embed formatting for results
✅ Tenant Isolation: Multi-tenant support with proper isolation
✅ Performance Monitoring: Comprehensive metrics and observability
"""

    return mcp


# Standalone server runner for testing
def run_multimodal_server():
    """Run the multi-modal analysis MCP server standalone."""
    import os

    # Check if we should run in standalone mode
    if os.getenv("RUN_MULTIMODAL_SERVER") == "1":
        mcp = create_multimodal_server()
        print("🚀 Starting Multi-Modal Analysis MCP Server...")
        mcp.run()
    else:
        print("INFO: Multi-modal server available but not running in standalone mode")
        print("💡 Set RUN_MULTIMODAL_SERVER=1 to run standalone")


if __name__ == "__main__":
    run_multimodal_server()


__all__ = ["create_multimodal_server", "run_multimodal_server"]
