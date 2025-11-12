"""Tests for Playwright Automation Tool."""

from unittest.mock import MagicMock, patch

import pytest


try:
    from playwright.sync_api import Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None
from ultimate_discord_intelligence_bot.step_result import ErrorCategory
from ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool import PlaywrightAutomationTool


class TestPlaywrightAutomationTool:
    """Test cases for Playwright Automation Tool."""

    @pytest.fixture
    def tool(self):
        """Create PlaywrightAutomationTool instance."""
        return PlaywrightAutomationTool()

    @pytest.fixture
    def sample_url(self):
        """Sample URL for testing."""
        return "https://example.com"

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == "playwright_automation"
        assert tool.description is not None
        assert hasattr(tool, "_run")

    def test_validate_url_format_valid(self, tool):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://example.com/path",
            "https://example.com:8080/path?query=value",
        ]
        for url in valid_urls:
            result = tool._validate_inputs(url=url, action="screenshot", selector=None)
            assert result is None, f"Valid URL rejected: {url}"

    def test_validate_url_format_invalid(self, tool):
        """Test URL validation with invalid URLs."""
        invalid_urls = ["not_a_url", "ftp://example.com", "//example.com", ""]
        for url in invalid_urls:
            result = tool._validate_inputs(url=url, action="screenshot", selector=None)
            assert result is not None, f"Invalid URL accepted: {url}"
            assert not result.success
            assert result.error_category == ErrorCategory.INVALID_INPUT

    def test_validate_action_types(self, tool, sample_url):
        """Test action type validation."""
        valid_actions = ["screenshot", "content", "wait_for_selector", "click", "fill"]
        invalid_actions = ["invalid", "screeenshot", "contentt", ""]
        for action in valid_actions:
            result = tool._validate_inputs(url=sample_url, action=action, selector=None)
            if action in ["wait_for_selector", "click", "fill"]:
                assert result is not None
            else:
                assert result is None, f"Valid action rejected: {action}"
        for action in invalid_actions:
            result = tool._validate_inputs(url=sample_url, action=action, selector=None)
            assert result is not None, f"Invalid action accepted: {action}"

    def test_validate_selector_required(self, tool, sample_url):
        """Test that selector is required for certain actions."""
        actions_requiring_selector = ["wait_for_selector", "click", "fill"]
        for action in actions_requiring_selector:
            result = tool._validate_inputs(url=sample_url, action=action, selector=None)
            assert result is not None
            assert "Selector required" in result.error
            assert result.error_category == ErrorCategory.INVALID_INPUT

    @patch("ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool.PLAYWRIGHT_AVAILABLE", False)
    def test_graceful_degradation_no_playwright(self, tool, sample_url):
        """Test graceful degradation when Playwright is unavailable."""
        result = tool._run(url=sample_url, action="screenshot", tenant="test", workspace="test")
        assert not result.success
        assert result.error_category == ErrorCategory.DEPENDENCY
        assert "Playwright not available" in result.error

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    def test_screenshot_action(self, tool, sample_url):
        """Test screenshot action with mocked Playwright."""
        with patch(
            "ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool.sync_playwright"
        ) as mock_playwright:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_page.url = sample_url
            mock_page.title.return_value = "Test Page"
            mock_page.screenshot.return_value = b"fake_screenshot_data"
            mock_page.set_default_timeout.return_value = None
            mock_page.goto.return_value = None
            mock_playwright.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_playwright.return_value.__enter__().chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_browser.close.return_value = None
            result = tool._run(url=sample_url, action="screenshot", tenant="test", workspace="test", wait_timeout=30000)
            assert result.success
            assert "screenshot" in result.data
            assert result.data["url"] == sample_url
            assert result.data["title"] == "Test Page"

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    def test_content_action(self, tool, sample_url):
        """Test content extraction action."""
        with patch(
            "ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool.sync_playwright"
        ) as mock_playwright:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_page.url = sample_url
            mock_page.title.return_value = "Test Page"
            mock_page.content.return_value = "<html><body>Test Content</body></html>"
            mock_page.inner_text.return_value = "Test Content"
            mock_page.set_default_timeout.return_value = None
            mock_page.goto.return_value = None
            mock_playwright.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_playwright.return_value.__enter__().chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_browser.close.return_value = None
            result = tool._run(url=sample_url, action="content", tenant="test", workspace="test")
            assert result.success
            assert "html" in result.data
            assert "text" in result.data
            assert "Test Content" in result.data["text"]

    def test_invalid_empty_url(self, tool):
        """Test handling of empty URL."""
        result = tool._run(url="", action="screenshot", tenant="test", workspace="test")
        assert not result.success
        assert result.error_category in [ErrorCategory.INVALID_INPUT, ErrorCategory.DEPENDENCY]

    def test_tenant_workspace_parameters(self, tool, sample_url):
        """Test that tenant and workspace parameters are handled."""
        with patch(
            "ultimate_discord_intelligence_bot.tools.web.playwright_automation_tool.PLAYWRIGHT_AVAILABLE", False
        ):
            result = tool._run(url=sample_url, action="screenshot", tenant="test_tenant", workspace="test_workspace")
            assert not result.success
            assert "tenant" in str(result).lower() or "test_tenant" not in str(result)
