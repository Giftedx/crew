"""Playwright browser automation tool for dynamic content scraping."""

from __future__ import annotations

import base64
from platform.core.step_result import ErrorCategory, ErrorContext, StepResult
from typing import Any
from urllib.parse import urlparse

from ultimate_discord_intelligence_bot.tools._base import BaseTool


try:
    from playwright.sync_api import Page, sync_playwright
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None
    PlaywrightTimeoutError = Exception


class PlaywrightAutomationTool(BaseTool[StepResult]):
    """Browser automation tool using Playwright for dynamic content.

    Enables scraping of JavaScript-rendered content, interacting with elements,
    taking screenshots, and extracting dynamic page content.
    """

    name: str = "playwright_automation"
    description: str = "Automate browser interactions using Playwright. Supports navigation, screenshots, content extraction, element interaction, and form filling on dynamic JavaScript-rendered websites."

    def _run(
        self,
        url: str,
        action: str = "screenshot",
        selector: str | None = None,
        text: str | None = None,
        wait_timeout: int = 30000,
        tenant: str = "default",
        workspace: str = "default",
        **kwargs: Any,
    ) -> StepResult:
        """Execute browser automation.

        Args:
            url: URL to navigate to
            action: Action to perform (screenshot, content, wait_for_selector, click, fill)
            selector: CSS selector for element interaction
            text: Text to fill in form fields
            wait_timeout: Wait timeout in milliseconds
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional arguments

        Returns:
            StepResult with automation results
        """
        if not PLAYWRIGHT_AVAILABLE:
            return StepResult.fail(
                "Playwright not available. Install with: pip install playwright && playwright install",
                error_category=ErrorCategory.DEPENDENCY,
                error_context=ErrorContext(
                    operation="browser_automation",
                    component="playwright_automation",
                    additional_context={"dependency": "playwright"},
                ),
            )
        validation_result = self._validate_inputs(url=url, action=action, selector=selector, **kwargs)
        if validation_result:
            return validation_result
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.set_default_timeout(wait_timeout)
                    page.goto(url, wait_until="networkidle", timeout=wait_timeout)
                    result = self._execute_action(page, action, selector, text, tenant, workspace)
                    return result
                finally:
                    browser.close()
        except PlaywrightTimeoutError as e:
            return StepResult.fail(
                f"Timeout waiting for page to load: {e!s}",
                error_category=ErrorCategory.TIMEOUT,
                error_context=ErrorContext(
                    operation="navigation",
                    component="playwright_automation",
                    additional_context={"url": url, "timeout": wait_timeout},
                ),
            )
        except Exception as e:
            return StepResult.fail(
                f"Browser automation failed: {e!s}",
                error_category=ErrorCategory.PROCESSING,
                error_context=ErrorContext(
                    operation="browser_automation",
                    component="playwright_automation",
                    additional_context={"url": url, "action": action, "exception_type": type(e).__name__},
                ),
            )

    def _validate_inputs(self, url: str, action: str, selector: str | None = None, **kwargs: Any) -> StepResult | None:
        """Validate tool inputs."""
        if not url or not isinstance(url, str):
            return StepResult.fail(
                "URL must be a non-empty string",
                error_category=ErrorCategory.INVALID_INPUT,
                error_context=ErrorContext(operation="validation", component="playwright_automation"),
            )
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return StepResult.fail(
                    "Invalid URL format",
                    error_category=ErrorCategory.INVALID_INPUT,
                    error_context=ErrorContext(operation="validation", component="playwright_automation"),
                )
        except Exception as e:
            return StepResult.fail(
                f"URL parsing failed: {e!s}",
                error_category=ErrorCategory.INVALID_INPUT,
                error_context=ErrorContext(operation="validation", component="playwright_automation"),
            )
        valid_actions = {"screenshot", "content", "wait_for_selector", "click", "fill"}
        if action not in valid_actions:
            return StepResult.fail(
                f"Invalid action. Must be one of: {', '.join(valid_actions)}",
                error_category=ErrorCategory.INVALID_INPUT,
                error_context=ErrorContext(operation="validation", component="playwright_automation"),
            )
        if action in {"wait_for_selector", "click", "fill"} and (not selector):
            return StepResult.fail(
                f"Selector required for action: {action}",
                error_category=ErrorCategory.INVALID_INPUT,
                error_context=ErrorContext(operation="validation", component="playwright_automation"),
            )
        return None

    def _execute_action(
        self, page: Page, action: str, selector: str | None, text: str | None, tenant: str, workspace: str
    ) -> StepResult:
        """Execute browser action."""
        try:
            if action == "screenshot":
                screenshot_bytes = page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                return StepResult.ok(
                    data={
                        "screenshot": screenshot_b64,
                        "url": page.url,
                        "title": page.title(),
                        "tenant": tenant,
                        "workspace": workspace,
                    }
                )
            elif action == "content":
                content = {
                    "url": page.url,
                    "title": page.title(),
                    "html": page.content(),
                    "text": page.inner_text("body"),
                    "tenant": tenant,
                    "workspace": workspace,
                }
                return StepResult.ok(data=content)
            elif action == "wait_for_selector":
                if not selector:
                    return StepResult.fail("Selector required for wait_for_selector")
                page.wait_for_selector(selector)
                element_text = page.inner_text(selector)
                return StepResult.ok(
                    data={
                        "url": page.url,
                        "selector": selector,
                        "element_text": element_text,
                        "tenant": tenant,
                        "workspace": workspace,
                    }
                )
            elif action == "click":
                if not selector:
                    return StepResult.fail("Selector required for click")
                page.click(selector)
                return StepResult.ok(
                    data={
                        "url": page.url,
                        "selector": selector,
                        "action": "clicked",
                        "tenant": tenant,
                        "workspace": workspace,
                    }
                )
            elif action == "fill":
                if not selector or not text:
                    return StepResult.fail("Selector and text required for fill")
                page.fill(selector, text)
                return StepResult.ok(
                    data={
                        "url": page.url,
                        "selector": selector,
                        "text": text,
                        "action": "filled",
                        "tenant": tenant,
                        "workspace": workspace,
                    }
                )
            else:
                return StepResult.fail(f"Unknown action: {action}", error_category=ErrorCategory.INVALID_INPUT)
        except Exception as e:
            return StepResult.fail(
                f"Action execution failed: {e!s}",
                error_category=ErrorCategory.PROCESSING,
                error_context=ErrorContext(
                    operation="action_execution",
                    component="playwright_automation",
                    additional_context={"action": action, "exception_type": type(e).__name__},
                ),
            )
