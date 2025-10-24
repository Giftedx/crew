"""Helper functions for rendering analysis results in Discord."""

from collections.abc import Mapping
from typing import Any

import discord


# Constants for display limits
MAX_URL_DISPLAY_LENGTH = 100
MAX_TITLE_DISPLAY_LENGTH = 80
MAX_KEYWORDS_COUNT_DISPLAY = 8
MAX_KEYWORD_TEXT_LENGTH = 200


def extract_result_data(result) -> tuple[str, dict, str | None, float]:
    """Extract status, data, error, and processing time from a variety of result shapes.

    Supports:
    - StepResult-like objects (have `.success`, `.data`, `.error`)
    - Mapping/dict shapes with keys: status/data/error/processing_time
    - Fallback to attribute-based `status/data/error` if present
    """
    # StepResult-like (preferred): expose success/error/data consistently
    if hasattr(result, "success") and hasattr(result, "data"):
        status = "success" if bool(getattr(result, "success", False)) else "error"
        data = getattr(result, "data", {}) or {}
        error = getattr(result, "error", None)
        processing_time = getattr(result, "processing_time", 0) or 0
        return status, data, error, processing_time

    # Mapping/dict-like (including StepResult acting as Mapping)
    if isinstance(result, Mapping):
        # Try to derive a sensible status when missing
        status = result.get("status")  # type: ignore[index]
        if not status:
            if result.get("error") is not None:  # type: ignore[index]
                status = "error"
            elif bool(result.get("success")):  # type: ignore[index]
                status = "success"
            else:
                status = "unknown"
        data = result.get("data", {})  # type: ignore[index]
        error = result.get("error", None)  # type: ignore[index]
        processing_time = result.get("processing_time", 0) or 0  # type: ignore[index]
        # Ensure mapping for data
        if not isinstance(data, dict):
            data = {}
        return str(status), data, error, processing_time

    # Attribute fallback (rare)
    if hasattr(result, "status") or hasattr(result, "data"):
        status = getattr(result, "status", "unknown")
        data = getattr(result, "data", {}) or {}
        error = getattr(result, "error", None)
        processing_time = getattr(result, "processing_time", 0) or 0
        return status, data, error, processing_time

    raise ValueError(f"Unexpected result format: {str(result)[:200]}")


def create_base_embed(platform: str, url: str, processing_time: float) -> Any:
    """Create the base embed with title and basic info."""
    embed = discord.Embed(
        title="✅ Content Analysis Complete",
        description=f"**Platform:** {platform}\n**Status:** Successfully analyzed",
        color=0x00FF00,
    )

    trunc_url = url[:MAX_URL_DISPLAY_LENGTH] + ("..." if len(url) > MAX_URL_DISPLAY_LENGTH else "")
    embed.add_field(
        name="📊 Analysis Details",
        value=(
            f"**URL:** {trunc_url}\n"
            f"**Platform:** {platform}\n"
            f"**Processing Time:** {processing_time:.1f}s\n"
            f"**Status:** ✅ Complete"
        ),
        inline=False,
    )

    return embed


def add_basic_video_info(embed: Any, download_info: dict[str, Any] | None) -> None:
    """Add basic video information fields."""
    if not download_info:
        return
    parts: list[str] = []
    title = download_info.get("title")
    if title:
        parts.append(f"**Title:** {str(title)[:MAX_TITLE_DISPLAY_LENGTH]}")
    uploader = download_info.get("uploader")
    if uploader:
        parts.append(f"**Uploader:** {uploader}")
    if "duration" in download_info:
        duration = download_info["duration"]
        try:
            seconds = int(duration)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            duration_str = f"{hours}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes}:{secs:02d}"
        except (ValueError, TypeError):
            duration_str = str(duration)
        parts.append(f"**Duration:** {duration_str}")
    if parts:
        embed.add_field(name="📹 Video Information", value="\n".join(parts), inline=False)


