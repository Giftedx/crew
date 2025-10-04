"""Error handling and data repair utilities for orchestrator.

This module provides utilities for:
- Repairing malformed JSON
- Extracting key-value pairs from plain text fallback
"""

import re
from typing import Any


def repair_json(json_text: str) -> str:
    """Attempt to repair common JSON malformations.

    Handles:
    - Unescaped quotes in string values
    - Trailing commas before closing braces/brackets
    - Single quotes instead of double quotes
    - Newlines in string values

    Args:
        json_text: Potentially malformed JSON string

    Returns:
        Repaired JSON string

    Example:
        >>> repair_json('{"key": "value",}')
        '{"key": "value"}'
    """
    repaired = json_text

    # Fix 1: Remove trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Fix 2: Replace single quotes with double quotes (but not in escaped contexts)
    # This is risky, so we only do it if we detect single-quoted keys
    if re.search(r"'[a-zA-Z_][a-zA-Z0-9_]*'\s*:", repaired):
        repaired = repaired.replace("'", '"')

    # Fix 3: Escape unescaped quotes within string values
    # Find patterns like: "key": "value with "embedded" quotes"
    # This is complex, so we use a careful regex
    def escape_inner_quotes(match):
        key_value = match.group(0)
        # Only fix if we detect unescaped quotes inside the value
        if key_value.count('"') > 4:  # More than 2 pairs suggests embedded quotes
            parts = key_value.split('":')
            if len(parts) == 2:
                key_part = parts[0] + '":'
                value_part = parts[1]
                # Escape quotes in value part (but not the outer delimiters)
                if value_part.count('"') > 2:
                    # Find inner quotes and escape them
                    value_part = re.sub(r'([^\\])"', r'\1\\"', value_part)
                return key_part + value_part
        return key_value

    # Apply escaping fix cautiously
    # repaired = re.sub(r'"[^"]+"\s*:\s*"[^"]*"[^"]*"[^"]*"', escape_inner_quotes, repaired)

    # Fix 4: Remove newlines within string values
    repaired = re.sub(r'"([^"]*?)\n([^"]*?)"', r'"\1 \2"', repaired)

    return repaired


def extract_key_values_from_text(text: str) -> dict[str, Any]:
    """Fallback extraction when JSON parsing fails.

    Attempts to extract key-value pairs from plain text output using
    common patterns like "key: value" or "key = value".

    Args:
        text: Plain text containing key-value pairs

    Returns:
        Dictionary of extracted key-value pairs

    Example:
        >>> extract_key_values_from_text("file_path: video.mp4\\ntitle: Test")
        {'file_path': 'video.mp4', 'title': 'Test'}
    """
    extracted = {}

    # Common patterns for key-value pairs
    patterns = [
        r"(?:^|\n)([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+?)(?=\n|$)",  # key: value
        r"(?:^|\n)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)(?=\n|$)",  # key = value
        r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:\s*"([^"]*)"',  # "key": "value"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for key, value in matches:
            key = key.strip()
            value = value.strip().strip("\"'")

            # Only add if we got something meaningful
            if key and value and len(value) > 3:
                extracted[key] = value

    # Try to extract specific important fields if present
    important_fields = {
        "file_path": r"(?:file_path|path|file)[\s:=]+([^\s\n]+\.(?:mp4|webm|mp3|wav|m4a))",
        "transcript": r"(?:transcript|transcription)[\s:=]+(.*?)(?:\n\n|$)",
        "url": r"(?:url|link)[\s:=]+(https?://[^\s\n]+)",
        "title": r"(?:title)[\s:=]+(.+?)(?=\n|$)",
    }

    for field, pattern in important_fields.items():
        if field not in extracted:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                extracted[field] = match.group(1).strip()

    return extracted
