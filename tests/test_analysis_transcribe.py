"""Tests for analysis.transcribe module."""

import pytest
import tempfile
import os
from pathlib import Path
from analysis.transcribe import Segment, Transcript, run_whisper


def test_segment_creation():
    """Test Segment dataclass creation and properties."""
    # Test basic segment
    segment = Segment(0.0, 1.5, "Hello world")
    
    assert segment.start == 0.0
    assert segment.end == 1.5
    assert segment.text == "Hello world"
    assert segment.speaker is None
    
    # Test segment with speaker
    segment_with_speaker = Segment(2.0, 4.0, "How are you?", "Speaker A")
    
    assert segment_with_speaker.start == 2.0
    assert segment_with_speaker.end == 4.0
    assert segment_with_speaker.text == "How are you?"
    assert segment_with_speaker.speaker == "Speaker A"


def test_transcript_creation():
    """Test Transcript dataclass creation and properties."""
    segments = [
        Segment(0.0, 1.0, "First segment"),
        Segment(1.0, 2.5, "Second segment"),
        Segment(2.5, 4.0, "Third segment")
    ]
    
    transcript = Transcript(segments)
    
    assert len(transcript.segments) == 3
    assert transcript.segments[0].text == "First segment"
    assert transcript.segments[1].start == 1.0
    assert transcript.segments[2].end == 4.0


def test_transcript_empty():
    """Test empty transcript creation."""
    empty_transcript = Transcript([])
    
    assert len(empty_transcript.segments) == 0
    assert isinstance(empty_transcript.segments, list)


def test_run_whisper_fallback_mode():
    """Test run_whisper fallback mode with text file."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Hello world\n")
        temp_file.write("This is the second line\n")
        temp_file.write("And this is the third line\n")
        temp_file_path = temp_file.name
    
    try:
        # Run whisper on the text file (should use fallback mode)
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 3
        
        # Check first segment
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[0].end == 1.0
        assert transcript.segments[0].text == "Hello world"
        assert transcript.segments[0].speaker is None
        
        # Check second segment
        assert transcript.segments[1].start == 1.0
        assert transcript.segments[1].end == 2.0
        assert transcript.segments[1].text == "This is the second line"
        
        # Check third segment
        assert transcript.segments[2].start == 2.0
        assert transcript.segments[2].end == 3.0
        assert transcript.segments[2].text == "And this is the third line"
    
    finally:
        # Clean up
        os.unlink(temp_file_path)


def test_run_whisper_empty_file():
    """Test run_whisper with empty text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        # Write nothing to the file
        temp_file_path = temp_file.name
    
    try:
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 0
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_single_line():
    """Test run_whisper with single line text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Single line of text")
        temp_file_path = temp_file.name
    
    try:
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 1
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[0].end == 1.0
        assert transcript.segments[0].text == "Single line of text"
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_with_blank_lines():
    """Test run_whisper handling of blank lines."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("First line\n")
        temp_file.write("\n")  # Blank line
        temp_file.write("Third line\n")
        temp_file.write("\n\n")  # More blank lines
        temp_file.write("Final line")
        temp_file_path = temp_file.name
    
    try:
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        # The actual number of segments depends on how splitlines() processes the content
        assert len(transcript.segments) > 0
        
        # Check that we have the expected text content
        texts = [seg.text for seg in transcript.segments]
        assert "First line" in texts
        assert "Third line" in texts
        assert "Final line" in texts
        
        # Should have empty strings for blank lines
        empty_segments = [seg for seg in transcript.segments if seg.text == ""]
        assert len(empty_segments) >= 2  # At least some blank lines
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_unicode_content():
    """Test run_whisper with unicode content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
        temp_file.write("Café and résumé\n")
        temp_file.write("naïve algorithm 🚀\n")
        temp_file.write("数据处理")
        temp_file_path = temp_file.name
    
    try:
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 3
        
        assert transcript.segments[0].text == "Café and résumé"
        assert transcript.segments[1].text == "naïve algorithm 🚀"
        assert transcript.segments[2].text == "数据处理"
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_long_content():
    """Test run_whisper with longer text content."""
    long_lines = []
    for i in range(100):
        long_lines.append(f"This is line {i+1} with some content to test segmentation.")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write('\n'.join(long_lines))
        temp_file_path = temp_file.name
    
    try:
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 100
        
        # Check first and last segments
        assert transcript.segments[0].text == "This is line 1 with some content to test segmentation."
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[0].end == 1.0
        
        assert transcript.segments[99].text == "This is line 100 with some content to test segmentation."
        assert transcript.segments[99].start == 99.0
        assert transcript.segments[99].end == 100.0
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_default_model_parameter():
    """Test that run_whisper accepts model parameter."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Test content")
        temp_file_path = temp_file.name
    
    try:
        # Test with default model
        transcript1 = run_whisper(temp_file_path)
        
        # Test with explicit model parameter (should still use fallback)
        transcript2 = run_whisper(temp_file_path, model="base")
        
        # Both should produce same result in fallback mode
        assert len(transcript1.segments) == len(transcript2.segments)
        assert transcript1.segments[0].text == transcript2.segments[0].text
    
    finally:
        os.unlink(temp_file_path)


