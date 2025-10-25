"""Integration tests for Playwright Automation Tool against real web pages."""

import pytest

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")


class TestPlaywrightAutomationIntegration:
    """Integration tests for Playwright Automation Tool."""

    def test_screenshot_capture_simple_page(self):
        """Test screenshot capture of a simple web page."""
        from ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool import PlaywrightAutomationTool
        
        tool = PlaywrightAutomationTool()
        
        result = tool._run(
            url="https://example.com",
            action="screenshot",
            tenant="test",
            workspace="test"
        )
        
        assert result.success
        assert "screenshot" in result.data
        assert len(result.data["screenshot"]) > 0  # Base64 encoded screenshot

    def test_content_extraction_simple_page(self):
        """Test content extraction from a simple web page."""
        from ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool import PlaywrightAutomationTool
        
        tool = PlaywrightAutomationTool()
        
        result = tool._run(
            url="https://example.com",
            action="content",
            tenant="test",
            workspace="test"
        )
        
        assert result.success
        assert "html" in result.data
        assert "text" in result.data
        assert "Example Domain" in result.data["text"]

    def test_performance_latency(self):
        """Test that automation completes within acceptable time limits."""
        import time
        from ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool import PlaywrightAutomationTool
        
        tool = PlaywrightAutomationTool()
        
        start_time = time.time()
        result = tool._run(
            url="https://example.com",
            action="screenshot",
            tenant="test",
            workspace="test"
        )
        elapsed_time = time.time() - start_time
        
        assert result.success
        assert elapsed_time < 10.0, f"Automation took {elapsed_time}s, exceeds 10s limit"

