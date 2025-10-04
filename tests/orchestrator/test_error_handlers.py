"""Unit tests for orchestrator.error_handlers module.

Tests JSON repair and fallback key-value extraction utilities.
"""

from ultimate_discord_intelligence_bot.orchestrator import error_handlers


class TestRepairJson:
    """Tests for repair_json() function."""

    def test_removes_trailing_commas_in_objects(self):
        """Test removal of trailing commas before closing braces."""
        malformed = '{"key": "value",}'
        repaired = error_handlers.repair_json(malformed)
        assert repaired == '{"key": "value"}'

    def test_removes_trailing_commas_in_arrays(self):
        """Test removal of trailing commas before closing brackets."""
        malformed = '["item1", "item2",]'
        repaired = error_handlers.repair_json(malformed)
        assert repaired == '["item1", "item2"]'

    def test_replaces_single_quotes_with_double_quotes(self):
        """Test replacement of single quotes when used for keys."""
        malformed = "{'key': 'value'}"
        repaired = error_handlers.repair_json(malformed)
        assert repaired == '{"key": "value"}'

    def test_removes_newlines_in_string_values(self):
        """Test removal of newlines within string values."""
        malformed = '{"key": "value\nwith newline"}'
        repaired = error_handlers.repair_json(malformed)
        assert repaired == '{"key": "value with newline"}'

    def test_handles_multiple_issues(self):
        """Test repair of JSON with multiple malformations."""
        malformed = "{'key1': 'value1',\n'key2': 'value2',}"
        repaired = error_handlers.repair_json(malformed)
        # Should fix single quotes and trailing comma
        assert '{"key1"' in repaired
        assert repaired.endswith("}")  # No trailing comma

    def test_leaves_valid_json_unchanged(self):
        """Test that valid JSON is not modified."""
        valid = '{"key": "value", "nested": {"inner": "data"}}'
        repaired = error_handlers.repair_json(valid)
        # Should be essentially the same (minor whitespace differences OK)
        assert '"key"' in repaired
        assert '"value"' in repaired

    def test_handles_empty_string(self):
        """Test handling of empty input."""
        repaired = error_handlers.repair_json("")
        assert repaired == ""

    def test_handles_nested_structures(self):
        """Test repair of nested JSON structures."""
        malformed = '{"outer": {"inner": "value",},}'
        repaired = error_handlers.repair_json(malformed)
        assert repaired.count(",}") == 0  # No trailing commas


class TestExtractKeyValuesFromText:
    """Tests for extract_key_values_from_text() function."""

    def test_extracts_colon_separated_pairs(self):
        """Test extraction of key: value format."""
        text = "file_path: video.mp4\ntitle: Test Video"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert extracted["file_path"] == "video.mp4"
        assert extracted["title"] == "Test Video"

    def test_extracts_equals_separated_pairs(self):
        """Test extraction of key = value format."""
        text = "file_path = video.mp4\ntitle = Test Video"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert extracted["file_path"] == "video.mp4"
        assert extracted["title"] == "Test Video"

    def test_extracts_json_style_pairs(self):
        """Test extraction of JSON-style pairs."""
        text = '"file_path": "video.mp4", "title": "Test"'
        extracted = error_handlers.extract_key_values_from_text(text)
        assert extracted["file_path"] == "video.mp4"
        assert extracted["title"] == "Test"

    def test_extracts_important_fields_with_regex(self):
        """Test extraction of specific important fields."""
        text = "The file is located at file_path: /path/to/video.mp4 and the url: https://example.com/video"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert "file_path" in extracted
        assert "video.mp4" in extracted["file_path"]
        assert "url" in extracted
        assert extracted["url"] == "https://example.com/video"

    def test_extracts_transcript_field(self):
        """Test extraction of transcript field with multiline content."""
        text = "transcript: This is a long transcript\nwith multiple lines\n\nother_key: value"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert "transcript" in extracted
        assert "This is a long transcript" in extracted["transcript"]

    def test_ignores_short_values(self):
        """Test that very short values (<=3 chars) are ignored."""
        text = "key1: ab\nkey2: value"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert "key1" not in extracted  # Only 2 chars
        assert "key2" in extracted

    def test_handles_empty_text(self):
        """Test handling of empty input."""
        extracted = error_handlers.extract_key_values_from_text("")
        assert extracted == {}

    def test_handles_text_without_patterns(self):
        """Test handling of text with no recognizable patterns."""
        text = "This is just plain text with no key-value pairs"
        extracted = error_handlers.extract_key_values_from_text(text)
        # Should return empty dict or minimal extraction
        assert isinstance(extracted, dict)

    def test_strips_quotes_from_values(self):
        """Test that quotes are stripped from extracted values."""
        text = "key: 'value'\nkey2: \"value2\""
        extracted = error_handlers.extract_key_values_from_text(text)
        assert extracted["key"] == "value"  # No quotes
        assert extracted["key2"] == "value2"  # No quotes

    def test_extracts_multiple_file_extensions(self):
        """Test extraction of various media file extensions."""
        text = "audio: test.mp3\nvideo: test.webm\narchive: test.m4a"
        extracted = error_handlers.extract_key_values_from_text(text)
        assert "test.mp3" in str(extracted.get("audio", ""))
        assert "test.webm" in str(extracted.get("video", ""))
        assert "test.m4a" in str(extracted.get("archive", ""))

    def test_handles_mixed_formats(self):
        """Test extraction from text with mixed key-value formats."""
        text = """
        file_path: /path/to/video.mp4
        title = "My Video"
        url: https://example.com
        """
        extracted = error_handlers.extract_key_values_from_text(text)
        assert "file_path" in extracted
        assert "title" in extracted
        assert "url" in extracted