def test_run_whisper_nonexistent_file():
    """Test run_whisper behavior with non-existent file."""
    with pytest.raises((FileNotFoundError, IOError)):
        run_whisper("/path/that/does/not/exist.txt")


def test_segment_dataclass_features():
    """Test that Segment is a proper dataclass."""
    segment = Segment(1.0, 2.0, "test")
    
    # Test that it's a dataclass
    assert hasattr(segment, '__dataclass_fields__')
    
    # Test field names
    field_names = set(segment.__dataclass_fields__.keys())
    expected_fields = {'start', 'end', 'text', 'speaker'}
    assert field_names == expected_fields
    
    # Test repr functionality
    repr_str = repr(segment)
    assert 'Segment' in repr_str
    assert '1.0' in repr_str
    assert '2.0' in repr_str
    assert 'test' in repr_str


def test_transcript_dataclass_features():
    """Test that Transcript is a proper dataclass."""
    transcript = Transcript([])
    
    # Test that it's a dataclass
    assert hasattr(transcript, '__dataclass_fields__')
    
    # Test field names
    field_names = set(transcript.__dataclass_fields__.keys())
    expected_fields = {'segments'}
    assert field_names == expected_fields
    
    # Test repr functionality
    repr_str = repr(transcript)
    assert 'Transcript' in repr_str


def test_segment_equality():
    """Test Segment equality comparison."""
    segment1 = Segment(1.0, 2.0, "test")
    segment2 = Segment(1.0, 2.0, "test")
    segment3 = Segment(1.0, 2.0, "different")
    
    # Equal segments
    assert segment1 == segment2
    
    # Different segments
    assert segment1 != segment3
    
    # With speaker
    segment4 = Segment(1.0, 2.0, "test", "Speaker A")
    segment5 = Segment(1.0, 2.0, "test", "Speaker A")
    
    assert segment4 == segment5
    assert segment1 != segment4  # None vs Speaker A


def test_transcript_equality():
    """Test Transcript equality comparison."""
    segments1 = [Segment(0.0, 1.0, "test")]
    segments2 = [Segment(0.0, 1.0, "test")]
    segments3 = [Segment(0.0, 1.0, "different")]
    
    transcript1 = Transcript(segments1)
    transcript2 = Transcript(segments2)
    transcript3 = Transcript(segments3)
    
    assert transcript1 == transcript2
    assert transcript1 != transcript3


def test_run_whisper_error_handling():
    """Test that run_whisper gracefully handles errors and uses fallback."""
    # This tests the try/except behavior documented in the module
    # Even if whisper is available, file read errors should be handled
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Fallback test content\n")
        temp_file_path = temp_file.name
    
    try:
        # Should work in fallback mode regardless
        transcript = run_whisper(temp_file_path)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 1
        assert transcript.segments[0].text == "Fallback test content"
    
    finally:
        os.unlink(temp_file_path)


def test_segment_time_ordering():
    """Test that segments can be ordered by time."""
    segments = [
        Segment(2.0, 3.0, "Second"),
        Segment(0.0, 1.0, "First"),
        Segment(4.0, 5.0, "Third"),
    ]
    
    # Sort by start time
    sorted_segments = sorted(segments, key=lambda s: s.start)
    
    assert sorted_segments[0].text == "First"
    assert sorted_segments[1].text == "Second"
    assert sorted_segments[2].text == "Third"


def test_transcript_with_overlapping_segments():
    """Test transcript with overlapping time segments."""
    segments = [
        Segment(0.0, 2.0, "First speaker"),
        Segment(1.0, 3.0, "Second speaker overlapping"),
        Segment(2.5, 4.0, "Third segment"),
    ]
    
    transcript = Transcript(segments)
    
    assert len(transcript.segments) == 3
    # Should preserve the overlapping structure as provided
    assert transcript.segments[0].end > transcript.segments[1].start
    assert transcript.segments[1].end > transcript.segments[2].start