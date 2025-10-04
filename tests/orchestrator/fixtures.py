"""
Shared test fixtures for orchestrator tests.

Provides reusable sample data for testing orchestrator helper methods.
"""

from typing import Any

import pytest


@pytest.fixture
def sample_crew_result() -> dict[str, Any]:
    """Sample CrewAI CrewOutput with all stages."""
    return {
        "raw": """
        # Acquisition Complete
        Successfully downloaded video from https://youtube.com/watch?v=example
        Duration: 1847 seconds
        Title: "The Future of AI Safety"
        Channel: AI Research Lab

        # Transcription Complete
        [00:00:15] Welcome to today's discussion on AI safety and alignment.
        [00:05:30] The key challenge is ensuring AI systems remain beneficial.
        [10:45] We need robust testing frameworks before deployment.

        # Analysis Complete
        **Main Themes:**
        - AI Safety: Critical importance of alignment research
        - Testing Infrastructure: Need for comprehensive validation
        - Deployment Risks: Careful rollout strategies required

        **Sentiment:** Professional, cautiously optimistic (0.65)
        **Confidence:** High (0.82)

        # Timeline of Key Points
        - 00:15 - Introduction to AI safety challenges
        - 05:30 - Discussion of alignment problems
        - 10:45 - Testing framework requirements
        """,
        "token_usage": {"total_tokens": 1250, "prompt_tokens": 850, "completion_tokens": 400},
        "tasks_output": [
            {
                "description": "Acquire content",
                "summary": "Downloaded video successfully",
                "raw": "Video acquired: 1847s duration",
            },
            {
                "description": "Transcribe content",
                "summary": "Generated transcript with timestamps",
                "raw": "[00:00:15] Welcome to discussion...",
            },
            {
                "description": "Analyze content",
                "summary": "Extracted themes and sentiment",
                "raw": "Themes: AI Safety, Testing...",
            },
        ],
    }


@pytest.fixture
def sample_acquisition_data() -> dict[str, Any]:
    """Sample acquisition stage output."""
    return {
        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Understanding Large Language Models",
        "duration": 1847,
        "channel": "AI Explained",
        "upload_date": "2024-01-15",
        "view_count": 125000,
        "like_count": 4200,
        "comment_count": 380,
        "description": "Deep dive into transformer architectures and attention mechanisms",
        "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "format": "best",
        "file_path": "/tmp/downloads/video_123.mp4",
        "file_size_bytes": 145678901,
    }


@pytest.fixture
def sample_transcript() -> str:
    """Sample transcript with timestamps."""
    return """[00:00:15] Welcome everyone to today's discussion on large language models.
[00:01:30] Let's start by understanding the transformer architecture.
[00:05:45] Attention mechanisms are the key innovation here.
[00:10:20] Self-attention allows the model to weigh different parts of the input.
[00:15:00] Layer normalization helps with training stability.
[00:20:15] Positional encodings preserve sequence information.
[00:25:30] The feed-forward networks process the attended features.
[00:30:00] Pre-training on large corpora is essential for performance.
[00:35:15] Fine-tuning adapts the model to specific tasks.
[00:40:00] Prompt engineering is an emerging best practice."""


@pytest.fixture
def sample_analysis_output() -> dict[str, Any]:
    """Sample analysis stage output."""
    return {
        "main_themes": [
            {
                "theme": "Transformer Architecture",
                "confidence": 0.92,
                "evidence": ["attention mechanisms", "layer normalization", "positional encodings"],
            },
            {
                "theme": "Training Methodology",
                "confidence": 0.85,
                "evidence": ["pre-training", "fine-tuning", "large corpora"],
            },
            {
                "theme": "Practical Applications",
                "confidence": 0.78,
                "evidence": ["prompt engineering", "task-specific adaptation"],
            },
        ],
        "sentiment": {"polarity": 0.68, "subjectivity": 0.42, "label": "positive"},
        "key_entities": [
            {"text": "transformer architecture", "type": "CONCEPT", "count": 5},
            {"text": "attention mechanisms", "type": "CONCEPT", "count": 8},
            {"text": "large language models", "type": "CONCEPT", "count": 12},
        ],
        "timeline": [
            {"timestamp": "00:00:15", "event": "Introduction to LLMs", "importance": 0.75},
            {"timestamp": "00:05:45", "event": "Attention mechanisms explained", "importance": 0.95},
            {"timestamp": "00:30:00", "event": "Pre-training discussion", "importance": 0.88},
        ],
        "confidence_score": 0.82,
        "coherence_score": 0.91,
        "factual_accuracy": 0.87,
    }


@pytest.fixture
def sample_crew_result_with_placeholders() -> dict[str, Any]:
    """Sample CrewAI result containing placeholder data (quality issue)."""
    return {
        "raw": """
        # Acquisition Complete
        Successfully downloaded the video
        Duration: [DURATION]
        Title: The content title

        # Analysis Complete
        **Main Themes:**
        - Theme 1: The first theme discussed
        - Theme 2: Another important topic
        - Theme 3: Additional content area

        **Sentiment:** The overall tone is [SENTIMENT]
        **Confidence:** [CONFIDENCE_SCORE]
        """,
        "token_usage": {"total_tokens": 250, "prompt_tokens": 150, "completion_tokens": 100},
        "tasks_output": [],
    }


@pytest.fixture
def sample_incomplete_crew_result() -> dict[str, Any]:
    """Sample CrewAI result with missing sections."""
    return {
        "raw": """
        # Acquisition Complete
        Downloaded video successfully.

        # Transcription
        [Transcription failed - audio quality too low]
        """,
        "token_usage": {"total_tokens": 80, "prompt_tokens": 50, "completion_tokens": 30},
        "tasks_output": [
            {"description": "Acquire content", "summary": "Success", "raw": "Downloaded"},
        ],
    }
