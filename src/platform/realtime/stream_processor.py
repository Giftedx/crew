"""
Real-time stream processing capabilities for the Ultimate Discord Intelligence Bot.

Provides high-performance stream processing with concurrent multi-source analysis,
live content monitoring, and real-time fact-checking capabilities.
"""

import asyncio
import contextlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Types of content streams."""

    YOUTUBE_LIVE = "youtube_live"
    TWITCH_STREAM = "twitch_stream"
    TWITTER_SPACE = "twitter_space"
    DISCORD_VOICE = "discord_voice"
    REDDIT_LIVE = "reddit_live"
    TIKTOK_LIVE = "tiktok_live"
    GENERIC_AUDIO = "generic_audio"
    GENERIC_VIDEO = "generic_video"
    TEXT_FEED = "text_feed"


class ProcessingPriority(Enum):
    """Processing priority levels."""

    CRITICAL = "critical"  # Real-time fact-checking
    HIGH = "high"  # Live content analysis
    NORMAL = "normal"  # Standard processing
    LOW = "low"  # Background processing
    BATCH = "batch"  # Batch processing


class StreamStatus(Enum):
    """Stream processing status."""

    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    TERMINATED = "terminated"


@dataclass
class StreamMetadata:
    """Metadata for a content stream."""

    stream_id: str
    stream_type: StreamType
    source_url: str
    title: str
    description: str
    start_time: float
    end_time: float | None = None
    viewer_count: int = 0
    language: str = "en"
    quality: str = "medium"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get stream duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def is_live(self) -> bool:
        """Check if stream is currently live."""
        return self.end_time is None

    @property
    def is_ended(self) -> bool:
        """Check if stream has ended."""
        return self.end_time is not None


@dataclass
class StreamChunk:
    """A chunk of content from a stream."""

    stream_id: str
    chunk_id: str
    content_type: str  # "audio", "video", "text", "metadata"
    data: bytes
    timestamp: float
    duration: float = 0.0
    sequence_number: int = 0
    quality_metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_audio(self) -> bool:
        """Check if chunk contains audio data."""
        return self.content_type == "audio"

    @property
    def is_video(self) -> bool:
        """Check if chunk contains video data."""
        return self.content_type == "video"

    @property
    def is_text(self) -> bool:
        """Check if chunk contains text data."""
        return self.content_type == "text"

    @property
    def size_bytes(self) -> int:
        """Get chunk size in bytes."""
        return len(self.data)


@dataclass
class ProcessingResult:
    """Result of stream processing."""

    chunk_id: str
    stream_id: str
    processing_time: float
    success: bool
    result_data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.success

    @property
    def has_high_confidence(self) -> bool:
        """Check if result has high confidence."""
        return self.confidence > 0.8


@dataclass
class StreamProcessorConfig:
    """Configuration for stream processor."""

    max_concurrent_streams: int = 10
    chunk_buffer_size: int = 1000
    processing_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    quality_threshold: float = 0.7
    priority_queue_size: int = 100
    enable_adaptive_processing: bool = True
    enable_quality_monitoring: bool = True
    enable_performance_optimization: bool = True

    @property
    def is_high_performance_mode(self) -> bool:
        """Check if high performance mode is enabled."""
        return (
            self.enable_adaptive_processing and self.enable_quality_monitoring and self.enable_performance_optimization
        )


class StreamProcessor:
    """
    High-performance real-time stream processor.

    Handles concurrent multi-source content streams with adaptive processing,
    quality monitoring, and intelligent prioritization for optimal performance.
    """

    def __init__(self, config: StreamProcessorConfig | None = None):
        """Initialize stream processor."""
        self.config = config or StreamProcessorConfig()
        self.active_streams: dict[str, StreamMetadata] = {}
        self.chunk_queues: dict[str, deque[StreamChunk]] = defaultdict(
            lambda: deque(maxlen=self.config.chunk_buffer_size)
        )
        self.processing_results: dict[str, list[ProcessingResult]] = defaultdict(list)
        self.performance_metrics = {
            "total_chunks_processed": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "success_rate": 0.0,
            "throughput_chunks_per_second": 0.0,
        }
        self._processing_tasks: dict[str, asyncio.Task[None]] = {}
        self._shutdown_event = asyncio.Event()
        self._processing_lock = asyncio.Lock()

        logger.info(f"Stream processor initialized with config: {self.config}")

    async def start_stream(
        self,
        stream_id: str,
        stream_type: StreamType,
        source_url: str,
        title: str,
        description: str = "",
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
    ) -> StreamMetadata:
        """Start processing a new content stream."""
        async with self._processing_lock:
            if stream_id in self.active_streams:
                raise ValueError(f"Stream {stream_id} is already active")

            if len(self.active_streams) >= self.config.max_concurrent_streams:
                raise RuntimeError("Maximum concurrent streams reached")

            metadata = StreamMetadata(
                stream_id=stream_id,
                stream_type=stream_type,
                source_url=source_url,
                title=title,
                description=description,
                start_time=time.time(),
            )

            self.active_streams[stream_id] = metadata
            self.chunk_queues[stream_id] = deque(maxlen=self.config.chunk_buffer_size)

            # Start processing task for this stream
            task = asyncio.create_task(self._process_stream(stream_id, priority))
            self._processing_tasks[stream_id] = task

            logger.info(f"Started stream {stream_id} of type {stream_type.value}")
            return metadata

    async def add_chunk(self, stream_id: str, chunk: StreamChunk) -> bool:
        """Add a chunk to the processing queue for a stream."""
        if stream_id not in self.active_streams:
            logger.warning(f"Stream {stream_id} not found")
            return False

        if not self.active_streams[stream_id].is_live:
            logger.warning(f"Stream {stream_id} is not live")
            return False

        try:
            self.chunk_queues[stream_id].append(chunk)
            logger.debug(f"Added chunk {chunk.chunk_id} to stream {stream_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add chunk to stream {stream_id}: {e}")
            return False

    async def stop_stream(self, stream_id: str) -> StreamMetadata | None:
        """Stop processing a stream."""
        async with self._processing_lock:
            if stream_id not in self.active_streams:
                return None

            metadata = self.active_streams[stream_id]
            metadata.end_time = time.time()

            # Cancel processing task
            if stream_id in self._processing_tasks:
                task = self._processing_tasks[stream_id]
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                del self._processing_tasks[stream_id]

            # Clean up
            del self.active_streams[stream_id]
            if stream_id in self.chunk_queues:
                del self.chunk_queues[stream_id]

            logger.info(f"Stopped stream {stream_id}, duration: {metadata.duration:.2f}s")
            return metadata

    async def get_stream_status(self, stream_id: str) -> StreamStatus:
        """Get the current status of a stream."""
        if stream_id not in self.active_streams:
            return StreamStatus.TERMINATED

        if stream_id in self._processing_tasks:
            task = self._processing_tasks[stream_id]
            if task.done():
                return StreamStatus.ERROR if task.exception() else StreamStatus.TERMINATED
            return StreamStatus.PROCESSING

        return StreamStatus.CONNECTED

    async def get_processing_results(self, stream_id: str) -> list[ProcessingResult]:
        """Get processing results for a stream."""
        return self.processing_results.get(stream_id, [])

    async def get_latest_result(self, stream_id: str) -> ProcessingResult | None:
        """Get the latest processing result for a stream."""
        results = self.processing_results.get(stream_id, [])
        return results[-1] if results else None

    async def _process_stream(self, stream_id: str, priority: ProcessingPriority) -> None:
        """Process chunks from a stream."""
        logger.info(f"Starting processing for stream {stream_id} with priority {priority.value}")

        try:
            while not self._shutdown_event.is_set():
                if stream_id not in self.active_streams:
                    break

                metadata = self.active_streams[stream_id]
                if not metadata.is_live:
                    break

                # Get next chunk
                chunk = await self._get_next_chunk(stream_id)
                if chunk is None:
                    await asyncio.sleep(0.1)  # Brief pause if no chunks
                    continue

                # Process chunk
                result = await self._process_chunk(stream_id, chunk, priority)
                if result:
                    self.processing_results[stream_id].append(result)
                    self._update_performance_metrics(result)

        except asyncio.CancelledError:
            logger.info(f"Processing cancelled for stream {stream_id}")
        except Exception as e:
            logger.error(f"Error processing stream {stream_id}: {e}")
        finally:
            logger.info(f"Processing ended for stream {stream_id}")

    async def _get_next_chunk(self, stream_id: str) -> StreamChunk | None:
        """Get the next chunk from a stream's queue."""
        if stream_id not in self.chunk_queues:
            return None

        queue = self.chunk_queues[stream_id]
        return queue.popleft() if queue else None

    async def _process_chunk(
        self, stream_id: str, chunk: StreamChunk, priority: ProcessingPriority
    ) -> ProcessingResult | None:
        """Process a single chunk."""
        start_time = time.time()

        try:
            # Simulate processing based on chunk type
            if chunk.is_audio:
                result_data = await self._process_audio_chunk(chunk)
            elif chunk.is_video:
                result_data = await self._process_video_chunk(chunk)
            elif chunk.is_text:
                result_data = await self._process_text_chunk(chunk)
            else:
                result_data = {"type": "unknown", "processed": True}

            processing_time = time.time() - start_time

            result = ProcessingResult(
                chunk_id=chunk.chunk_id,
                stream_id=stream_id,
                processing_time=processing_time,
                success=True,
                result_data=result_data,
                confidence=0.85,  # Simulated confidence
            )

            logger.debug(f"Processed chunk {chunk.chunk_id} in {processing_time:.3f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to process chunk {chunk.chunk_id}: {e}")

            return ProcessingResult(
                chunk_id=chunk.chunk_id,
                stream_id=stream_id,
                processing_time=processing_time,
                success=False,
                error_message=str(e),
                confidence=0.0,
            )

    async def _process_audio_chunk(self, chunk: StreamChunk) -> dict[str, Any]:
        """Process an audio chunk."""
        # Simulate audio processing (transcription, emotion detection, etc.)
        await asyncio.sleep(0.05)  # Simulate processing time

        return {
            "type": "audio",
            "transcription": "Simulated transcription text",
            "emotion": "neutral",
            "confidence": 0.85,
            "duration": chunk.duration,
            "quality": "good",
        }

    async def _process_video_chunk(self, chunk: StreamChunk) -> dict[str, Any]:
        """Process a video chunk."""
        # Simulate video processing (scene detection, object tracking, etc.)
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "type": "video",
            "scene_type": "indoor",
            "objects_detected": ["person", "computer"],
            "confidence": 0.80,
            "duration": chunk.duration,
            "quality": "medium",
        }

    async def _process_text_chunk(self, chunk: StreamChunk) -> dict[str, Any]:
        """Process a text chunk."""
        # Simulate text processing (sentiment analysis, topic extraction, etc.)
        await asyncio.sleep(0.02)  # Simulate processing time

        return {
            "type": "text",
            "sentiment": "positive",
            "topics": ["technology", "ai"],
            "confidence": 0.90,
            "length": len(chunk.data),
        }

    def _update_performance_metrics(self, result: ProcessingResult) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_chunks_processed"] += 1
        self.performance_metrics["total_processing_time"] += result.processing_time
        self.performance_metrics["average_processing_time"] = (
            self.performance_metrics["total_processing_time"] / self.performance_metrics["total_chunks_processed"]
        )

        # Update success rate
        total_results = sum(len(results) for results in self.processing_results.values())
        successful_results = sum(len([r for r in results if r.success]) for results in self.processing_results.values())
        self.performance_metrics["success_rate"] = successful_results / total_results if total_results > 0 else 0.0

        # Update throughput
        current_time = time.time()
        if hasattr(self, "_last_throughput_calculation"):
            time_diff = current_time - self._last_throughput_calculation
            if time_diff > 0:
                self.performance_metrics["throughput_chunks_per_second"] = 1.0 / time_diff
        self._last_throughput_calculation = current_time

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return dict(self.performance_metrics)

    async def get_stream_statistics(self) -> dict[str, Any]:
        """Get statistics about active streams."""
        return {
            "active_streams": len(self.active_streams),
            "total_chunks_queued": sum(len(queue) for queue in self.chunk_queues.values()),
            "total_results": sum(len(results) for results in self.processing_results.values()),
            "stream_types": {
                stream_type.value: len([s for s in self.active_streams.values() if s.stream_type == stream_type])
                for stream_type in StreamType
            },
        }

    async def shutdown(self) -> None:
        """Shutdown the stream processor."""
        logger.info("Shutting down stream processor...")

        # Signal shutdown
        self._shutdown_event.set()

        # Stop all active streams
        for stream_id in list(self.active_streams.keys()):
            await self.stop_stream(stream_id)

        # Wait for all tasks to complete
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks.values(), return_exceptions=True)

        logger.info("Stream processor shutdown complete")

    async def __aenter__(self) -> "StreamProcessor":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.shutdown()


