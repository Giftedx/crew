"""
Discord-specific metrics collection and monitoring.

This module provides comprehensive metrics collection for Discord AI chatbot
operations including conversation tracking, user engagement, and system performance.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import Any


@dataclass
class ConversationMetrics:
    """Metrics for individual conversations."""

    conversation_id: str
    user_id: str
    guild_id: str
    channel_id: str
    start_time: float
    end_time: float | None = None
    message_count: int = 0
    bot_responses: int = 0
    avg_response_time_ms: float = 0.0
    user_satisfaction_score: float | None = None
    topics_discussed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserEngagementMetrics:
    """Metrics for user engagement patterns."""

    user_id: str
    total_conversations: int = 0
    total_messages: int = 0
    avg_conversation_length: float = 0.0
    avg_response_time: float = 0.0
    satisfaction_scores: list[float] = field(default_factory=list)
    preferred_topics: dict[str, int] = field(default_factory=dict)
    engagement_trend: str = "stable"
    last_active: float = 0.0
    opt_in_status: bool = False


@dataclass
class GuildMetrics:
    """Metrics for Discord guild (server) activity."""

    guild_id: str
    active_users: int = 0
    total_conversations: int = 0
    avg_conversation_length: float = 0.0
    peak_activity_hours: list[int] = field(default_factory=list)
    popular_channels: dict[str, int] = field(default_factory=list)
    user_retention_rate: float = 0.0
    satisfaction_avg: float = 0.0


@dataclass
class PersonalityMetrics:
    """Metrics for bot personality evolution."""

    trait_name: str
    current_value: float
    evolution_history: list[tuple[float, float]] = field(default_factory=list)
    user_feedback_count: int = 0
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0
    last_updated: float = 0.0


class DiscordMetricsCollector:
    """
    Comprehensive metrics collector for Discord AI chatbot.

    This collector tracks conversations, user engagement, guild activity,
    and personality evolution metrics.
    """

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self._active_conversations: dict[str, ConversationMetrics] = {}
        self._conversation_history: deque = deque(maxlen=max_history_size)
        self._user_metrics: dict[str, UserEngagementMetrics] = {}
        self._user_activity_history: deque = deque(maxlen=max_history_size)
        self._guild_metrics: dict[str, GuildMetrics] = {}
        self._personality_metrics: dict[str, PersonalityMetrics] = {}
        self._system_metrics: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()
        self._stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_bot_responses": 0,
            "avg_response_time_ms": 0.0,
            "user_satisfaction_avg": 0.0,
            "active_users_24h": 0,
            "conversation_success_rate": 0.0,
        }

    async def start_conversation(
        self, conversation_id: str, user_id: str, guild_id: str, channel_id: str, metadata: dict[str, Any] | None = None
    ) -> StepResult:
        """Start tracking a new conversation."""
        try:
            async with self._lock:
                conversation = ConversationMetrics(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    start_time=time.time(),
                    metadata=metadata or {},
                )
                self._active_conversations[conversation_id] = conversation
                await self._update_user_metrics(user_id, guild_id, "conversation_started")
                await self._update_guild_metrics(guild_id, channel_id, "conversation_started")
                return StepResult.ok(data={"conversation_id": conversation_id, "action": "conversation_started"})
        except Exception as e:
            return StepResult.fail(f"Failed to start conversation tracking: {e!s}")

    async def end_conversation(
        self, conversation_id: str, satisfaction_score: float | None = None, topics_discussed: list[str] | None = None
    ) -> StepResult:
        """End conversation tracking and compute final metrics."""
        try:
            async with self._lock:
                if conversation_id not in self._active_conversations:
                    return StepResult.fail(f"Conversation {conversation_id} not found")
                conversation = self._active_conversations[conversation_id]
                conversation.end_time = time.time()
                if satisfaction_score is not None:
                    conversation.user_satisfaction_score = satisfaction_score
                if topics_discussed:
                    conversation.topics_discussed = topics_discussed
                conversation.end_time - conversation.start_time
                if conversation.bot_responses > 0:
                    conversation.avg_response_time_ms = (
                        conversation.avg_response_time_ms * (conversation.bot_responses - 1)
                        + (conversation.end_time - conversation.start_time) * 1000
                    ) / conversation.bot_responses
                self._conversation_history.append(conversation)
                del self._active_conversations[conversation_id]
                await self._update_conversation_stats(conversation)
                await self._update_user_engagement(conversation)
                return StepResult.ok(data={"conversation_id": conversation_id, "action": "conversation_ended"})
        except Exception as e:
            return StepResult.fail(f"Failed to end conversation tracking: {e!s}")

    async def record_message(
        self,
        conversation_id: str,
        user_id: str,
        message_type: str,
        response_time_ms: float | None = None,
        topic: str | None = None,
    ) -> StepResult:
        """Record a message in an active conversation."""
        try:
            async with self._lock:
                if conversation_id not in self._active_conversations:
                    return StepResult.fail(f"Conversation {conversation_id} not found")
                conversation = self._active_conversations[conversation_id]
                conversation.message_count += 1
                if message_type == "bot":
                    conversation.bot_responses += 1
                    if response_time_ms is not None:
                        if conversation.avg_response_time_ms == 0:
                            conversation.avg_response_time_ms = response_time_ms
                        else:
                            conversation.avg_response_time_ms = (
                                conversation.avg_response_time_ms * (conversation.bot_responses - 1) + response_time_ms
                            ) / conversation.bot_responses
                if topic and topic not in conversation.topics_discussed:
                    conversation.topics_discussed.append(topic)
                await self._update_user_metrics(user_id, conversation.guild_id, "message_sent")
                self._stats["total_messages"] += 1
                if message_type == "bot":
                    self._stats["total_bot_responses"] += 1
                return StepResult.ok(data={"message_recorded": True, "message_type": message_type})
        except Exception as e:
            return StepResult.fail(f"Failed to record message: {e!s}")

    async def record_personality_feedback(self, trait_name: str, feedback_value: float, user_id: str) -> StepResult:
        """Record user feedback on personality traits."""
        try:
            async with self._lock:
                if trait_name not in self._personality_metrics:
                    self._personality_metrics[trait_name] = PersonalityMetrics(
                        trait_name=trait_name, current_value=0.0, last_updated=time.time()
                    )
                trait_metrics = self._personality_metrics[trait_name]
                trait_metrics.user_feedback_count += 1
                trait_metrics.last_updated = time.time()
                if feedback_value > 0:
                    trait_metrics.positive_feedback_count += 1
                elif feedback_value < 0:
                    trait_metrics.negative_feedback_count += 1
                trait_metrics.evolution_history.append((time.time(), trait_metrics.current_value))
                if len(trait_metrics.evolution_history) > 1000:
                    trait_metrics.evolution_history = trait_metrics.evolution_history[-1000:]
                return StepResult.ok(
                    data={
                        "trait_name": trait_name,
                        "feedback_recorded": True,
                        "total_feedback": trait_metrics.user_feedback_count,
                    }
                )
        except Exception as e:
            return StepResult.fail(f"Failed to record personality feedback: {e!s}")

    async def update_personality_trait(self, trait_name: str, new_value: float) -> StepResult:
        """Update a personality trait value."""
        try:
            async with self._lock:
                if trait_name not in self._personality_metrics:
                    self._personality_metrics[trait_name] = PersonalityMetrics(
                        trait_name=trait_name, current_value=new_value, last_updated=time.time()
                    )
                else:
                    trait_metrics = self._personality_metrics[trait_name]
                    trait_metrics.current_value = new_value
                    trait_metrics.last_updated = time.time()
                return StepResult.ok(data={"trait_name": trait_name, "new_value": new_value})
        except Exception as e:
            return StepResult.fail(f"Failed to update personality trait: {e!s}")

    async def _update_user_metrics(self, user_id: str, guild_id: str, action: str):
        """Update user engagement metrics."""
        if user_id not in self._user_metrics:
            self._user_metrics[user_id] = UserEngagementMetrics(user_id=user_id, last_active=time.time())
        user_metrics = self._user_metrics[user_id]
        user_metrics.last_active = time.time()
        if action == "conversation_started":
            user_metrics.total_conversations += 1
        elif action == "message_sent":
            user_metrics.total_messages += 1

    async def _update_guild_metrics(self, guild_id: str, channel_id: str, action: str):
        """Update guild activity metrics."""
        if guild_id not in self._guild_metrics:
            self._guild_metrics[guild_id] = GuildMetrics(guild_id=guild_id)
        guild_metrics = self._guild_metrics[guild_id]
        if action == "conversation_started":
            guild_metrics.total_conversations += 1
            guild_metrics.active_users += 1
        if channel_id in guild_metrics.popular_channels:
            guild_metrics.popular_channels[channel_id] += 1
        else:
            guild_metrics.popular_channels[channel_id] = 1

    async def _update_conversation_stats(self, conversation: ConversationMetrics):
        """Update overall conversation statistics."""
        self._stats["total_conversations"] += 1
        if conversation.avg_response_time_ms > 0:
            total_responses = self._stats["total_bot_responses"]
            if total_responses > 0:
                self._stats["avg_response_time_ms"] = (
                    self._stats["avg_response_time_ms"] * (total_responses - 1) + conversation.avg_response_time_ms
                ) / total_responses
        if conversation.user_satisfaction_score is not None:
            satisfaction_scores = [
                c.user_satisfaction_score for c in self._conversation_history if c.user_satisfaction_score is not None
            ]
            if satisfaction_scores:
                self._stats["user_satisfaction_avg"] = sum(satisfaction_scores) / len(satisfaction_scores)

    async def _update_user_engagement(self, conversation: ConversationMetrics):
        """Update user engagement metrics based on conversation."""
        user_id = conversation.user_id
        if user_id in self._user_metrics:
            user_metrics = self._user_metrics[user_id]
            if user_metrics.total_conversations > 0:
                conversation_length = conversation.message_count
                user_metrics.avg_conversation_length = (
                    user_metrics.avg_conversation_length * (user_metrics.total_conversations - 1) + conversation_length
                ) / user_metrics.total_conversations
            if conversation.avg_response_time_ms > 0:
                if user_metrics.avg_response_time == 0:
                    user_metrics.avg_response_time = conversation.avg_response_time_ms
                else:
                    user_metrics.avg_response_time = (
                        user_metrics.avg_response_time + conversation.avg_response_time_ms
                    ) / 2
            if conversation.user_satisfaction_score is not None:
                user_metrics.satisfaction_scores.append(conversation.user_satisfaction_score)
                if len(user_metrics.satisfaction_scores) > 100:
                    user_metrics.satisfaction_scores = user_metrics.satisfaction_scores[-100:]
            for topic in conversation.topics_discussed:
                if topic in user_metrics.preferred_topics:
                    user_metrics.preferred_topics[topic] += 1
                else:
                    user_metrics.preferred_topics[topic] = 1

    async def get_conversation_metrics(self, conversation_id: str) -> StepResult:
        """Get metrics for a specific conversation."""
        try:
            async with self._lock:
                if conversation_id in self._active_conversations:
                    conversation = self._active_conversations[conversation_id]
                    return StepResult.ok(data={"conversation": conversation, "status": "active"})
                for conversation in self._conversation_history:
                    if conversation.conversation_id == conversation_id:
                        return StepResult.ok(data={"conversation": conversation, "status": "completed"})
                return StepResult.fail(f"Conversation {conversation_id} not found")
        except Exception as e:
            return StepResult.fail(f"Failed to get conversation metrics: {e!s}")

    async def get_user_metrics(self, user_id: str) -> StepResult:
        """Get engagement metrics for a specific user."""
        try:
            async with self._lock:
                if user_id not in self._user_metrics:
                    return StepResult.fail(f"User {user_id} not found")
                user_metrics = self._user_metrics[user_id]
                recent_scores = user_metrics.satisfaction_scores[-10:] if user_metrics.satisfaction_scores else []
                if len(recent_scores) >= 5:
                    early_avg = sum(recent_scores[:5]) / 5
                    late_avg = sum(recent_scores[-5:]) / 5
                    if late_avg > early_avg * 1.1:
                        user_metrics.engagement_trend = "increasing"
                    elif late_avg < early_avg * 0.9:
                        user_metrics.engagement_trend = "decreasing"
                    else:
                        user_metrics.engagement_trend = "stable"
                return StepResult.ok(data={"user_metrics": user_metrics})
        except Exception as e:
            return StepResult.fail(f"Failed to get user metrics: {e!s}")

    async def get_guild_metrics(self, guild_id: str) -> StepResult:
        """Get activity metrics for a specific guild."""
        try:
            async with self._lock:
                if guild_id not in self._guild_metrics:
                    return StepResult.fail(f"Guild {guild_id} not found")
                guild_metrics = self._guild_metrics[guild_id]
                if guild_metrics.total_conversations > 0:
                    hour_activity = defaultdict(int)
                    for conversation in self._conversation_history:
                        if conversation.guild_id == guild_id:
                            hour = int(time.strftime("%H", time.localtime(conversation.start_time)))
                            hour_activity[hour] += 1
                    guild_metrics.peak_activity_hours = sorted(
                        hour_activity.keys(), key=lambda h: hour_activity[h], reverse=True
                    )[:5]
                return StepResult.ok(data={"guild_metrics": guild_metrics})
        except Exception as e:
            return StepResult.fail(f"Failed to get guild metrics: {e!s}")

    async def get_personality_metrics(self, trait_name: str | None = None) -> StepResult:
        """Get personality evolution metrics."""
        try:
            async with self._lock:
                if trait_name:
                    if trait_name not in self._personality_metrics:
                        return StepResult.fail(f"Trait {trait_name} not found")
                    return StepResult.ok(data={"trait_metrics": self._personality_metrics[trait_name]})
                else:
                    return StepResult.ok(data={"all_traits": self._personality_metrics})
        except Exception as e:
            return StepResult.fail(f"Failed to get personality metrics: {e!s}")

    async def get_comprehensive_stats(self) -> StepResult:
        """Get comprehensive statistics across all metrics."""
        try:
            async with self._lock:
                current_time = time.time()
                active_users_24h = sum(
                    1 for user_metrics in self._user_metrics.values() if current_time - user_metrics.last_active < 86400
                )
                self._stats["active_users_24h"] = active_users_24h
                total_conversations = len(self._conversation_history)
                successful_conversations = sum(
                    1
                    for conv in self._conversation_history
                    if conv.user_satisfaction_score is not None and conv.user_satisfaction_score >= 0.5
                )
                if total_conversations > 0:
                    self._stats["conversation_success_rate"] = successful_conversations / total_conversations
                return StepResult.ok(
                    data={
                        "system_stats": self._stats,
                        "active_conversations": len(self._active_conversations),
                        "total_users": len(self._user_metrics),
                        "total_guilds": len(self._guild_metrics),
                        "personality_traits": len(self._personality_metrics),
                        "conversation_history_size": len(self._conversation_history),
                    }
                )
        except Exception as e:
            return StepResult.fail(f"Failed to get comprehensive stats: {e!s}")

    async def cleanup_old_data(self, max_age_hours: int = 168) -> StepResult:
        """Clean up old metrics data to prevent memory bloat."""
        try:
            async with self._lock:
                current_time = time.time()
                max_age_seconds = max_age_hours * 3600
                old_conversations = [
                    conv for conv in self._conversation_history if current_time - conv.start_time > max_age_seconds
                ]
                for conv in old_conversations:
                    self._conversation_history.remove(conv)
                inactive_users = [
                    user_id
                    for user_id, user_metrics in self._user_metrics.items()
                    if current_time - user_metrics.last_active > max_age_seconds
                ]
                for user_id in inactive_users:
                    del self._user_metrics[user_id]
                return StepResult.ok(
                    data={"conversations_cleaned": len(old_conversations), "users_cleaned": len(inactive_users)}
                )
        except Exception as e:
            return StepResult.fail(f"Failed to cleanup old data: {e!s}")


def create_discord_metrics_collector(max_history_size: int = 10000) -> DiscordMetricsCollector:
    """Create a Discord metrics collector with the specified configuration."""
    return DiscordMetricsCollector(max_history_size)