def add_sentiment_field(embed: Any, analysis_results: dict[str, Any] | None) -> None:
    """Add sentiment analysis field."""
    if not analysis_results or "sentiment" not in analysis_results:
        return
    sentiment = analysis_results.get("sentiment", {})
    if not isinstance(sentiment, dict):
        return
    compound = sentiment.get("compound", 0)
    if compound > 0.05:
        sentiment_text = f"😊 Positive ({compound:.2f})"
        sentiment_color = "🟢"
    elif compound < -0.05:
        sentiment_text = f"😞 Negative ({compound:.2f})"
        sentiment_color = "🔴"
    else:
        sentiment_text = f"😐 Neutral ({compound:.2f})"
        sentiment_color = "🟡"
    embed.add_field(
        name="🎭 Sentiment Analysis",
        value=f"{sentiment_color} {sentiment_text}",
        inline=True,
    )


def add_keywords_field(embed: Any, analysis_results: dict[str, Any] | None) -> None:
    """Add keywords/topics field."""
    if not analysis_results or "keywords" not in analysis_results:
        return
    keywords = analysis_results.get("keywords")
    if not keywords or not isinstance(keywords, list):
        return
    shown = ", ".join(keywords[:MAX_KEYWORDS_COUNT_DISPLAY])
    truncated = shown[:MAX_KEYWORD_TEXT_LENGTH]
    if len(shown) > MAX_KEYWORD_TEXT_LENGTH:
        truncated += "..."
    embed.add_field(name="🏷️ Key Topics", value=truncated, inline=True)


def add_fallacies_field(embed: Any, fallacy_info: dict[str, Any] | None) -> None:
    """Add logical fallacies field."""
    if not fallacy_info or not isinstance(fallacy_info, dict):
        return
    fallacies = fallacy_info.get("fallacies", [])
    if not fallacies or not isinstance(fallacies, list):
        return
    fallacy_count = len(fallacies)
    top_types = [f.get("type", f.get("name", str(f)[:20])) for f in fallacies[:3] if f]
    text = f"Found {fallacy_count} fallac{'y' if fallacy_count == 1 else 'ies'}"
    if top_types:
        text += f": {', '.join(top_types)}"
        if fallacy_count > 3:
            text += ", ..."
    embed.add_field(name="🧠 Logical Analysis", value=text, inline=True)


def add_summary_field(embed: Any, perspective_info: dict[str, Any] | None) -> None:
    """Add summary/perspective field."""
    if not perspective_info or not isinstance(perspective_info, dict):
        return
    summary = perspective_info.get("summary", "")
    if summary and isinstance(summary, str):
        # Truncate summary if too long
        max_summary_length = 300
        if len(summary) > max_summary_length:
            summary = summary[:max_summary_length] + "..."
        embed.add_field(name="📝 Summary", value=summary, inline=False)


def add_transcript_field(embed: Any, transcription_info: dict[str, Any] | None) -> None:
    """Add transcript information field."""
    if not transcription_info or not isinstance(transcription_info, dict):
        return
    transcript_length = transcription_info.get("length")
    if transcript_length:
        embed.add_field(
            name="📋 Transcript",
            value=f"Transcript available ({transcript_length} characters)",
            inline=True,
        )


def add_fallback_content_summary(embed: Any, data: dict[str, Any]) -> None:
    """Add fallback content summary when no specific analysis is available."""
    summary_parts = []
    if "title" in data:
        title = str(data["title"])[:MAX_TITLE_DISPLAY_LENGTH]
        summary_parts.append(f"**Title:** {title}")
    if "duration" in data:
        summary_parts.append(f"**Duration:** {data['duration']}")
    if "transcript_length" in data:
        summary_parts.append(f"**Transcript Length:** {data['transcript_length']} chars")
    if summary_parts:
        embed.add_field(
            name="📋 Content Summary",
            value="\n".join(summary_parts[:5]),
            inline=False,
        )


def add_completion_note(embed: Any) -> None:
    """Add final completion note."""
    embed.add_field(
        name="💡 Note",
        value="Full content analysis completed with transcription and processing pipeline.",
        inline=False,
    )
