"""
Message batching system for efficient Discord message processing.

This module implements intelligent message batching to optimize processing
throughput and reduce API calls while maintaining responsiveness.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from performance_optimization.src.ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class BatchedMessage:
    """Represents a message in a batch."""

    message_id: str
    user_id: str
    guild_id: str
    channel_id: str
    content: str
    timestamp: float
    priority: int = 0  # Higher number = higher priority
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageBatch:
    """Represents a batch of messages to be processed."""

    batch_id: str
    messages: list[BatchedMessage]
    created_at: float
    max_age_seconds: float = 5.0
    max_size: int = 10

    @property
    def age_seconds(self) -> float:
        """Get the age of this batch in seconds."""
        return time.time() - self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if this batch has expired."""
        return self.age_seconds > self.max_age_seconds

    @property
    def is_full(self) -> bool:
        """Check if this batch is full."""
        return len(self.messages) >= self.max_size

    @property
    def priority_score(self) -> float:
        """Calculate priority score for this batch."""
        if not self.messages:
            return 0.0

        # Weight by highest priority message and batch size
        max_priority = max(msg.priority for msg in self.messages)
        size_factor = min(len(self.messages) / self.max_size, 1.0)

        return max_priority + (size_factor * 0.5)


@dataclass
class BatchConfig:
    """Configuration for message batching."""

    max_batch_size: int = 10
    max_batch_age_seconds: float = 5.0
    max_concurrent_batches: int = 3
    priority_threshold: int = 5  # Messages above this priority bypass batching
    enable_smart_batching: bool = True
    guild_isolation: bool = True  # Separate batches by guild


