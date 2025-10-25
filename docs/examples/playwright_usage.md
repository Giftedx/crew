# Playwright Automation Tool - Usage Examples

This document provides practical examples for using the Playwright Automation Tool in various scenarios.

## Installation

```bash
pip install playwright
playwright install chromium
```

## Basic Usage

### Example 1: Capture Screenshot

Capture a full-page screenshot of a website:

```python
from ultimate_discord_intelligence_bot.tools.web import PlaywrightAutomationTool

tool = PlaywrightAutomationTool()

result = tool._run(
    url="https://example.com",
    action="screenshot",
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    screenshot_b64 = result.data["screenshot"]
    # screenshot_b64 is base64-encoded PNG image
    print(f"Screenshot captured: {result.data['title']}")
else:
    print(f"Error: {result.error}")
```

### Example 2: Extract Page Content

Extract HTML and text content from a dynamic page:

```python
result = tool._run(
    url="https://example.com",
    action="content",
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    html_content = result.data["html"]
    text_content = result.data["text"]
    print(f"Page title: {result.data['title']}")
    print(f"Text length: {len(text_content)} characters")
```

### Example 3: Wait for Element

Wait for a specific element to appear on the page:

```python
result = tool._run(
    url="https://example.com",
    action="wait_for_selector",
    selector="h1.page-title",
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    element_text = result.data["element_text"]
    print(f"Found element: {element_text}")
```

### Example 4: Click Element

Click a button or link:

```python
result = tool._run(
    url="https://example.com",
    action="click",
    selector="button#submit",
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    print("Element clicked successfully")
```

### Example 5: Fill Form Field

Fill a form input field:

```python
result = tool._run(
    url="https://example.com",
    action="fill",
    selector="input#search",
    text="my search query",
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    print("Form field filled successfully")
```

## Advanced Scenarios

### Scenario 1: Social Media Scraping

Capture social media post content:

```python
result = tool._run(
    url="https://twitter.com/user/status/123456",
    action="content",
    wait_timeout=60000,  # 60 seconds for slow-loading pages
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    # Extract tweet text
    tweet_text = result.data["text"]
    # Process or store the content
    print(f"Tweet content: {tweet_text}")
```

### Scenario 2: Form Automation

Fill and submit a form:

```python
# Step 1: Fill form fields
tool._run(
    url="https://example.com/form",
    action="fill",
    selector="input#name",
    text="John Doe",
    tenant="my_tenant",
    workspace="my_workspace"
)

tool._run(
    url="https://example.com/form",
    action="fill",
    selector="input#email",
    text="john@example.com",
    tenant="my_tenant",
    workspace="my_workspace"
)

# Step 2: Submit form
tool._run(
    url="https://example.com/form",
    action="click",
    selector="button#submit",
    tenant="my_tenant",
    workspace="my_workspace"
)
```

### Scenario 3: Dynamic Content Extraction

Extract content from a JavaScript-rendered page:

```python
result = tool._run(
    url="https://spa-example.com",
    action="content",
    wait_timeout=45000,  # Wait longer for JS to load
    tenant="my_tenant",
    workspace="my_workspace"
)

if result.success:
    # Content includes JavaScript-rendered elements
    html = result.data["html"]
    text = result.data["text"]
    print(f"Captured {len(text)} characters from dynamic page")
```

### Scenario 4: Screenshot Before/After

Capture screenshots before and after interaction:

```python
# Before screenshot
before = tool._run(
    url="https://example.com/page",
    action="screenshot",
    tenant="my_tenant",
    workspace="my_workspace"
)

# Perform action
tool._run(
    url="https://example.com/page",
    action="click",
    selector="button#expand",
    tenant="my_tenant",
    workspace="my_workspace"
)

# After screenshot
after = tool._run(
    url="https://example.com/page",
    action="screenshot",
    tenant="my_tenant",
    workspace="my_workspace"
)

# Compare or store both screenshots
print(f"Before: {before.data['screenshot'][:50]}...")
print(f"After: {after.data['screenshot'][:50]}...")
```

## Error Handling

### Handle Dependency Errors

```python
result = tool._run(
    url="https://example.com",
    action="screenshot",
    tenant="my_tenant",
    workspace="my_workspace"
)

if not result.success:
    if result.error_category == ErrorCategory.DEPENDENCY:
        print("Playwright not installed. Run: pip install playwright && playwright install")
    elif result.error_category == ErrorCategory.TIMEOUT:
        print("Page load timeout. Try increasing wait_timeout parameter")
    elif result.error_category == ErrorCategory.INVALID_INPUT:
        print(f"Invalid input: {result.error}")
    else:
        print(f"Automation failed: {result.error}")
```

### Handle Timeout Errors

```python
try:
    result = tool._run(
        url="https://slow-loading-site.com",
        action="content",
        wait_timeout=60000,  # 60 seconds
        tenant="my_tenant",
        workspace="my_workspace"
    )
except Exception as e:
    print(f"Timeout occurred: {e}")
    # Retry with longer timeout or fallback to static scraping
```

## Performance Optimization

### Use Appropriate Timeouts

```python
# Fast pages
result = tool._run(
    url="https://fast-site.com",
    action="screenshot",
    wait_timeout=10000,  # 10 seconds
    tenant="my_tenant",
    workspace="my_workspace"
)

# Slow pages
result = tool._run(
    url="https://slow-site.com",
    action="content",
    wait_timeout=60000,  # 60 seconds
    tenant="my_tenant",
    workspace="my_workspace"
)
```

### Batch Operations

```python
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

results = []
for url in urls:
    result = tool._run(
        url=url,
        action="screenshot",
        tenant="my_tenant",
        workspace="my_workspace"
    )
    results.append(result)

successful = [r for r in results if r.success]
print(f"Captured {len(successful)} screenshots")
```

## Best Practices

1. **Use Headless Mode**: Always run in headless mode (`PLAYWRIGHT_HEADLESS=true`) for production
2. **Set Appropriate Timeouts**: Match timeout to expected page load time
3. **Handle Errors Gracefully**: Always check `result.success` before accessing data
4. **Respect Rate Limits**: Don't hammer servers with too many requests
5. **Use Tenant Isolation**: Always pass tenant and workspace parameters
6. **Monitor Resource Usage**: Browser automation is memory-intensive
7. **Cache Results**: Store screenshots/content to avoid repeated scrapes

## Troubleshooting

### Common Issues

**Issue**: "Playwright not available"
- **Solution**: Install with `pip install playwright && playwright install chromium`

**Issue**: Timeout errors
- **Solution**: Increase `wait_timeout` parameter or check network connectivity

**Issue**: Element not found
- **Solution**: Verify selector is correct and wait for element with `wait_for_selector` first

**Issue**: Memory errors
- **Solution**: Reduce concurrent automation tasks or increase available memory

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

result = tool._run(
    url="https://example.com",
    action="screenshot",
    tenant="my_tenant",
    workspace="my_workspace"
)
```

## See Also

- [Tool Reference](../tools_reference.md)
- [Installation Guide](../../README.md)
- [Configuration](../configuration.md)
