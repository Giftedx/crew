"""Tests for Speaker Diarization Service."""
from __future__ import annotations
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from analysis.transcription.speaker_diarization_service import SpeakerDiarizationService, SpeakerSegment, get_diarization_service
from platform.core.step_result import StepResult

class TestSpeakerDiarizationService:
    """Test speaker diarization service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = SpeakerDiarizationService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._diarization_cache) == 0
        assert self.service._diarization_model is None

    def test_diarize_fallback(self) -> None:
        """Test diarization with fallback model."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'dummy audio content')
            audio_path = Path(f.name)
        try:
            result = self.service.diarize_audio(audio_path, model='fast', use_cache=False)
            assert result.success
            assert result.data is not None
            assert 'segments' in result.data
            assert 'num_speakers' in result.data
            assert 'speaker_map' in result.data
            assert result.data['num_speakers'] == 1
            assert len(result.data['segments']) == 1
            assert result.data['model'].startswith('fallback')
        finally:
            audio_path.unlink()

    def test_diarize_empty_file(self) -> None:
        """Test handling of empty audio file."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            audio_path = Path(f.name)
        try:
            result = self.service.diarize_audio(audio_path, model='fast')
            assert not result.success
            assert result.status == 'bad_request'
            assert 'not found' in result.error.lower()
        finally:
            audio_path.unlink()

    def test_diarization_cache_hit(self) -> None:
        """Test diarization cache functionality."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'test audio content')
            audio_path = Path(f.name)
        try:
            result1 = self.service.diarize_audio(audio_path, model='fast', use_cache=True)
            assert result1.success
            assert result1.data['cache_hit'] is False
            result2 = self.service.diarize_audio(audio_path, model='fast', use_cache=True)
            assert result2.success
            assert result2.data['cache_hit'] is True
            assert result1.data['num_speakers'] == result2.data['num_speakers']
        finally:
            audio_path.unlink()

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        self.service.diarize_audio('dummy1.mp3', use_cache=True)
        self.service.diarize_audio('dummy2.mp3', use_cache=True)
        assert len(self.service._diarization_cache) > 0
        result = self.service.clear_cache()
        assert result.success
        assert result.data['cleared_entries'] > 0
        assert len(self.service._diarization_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        self.service.diarize_audio('dummy1.mp3', model='fast', use_cache=True)
        self.service.diarize_audio('dummy2.mp3', model='balanced', use_cache=True)
        result = self.service.get_cache_stats()
        assert result.success
        assert result.data is not None
        assert 'total_cached' in result.data
        assert 'cache_size_limit' in result.data
        assert 'models_cached' in result.data
        assert result.data['total_cached'] >= 2
        assert result.data['cache_size_limit'] == 100

    def test_model_selection(self) -> None:
        """Test model selection logic."""
        assert self.service._select_model('fast') == 'pyannote/speaker-diarization-mini'
        assert self.service._select_model('balanced') == 'pyannote/speaker-diarization'
        assert self.service._select_model('quality') == 'pyannote/speaker-diarization'
        assert self.service._select_model('unknown') == 'pyannote/speaker-diarization'

    def test_speaker_identification(self) -> None:
        """Test speaker identification logic."""
        speaker_name = self.service._identify_speaker('SPEAKER_00', Path('test.mp3'))
        assert speaker_name == 'Host'
        speaker_name2 = self.service._identify_speaker('SPEAKER_01', Path('test.mp3'))
        assert speaker_name2 == 'Guest 1'

    def test_speaker_role_inference(self) -> None:
        """Test speaker role inference."""
        role = self.service._infer_speaker_role('SPEAKER_00', 0.0, 60.0)
        assert role == 'host'
        role2 = self.service._infer_speaker_role('SPEAKER_01', 3600.0, 3660.0)
        assert role2 == 'guest'

    def test_align_transcript_with_diarization(self) -> None:
        """Test transcript alignment with diarization."""
        from analysis.transcription.asr_service import TranscriptionSegment
        transcript_segments = [TranscriptionSegment(start=0.0, end=5.0, text='Hello world'), TranscriptionSegment(start=5.0, end=10.0, text='This is a test')]
        speaker_segments = [SpeakerSegment(start=0.0, end=7.0, speaker_id='SPEAKER_00', speaker_name='Host'), SpeakerSegment(start=7.0, end=10.0, speaker_id='SPEAKER_01', speaker_name='Guest')]
        aligned = self.service._align_transcript_with_diarization(transcript_segments, speaker_segments)
        assert len(aligned) == 2
        assert 'Hello world' in aligned[0].transcript_text
        assert 'This is a test' in aligned[1].transcript_text

class TestSpeakerDiarizationServiceSingleton:
    """Test singleton instance management."""

    def test_get_diarization_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_diarization_service()
        service2 = get_diarization_service()
        assert service1 is service2
        assert isinstance(service1, SpeakerDiarizationService)

class TestSpeakerDiarizationWithMocking:
    """Test diarization service with mocked dependencies."""

    @patch('pyannote.audio.Pipeline.from_pretrained')
    def test_diarize_pyannote_model(self, mock_pipeline):
        """Test diarization with pyannote model."""
        mock_model = MagicMock()
        mock_pipeline.return_value = mock_model
        mock_diarization = MagicMock()
        mock_diarization.itertracks.return_value = [(MagicMock(start=0.0, end=5.0), None, 'SPEAKER_00'), (MagicMock(start=5.0, end=10.0), None, 'SPEAKER_01')]
        mock_diarization.get_timeline.return_value.extent.end = 10.0
        mock_model.return_value = mock_diarization
        with patch('analysis.transcription.speaker_diarization_service.PYANNOTE_AVAILABLE', True):
            service = SpeakerDiarizationService()
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(b'audio')
                audio_path = Path(f.name)
            try:
                result = service.diarize_audio(audio_path, model='balanced', use_cache=False)
                assert result.success
                assert result.data['num_speakers'] == 2
                assert len(result.data['segments']) == 2
                assert result.data['model'] == 'pyannote/speaker-diarization'
                mock_pipeline.assert_called_once()
            finally:
                audio_path.unlink()

    def test_diarize_with_transcript_integration(self) -> None:
        """Test diarization with transcript integration."""
        from analysis.transcription.asr_service import ASRService
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'audio content')
            audio_path = Path(f.name)
        try:
            asr_service = ASRService()
            StepResult.ok(data={'text': 'This is a test transcript', 'segments': [{'start': 0.0, 'end': 5.0, 'text': 'This is a test', 'confidence': 0.9}, {'start': 5.0, 'end': 10.0, 'text': 'transcript', 'confidence': 0.8}], 'model': 'test-asr', 'duration': 10.0, 'confidence': 0.85})
            service = SpeakerDiarizationService()
            with patch.object(service, '_diarize_audio') as mock_diarize:
                mock_diarize.return_value = mock_diarize.return_value = type('DiarizationResult', (), {'segments': [SpeakerSegment(start=0.0, end=10.0, speaker_id='SPEAKER_00', speaker_name='Host', speaker_role='host', confidence=0.8)], 'num_speakers': 1, 'speaker_map': {'SPEAKER_00': 'Host'}, 'model': 'test-model', 'duration': 10.0, 'confidence': 0.8})()
                result = service.diarize_with_transcript(audio_path=audio_path, asr_service=asr_service, model='balanced', use_cache=False)
                assert result.success
                assert result.data['num_speakers'] == 1
                assert 'transcript_text' in result.data
                assert result.data['transcript_segments'] >= 2
        finally:
            audio_path.unlink()

class TestSpeakerSegment:
    """Test speaker segment data structure."""

    def test_create_speaker_segment(self) -> None:
        """Test creating speaker segment."""
        segment = SpeakerSegment(start=0.0, end=5.0, speaker_id='SPEAKER_00', speaker_name='Host', speaker_role='host', confidence=0.9, transcript_text='Hello world')
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.speaker_id == 'SPEAKER_00'
        assert segment.speaker_name == 'Host'
        assert segment.speaker_role == 'host'
        assert segment.confidence == 0.9
        assert segment.transcript_text == 'Hello world'

    def test_speaker_segment_to_dict(self) -> None:
        """Test converting speaker segment to dictionary."""
        segment = SpeakerSegment(start=1.0, end=6.0, speaker_id='SPEAKER_01', speaker_name='Guest', speaker_role='guest', confidence=0.85)
        segment_dict = segment.__dict__
        assert segment_dict['start'] == 1.0
        assert segment_dict['end'] == 6.0
        assert segment_dict['speaker_id'] == 'SPEAKER_01'
        assert segment_dict['speaker_name'] == 'Guest'
        assert segment_dict['speaker_role'] == 'guest'
        assert segment_dict['confidence'] == 0.85