# Global processor instance
_global_processor: StreamProcessor | None = None


def get_global_stream_processor() -> StreamProcessor:
    """Get the global stream processor instance."""
    global _global_processor
    if _global_processor is None:
        _global_processor = StreamProcessor()
    return _global_processor


def set_global_stream_processor(processor: StreamProcessor) -> None:
    """Set the global stream processor instance."""
    global _global_processor
    _global_processor = processor


# Convenience functions for global processor
async def start_stream(
    stream_id: str,
    stream_type: StreamType,
    source_url: str,
    title: str,
    description: str = "",
    priority: ProcessingPriority = ProcessingPriority.NORMAL,
) -> StreamMetadata:
    """Start a stream using the global processor."""
    return await get_global_stream_processor().start_stream(
        stream_id, stream_type, source_url, title, description, priority
    )


async def add_chunk(stream_id: str, chunk: StreamChunk) -> bool:
    """Add a chunk using the global processor."""
    return await get_global_stream_processor().add_chunk(stream_id, chunk)


async def stop_stream(stream_id: str) -> StreamMetadata | None:
    """Stop a stream using the global processor."""
    return await get_global_stream_processor().stop_stream(stream_id)


async def get_processing_results(stream_id: str) -> list[ProcessingResult]:
    """Get processing results using the global processor."""
    return await get_global_stream_processor().get_processing_results(stream_id)
