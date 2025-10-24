"""Integration tests for Discord AI safety and moderation system."""

import pytest

from src.discord.safety import (
    AlertConfig,
    AlertSeverity,
    AlertType,
    ContentFilterConfig,
    RateLimitConfig,
    create_content_filter,
    create_moderation_alert_manager,
    create_rate_limiter,
    create_safety_manager,
)


class TestContentFilter:
    """Test content filtering functionality."""

    @pytest.fixture
    def content_filter(self):
        """Create a content filter for testing."""
        config = ContentFilterConfig(
            low_risk_threshold=0.3,
            medium_risk_threshold=0.6,
            high_risk_threshold=0.8,
            critical_threshold=0.9,
        )
        return create_content_filter(config)

    @pytest.mark.asyncio
    async def test_safe_content_passes(self, content_filter):
        """Test that safe content passes filtering."""
        result = await content_filter.filter_content(
            content="Hello, how are you today?", user_id="test_user", guild_id="test_guild"
        )

        assert result.success
        filter_result = result.data["filter_result"]
        assert filter_result.is_safe
        assert filter_result.severity.value == "safe"
        assert not filter_result.categories

    @pytest.mark.asyncio
    async def test_spam_content_detected(self, content_filter):
        """Test that spam content is detected."""
        spam_content = "BUY NOW! CLICK HERE! FREE MONEY! BUY NOW! CLICK HERE!"

        result = await content_filter.filter_content(content=spam_content, user_id="test_user", guild_id="test_guild")

        assert result.success
        filter_result = result.data["filter_result"]
        assert not filter_result.is_safe
        assert "spam" in [cat.value for cat in filter_result.categories]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, content_filter):
        """Test rate limiting functionality."""
        user_id = "test_user"

        # Send multiple messages quickly
        for i in range(15):  # Exceed the default limit of 10 per minute
            result = await content_filter.filter_content(
                content=f"Test message {i}", user_id=user_id, guild_id="test_guild"
            )

            if i >= 10:  # Should hit rate limit
                assert not result.success
                assert "rate limit" in result.error.lower()
                break
            else:
                assert result.success

    @pytest.mark.asyncio
    async def test_caching(self, content_filter):
        """Test content filtering caching."""
        content = "This is a test message"
        user_id = "test_user"

        # First request
        result1 = await content_filter.filter_content(content, user_id, "test_guild")
        assert result1.success

        # Second request (should be cached)
        result2 = await content_filter.filter_content(content, user_id, "test_guild")
        assert result2.success

        # Check that cache was used
        stats = content_filter.get_statistics()
        assert stats["cache_hits"] >= 1


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        config = RateLimitConfig(
            user_messages_per_minute=5,
            user_messages_per_hour=50,
            cooldown_seconds=60,
        )
        return create_rate_limiter(config)

    @pytest.mark.asyncio
    async def test_rate_limit_check_passes(self, rate_limiter):
        """Test that requests within limits pass."""
        result = await rate_limiter.check_rate_limit(
            user_id="test_user", guild_id="test_guild", channel_id="test_channel"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test that exceeding rate limits is detected."""
        user_id = "test_user"

        # Send requests up to the limit
        for i in range(5):
            result = await rate_limiter.check_rate_limit(
                user_id=user_id, guild_id="test_guild", channel_id="test_channel"
            )
            assert result.success

        # Next request should be rate limited
        result = await rate_limiter.check_rate_limit(user_id=user_id, guild_id="test_guild", channel_id="test_channel")

        assert not result.success
        assert "rate limit" in result.error.lower()

    @pytest.mark.asyncio
    async def test_user_status(self, rate_limiter):
        """Test getting user status."""
        user_id = "test_user"

        # Check initial status
        status = rate_limiter.get_user_status(user_id)
        assert status["user_id"] == user_id
        assert status["requests_last_hour"] == 0
        assert not status["in_cooldown"]

        # Make a request
        await rate_limiter.check_rate_limit(user_id, "test_guild", "test_channel")

        # Check updated status
        status = rate_limiter.get_user_status(user_id)
        assert status["requests_last_hour"] == 1

    @pytest.mark.asyncio
    async def test_statistics(self, rate_limiter):
        """Test rate limiter statistics."""
        stats = rate_limiter.get_statistics()
        assert "total_requests" in stats
        assert "rate_limited_requests" in stats
        assert "avg_check_time_ms" in stats


class TestModerationAlertManager:
    """Test moderation alert functionality."""

    @pytest.fixture
    def alert_manager(self):
        """Create an alert manager for testing."""
        config = AlertConfig(
            enable_alerts=True,
            auto_escalate_threshold=3,
            escalation_time_window=60,
        )
        return create_moderation_alert_manager(config)

    @pytest.mark.asyncio
    async def test_create_alert(self, alert_manager):
        """Test creating a moderation alert."""
        result = await alert_manager.create_alert(
            alert_type=AlertType.HARASSMENT,
            severity=AlertSeverity.HIGH,
            user_id="test_user",
            content="Test harassment content",
            guild_id="test_guild",
            channel_id="test_channel",
            message_id="test_message",
            metadata={"test": "data"},
        )

        assert result.success
        assert "alert_id" in result.data

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_manager):
        """Test acknowledging an alert."""
        # Create an alert first
        create_result = await alert_manager.create_alert(
            alert_type=AlertType.SPAM_DETECTED,
            severity=AlertSeverity.MEDIUM,
            user_id="test_user",
            content="Spam content",
            guild_id="test_guild",
        )

        alert_id = create_result.data["alert_id"]

        # Acknowledge the alert
        result = await alert_manager.acknowledge_alert(alert_id, "moderator_1")
        assert result.success

    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_manager):
        """Test resolving an alert."""
        # Create an alert first
        create_result = await alert_manager.create_alert(
            alert_type=AlertType.NSFW_CONTENT,
            severity=AlertSeverity.HIGH,
            user_id="test_user",
            content="NSFW content",
            guild_id="test_guild",
        )

        alert_id = create_result.data["alert_id"]

        # Resolve the alert
        result = await alert_manager.resolve_alert(alert_id, "moderator_1", "Content removed and user warned")
        assert result.success

    @pytest.mark.asyncio
    async def test_get_pending_alerts(self, alert_manager):
        """Test getting pending alerts."""
        # Create a few alerts
        for i in range(3):
            await alert_manager.create_alert(
                alert_type=AlertType.CONTENT_VIOLATION,
                severity=AlertSeverity.MEDIUM,
                user_id=f"test_user_{i}",
                content=f"Test content {i}",
                guild_id="test_guild",
            )

        # Get pending alerts
        result = await alert_manager.get_pending_alerts()
        assert result.success
        assert len(result.data["pending_alerts"]) >= 3

    @pytest.mark.asyncio
    async def test_auto_escalation(self, alert_manager):
        """Test automatic escalation."""
        user_id = "test_user"

        # Create multiple alerts for the same user
        for i in range(4):  # Exceed threshold of 3
            await alert_manager.create_alert(
                alert_type=AlertType.HARASSMENT,
                severity=AlertSeverity.MEDIUM,
                user_id=user_id,
                content=f"Harassment content {i}",
                guild_id="test_guild",
            )

        # Check that alerts were escalated
        user_alerts = await alert_manager.get_user_alerts(user_id)
        assert user_alerts.success

        alerts = user_alerts.data["alerts"]
        escalated_alerts = [alert for alert in alerts if alert["status"] == "escalated"]
        assert len(escalated_alerts) > 0

    @pytest.mark.asyncio
    async def test_statistics(self, alert_manager):
        """Test alert manager statistics."""
        stats = alert_manager.get_statistics()
        assert "total_alerts_generated" in stats
        assert "alerts_by_type" in stats
        assert "alerts_by_severity" in stats


class TestSafetyManager:
    """Test integrated safety management."""

    @pytest.fixture
    def safety_manager(self):
        """Create a safety manager for testing."""
        return create_safety_manager()

    @pytest.mark.asyncio
    async def test_safe_message_processing(self, safety_manager):
        """Test processing a safe message."""
        result = await safety_manager.process_message(
            content="Hello, this is a safe message",
            user_id="test_user",
            guild_id="test_guild",
            channel_id="test_channel",
            message_id="test_message",
        )

        assert result.success
        assert result.data["safety_check"] == "passed"
        assert "rate_limit" in result.data["checks_performed"]
        assert "content_filter" in result.data["checks_performed"]

    @pytest.mark.asyncio
    async def test_unsafe_content_filtering(self, safety_manager):
        """Test filtering of unsafe content."""
        result = await safety_manager.process_message(
            content="BUY NOW! CLICK HERE! FREE MONEY! SPAM SPAM SPAM!",
            user_id="test_user",
            guild_id="test_guild",
            channel_id="test_channel",
            message_id="test_message",
        )

        assert not result.success
        assert result.data["safety_check"] == "failed"
        assert result.data["reason"] == "content_filtered"
        assert "filter_result" in result.data

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, safety_manager):
        """Test rate limit enforcement."""
        user_id = "test_user"

        # Send multiple messages quickly to trigger rate limiting
        for i in range(12):  # Exceed default limit
            result = await safety_manager.process_message(
                content=f"Test message {i}", user_id=user_id, guild_id="test_guild", channel_id="test_channel"
            )

            if i >= 10:  # Should hit rate limit
                assert not result.success
                assert result.data["reason"] == "rate_limit"
                break
            else:
                assert result.success

    @pytest.mark.asyncio
    async def test_user_safety_status(self, safety_manager):
        """Test getting user safety status."""
        user_id = "test_user"

        # Process a few messages
        for i in range(3):
            await safety_manager.process_message(
                content=f"Test message {i}", user_id=user_id, guild_id="test_guild", channel_id="test_channel"
            )

        # Get safety status
        result = await safety_manager.get_user_safety_status(user_id)
        assert result.success

        status = result.data
        assert status["user_id"] == user_id
        assert "rate_limit_status" in status
        assert "recent_alerts" in status
        assert "safety_score" in status
        assert 0 <= status["safety_score"] <= 100

    @pytest.mark.asyncio
    async def test_guild_safety_overview(self, safety_manager):
        """Test getting guild safety overview."""
        guild_id = "test_guild"

        # Process some messages to generate data
        for i in range(5):
            await safety_manager.process_message(
                content=f"Test message {i}", user_id=f"test_user_{i}", guild_id=guild_id, channel_id="test_channel"
            )

        # Get safety overview
        result = await safety_manager.get_guild_safety_overview(guild_id)
        assert result.success

        overview = result.data
        assert overview["guild_id"] == guild_id
        assert "total_alerts" in overview
        assert "pending_alerts" in overview
        assert "safety_metrics" in overview
        assert "safety_score" in overview["safety_metrics"]

    @pytest.mark.asyncio
    async def test_safety_statistics(self, safety_manager):
        """Test getting comprehensive safety statistics."""
        # Process some messages
        for i in range(3):
            await safety_manager.process_message(
                content=f"Test message {i}", user_id=f"test_user_{i}", guild_id="test_guild", channel_id="test_channel"
            )

        stats = safety_manager.get_safety_statistics()

        assert "safety_manager" in stats
        assert "content_filter" in stats
        assert "rate_limiter" in stats
        assert "alert_manager" in stats

        # Check specific metrics
        assert stats["safety_manager"]["total_messages_processed"] >= 3

    @pytest.mark.asyncio
    async def test_auto_actions_configuration(self, safety_manager):
        """Test configuring auto actions."""
        # Test default configuration
        result = await safety_manager.process_message(
            content="BUY NOW! SPAM!", user_id="test_user", guild_id="test_guild", channel_id="test_channel"
        )

        # Should fail due to content filtering
        assert not result.success

        # Disable auto content filtering
        safety_manager.configure_auto_actions(auto_filter_content=False)

        # Same message should now pass
        result = await safety_manager.process_message(
            content="BUY NOW! SPAM!", user_id="test_user", guild_id="test_guild", channel_id="test_channel"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_cleanup(self, safety_manager):
        """Test proper cleanup of resources."""
        # This should not raise any exceptions
        await safety_manager.close()


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete safety workflow integration."""
    # Create safety manager
    safety_manager = create_safety_manager()

    try:
        # Test normal user workflow
        safe_result = await safety_manager.process_message(
            content="Hello everyone! How's your day going?",
            user_id="normal_user",
            guild_id="test_guild",
            channel_id="general",
        )
        assert safe_result.success

        # Test problematic user workflow
        for i in range(12):  # Trigger rate limiting
            result = await safety_manager.process_message(
                content="SPAM MESSAGE! BUY NOW!", user_id="spam_user", guild_id="test_guild", channel_id="general"
            )

            if i < 10:
                # First few should be content filtered
                assert not result.success
                assert result.data["reason"] == "content_filtered"
            else:
                # Later ones should be rate limited
                assert not result.success
                assert result.data["reason"] == "rate_limit"
                break

        # Verify alerts were created
        pending_alerts = await safety_manager.alert_manager.get_pending_alerts()
        assert pending_alerts.success
        assert len(pending_alerts.data["pending_alerts"]) > 0

        # Check statistics
        stats = safety_manager.get_safety_statistics()
        assert stats["safety_manager"]["total_messages_processed"] > 0
        assert stats["safety_manager"]["messages_filtered"] > 0
        assert stats["safety_manager"]["rate_limits_hit"] > 0
        assert stats["safety_manager"]["alerts_generated"] > 0

    finally:
        await safety_manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