class MessageBatcher:
    """
    Intelligent message batcher for Discord message processing.

    This batcher groups messages together for efficient processing while
    maintaining responsiveness for high-priority messages.
    """

    def __init__(self, config: BatchConfig, processor: Callable[[MessageBatch], Awaitable[StepResult]]):
        self.config = config
        self.processor = processor

        # Batch storage by guild (if guild isolation enabled)
        self._batches: dict[str, list[MessageBatch]] = defaultdict(list)
        self._batch_lock = asyncio.Lock()
        self._processing_tasks: dict[str, asyncio.Task] = {}
        self._stats: dict[str, Any] = {
            "total_batches": 0,
            "total_messages": 0,
            "avg_batch_size": 0.0,
            "avg_processing_time": 0.0,
            "high_priority_bypasses": 0,
        }

        # Start background processing
        self._background_task = asyncio.create_task(self._background_processor())

    async def add_message(self, message_data: dict[str, Any]) -> StepResult:
        """
        Add a message to the batching system.

        Args:
            message_data: Discord message data

        Returns:
            StepResult indicating success/failure
        """
        try:
            # Create batched message
            batched_msg = self._create_batched_message(message_data)

            # Check if message should bypass batching (high priority)
            if batched_msg.priority >= self.config.priority_threshold:
                self._stats["high_priority_bypasses"] += 1
                return await self._process_single_message(batched_msg)

            # Add to appropriate batch
            guild_key = batched_msg.guild_id if self.config.guild_isolation else "global"

            async with self._batch_lock:
                batch = await self._find_or_create_batch(guild_key, batched_msg)
                batch.messages.append(batched_msg)

                # Check if batch should be processed immediately
                if batch.is_full:
                    await self._schedule_batch_processing(guild_key, batch)

                self._stats["total_messages"] += 1

            return StepResult.ok(data={"action": "message_batched", "batch_id": batch.batch_id})

        except Exception as e:
            return StepResult.fail(f"Failed to add message to batch: {e!s}")

    def _create_batched_message(self, message_data: dict[str, Any]) -> BatchedMessage:
        """Create a BatchedMessage from Discord message data."""
        # Determine priority based on content and context
        priority = self._calculate_priority(message_data)

        return BatchedMessage(
            message_id=message_data["id"],
            user_id=message_data["author"]["id"],
            guild_id=message_data["guild_id"],
            channel_id=message_data["channel_id"],
            content=message_data["content"],
            timestamp=message_data.get("timestamp", time.time()),
            priority=priority,
            metadata={
                "username": message_data["author"].get("username"),
                "channel_type": message_data.get("channel_type", "text"),
                "mentions": message_data.get("mentions", []),
                "direct_mention": self._is_direct_mention(message_data["content"]),
            },
        )

    def _calculate_priority(self, message_data: dict[str, Any]) -> int:
        """Calculate priority for a message based on various factors."""
        priority = 0
        content = message_data["content"]

        # Direct mentions get high priority
        if self._is_direct_mention(content):
            priority += 5

        # Urgent keywords
        urgent_keywords = ["urgent", "help", "emergency", "asap", "quick"]
        if any(keyword in content.lower() for keyword in urgent_keywords):
            priority += 3

        # Question marks increase priority
        priority += content.count("?") * 2

        # Channel type affects priority
        channel_type = message_data.get("channel_type", "text")
        if channel_type in ["voice", "stage"]:
            priority += 2

        # Recent timestamp gets slight priority boost
        timestamp = message_data.get("timestamp", time.time())
        age_seconds = time.time() - timestamp
        if age_seconds < 30:  # Very recent messages
            priority += 1

        return min(priority, 10)  # Cap at 10

    def _is_direct_mention(self, content: str) -> bool:
        """Check if content contains a direct mention."""
        # This would integrate with the actual bot mention detection
        return "@bot" in content.lower() or content.startswith("@")

    async def _find_or_create_batch(self, guild_key: str, message: BatchedMessage) -> MessageBatch:
        """Find an existing batch or create a new one."""
        batches = self._batches[guild_key]

        # Look for existing batch that can accommodate this message
        for batch in batches:
            if not batch.is_full and not batch.is_expired:
                # Check if batch is compatible (similar priority, recent)
                if abs(batch.messages[0].priority - message.priority) <= 2:
                    return batch

        # Create new batch
        batch_id = f"batch_{int(time.time() * 1000)}_{len(batches)}"
        new_batch = MessageBatch(
            batch_id=batch_id,
            messages=[],
            created_at=time.time(),
            max_age_seconds=self.config.max_batch_age_seconds,
            max_size=self.config.max_batch_size,
        )

        batches.append(new_batch)
        return new_batch

    async def _schedule_batch_processing(self, guild_key: str, batch: MessageBatch):
        """Schedule a batch for processing."""
        # Remove from pending batches
        self._batches[guild_key].remove(batch)

        # Create processing task
        task = asyncio.create_task(self._process_batch(batch))
        self._processing_tasks[batch.batch_id] = task

        # Clean up task when complete
        task.add_done_callback(lambda t: self._processing_tasks.pop(batch.batch_id, None))

    async def _process_single_message(self, message: BatchedMessage) -> StepResult:
        """Process a single high-priority message immediately."""
        # Create a single-message batch
        batch = MessageBatch(batch_id=f"single_{message.message_id}", messages=[message], created_at=time.time())

        return await self._process_batch(batch)

    async def _process_batch(self, batch: MessageBatch) -> StepResult:
        """Process a batch of messages."""
        start_time = time.time()

        try:
            # Sort messages by priority (highest first)
            batch.messages.sort(key=lambda msg: msg.priority, reverse=True)

            # Process the batch
            result = await self.processor(batch)

            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(batch, processing_time)

            return result

        except Exception as e:
            return StepResult.fail(f"Batch processing failed: {e!s}")

    def _update_stats(self, batch: MessageBatch, processing_time: float):
        """Update batch processing statistics."""
        self._stats["total_batches"] += 1
        self._stats["avg_batch_size"] = (
            self._stats["avg_batch_size"] * (self._stats["total_batches"] - 1) + len(batch.messages)
        ) / self._stats["total_batches"]
        self._stats["avg_processing_time"] = (
            self._stats["avg_processing_time"] * (self._stats["total_batches"] - 1) + processing_time
        ) / self._stats["total_batches"]

    async def _background_processor(self):
        """Background task to process expired batches."""
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second

                async with self._batch_lock:
                    current_time = time.time()

                    # Process expired batches
                    for guild_key in list(self._batches.keys()):
                        batches = self._batches[guild_key]
                        expired_batches = [b for b in batches if b.is_expired]

                        for batch in expired_batches:
                            batches.remove(batch)
                            await self._schedule_batch_processing(guild_key, batch)

                        # Clean up empty guild keys
                        if not batches:
                            del self._batches[guild_key]

            except Exception as e:
                # Log error but continue processing
                print(f"Background processor error: {e!s}")

    async def get_stats(self) -> StepResult:
        """Get batching statistics."""
        async with self._batch_lock:
            stats = self._stats.copy()
            stats["pending_batches"] = sum(len(batches) for batches in self._batches.values())
            stats["active_processing_tasks"] = len(self._processing_tasks)

            # Add per-guild stats
            stats["guild_stats"] = {}
            for guild_key, batches in self._batches.items():
                stats["guild_stats"][guild_key] = {
                    "pending_batches": len(batches),
                    "total_messages": sum(len(batch.messages) for batch in batches),
                }

        return StepResult.ok(data=stats)

    async def flush_all_batches(self) -> StepResult:
        """Force process all pending batches."""
        async with self._batch_lock:
            all_batches = []

            for guild_key, batches in self._batches.items():
                all_batches.extend(batches)
                self._batches[guild_key].clear()

            # Process all batches concurrently
            tasks = []
            for batch in all_batches:
                task = asyncio.create_task(self._process_batch(batch))
                tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successful vs failed
                successful = sum(1 for r in results if isinstance(r, StepResult) and r.success)
                failed = len(results) - successful

                return StepResult.ok(
                    data={
                        "action": "batches_flushed",
                        "total_batches": len(all_batches),
                        "successful": successful,
                        "failed": failed,
                    }
                )

            return StepResult.ok(data={"action": "no_batches_to_flush"})

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the batcher."""
        # Cancel background task
        self._background_task.cancel()

        try:
            await self._background_task
        except asyncio.CancelledError:
            pass

        # Flush all remaining batches
        await self.flush_all_batches()

        # Cancel any remaining processing tasks
        for task in self._processing_tasks.values():
            task.cancel()

        return StepResult.ok(data={"action": "batcher_shutdown_complete"})


class SmartMessageBatcher(MessageBatcher):
    """
    Enhanced message batcher with smart batching algorithms.

    This batcher uses machine learning and heuristics to optimize
    batch composition and processing timing.
    """

    def __init__(self, config: BatchConfig, processor: Callable[[MessageBatch], Awaitable[StepResult]]):
        super().__init__(config, processor)

        # Smart batching features
        self._message_similarity_threshold = 0.7
        self._user_behavior_cache: dict[str, dict[str, Any]] = {}
        self._optimal_batch_sizes: dict[str, int] = {}

    def _calculate_priority(self, message_data: dict[str, Any]) -> int:
        """Enhanced priority calculation with user behavior analysis."""
        base_priority = super()._calculate_priority(message_data)

        # Adjust based on user behavior patterns
        user_id = message_data["author"]["id"]
        user_behavior = self._user_behavior_cache.get(user_id, {})

        # Users who typically get quick responses get higher priority
        avg_response_time = user_behavior.get("avg_response_time", 60.0)
        if avg_response_time < 30.0:
            base_priority += 1

        # Users with high engagement get priority boost
        engagement_score = user_behavior.get("engagement_score", 0.5)
        if engagement_score > 0.8:
            base_priority += 1

        return min(base_priority, 10)

    async def _find_or_create_batch(self, guild_key: str, message: BatchedMessage) -> MessageBatch:
        """Enhanced batch finding with similarity matching."""
        if not self.config.enable_smart_batching:
            return await super()._find_or_create_batch(guild_key, message)

        batches = self._batches[guild_key]

        # Look for existing batch with similar content
        for batch in batches:
            if not batch.is_full and not batch.is_expired:
                # Check content similarity
                if self._is_content_similar(message.content, batch.messages[0].content):
                    return batch

        # Create new batch with optimal size for this guild
        optimal_size = self._optimal_batch_sizes.get(guild_key, self.config.max_batch_size)

        batch_id = f"smart_batch_{int(time.time() * 1000)}_{len(batches)}"
        new_batch = MessageBatch(
            batch_id=batch_id,
            messages=[],
            created_at=time.time(),
            max_age_seconds=self.config.max_batch_age_seconds,
            max_size=optimal_size,
        )

        batches.append(new_batch)
        return new_batch

    def _is_content_similar(self, content1: str, content2: str) -> bool:
        """Check if two message contents are similar."""
        # Simple similarity check based on common words
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        similarity = len(intersection) / len(union)
        return similarity >= self._message_similarity_threshold

    def _update_stats(self, batch: MessageBatch, processing_time: float):
        """Enhanced stats update with learning."""
        super()._update_stats(batch, processing_time)

        # Learn optimal batch sizes per guild
        guild_key = batch.messages[0].guild_id if self.config.guild_isolation else "global"

        if guild_key not in self._optimal_batch_sizes:
            self._optimal_batch_sizes[guild_key] = len(batch.messages)
        else:
            # Gradually adjust optimal size based on performance
            current_optimal = self._optimal_batch_sizes[guild_key]
            actual_size = len(batch.messages)

            # If processing was fast, we can handle larger batches
            if processing_time < 2.0 and actual_size < current_optimal * 1.2:
                self._optimal_batch_sizes[guild_key] = min(int(current_optimal * 1.1), self.config.max_batch_size)
            # If processing was slow, reduce optimal size
            elif processing_time > 5.0 and actual_size > current_optimal * 0.8:
                self._optimal_batch_sizes[guild_key] = max(int(current_optimal * 0.9), 1)


# Factory function for creating batchers
def create_message_batcher(
    config: BatchConfig, processor: Callable[[MessageBatch], Awaitable[StepResult]], smart_batching: bool = True
) -> MessageBatcher:
    """Create a message batcher with the specified configuration."""
    if smart_batching:
        return SmartMessageBatcher(config, processor)
    else:
        return MessageBatcher(config, processor)
