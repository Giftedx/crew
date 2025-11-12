from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


class RateLimitAction(Enum):
    """Actions to take when rate limit is exceeded."""

    WARN = "warn"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    TEMP_MUTE = "temp_mute"
    TEMP_BAN = "temp_ban"


class RateLimitScope(Enum):
    """Scope of rate limiting."""

    USER = "user"
    GUILD = "guild"
    CHANNEL = "channel"
    GLOBAL = "global"


@dataclass
class RateLimitRule:
    """Individual rate limiting rule."""

    name: str
    scope: RateLimitScope
    max_requests: int
    window_seconds: int
    action: RateLimitAction
    action_duration_seconds: int | None = None
    enabled: bool = True
    priority: int = 0


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting system."""

    enable_default_rules: bool = True
    user_messages_per_minute: int = 10
    user_messages_per_hour: int = 100
    user_messages_per_day: int = 500
    guild_messages_per_minute: int = 1000
    guild_messages_per_hour: int = 10000
    channel_messages_per_minute: int = 100
    channel_messages_per_hour: int = 1000
    global_messages_per_minute: int = 10000
    global_messages_per_hour: int = 100000
    warn_threshold: float = 0.8
    action_threshold: float = 1.0
    cooldown_seconds: int = 60
    escalation_cooldown_seconds: int = 300
    cleanup_interval_seconds: int = 300
    max_storage_time_seconds: int = 86400


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    remaining_requests: int
    reset_time: float
    action_required: RateLimitAction | None
    warning_issued: bool
    metadata: dict[str, Any]


class RateLimiter:
    """Advanced rate limiting system for Discord interactions."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._user_requests: dict[str, deque] = defaultdict(lambda: deque())
        self._guild_requests: dict[str, deque] = defaultdict(lambda: deque())
        self._channel_requests: dict[str, deque] = defaultdict(lambda: deque())
        self._global_requests: deque = deque()
        self._rules: list[RateLimitRule] = []
        self._user_actions: dict[str, list[tuple[float, RateLimitAction]]] = defaultdict(list)
        self._guild_actions: dict[str, list[tuple[float, RateLimitAction]]] = defaultdict(list)
        self._channel_actions: dict[str, list[tuple[float, RateLimitAction]]] = defaultdict(list)
        self._user_cooldowns: dict[str, float] = {}
        self._guild_cooldowns: dict[str, float] = {}
        self._channel_cooldowns: dict[str, float] = {}
        self._stats = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "warnings_issued": 0,
            "actions_taken": 0,
            "cooldowns_activated": 0,
            "avg_check_time_ms": 0.0,
        }
        # Start background cleanup loop only if an event loop is running; otherwise, defer until first use
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(self._cleanup_loop())
        except RuntimeError:
            # No running loop (e.g., during object construction in sync context/tests)
            self._cleanup_task = None
        if config.enable_default_rules:
            self._setup_default_rules()

    async def check_rate_limit(
        self, user_id: str, guild_id: str | None = None, channel_id: str | None = None, request_type: str = "message"
    ) -> StepResult:
        """Check if request is within rate limits."""
        try:
            # Ensure cleanup loop is started when an event loop is available
            if getattr(self, "_cleanup_task", None) is None:
                try:
                    loop = asyncio.get_running_loop()
                    self._cleanup_task = loop.create_task(self._cleanup_loop())
                except RuntimeError:
                    # Still no running loop; proceed without background cleanup
                    pass
            start_time = time.time()
            await self._cleanup_old_data()
            cooldown_check = await self._check_cooldowns(user_id, guild_id, channel_id)
            if not cooldown_check.success:
                return cooldown_check
            for rule in sorted(self._rules, key=lambda r: r.priority, reverse=True):
                if not rule.enabled:
                    continue
                rule_result = await self._check_rule(rule, user_id, guild_id, channel_id)
                if not rule_result.allowed:
                    await self._record_violation(rule, user_id, guild_id, channel_id)
                    if rule_result.action_required:
                        await self._take_action(rule_result.action_required, user_id, guild_id, channel_id)
                    self._stats["rate_limited_requests"] += 1
                    return StepResult.fail(
                        f"Rate limit exceeded for {rule.name}", data={"rate_limit_result": rule_result}
                    )
                if rule_result.warning_issued:
                    await self._issue_warning(user_id, guild_id, channel_id, rule)
                    self._stats["warnings_issued"] += 1
            await self._record_request(user_id, guild_id, channel_id)
            self._stats["total_requests"] += 1
            processing_time = (time.time() - start_time) * 1000
            self._update_avg_check_time(processing_time)
            return StepResult.ok(data={"rate_limit_check": "passed"})
        except Exception as e:
            return StepResult.fail(f"Rate limit check failed: {e!s}")

    async def _check_rule(
        self, rule: RateLimitRule, user_id: str, guild_id: str | None, channel_id: str | None
    ) -> RateLimitResult:
        """Check a specific rate limit rule."""
        current_time = time.time()
        if rule.scope == RateLimitScope.USER:
            requests = self._user_requests[user_id]
        elif rule.scope == RateLimitScope.GUILD and guild_id:
            requests = self._guild_requests[guild_id]
        elif rule.scope == RateLimitScope.CHANNEL and channel_id:
            requests = self._channel_requests[channel_id]
        else:
            requests = self._global_requests
        window_start = current_time - rule.window_seconds
        while requests and requests[0] < window_start:
            requests.popleft()
        current_requests = len(requests)
        remaining_requests = max(0, rule.max_requests - current_requests)
        allowed = current_requests < rule.max_requests
        warning_threshold = rule.max_requests * self.config.warn_threshold
        warning_issued = current_requests >= warning_threshold and current_requests < rule.max_requests
        action_required = None
        if not allowed:
            action_required = rule.action
        reset_time = current_time + rule.window_seconds
        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining_requests,
            reset_time=reset_time,
            action_required=action_required,
            warning_issued=warning_issued,
            metadata={
                "rule_name": rule.name,
                "scope": rule.scope.value,
                "current_requests": current_requests,
                "max_requests": rule.max_requests,
                "window_seconds": rule.window_seconds,
            },
        )

    async def _check_cooldowns(self, user_id: str, guild_id: str | None, channel_id: str | None) -> StepResult:
        """Check if entity is in cooldown period."""
        current_time = time.time()
        if user_id in self._user_cooldowns:
            cooldown_end = self._user_cooldowns[user_id]
            if current_time < cooldown_end:
                remaining = cooldown_end - current_time
                return StepResult.fail(f"User in cooldown for {remaining:.1f} seconds")
        if guild_id and guild_id in self._guild_cooldowns:
            cooldown_end = self._guild_cooldowns[guild_id]
            if current_time < cooldown_end:
                remaining = cooldown_end - current_time
                return StepResult.fail(f"Guild in cooldown for {remaining:.1f} seconds")
        if channel_id and channel_id in self._channel_cooldowns:
            cooldown_end = self._channel_cooldowns[channel_id]
            if current_time < cooldown_end:
                remaining = cooldown_end - current_time
                return StepResult.fail(f"Channel in cooldown for {remaining:.1f} seconds")
        return StepResult.ok(data={"cooldown_check": "passed"})

    async def _record_request(self, user_id: str, guild_id: str | None, channel_id: str | None):
        """Record a successful request."""
        current_time = time.time()
        self._user_requests[user_id].append(current_time)
        if guild_id:
            self._guild_requests[guild_id].append(current_time)
        if channel_id:
            self._channel_requests[channel_id].append(current_time)
        self._global_requests.append(current_time)

    async def _record_violation(self, rule: RateLimitRule, user_id: str, guild_id: str | None, channel_id: str | None):
        """Record a rate limit violation."""
        current_time = time.time()
        if rule.scope == RateLimitScope.USER:
            self._user_actions[user_id].append((current_time, rule.action))
        elif rule.scope == RateLimitScope.GUILD and guild_id:
            self._guild_actions[guild_id].append((current_time, rule.action))
        elif rule.scope == RateLimitScope.CHANNEL and channel_id:
            self._channel_actions[channel_id].append((current_time, rule.action))

    async def _take_action(self, action: RateLimitAction, user_id: str, guild_id: str | None, channel_id: str | None):
        """Take moderation action for rate limit violation."""
        current_time = time.time()
        duration = None
        if action in [RateLimitAction.TEMP_MUTE, RateLimitAction.TEMP_BAN]:
            duration = self.config.escalation_cooldown_seconds
        cooldown_duration = duration or self.config.cooldown_seconds
        if user_id:
            self._user_cooldowns[user_id] = current_time + cooldown_duration
        if guild_id:
            self._guild_cooldowns[guild_id] = current_time + cooldown_duration
        if channel_id:
            self._channel_cooldowns[channel_id] = current_time + cooldown_duration
        self._stats["actions_taken"] += 1
        self._stats["cooldowns_activated"] += 1
        {
            "type": "rate_limit_cooldown",
            "user_id": user_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "action_type": action.value,
            "duration": cooldown_duration,
            "reason": f"Rate limit exceeded: {action.value}",
            "timestamp": time.time(),
        }

    async def _issue_warning(self, user_id: str, guild_id: str | None, channel_id: str | None, rule: RateLimitRule):
        """Issue a warning for approaching rate limit.

        Integration point: Requires Discord bot with SEND_MESSAGES permission.
        Implementation should send DM or channel message to user.

        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID (optional)
            channel_id: Discord channel ID (optional)
            rule: Rate limit rule that was approached
        """
        {
            "type": "rate_limit_warning",
            "user_id": user_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "content": f"⚠️ Warning: You are approaching the rate limit for {rule.name}. Please slow down.",
            "timestamp": time.time(),
        }

    async def _cleanup_old_data(self):
        """Clean up old request data."""
        current_time = time.time()
        cutoff_time = current_time - self.config.max_storage_time_seconds
        for user_id in list(self._user_requests.keys()):
            requests = self._user_requests[user_id]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self._user_requests[user_id]
        for guild_id in list(self._guild_requests.keys()):
            requests = self._guild_requests[guild_id]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self._guild_requests[guild_id]
        for channel_id in list(self._channel_requests.keys()):
            requests = self._channel_requests[channel_id]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self._channel_requests[channel_id]
        while self._global_requests and self._global_requests[0] < cutoff_time:
            self._global_requests.popleft()
        self._cleanup_old_actions(current_time)

    def _cleanup_old_actions(self, current_time: float):
        """Clean up old action records."""
        cutoff_time = current_time - self.config.max_storage_time_seconds
        for user_id in list(self._user_actions.keys()):
            actions = self._user_actions[user_id]
            self._user_actions[user_id] = [
                (timestamp, action) for timestamp, action in actions if timestamp > cutoff_time
            ]
            if not self._user_actions[user_id]:
                del self._user_actions[user_id]
        for guild_id in list(self._guild_actions.keys()):
            actions = self._guild_actions[guild_id]
            self._guild_actions[guild_id] = [
                (timestamp, action) for timestamp, action in actions if timestamp > cutoff_time
            ]
            if not self._guild_actions[guild_id]:
                del self._guild_actions[guild_id]
        for channel_id in list(self._channel_actions.keys()):
            actions = self._channel_actions[channel_id]
            self._channel_actions[channel_id] = [
                (timestamp, action) for timestamp, action in actions if timestamp > cutoff_time
            ]
            if not self._channel_actions[channel_id]:
                del self._channel_actions[channel_id]

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self._cleanup_old_data()
            except Exception as e:
                print(f"Cleanup error: {e}")

    def _setup_default_rules(self):
        """Setup default rate limiting rules."""
        default_rules = [
            RateLimitRule(
                name="user_messages_per_minute",
                scope=RateLimitScope.USER,
                max_requests=self.config.user_messages_per_minute,
                window_seconds=60,
                action=RateLimitAction.TEMP_MUTE,
                action_duration_seconds=300,
                priority=100,
            ),
            RateLimitRule(
                name="user_messages_per_hour",
                scope=RateLimitScope.USER,
                max_requests=self.config.user_messages_per_hour,
                window_seconds=3600,
                action=RateLimitAction.TEMP_MUTE,
                action_duration_seconds=1800,
                priority=90,
            ),
            RateLimitRule(
                name="guild_messages_per_minute",
                scope=RateLimitScope.GUILD,
                max_requests=self.config.guild_messages_per_minute,
                window_seconds=60,
                action=RateLimitAction.WARN,
                priority=80,
            ),
            RateLimitRule(
                name="channel_messages_per_minute",
                scope=RateLimitScope.CHANNEL,
                max_requests=self.config.channel_messages_per_minute,
                window_seconds=60,
                action=RateLimitAction.WARN,
                priority=70,
            ),
        ]
        self._rules.extend(default_rules)

    def add_rule(self, rule: RateLimitRule):
        """Add a custom rate limiting rule."""
        self._rules.append(rule)

    def remove_rule(self, rule_name: str):
        """Remove a rate limiting rule by name."""
        self._rules = [rule for rule in self._rules if rule.name != rule_name]

    def enable_rule(self, rule_name: str):
        """Enable a rate limiting rule."""
        for rule in self._rules:
            if rule.name == rule_name:
                rule.enabled = True
                break

    def disable_rule(self, rule_name: str):
        """Disable a rate limiting rule."""
        for rule in self._rules:
            if rule.name == rule_name:
                rule.enabled = False
                break

    def _update_avg_check_time(self, processing_time: float):
        """Update average check time statistics."""
        total_requests = self._stats["total_requests"]
        current_avg = self._stats["avg_check_time_ms"]
        if total_requests > 0:
            self._stats["avg_check_time_ms"] = (current_avg * (total_requests - 1) + processing_time) / total_requests
        else:
            self._stats["avg_check_time_ms"] = processing_time

    def get_statistics(self) -> dict[str, Any]:
        """Get rate limiting statistics."""
        return self._stats.copy()

    def get_user_status(self, user_id: str) -> dict[str, Any]:
        """Get current status for a specific user."""
        current_time = time.time()
        user_requests = self._user_requests.get(user_id, deque())
        while user_requests and user_requests[0] < current_time - 3600:
            user_requests.popleft()
        return {
            "user_id": user_id,
            "requests_last_hour": len(user_requests),
            "in_cooldown": user_id in self._user_cooldowns,
            "cooldown_until": self._user_cooldowns.get(user_id, None),
            "recent_actions": [
                {"timestamp": timestamp, "action": action.value}
                for timestamp, action in self._user_actions.get(user_id, [])
                if timestamp > current_time - 3600
            ],
        }

    async def close(self):
        """Clean up resources."""
        task = getattr(self, "_cleanup_task", None)
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def create_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
    """Create a rate limiter with the specified configuration."""
    if config is None:
        config = RateLimitConfig()
    return RateLimiter(config)
