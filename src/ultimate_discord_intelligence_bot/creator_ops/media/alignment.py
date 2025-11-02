"""
Transcript alignment merging ASR + diarization into canonical transcript.

This module provides comprehensive transcript alignment with cleanup,
provenance tracking, and JSON output for creator content.
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.creator_ops.media.asr import ASRResult, ASRSegment
    from ultimate_discord_intelligence_bot.creator_ops.media.diarization import DiarizationResult, DiarizationSegment
logger = logging.getLogger(__name__)

@dataclass
class AlignedSegment:
    """Aligned transcript segment with speaker and timing information."""
    start_time: float
    end_time: float
    speaker: str | None
    text: str
    confidence: float | None = None
    language: str | None = None
    is_overlap: bool = False
    overlap_speakers: list[str] | None = None

@dataclass
class AlignedTranscript:
    """Complete aligned transcript with metadata."""
    segments: list[AlignedSegment]
    speakers: list[str]
    total_duration: float
    word_count: int
    speaker_turns: int
    overlap_percentage: float
    cleanup_applied: list[str]
    provenance: dict[str, Any]
    created_at: datetime

class TranscriptAlignment:
    """
    Transcript alignment merging ASR + diarization with comprehensive cleanup.

    Features:
    - Merge ASR and diarization timestamps
    - Handle overlapping speakers
    - Text cleanup and normalization
    - Provenance tracking
    - JSON output with metadata
    """

    def __init__(self) -> None:
        """Initialize transcript alignment."""
        self.cleanup_patterns = self._initialize_cleanup_patterns()

    def _initialize_cleanup_patterns(self) -> dict[str, re.Pattern]:
        """Initialize text cleanup patterns."""
        return {'filler_words': re.compile('\\b(um|uh|er|ah|like|you know|basically|literally|actually|so|well)\\b', re.IGNORECASE), 'stutters': re.compile('\\b(\\w+)\\s+\\1\\b', re.IGNORECASE), 'repeated_words': re.compile('\\b(\\w+)\\s+\\1\\s+\\1\\b', re.IGNORECASE), 'extra_spaces': re.compile('\\s+'), 'punctuation_spacing': re.compile('\\s+([,.!?;:])'), 'quotes': re.compile('["""]'), 'dashes': re.compile('[\\u2014\\u2013-]+')}

    def align_transcripts(self, asr_result: ASRResult, diarization_result: DiarizationResult, cleanup_options: dict[str, bool] | None=None) -> StepResult:
        """
        Align ASR and diarization results into canonical transcript.

        Args:
            asr_result: ASR transcription result
            diarization_result: Speaker diarization result
            cleanup_options: Text cleanup options

        Returns:
            StepResult with AlignedTranscript
        """
        try:
            cleanup_opts = cleanup_options or {'remove_fillers': True, 'fix_stutters': True, 'normalize_punctuation': True, 'capitalize_sentences': True, 'remove_extra_spaces': True}
            aligned_segments = self._align_segments(asr_result.segments, diarization_result.segments)
            cleanup_applied = []
            for segment in aligned_segments:
                original_text = segment.text
                segment.text = self._cleanup_text(segment.text, cleanup_opts)
                if segment.text != original_text:
                    cleanup_applied.append(f'cleaned_segment_{len(cleanup_applied)}')
            speakers = list({segment.speaker for segment in aligned_segments if segment.speaker})
            total_duration = max((segment.end_time for segment in aligned_segments)) if aligned_segments else 0.0
            word_count = sum((len(segment.text.split()) for segment in aligned_segments))
            speaker_turns = self._count_speaker_turns(aligned_segments)
            overlap_percentage = self._calculate_overlap_percentage(aligned_segments, total_duration)
            provenance = {'asr_model': asr_result.model_name, 'asr_device': asr_result.device, 'asr_processing_time': asr_result.processing_time, 'diarization_model': diarization_result.model_name, 'diarization_device': diarization_result.device, 'diarization_processing_time': diarization_result.processing_time, 'alignment_timestamp': datetime.utcnow().isoformat(), 'cleanup_options': cleanup_opts, 'cleanup_applied': cleanup_applied}
            aligned_transcript = AlignedTranscript(segments=aligned_segments, speakers=speakers, total_duration=total_duration, word_count=word_count, speaker_turns=speaker_turns, overlap_percentage=overlap_percentage, cleanup_applied=cleanup_applied, provenance=provenance, created_at=datetime.utcnow())
            return StepResult.ok(data=aligned_transcript)
        except Exception as e:
            logger.error(f'Transcript alignment failed: {e!s}')
            return StepResult.fail(f'Transcript alignment failed: {e!s}')

    def _align_segments(self, asr_segments: list[ASRSegment], diarization_segments: list[DiarizationSegment]) -> list[AlignedSegment]:
        """Align ASR and diarization segments."""
        aligned_segments = []
        asr_segments = sorted(asr_segments, key=lambda x: x.start_time)
        diarization_segments = sorted(diarization_segments, key=lambda x: x.start_time)
        speaker_map = self._create_speaker_map(diarization_segments)
        for asr_segment in asr_segments:
            overlapping_speakers = self._find_overlapping_speakers(asr_segment.start_time, asr_segment.end_time, speaker_map)
            primary_speaker = self._determine_primary_speaker(asr_segment.start_time, asr_segment.end_time, overlapping_speakers)
            is_overlap = len(overlapping_speakers) > 1
            overlap_speakers = overlapping_speakers if is_overlap else None
            aligned_segment = AlignedSegment(start_time=asr_segment.start_time, end_time=asr_segment.end_time, speaker=primary_speaker, text=asr_segment.text, confidence=asr_segment.confidence, language=asr_segment.language, is_overlap=is_overlap, overlap_speakers=overlap_speakers)
            aligned_segments.append(aligned_segment)
        return aligned_segments

    def _create_speaker_map(self, diarization_segments: list[DiarizationSegment]) -> list[dict[str, Any]]:
        """Create a mapping of time ranges to speakers."""
        speaker_map = []
        for segment in diarization_segments:
            speaker_map.append({'start_time': segment.start_time, 'end_time': segment.end_time, 'speaker': segment.speaker, 'confidence': segment.confidence})
        return speaker_map

    def _find_overlapping_speakers(self, start_time: float, end_time: float, speaker_map: list[dict[str, Any]]) -> list[str]:
        """Find speakers overlapping with the given time range."""
        overlapping_speakers = []
        for speaker_info in speaker_map:
            if speaker_info['start_time'] < end_time and speaker_info['end_time'] > start_time:
                overlapping_speakers.append(speaker_info['speaker'])
        return list(set(overlapping_speakers))

    def _determine_primary_speaker(self, start_time: float, end_time: float, overlapping_speakers: list[str]) -> str | None:
        """Determine the primary speaker for a time range."""
        if not overlapping_speakers:
            return None
        if len(overlapping_speakers) == 1:
            return overlapping_speakers[0]
        return overlapping_speakers[0]

    def _cleanup_text(self, text: str, cleanup_options: dict[str, bool]) -> str:
        """Apply text cleanup based on options."""
        cleaned_text = text
        if cleanup_options.get('remove_fillers', False):
            cleaned_text = self.cleanup_patterns['filler_words'].sub('', cleaned_text)
        if cleanup_options.get('fix_stutters', False):
            cleaned_text = self.cleanup_patterns['stutters'].sub('\\1', cleaned_text)
            cleaned_text = self.cleanup_patterns['repeated_words'].sub('\\1', cleaned_text)
        if cleanup_options.get('normalize_punctuation', False):
            cleaned_text = self.cleanup_patterns['quotes'].sub('"', cleaned_text)
            cleaned_text = self.cleanup_patterns['dashes'].sub('-', cleaned_text)
            cleaned_text = self.cleanup_patterns['punctuation_spacing'].sub('\\1', cleaned_text)
        if cleanup_options.get('remove_extra_spaces', False):
            cleaned_text = self.cleanup_patterns['extra_spaces'].sub(' ', cleaned_text)
        if cleanup_options.get('capitalize_sentences', False):
            cleaned_text = self._capitalize_sentences(cleaned_text)
        return cleaned_text.strip()

    def _capitalize_sentences(self, text: str) -> str:
        """Capitalize the first letter of each sentence."""
        sentences = re.split('([.!?]+)', text)
        capitalized_sentences = []
        for i, sentence in enumerate(sentences):
            if i % 2 == 0:
                if sentence.strip():
                    capitalized_sentences.append(sentence.strip().capitalize())
                else:
                    capitalized_sentences.append(sentence)
            else:
                capitalized_sentences.append(sentence)
        return ''.join(capitalized_sentences)

    def _count_speaker_turns(self, segments: list[AlignedSegment]) -> int:
        """Count the number of speaker turns."""
        if not segments:
            return 0
        turns = 1
        current_speaker = segments[0].speaker
        for segment in segments[1:]:
            if segment.speaker != current_speaker:
                turns += 1
                current_speaker = segment.speaker
        return turns

    def _calculate_overlap_percentage(self, segments: list[AlignedSegment], total_duration: float) -> float:
        """Calculate the percentage of overlapping speech."""
        if not segments or total_duration == 0:
            return 0.0
        overlap_duration = 0.0
        for segment in segments:
            if segment.is_overlap:
                overlap_duration += segment.end_time - segment.start_time
        return overlap_duration / total_duration * 100

    def export_to_json(self, aligned_transcript: AlignedTranscript) -> dict[str, Any]:
        """Export aligned transcript to JSON format."""
        return {'metadata': {'speakers': aligned_transcript.speakers, 'total_duration': aligned_transcript.total_duration, 'word_count': aligned_transcript.word_count, 'speaker_turns': aligned_transcript.speaker_turns, 'overlap_percentage': aligned_transcript.overlap_percentage, 'created_at': aligned_transcript.created_at.isoformat()}, 'provenance': aligned_transcript.provenance, 'segments': [{'start_time': segment.start_time, 'end_time': segment.end_time, 'speaker': segment.speaker, 'text': segment.text, 'confidence': segment.confidence, 'language': segment.language, 'is_overlap': segment.is_overlap, 'overlap_speakers': segment.overlap_speakers} for segment in aligned_transcript.segments]}

    def export_to_srt(self, aligned_transcript: AlignedTranscript) -> str:
        """Export aligned transcript to SRT subtitle format."""
        srt_content = []
        for i, segment in enumerate(aligned_transcript.segments, 1):
            start_time = self._format_srt_timestamp(segment.start_time)
            end_time = self._format_srt_timestamp(segment.end_time)
            text = f'[{segment.speaker}]: {segment.text}' if segment.speaker else segment.text
            srt_content.append(f'{i}')
            srt_content.append(f'{start_time} --> {end_time}')
            srt_content.append(text)
            srt_content.append('')
        return '\n'.join(srt_content)

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int(seconds % 3600 // 60)
        secs = int(seconds % 60)
        millisecs = int(seconds % 1 * 1000)
        return f'{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}'