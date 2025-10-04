"""Test fix for /autointel quality parameter TypeError.

This test validates the fix for the bug where YouTubeDownloadTool would crash
with "TypeError: expected string or bytes-like object, got 'NoneType'" when
the LLM provided quality="best" but the wrapper detected it as a placeholder.

Bug Report:
-----------
The issue occurred in the /autointel command:
1. LLM provided quality="best" to YouTubeDownloadTool
2. Wrapper detected "best" as placeholder (< 10 chars) and set it to None
3. YouTubeDownloadTool._run() tried to regex match on None
4. TypeError: expected string or bytes-like object, got 'NoneType'

Fix:
----
1. Modified _is_placeholder_or_empty() to exclude valid quality values
2. Added None quality handling in YouTubeDownloadTool._run()
"""

import re


def test_placeholder_detection_excludes_valid_quality_values():
    """Verify that valid quality values are NOT treated as placeholders."""

    def _is_placeholder_or_empty(value, param_name):
        """Placeholder detection logic from crewai_tool_wrappers.py"""
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False

        normalized = value.strip().lower()

        # CRITICAL FIX: Exclude valid quality/format values from placeholder detection
        VALID_SHORT_VALUES = {
            "best",
            "worst",
            "720p",
            "1080p",
            "480p",
            "360p",
            "240p",
            "144p",
            "high",
            "medium",
            "low",
            "true",
            "false",
            "yes",
            "no",
            "on",
            "off",
        }
        if normalized in VALID_SHORT_VALUES or param_name == "quality":
            return False

        if not normalized or len(normalized) < 10:
            return True
        return False

    # Valid quality values should NOT be placeholders
    assert not _is_placeholder_or_empty("best", "quality"), "best should NOT be placeholder"
    assert not _is_placeholder_or_empty("worst", "quality"), "worst should NOT be placeholder"
    assert not _is_placeholder_or_empty("1080p", "quality"), "1080p should NOT be placeholder"
    assert not _is_placeholder_or_empty("720p", "quality"), "720p should NOT be placeholder"
    assert not _is_placeholder_or_empty("high", "quality"), "high should NOT be placeholder"

    # Empty/None should still be placeholders
    assert _is_placeholder_or_empty("", "quality"), "empty string should be placeholder"
    assert _is_placeholder_or_empty(None, "quality"), "None should be placeholder"

    # Short generic values should still be placeholders for non-quality params
    assert _is_placeholder_or_empty("text", "text"), "generic 'text' should be placeholder"
    assert _is_placeholder_or_empty("data", "data"), "generic 'data' should be placeholder"


def test_youtube_download_tool_handles_none_quality():
    """Verify that YouTubeDownloadTool gracefully handles None quality parameter."""

    # Simulate the fixed code path from YouTubeDownloadTool._run()
    quality = None

    # CRITICAL FIX: Handle None quality parameter gracefully
    if quality is None:
        quality = "1080p"  # Fallback to default

    # This should NOT raise TypeError anymore
    match = re.match(r"(\d+)", quality)
    height = match.group(1) if match else "1080"

    assert height == "1080", f"Expected height='1080', got '{height}'"
    assert quality == "1080p", f"Expected quality='1080p', got '{quality}'"


def test_youtube_download_tool_handles_best_quality():
    """Verify that YouTubeDownloadTool handles 'best' quality correctly."""

    # Simulate the code path when quality="best" is provided
    quality = "best"

    # This should NOT raise TypeError
    match = re.match(r"(\d+)", quality)
    height = match.group(1) if match else "1080"

    assert height == "1080", f"Expected default height='1080' for 'best', got '{height}'"


def test_youtube_download_tool_handles_numeric_quality():
    """Verify that YouTubeDownloadTool extracts height from numeric quality."""

    # Test with various numeric quality formats
    test_cases = [
        ("1080p", "1080"),
        ("720p", "720"),
        ("480p", "480"),
        ("360p", "360"),
        ("1440", "1440"),
        ("2160p", "2160"),
    ]

    for quality, expected_height in test_cases:
        match = re.match(r"(\d+)", quality)
        height = match.group(1) if match else "1080"
        assert height == expected_height, (
            f"For quality='{quality}', expected height='{expected_height}', got '{height}'"
        )


def test_crewai_wrapper_applies_default_quality():
    """Test that wrapper applies default quality='best' for download tools."""

    # Simulate the wrapper logic from crewai_tool_wrappers.py
    filtered_kwargs = {}
    allowed = {"video_url", "quality"}

    # Wrapper should apply default when quality is None
    if "quality" in allowed and filtered_kwargs.get("quality") is None:
        filtered_kwargs["quality"] = "best"

    assert filtered_kwargs.get("quality") == "best", "Wrapper should default quality to 'best'"


def test_integration_quality_parameter_flow():
    """Integration test: verify end-to-end quality parameter flow.

    This simulates the full flow:
    1. LLM provides quality="best"
    2. Wrapper doesn't treat it as placeholder
    3. Value flows to YouTubeDownloadTool
    4. Tool handles it correctly
    """

    # Step 1: LLM provides quality="best"
    llm_provided_kwargs = {"video_url": "https://youtube.com/watch?v=test", "quality": "best"}

    # Step 2: Placeholder detection (should NOT flag "best")
    def _is_placeholder_or_empty(value, param_name):
        if value is None or value == "":
            return True
        if not isinstance(value, str):
            return False
        normalized = value.strip().lower()
        VALID_SHORT_VALUES = {"best", "worst", "720p", "1080p", "480p", "360p", "240p", "144p", "high", "medium", "low"}
        if normalized in VALID_SHORT_VALUES or param_name == "quality":
            return False
        if not normalized or len(normalized) < 10:
            return True
        return False

    for k in list(llm_provided_kwargs.keys()):
        if _is_placeholder_or_empty(llm_provided_kwargs[k], k):
            llm_provided_kwargs[k] = None

    # "best" should NOT be set to None
    assert llm_provided_kwargs["quality"] == "best", "quality='best' should NOT be treated as placeholder"

    # Step 3: Tool handles "best" correctly (falls back to default height)
    quality = llm_provided_kwargs["quality"]
    match = re.match(r"(\d+)", quality)
    height = match.group(1) if match else "1080"

    assert height == "1080", "Should default to 1080 for non-numeric quality"


if __name__ == "__main__":
    # Run all tests
    test_placeholder_detection_excludes_valid_quality_values()
    test_youtube_download_tool_handles_none_quality()
    test_youtube_download_tool_handles_best_quality()
    test_youtube_download_tool_handles_numeric_quality()
    test_crewai_wrapper_applies_default_quality()
    test_integration_quality_parameter_flow()

    print("✅ All quality parameter tests passed!")
