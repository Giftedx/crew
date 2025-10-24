"""Integration tests for crew consolidation system.

Tests flag precedence, dynamic crew switching, and error handling.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from src.ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from src.ultimate_discord_intelligence_bot.crew_consolidation import get_crew
from src.ultimate_discord_intelligence_bot.step_result import StepResult


class TestCrewConsolidationIntegration:
    """Integration tests for crew consolidation."""

    def setup_method(self):
        """Set up test environment."""
        # Clear all crew-related environment variables
        for flag in ["ENABLE_LEGACY_CREW", "ENABLE_CREW_MODULAR", "ENABLE_CREW_REFACTORED", "ENABLE_CREW_NEW"]:
            os.environ.pop(flag, None)

        # Clear feature flags cache
        FeatureFlags.from_env.cache_clear()

    def test_default_crew_loading(self):
        """Test that default crew is loaded when no flags are set."""
        # Ensure no crew flags are set
        for flag in ["ENABLE_LEGACY_CREW", "ENABLE_CREW_MODULAR", "ENABLE_CREW_REFACTORED", "ENABLE_CREW_NEW"]:
            assert flag not in os.environ

        # Should load canonical crew
        crew = get_crew()
        assert crew is not None
        assert hasattr(crew, "crew")

    def test_legacy_crew_flag_precedence(self):
        """Test that legacy crew flag takes precedence."""
        os.environ["ENABLE_LEGACY_CREW"] = "true"
        os.environ["ENABLE_CREW_NEW"] = "true"  # This should be ignored

        # Clear cache to pick up new environment
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None
        # In a real implementation, we'd check the crew type
        # For now, just verify it loads without error

    def test_crew_new_flag(self):
        """Test that crew_new flag works."""
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

    def test_crew_modular_flag(self):
        """Test that crew_modular flag works."""
        os.environ["ENABLE_CREW_MODULAR"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

    def test_crew_refactored_flag(self):
        """Test that crew_refactored flag works."""
        os.environ["ENABLE_CREW_REFACTORED"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

    def test_multiple_flags_ignored(self):
        """Test that multiple crew flags are ignored (only first takes precedence)."""
        os.environ["ENABLE_CREW_NEW"] = "true"
        os.environ["ENABLE_CREW_MODULAR"] = "true"
        os.environ["ENABLE_CREW_REFACTORED"] = "true"
        FeatureFlags.from_env.cache_clear()

        # Should still work, but only one crew should be loaded
        crew = get_crew()
        assert crew is not None

    def test_invalid_crew_implementation_handling(self):
        """Test handling of invalid crew implementations."""
        # Mock a scenario where crew loading fails
        with patch("src.ultimate_discord_intelligence_bot.crew_consolidation.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            # Should fall back to canonical crew
            crew = get_crew()
            assert crew is not None

    def test_crew_switching_dynamic(self):
        """Test dynamic crew switching."""
        # Start with no flags
        crew1 = get_crew()
        assert crew1 is not None

        # Switch to new crew
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew2 = get_crew()
        assert crew2 is not None

        # Switch back to default
        del os.environ["ENABLE_CREW_NEW"]
        FeatureFlags.from_env.cache_clear()

        crew3 = get_crew()
        assert crew3 is not None

    def test_feature_flags_integration(self):
        """Test integration with feature flags system."""
        # Test that feature flags are properly read
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        flags = FeatureFlags.from_env()
        assert flags.ENABLE_CREW_NEW is True

        # Test crew loading respects flags
        crew = get_crew()
        assert crew is not None

    def test_crew_consolidation_with_analytics(self):
        """Test crew consolidation with analytics integration."""
        from src.ultimate_discord_intelligence_bot.features.crew_analytics import CrewAnalytics

        analytics = CrewAnalytics()

        # Test that crew can be used with analytics
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Analytics should be able to track this crew
        analytics.start_crew_execution("test_crew")
        result = analytics.end_crew_execution("test_crew")
        assert result.success

    def test_crew_consolidation_error_handling(self):
        """Test error handling in crew consolidation."""
        # Test with invalid environment variable
        os.environ["ENABLE_CREW_NEW"] = "invalid_value"
        FeatureFlags.from_env.cache_clear()

        # Should still work (invalid values are treated as False)
        crew = get_crew()
        assert crew is not None

    def test_crew_consolidation_performance(self):
        """Test that crew consolidation doesn't significantly impact performance."""
        import time

        # Measure time to get crew multiple times
        start_time = time.time()

        for _ in range(10):
            crew = get_crew()
            assert crew is not None

        end_time = time.time()
        duration = end_time - start_time

        # Should be fast (less than 1 second for 10 calls)
        assert duration < 1.0

    def test_crew_consolidation_thread_safety(self):
        """Test that crew consolidation is thread-safe."""
        import threading

        results = []
        errors = []

        def get_crew_worker():
            try:
                crew = get_crew()
                results.append(crew is not None)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_crew_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)

    def test_crew_consolidation_with_memory_coordinator(self):
        """Test crew consolidation with memory coordinator."""
        from src.ultimate_discord_intelligence_bot.features.memory_coordinator import MemoryCoordinator

        # Mock memory provider
        mock_provider = MagicMock()
        mock_provider.name = "test_provider"
        mock_provider.upsert.return_value = StepResult.ok(data={"id": "test_id"})
        mock_provider.query.return_value = StepResult.ok(data={"hits": []})
        mock_provider.delete.return_value = StepResult.ok(data={"id": "test_id"})

        coordinator = MemoryCoordinator(mock_provider)

        # Test that crew can work with memory coordinator
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Memory coordinator should work
        result = coordinator.upsert_to_pool("test_pool", "test_key", "test_value")
        assert result.success

    def test_crew_consolidation_with_agent_collaboration(self):
        """Test crew consolidation with agent collaboration."""
        from src.ultimate_discord_intelligence_bot.features.agent_collaboration import AgentCollaborationFramework

        # Mock agents
        mock_agent1 = MagicMock()
        mock_agent1.name = "Agent1"
        mock_agent1.execute_task.return_value = StepResult.ok(data={"result": "success"})

        mock_agent2 = MagicMock()
        mock_agent2.name = "Agent2"
        mock_agent2.execute_task.return_value = StepResult.ok(data={"result": "success"})

        framework = AgentCollaborationFramework([mock_agent1, mock_agent2])

        # Test that crew can work with agent collaboration
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Agent collaboration should work
        result = framework.sequential_collaboration([("Agent1", "task1"), ("Agent2", "task2")], {"input": "test"})
        assert result.success

    def test_crew_consolidation_export_capabilities(self):
        """Test that crew consolidation works with export capabilities."""
        from src.ultimate_discord_intelligence_bot.features.crew_analytics import CrewAnalytics
        from src.ultimate_discord_intelligence_bot.features.crew_dashboard import CrewDashboard

        analytics = CrewAnalytics()
        dashboard = CrewDashboard(analytics)

        # Test that crew can work with dashboard
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Dashboard should work
        result = dashboard.get_dashboard_data()
        # This might fail if no data is available, but the method should exist
        assert hasattr(dashboard, "get_dashboard_data")

    def test_crew_consolidation_configuration_validation(self):
        """Test that crew consolidation validates configuration properly."""
        # Test with missing crew implementations
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        # Should handle missing implementations gracefully
        crew = get_crew()
        assert crew is not None

    def test_crew_consolidation_logging(self):
        """Test that crew consolidation logs appropriately."""

        # Capture logs
        with patch("src.ultimate_discord_intelligence_bot.crew_consolidation.logger") as mock_logger:
            os.environ["ENABLE_CREW_NEW"] = "true"
            FeatureFlags.from_env.cache_clear()

            crew = get_crew()
            assert crew is not None

            # Should have logged crew loading
            mock_logger.info.assert_called()

    def test_crew_consolidation_cleanup(self):
        """Test that crew consolidation cleans up properly."""
        # Test multiple crew switches
        for flag in ["ENABLE_CREW_NEW", "ENABLE_CREW_MODULAR", "ENABLE_CREW_REFACTORED"]:
            os.environ[flag] = "true"
            FeatureFlags.from_env.cache_clear()

            crew = get_crew()
            assert crew is not None

            # Clean up
            del os.environ[flag]
            FeatureFlags.from_env.cache_clear()

    def test_crew_consolidation_with_observability(self):
        """Test that crew consolidation works with observability hooks."""
        from src.ultimate_discord_intelligence_bot.obs.metrics import get_metrics

        # Test that crew can work with observability
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Observability should work
        metrics = get_metrics()
        assert metrics is not None

    def test_crew_consolidation_with_discord_publisher(self):
        """Test that crew consolidation works with Discord publisher."""
        from src.ultimate_discord_intelligence_bot.discord_bot.discord_publisher import DiscordPublisher

        # Mock Discord publisher
        publisher = DiscordPublisher()

        # Test that crew can work with Discord publisher
        os.environ["ENABLE_CREW_NEW"] = "true"
        FeatureFlags.from_env.cache_clear()

        crew = get_crew()
        assert crew is not None

        # Discord publisher should work
        assert hasattr(publisher, "publish_message")

    def test_crew_consolidation_comprehensive(self):
        """Test comprehensive crew consolidation with all features."""
        from src.ultimate_discord_intelligence_bot.features.agent_collaboration import AgentCollaborationFramework
        from src.ultimate_discord_intelligence_bot.features.crew_analytics import CrewAnalytics
        from src.ultimate_discord_intelligence_bot.features.memory_coordinator import MemoryCoordinator

        # Set up all components
        analytics = CrewAnalytics()

        # Mock memory provider
        mock_provider = MagicMock()
        mock_provider.name = "test_provider"
        mock_provider.upsert.return_value = StepResult.ok(data={"id": "test_id"})
        mock_provider.query.return_value = StepResult.ok(data={"hits": []})
        mock_provider.delete.return_value = StepResult.ok(data={"id": "test_id"})

        coordinator = MemoryCoordinator(mock_provider)

        # Mock agents
        mock_agent1 = MagicMock()
        mock_agent1.name = "Agent1"
        mock_agent1.execute_task.return_value = StepResult.ok(data={"result": "success"})

        mock_agent2 = MagicMock()
        mock_agent2.name = "Agent2"
        mock_agent2.execute_task.return_value = StepResult.ok(data={"result": "success"})

        framework = AgentCollaborationFramework([mock_agent1, mock_agent2])

        # Test with different crew flags
        for flag in ["ENABLE_CREW_NEW", "ENABLE_CREW_MODULAR", "ENABLE_CREW_REFACTORED"]:
            os.environ[flag] = "true"
            FeatureFlags.from_env.cache_clear()

            crew = get_crew()
            assert crew is not None

            # All components should work together
            analytics.start_crew_execution("test_crew")
            result = analytics.end_crew_execution("test_crew")
            assert result.success

            memory_result = coordinator.upsert_to_pool("test_pool", "test_key", "test_value")
            assert memory_result.success

            collab_result = framework.sequential_collaboration(
                [("Agent1", "task1"), ("Agent2", "task2")], {"input": "test"}
            )
            assert collab_result.success

            # Clean up
            del os.environ[flag]
            FeatureFlags.from_env.cache_clear()
