import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import subprocess
import tempfile
import hashlib
from crewai_tools import BaseTool

# Advanced transcription imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Install with: pip install openai-whisper")

try:
    from pyannote.audio import Pipeline
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logging.warning("PyAnnote not available. Install with: pip install pyannote.audio")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
    # Download required NLTK data
    nltk.download('punkt', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('stopwords', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    language: Optional[str] = None
    
@dataclass
class SpeakerProfile:
    """Represents a speaker profile with characteristics"""
    speaker_id: str
    name: Optional[str] = None
    role: Optional[str] = None  # host, co-host, guest, staff
    total_speaking_time: float = 0.0
    segment_count: int = 0
    topics: List[str] = None
    sentiment_scores: Dict[str, float] = None
    confidence_score: float = 0.0
    voice_characteristics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []
        if self.sentiment_scores is None:
            self.sentiment_scores = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0, 'compound': 0.0}
        if self.voice_characteristics is None:
            self.voice_characteristics = {}

@dataclass
class ContentAnalysisResult:
    """Complete content analysis result"""
    file_path: str
    analysis_id: str
    timestamp: str
    duration: float
    transcription: List[TranscriptionSegment]
    speakers: List[SpeakerProfile]
    topics: List[Dict[str, Any]]
    sentiment_analysis: Dict[str, Any]
    key_moments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float
    status: str = "completed"
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class EnhancedTranscriptionEngine:
    """Enhanced transcription engine with multiple AI models"""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        self.model_size = model_size
        self.device = self._determine_device(device)
        self.whisper_model = None
        self.diarization_pipeline = None
        self._initialize_models()
    
    def _determine_device(self, device: str) -> str:
        """Determine optimal device for processing"""
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return "mps"  # Apple Silicon
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        return device
    
    def _initialize_models(self):
        """Initialize AI models for transcription and diarization"""
        try:
            # Initialize Whisper model
            if WHISPER_AVAILABLE:
                logging.info(f"Loading Whisper model '{self.model_size}' on {self.device}")
                self.whisper_model = whisper.load_model(self.model_size, device=self.device)
                logging.info("Whisper model loaded successfully")
            
            # Initialize speaker diarization pipeline
            if PYANNOTE_AVAILABLE:
                token = os.getenv("HUGGINGFACE_TOKEN")
                if token:
                    logging.info("Loading PyAnnote diarization pipeline")
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=token
                    )
                    if self.device != "cpu":
                        self.diarization_pipeline.to(torch.device(self.device))
                    logging.info("Diarization pipeline loaded successfully")
                else:
                    logging.warning("HUGGINGFACE_TOKEN not set, speaker diarization disabled")
        
        except Exception as e:
            logging.error(f"Error initializing transcription models: {e}")
    
    async def transcribe_with_speakers(self, audio_path: str, language: str = None) -> List[TranscriptionSegment]:
        """Transcribe audio with speaker identification"""
        
        try:
            # Step 1: Perform diarization to identify speakers
            speaker_segments = []
            if self.diarization_pipeline:
                logging.info("Performing speaker diarization")
                diarization = self.diarization_pipeline(audio_path)
                
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speaker_segments.append({
                        'start': turn.start,
                        'end': turn.end,
                        'speaker': speaker
                    })
                
                logging.info(f"Identified {len(set(seg['speaker'] for seg in speaker_segments))} unique speakers")
            
            # Step 2: Transcribe audio with Whisper
            transcription_segments = []
            if self.whisper_model:
                logging.info("Transcribing audio with Whisper")
                
                # Transcribe with word-level timestamps
                result = self.whisper_model.transcribe(
                    audio_path,
                    language=language,
                    word_timestamps=True,
                    verbose=False
                )
                
                # Convert to segments with speaker mapping
                for segment in result.get("segments", []):
                    # Find speaker for this time range
                    segment_start = segment["start"]
                    segment_end = segment["end"]
                    
                    speaker_id = self._find_speaker_for_time_range(
                        segment_start, segment_end, speaker_segments
                    )
                    
                    transcription_segment = TranscriptionSegment(
                        start_time=segment_start,
                        end_time=segment_end,
                        text=segment["text"].strip(),
                        confidence=segment.get("avg_logprob", 0.0),
                        speaker_id=speaker_id,
                        language=result.get("language", "unknown")
                    )
                    
                    transcription_segments.append(transcription_segment)
                
                logging.info(f"Generated {len(transcription_segments)} transcription segments")
            
            return transcription_segments
        
        except Exception as e:
            logging.error(f"Error in transcription with speakers: {e}")
            # Fallback to basic transcription
            return await self._fallback_transcribe(audio_path, language)
    
    def _find_speaker_for_time_range(self, start: float, end: float, speaker_segments: List[Dict]) -> Optional[str]:
        """Find the most likely speaker for a given time range"""
        
        if not speaker_segments:
            return None
        
        # Find overlapping speaker segments
        overlapping_speakers = []
        
        for seg in speaker_segments:
            # Calculate overlap
            overlap_start = max(start, seg['start'])
            overlap_end = min(end, seg['end'])
            
            if overlap_start < overlap_end:  # There is overlap
                overlap_duration = overlap_end - overlap_start
                overlapping_speakers.append({
                    'speaker': seg['speaker'],
                    'overlap': overlap_duration
                })
        
        if overlapping_speakers:
            # Return speaker with most overlap
            best_match = max(overlapping_speakers, key=lambda x: x['overlap'])
            return best_match['speaker']
        
        return None
    
    async def _fallback_transcribe(self, audio_path: str, language: str = None) -> List[TranscriptionSegment]:
        """Fallback transcription without speaker identification"""
        
        if not self.whisper_model:
            raise Exception("No transcription models available")
        
        try:
            result = self.whisper_model.transcribe(audio_path, language=language)
            
            segments = []
            for segment in result.get("segments", []):
                transcription_segment = TranscriptionSegment(
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("avg_logprob", 0.0),
                    language=result.get("language", "unknown")
                )
                segments.append(transcription_segment)
            
            return segments
        
        except Exception as e:
            logging.error(f"Fallback transcription failed: {e}")
            return []

