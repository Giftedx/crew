# Analysis Module Documentation

The analysis package provides utilities for processing and analyzing transcript data, topics, and other content. These modules support the ingestion pipeline and RAG functionality.

## Overview

**Location:** `src/analysis/`

The analysis modules handle:
- Transcript segmentation for vector storage
- Topic extraction and classification  
- Audio transcription with Whisper
- Content chunking for retrieval systems

## Modules

### Transcript Segmenter

**File:** `src/analysis/segmenter.py`

Splits transcripts into overlapping chunks optimized for retrieval augmented generation (RAG).

#### Core Classes

```python
@dataclass
class Chunk:
    text: str      # Chunk content
    start: float   # Start timestamp  
    end: float     # End timestamp
```

#### Functions

```python
def chunk_transcript(
    transcript: Transcript, 
    *, 
    max_chars: int = 800,
    overlap: int = 200
) -> List[Chunk]:
    """Split transcript into overlapping chunks.
    
    Parameters
    ----------
    transcript : Transcript
        Transcript to split
    max_chars : int, default 800
        Target maximum characters per chunk
    overlap : int, default 200
        Overlap size in characters between consecutive chunks
        
    Returns
    -------
    List[Chunk]
        Overlapping chunks with timestamps
    """
```

#### Usage Example

```python
from analysis.transcribe import Transcript
from analysis.segmenter import chunk_transcript

# Assuming you have a transcript
transcript = Transcript(...)

# Chunk with default settings
chunks = chunk_transcript(transcript)

# Custom chunking
chunks = chunk_transcript(
    transcript,
    max_chars=1000,
    overlap=150
)

for chunk in chunks:
    print(f"[{chunk.start:.1f}s-{chunk.end:.1f}s]: {chunk.text}")
```

#### Integration

The segmenter is used by:
- Ingestion pipeline for vector storage preparation
- Memory system for transcript indexing
- RAG context preparation

### Topic Extraction

**File:** `src/analysis/topics.py`

Extracts and classifies topics from text content using NLP techniques.

**Features:**
- Topic modeling
- Keyword extraction
- Content categorization
- Semantic analysis

**Integration Points:**
- Content classification pipeline
- Search result filtering
- Content recommendation
- Debate topic identification

### Audio Transcription

**File:** `src/analysis/transcribe.py`

Core transcription utilities and the `Transcript` data class.

#### Core Classes

```python
@dataclass
class Transcript:
    """Represents a processed transcript with timing information."""
    segments: List[TranscriptSegment]
    language: str
    confidence: float
    source: str  # Source file or URL
    
@dataclass 
class TranscriptSegment:
    """Individual segment of transcript with timing."""
    text: str
    start: float  # Start time in seconds
    end: float    # End time in seconds
    confidence: float  # Segment confidence score
```

#### Integration

Used by:
- Audio transcription tool
- Ingestion pipeline
- Memory storage
- Search indexing

## Configuration

Analysis modules are configured through:

### Segmentation Settings

```python
# In ingestion pipeline
CHUNK_SETTINGS = {
    'max_chars': 800,      # Optimal for embedding models
    'overlap': 200,        # Ensures context continuity
    'min_chunk_size': 100  # Prevents tiny chunks
}
```

### Topic Analysis Settings

```python
# Topic extraction parameters
TOPIC_CONFIG = {
    'min_topic_words': 3,
    'max_topics_per_doc': 5,
    'confidence_threshold': 0.7
}
```

## Performance Characteristics

### Segmenter Performance
- **Speed:** ~1000 chunks/second for typical transcripts
- **Memory:** O(n) where n is transcript length
- **Chunk Size:** Optimized for embedding model limits (512-1024 tokens)

### Topic Extraction Performance
- **Speed:** Depends on text length and model complexity
- **Accuracy:** Higher confidence with longer text segments
- **Language Support:** English optimized, multilingual capable

## Error Handling

All analysis modules follow consistent error handling patterns:

```python
try:
    chunks = chunk_transcript(transcript)
except InvalidTranscriptError as e:
    logger.error(f"Transcript processing failed: {e}")
    return []
```

Common exceptions:
- `InvalidTranscriptError` - Malformed transcript data
- `ChunkingError` - Segmentation failure
- `TopicExtractionError` - Topic analysis failure

## Testing

Analysis modules are tested through:
- Unit tests: Various `test_*_tool.py` files (for tool integration)
- Analysis-specific tests: `test_analysis_topics.py` (completed)
- Integration tests: Ingestion pipeline tests
- Performance benchmarks: Topic extraction speed tests

**Missing Test Coverage:**
- `test_segmenter.py` - **Needs to be created**
- `test_transcribe.py` - **Needs to be created**## Integration Workflows

### Typical Ingestion Flow

```python
# 1. Transcription
transcript = transcribe_audio(audio_file)

# 2. Segmentation  
chunks = chunk_transcript(transcript, max_chars=800)

# 3. Topic extraction
topics = extract_topics([chunk.text for chunk in chunks])

# 4. Vector storage
for chunk in chunks:
    store_vector_embedding(chunk.text, chunk.start, chunk.end)
```

### Memory Retrieval Flow

```python
# Query processing
query = "What did they say about AI?"

# Semantic search in chunked content
relevant_chunks = vector_search(query, namespace="transcripts")

# Topic filtering
filtered_chunks = filter_by_topics(relevant_chunks, ["ai", "technology"])

# Context reconstruction
context = reconstruct_context(filtered_chunks)
```

## Dependencies

Analysis modules depend on:
- **Core Python:** `dataclasses`, `typing`
- **NLP Libraries:** For topic extraction
- **Audio Processing:** For transcription support
- **Vector Storage:** For chunk embedding

## Future Enhancements

Planned improvements:
1. **Multi-language support** - Better topic extraction for non-English
2. **Smart chunking** - Sentence-boundary aware segmentation
3. **Topic hierarchies** - Nested topic classification
4. **Performance optimization** - Faster processing for long transcripts

## See Also

- [Ingestion Guide](ingestion.md) - How analysis integrates with ingestion
- [Memory Documentation](memory.md) - Storage of analyzed content
- [Tools Reference](tools_reference.md) - Related analysis tools