class SpeakerAnalysisEngine:
    """Advanced speaker analysis and profiling"""
    
    def __init__(self):
        self.speaker_database = {}  # Persistent speaker profiles
        self.sentiment_analyzer = None
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize analysis tools"""
        if NLTK_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def analyze_speakers(self, segments: List[TranscriptionSegment]) -> List[SpeakerProfile]:
        """Analyze speakers from transcription segments"""
        
        # Group segments by speaker
        speaker_segments = {}
        for segment in segments:
            speaker_id = segment.speaker_id or "unknown"
            if speaker_id not in speaker_segments:
                speaker_segments[speaker_id] = []
            speaker_segments[speaker_id].append(segment)
        
        # Create speaker profiles
        speaker_profiles = []
        for speaker_id, speaker_segs in speaker_segments.items():
            profile = self._create_speaker_profile(speaker_id, speaker_segs)
            speaker_profiles.append(profile)
        
        return speaker_profiles
    
    def _create_speaker_profile(self, speaker_id: str, segments: List[TranscriptionSegment]) -> SpeakerProfile:
        """Create detailed speaker profile"""
        
        # Calculate basic statistics
        total_time = sum(seg.end_time - seg.start_time for seg in segments)
        segment_count = len(segments)
        
        # Combine all text for analysis
        full_text = " ".join(seg.text for seg in segments)
        
        # Analyze sentiment
        sentiment_scores = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0, 'compound': 0.0}
        if self.sentiment_analyzer and full_text.strip():
            sentiment_result = self.sentiment_analyzer.polarity_scores(full_text)
            sentiment_scores.update(sentiment_result)
        
        # Extract topics and keywords
        topics = self._extract_topics(full_text)
        
        # Calculate confidence score based on transcription confidence
        avg_confidence = sum(seg.confidence for seg in segments) / len(segments) if segments else 0.0
        
        # Determine speaker role based on speaking patterns
        role = self._determine_speaker_role(speaker_id, total_time, segment_count, segments)
        
        # Generate speaker name if possible
        speaker_name = self._generate_speaker_name(speaker_id, full_text, role)
        
        profile = SpeakerProfile(
            speaker_id=speaker_id,
            name=speaker_name,
            role=role,
            total_speaking_time=total_time,
            segment_count=segment_count,
            topics=topics,
            sentiment_scores=sentiment_scores,
            confidence_score=avg_confidence
        )
        
        return profile
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from speaker text"""
        
        if not NLTK_AVAILABLE or not text.strip():
            return []
        
        try:
            # Tokenize and remove stopwords
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 3]
            
            # Calculate word frequency
            from collections import Counter
            word_freq = Counter(words)
            
            # Return top topics
            return [word for word, count in word_freq.most_common(10)]
        
        except Exception as e:
            logging.warning(f"Topic extraction failed: {e}")
            return []
    
    def _determine_speaker_role(self, speaker_id: str, total_time: float, segment_count: int, segments: List[TranscriptionSegment]) -> str:
        """Determine speaker role based on speaking patterns"""
        
        # Analyze speaking patterns
        avg_segment_length = total_time / segment_count if segment_count > 0 else 0
        
        # Look for role indicators in speech
        full_text = " ".join(seg.text.lower() for seg in segments)
        
        # Host indicators
        host_phrases = ["welcome back", "today's show", "our guest", "let's talk about", "thanks for watching"]
        if any(phrase in full_text for phrase in host_phrases):
            return "host"
        
        # Co-host indicators (shorter segments, responsive speech)
        if avg_segment_length < 10 and "yeah" in full_text and "exactly" in full_text:
            return "co-host"
        
        # Guest indicators (longer explanations, topic expertise)
        guest_phrases = ["in my experience", "what i do", "my work", "i believe"]
        if avg_segment_length > 30 and any(phrase in full_text for phrase in guest_phrases):
            return "guest"
        
        # Staff indicators (technical or administrative language)
        staff_phrases = ["technical difficulties", "we'll be right back", "audio check"]
        if any(phrase in full_text for phrase in staff_phrases):
            return "staff"
        
        # Default classification based on speaking time
        if total_time > 300:  # 5+ minutes
            return "main_speaker"
        elif total_time > 60:  # 1+ minute
            return "secondary_speaker"
        else:
            return "minor_speaker"
    
    def _generate_speaker_name(self, speaker_id: str, text: str, role: str) -> Optional[str]:
        """Generate or infer speaker name"""
        
        # Look for self-introductions
        if "my name is" in text.lower():
            # Simple name extraction (could be improved with NER)
            import re
            match = re.search(r"my name is (\w+)", text.lower())
            if match:
                return match.group(1).title()
        
        # Role-based naming
        role_names = {
            "host": "Host",
            "co-host": "Co-Host",
            "guest": "Guest",
            "staff": "Staff Member"
        }
        
        base_name = role_names.get(role, "Speaker")
        return f"{base_name} {speaker_id.split('_')[-1] if '_' in speaker_id else speaker_id}"

class TopicAnalysisEngine:
    """Advanced topic extraction and analysis"""
    
    def __init__(self):
        self.topic_models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize topic analysis models"""
        # Could integrate with advanced models like BERT, spaCy, etc.
        pass
    
    def extract_topics_and_opinions(self, segments: List[TranscriptionSegment], speaker_profiles: List[SpeakerProfile]) -> List[Dict[str, Any]]:
        """Extract topics, opinions, and viewpoints from content"""
        
        # Group content by topics
        topics = []
        
        # Analyze full content for main themes
        full_text = " ".join(seg.text for seg in segments)
        main_topics = self._identify_main_topics(full_text)
        
        for topic in main_topics:
            topic_analysis = {
                'topic': topic,
                'mentions': self._count_topic_mentions(topic, segments),
                'speaker_positions': self._analyze_speaker_positions(topic, segments, speaker_profiles),
                'sentiment': self._analyze_topic_sentiment(topic, segments),
                'key_quotes': self._extract_key_quotes(topic, segments),
                'time_distribution': self._analyze_time_distribution(topic, segments)
            }
            topics.append(topic_analysis)
        
        return topics
    
    def _identify_main_topics(self, text: str) -> List[str]:
        """Identify main topics in the content"""
        
        if not text.strip():
            return []
        
        # Simple keyword-based topic identification
        # In production, this would use more sophisticated NLP models
        
        topic_keywords = {
            'politics': ['government', 'election', 'policy', 'political', 'vote', 'democracy'],
            'technology': ['ai', 'artificial intelligence', 'computer', 'software', 'tech', 'digital'],
            'science': ['research', 'study', 'experiment', 'scientific', 'data', 'evidence'],
            'health': ['medical', 'health', 'disease', 'treatment', 'doctor', 'medicine'],
            'economy': ['economic', 'money', 'market', 'business', 'financial', 'investment'],
            'environment': ['climate', 'environmental', 'carbon', 'pollution', 'green', 'sustainability'],
            'education': ['school', 'university', 'learning', 'education', 'teaching', 'student']
        }
        
        identified_topics = []
        text_lower = text.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics[:5]  # Return top 5 topics
    
    def _count_topic_mentions(self, topic: str, segments: List[TranscriptionSegment]) -> int:
        """Count mentions of a topic across segments"""
        # Simplified implementation
        count = 0
        for segment in segments:
            if topic.lower() in segment.text.lower():
                count += 1
        return count
    
    def _analyze_speaker_positions(self, topic: str, segments: List[TranscriptionSegment], speaker_profiles: List[SpeakerProfile]) -> Dict[str, Any]:
        """Analyze speaker positions on a topic"""
        
        positions = {}
        
        for profile in speaker_profiles:
            speaker_segments = [seg for seg in segments if seg.speaker_id == profile.speaker_id]
            topic_segments = [seg for seg in speaker_segments if topic.lower() in seg.text.lower()]
            
            if topic_segments:
                # Analyze sentiment of topic-related segments
                topic_text = " ".join(seg.text for seg in topic_segments)
                
                if NLTK_AVAILABLE and hasattr(self, 'sentiment_analyzer'):
                    sentiment = SentimentIntensityAnalyzer().polarity_scores(topic_text)
                    
                    position = "neutral"
                    if sentiment['compound'] > 0.1:
                        position = "positive"
                    elif sentiment['compound'] < -0.1:
                        position = "negative"
                    
                    positions[profile.speaker_id] = {
                        'position': position,
                        'confidence': abs(sentiment['compound']),
                        'key_statements': [seg.text for seg in topic_segments[:3]]  # Top 3 statements
                    }
        
        return positions
    
    def _analyze_topic_sentiment(self, topic: str, segments: List[TranscriptionSegment]) -> Dict[str, float]:
        """Analyze overall sentiment around a topic"""
        
        topic_segments = [seg for seg in segments if topic.lower() in seg.text.lower()]
        
        if not topic_segments or not NLTK_AVAILABLE:
            return {'positive': 0.0, 'neutral': 1.0, 'negative': 0.0, 'compound': 0.0}
        
        topic_text = " ".join(seg.text for seg in topic_segments)
        return SentimentIntensityAnalyzer().polarity_scores(topic_text)
    
    def _extract_key_quotes(self, topic: str, segments: List[TranscriptionSegment]) -> List[Dict[str, Any]]:
        """Extract key quotes related to a topic"""
        
        topic_segments = [seg for seg in segments if topic.lower() in seg.text.lower()]
        
        # Sort by length and confidence to get most substantial quotes
        key_quotes = []
        for seg in sorted(topic_segments, key=lambda x: (len(x.text), x.confidence), reverse=True)[:5]:
            key_quotes.append({
                'text': seg.text,
                'speaker': seg.speaker_id,
                'timestamp': seg.start_time,
                'confidence': seg.confidence
            })
        
        return key_quotes
    
    def _analyze_time_distribution(self, topic: str, segments: List[TranscriptionSegment]) -> Dict[str, float]:
        """Analyze when in the content the topic is discussed"""
        
        topic_segments = [seg for seg in segments if topic.lower() in seg.text.lower()]
        
        if not topic_segments:
            return {'early': 0.0, 'middle': 0.0, 'late': 0.0}
        
        # Assuming content duration
        total_duration = max(seg.end_time for seg in segments) if segments else 0
        if total_duration == 0:
            return {'early': 0.0, 'middle': 0.0, 'late': 0.0}
        
        early_cutoff = total_duration / 3
        late_cutoff = total_duration * 2 / 3
        
        early_count = sum(1 for seg in topic_segments if seg.start_time < early_cutoff)
        middle_count = sum(1 for seg in topic_segments if early_cutoff <= seg.start_time < late_cutoff)
        late_count = sum(1 for seg in topic_segments if seg.start_time >= late_cutoff)
        
        total_topic_segments = len(topic_segments)
        
        return {
            'early': early_count / total_topic_segments if total_topic_segments > 0 else 0.0,
            'middle': middle_count / total_topic_segments if total_topic_segments > 0 else 0.0,
            'late': late_count / total_topic_segments if total_topic_segments > 0 else 0.0
        }

class EnhancedContentAnalysisTool(BaseTool):
    """Enhanced content analysis tool with AI transcription and speaker analysis"""
    
    name: str = "Enhanced Content Analysis Tool"
    description: str = "Perform comprehensive content analysis including transcription, speaker identification, topic extraction, and sentiment analysis"
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        super().__init__()
        self.transcription_engine = EnhancedTranscriptionEngine(model_size, device)
        self.speaker_engine = SpeakerAnalysisEngine()
        self.topic_engine = TopicAnalysisEngine()
    
    def _run(self, file_path: str, language: str = None, include_topics: bool = True, include_sentiment: bool = True) -> str:
        """Analyze video/audio content comprehensively"""
        
        try:
            start_time = datetime.now()
            file_path = Path(file_path)
            
            if not file_path.exists():
                return json.dumps({
                    'status': 'error',
                    'error': f'File not found: {file_path}'
                })
            
            # Extract audio if needed
            audio_path = self._extract_audio(file_path)
            
            # Generate unique analysis ID
            analysis_id = hashlib.md5(f"{file_path}_{start_time}".encode()).hexdigest()[:12]
            
            # Step 1: Transcribe with speaker identification
            logging.info(f"Starting transcription for {file_path.name}")
            segments = asyncio.run(
                self.transcription_engine.transcribe_with_speakers(audio_path, language)
            )
            
            if not segments:
                return json.dumps({
                    'status': 'error',
                    'error': 'Transcription failed or no audio detected'
                })
            
            # Step 2: Analyze speakers
            logging.info("Analyzing speakers")
            speaker_profiles = self.speaker_engine.analyze_speakers(segments)
            
            # Step 3: Extract topics and opinions (if requested)
            topics = []
            if include_topics:
                logging.info("Extracting topics and opinions")
                topics = self.topic_engine.extract_topics_and_opinions(segments, speaker_profiles)
            
            # Step 4: Overall sentiment analysis (if requested)
            overall_sentiment = {}
            if include_sentiment and NLTK_AVAILABLE:
                full_text = " ".join(seg.text for seg in segments)
                if full_text.strip():
                    overall_sentiment = SentimentIntensityAnalyzer().polarity_scores(full_text)
            
            # Step 5: Identify key moments
            key_moments = self._identify_key_moments(segments, speaker_profiles)
            
            # Step 6: Calculate duration
            duration = max(seg.end_time for seg in segments) if segments else 0
            
            # Step 7: Compile results
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ContentAnalysisResult(
                file_path=str(file_path),
                analysis_id=analysis_id,
                timestamp=start_time.isoformat(),
                duration=duration,
                transcription=segments,
                speakers=speaker_profiles,
                topics=topics,
                sentiment_analysis=overall_sentiment,
                key_moments=key_moments,
                metadata={
                    'language': language or 'auto',
                    'model_size': self.transcription_engine.model_size,
                    'device': self.transcription_engine.device,
                    'total_segments': len(segments),
                    'unique_speakers': len(speaker_profiles)
                },
                processing_time=processing_time
            )
            
            # Save results
            self._save_analysis_results(result)
            
            # Clean up temporary audio file
            if audio_path != str(file_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            logging.info(f"Content analysis completed in {processing_time:.2f}s")
            
            # Convert to serializable format
            return json.dumps(self._serialize_result(result), indent=2)
        
        except Exception as e:
            logging.error(f"Content analysis failed: {e}")
            return json.dumps({
                'status': 'error',
                'error': str(e),
                'file_path': str(file_path),
                'timestamp': datetime.now().isoformat()
            })
    
    def _extract_audio(self, file_path: Path) -> str:
        """Extract audio from video file if needed"""
        
        # Check if file is already audio
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        if file_path.suffix.lower() in audio_extensions:
            return str(file_path)
        
        # Extract audio from video
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', str(file_path),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for Whisper
                '-ac', '1',      # Mono
                '-y',            # Overwrite
                temp_audio_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                logging.info(f"Extracted audio to {temp_audio_path}")
                return temp_audio_path
            else:
                logging.error(f"Audio extraction failed: {result.stderr}")
                return str(file_path)  # Try with original file
        
        except Exception as e:
            logging.warning(f"Audio extraction failed: {e}, using original file")
            return str(file_path)
    
    def _identify_key_moments(self, segments: List[TranscriptionSegment], speaker_profiles: List[SpeakerProfile]) -> List[Dict[str, Any]]:
        """Identify key moments in the content"""
        
        key_moments = []
        
        # Look for speaker changes (potential topic transitions)
        current_speaker = None
        for i, segment in enumerate(segments):
            if segment.speaker_id != current_speaker:
                if current_speaker is not None:  # Not the first speaker change
                    key_moments.append({
                        'type': 'speaker_change',
                        'timestamp': segment.start_time,
                        'description': f'Speaker change to {segment.speaker_id}',
                        'importance': 'medium'
                    })
                current_speaker = segment.speaker_id
        
        # Look for high-confidence segments (likely important statements)
        high_confidence_segments = [seg for seg in segments if seg.confidence > 0.8]
        for segment in sorted(high_confidence_segments, key=lambda x: x.confidence, reverse=True)[:5]:
            key_moments.append({
                'type': 'high_confidence_statement',
                'timestamp': segment.start_time,
                'description': segment.text,
                'speaker': segment.speaker_id,
                'confidence': segment.confidence,
                'importance': 'high'
            })
        
        # Look for emotional peaks (high sentiment scores)
        if NLTK_AVAILABLE:
            sentiment_analyzer = SentimentIntensityAnalyzer()
            for segment in segments:
                if len(segment.text) > 50:  # Only analyze substantial segments
                    sentiment = sentiment_analyzer.polarity_scores(segment.text)
                    if abs(sentiment['compound']) > 0.6:  # Strong sentiment
                        emotional_type = 'positive' if sentiment['compound'] > 0 else 'negative'
                        key_moments.append({
                            'type': f'{emotional_type}_emotional_peak',
                            'timestamp': segment.start_time,
                            'description': segment.text,
                            'speaker': segment.speaker_id,
                            'sentiment_score': sentiment['compound'],
                            'importance': 'high'
                        })
        
        # Sort by timestamp and return
        return sorted(key_moments, key=lambda x: x['timestamp'])
    
    def _save_analysis_results(self, result: ContentAnalysisResult):
        """Save analysis results to file"""
        
        try:
            # Create analysis directory
            analysis_dir = Path("F:/yt-auto/crewaiv2/CrewAI_Content_System/Analysis")
            analysis_dir.mkdir(parents=True, exist_ok=True)
            
            # Save full results
            output_file = analysis_dir / f"{result.analysis_id}_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_result(result), f, indent=2, ensure_ascii=False)
            
            logging.info(f"Analysis results saved to {output_file}")
        
        except Exception as e:
            logging.warning(f"Failed to save analysis results: {e}")
    
    def _serialize_result(self, result: ContentAnalysisResult) -> Dict[str, Any]:
        """Convert result to JSON-serializable format"""
        
        return {
            'file_path': result.file_path,
            'analysis_id': result.analysis_id,
            'timestamp': result.timestamp,
            'duration': result.duration,
            'status': result.status,
            'processing_time': result.processing_time,
            'metadata': result.metadata,
            'transcription': [
                {
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'text': seg.text,
                    'confidence': seg.confidence,
                    'speaker_id': seg.speaker_id,
                    'speaker_name': seg.speaker_name,
                    'language': seg.language
                } for seg in result.transcription
            ],
            'speakers': [
                {
                    'speaker_id': sp.speaker_id,
                    'name': sp.name,
                    'role': sp.role,
                    'total_speaking_time': sp.total_speaking_time,
                    'segment_count': sp.segment_count,
                    'topics': sp.topics,
                    'sentiment_scores': sp.sentiment_scores,
                    'confidence_score': sp.confidence_score
                } for sp in result.speakers
            ],
            'topics': result.topics,
            'sentiment_analysis': result.sentiment_analysis,
            'key_moments': result.key_moments,
            'errors': result.errors
        }

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize analysis tool
    analysis_tool = EnhancedContentAnalysisTool(model_size="base", device="auto")
    
    # Test file path (replace with actual file)
    test_file = "F:/yt-auto/crewaiv2/test_video.mp4"
    
    if Path(test_file).exists():
        print("Starting content analysis...")
        result = analysis_tool._run(test_file, language="en", include_topics=True, include_sentiment=True)
        
        # Parse and display results
        analysis_result = json.loads(result)
        if analysis_result.get('status') != 'error':
            print(f"\nAnalysis completed!")
            print(f"Duration: {analysis_result['duration']:.1f} seconds")
            print(f"Speakers found: {len(analysis_result['speakers'])}")
            print(f"Topics identified: {len(analysis_result['topics'])}")
            print(f"Processing time: {analysis_result['processing_time']:.2f} seconds")
        else:
            print(f"Analysis failed: {analysis_result['error']}")
    else:
        print(f"Test file not found: {test_file}")