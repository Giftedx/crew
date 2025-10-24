# Discord Publisher Guide

This guide explains how to use the Discord publisher system for publishing messages to Discord channels with tenant isolation and feature flag control.

## Overview

The Discord publisher system provides a secure way to publish messages to Discord channels with:

- Feature flag control (`ENABLE_DISCORD_PUBLISHING`)
- Tenant isolation for multi-tenant environments
- Dry-run mode for testing
- Webhook-based publishing
- Error handling and retry logic

## Configuration

### Environment Variables

Configure the Discord publisher using environment variables:

```bash
# Enable Discord publishing
export ENABLE_DISCORD_PUBLISHING=true

# Discord webhook URL
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Optional: Custom webhook for different tenants
export DISCORD_WEBHOOK_URL_TENANT_A=https://discord.com/api/webhooks/TENANT_A_WEBHOOK
export DISCORD_WEBHOOK_URL_TENANT_B=https://discord.com/api/webhooks/TENANT_B_WEBHOOK
```

### .env File

Add configuration to your `.env` file:

```bash
# Discord Publishing
ENABLE_DISCORD_PUBLISHING=false
DISCORD_WEBHOOK_URL=

# Tenant-specific webhooks (optional)
DISCORD_WEBHOOK_URL_TENANT_A=
DISCORD_WEBHOOK_URL_TENANT_B=
```

## Usage

### Basic Usage

```python
from scripts.post_to_discord import post_to_discord

# Publish a message
success = post_to_discord("Hello, Discord!")

if success:
    print("Message published successfully")
else:
    print("Failed to publish message")
```

### Dry Run Mode

Test publishing without actually sending messages:

```python
# Dry run - logs the action without sending
success = post_to_discord("Test message", dry_run=True)

if success:
    print("Dry run successful - message would be published")
```

### Tenant-Aware Publishing

```python
def publish_for_tenant(tenant: str, message: str) -> bool:
    """Publish message for specific tenant."""
    # Check if publishing is enabled
    from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
    
    flags = FeatureFlags.from_env()
    if not flags.is_enabled("ENABLE_DISCORD_PUBLISHING"):
        print(f"Discord publishing disabled for tenant {tenant}")
        return False
    
    # Use tenant-specific webhook if available
    webhook_url = os.getenv(f"DISCORD_WEBHOOK_URL_{tenant.upper()}")
    if not webhook_url:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print(f"No webhook URL configured for tenant {tenant}")
        return False
    
    # Publish message
    return post_to_discord(message, webhook_url=webhook_url)
```

## Webhook Setup

### Creating a Discord Webhook

1. **Go to your Discord server**
2. **Right-click on the channel** where you want to post
3. **Select "Edit Channel"**
4. **Go to "Integrations" tab**
5. **Click "Create Webhook"**
6. **Copy the webhook URL**

### Webhook URL Format

```
https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
```

### Security Considerations

- **Keep webhook URLs secret** - Don't commit them to version control
- **Use environment variables** - Store webhooks in `.env` files
- **Rotate webhooks regularly** - Change webhook tokens periodically
- **Limit webhook permissions** - Use read-only channels when possible

## Message Formatting

### Basic Messages

```python
# Simple text message
post_to_discord("Hello, Discord!")

# Multi-line message
message = """
# System Update

The system has been updated with the following changes:
- Fixed bug in user authentication
- Improved performance by 20%
- Added new features

Please test the changes and report any issues.
"""
post_to_discord(message)
```

### Rich Messages

```python
# Message with formatting
message = """
**🚨 Alert: High CPU Usage**

*Server:* production-01
*CPU Usage:* 95%
*Memory Usage:* 87%
*Timestamp:* 2024-01-15 14:30:00 UTC

**Recommended Actions:**
1. Check running processes
2. Restart services if needed
3. Monitor for 15 minutes
"""
post_to_discord(message)
```

### Code Blocks

```python
# Code formatting
message = """
```python
def process_data(data):
    result = []
    for item in data:
        if item.is_valid():
            result.append(item.process())
    return result
```

"""
post_to_discord(message)

```

## Error Handling

### Common Errors

1. **Webhook URL not configured**
   ```python
   if not webhook_url:
       print("DISCORD_WEBHOOK_URL not set")
       return False
   ```

2. **Network timeout**

   ```python
   try:
       response = requests.post(webhook_url, timeout=10)
   except requests.exceptions.Timeout:
       print("Request timeout - webhook may be slow")
       return False
   ```

3. **Invalid webhook**

   ```python
   if response.status_code == 404:
       print("Webhook not found - check URL")
       return False
   ```

### Retry Logic

```python
import time
from requests.exceptions import RequestException

def post_with_retry(message: str, max_retries: int = 3) -> bool:
    """Post message with retry logic."""
    for attempt in range(max_retries):
        try:
            success = post_to_discord(message)
            if success:
                return True
        except RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return False
```

## Testing

### Unit Tests

```python
def test_discord_publisher():
    """Test Discord publisher functionality."""
    from scripts.post_to_discord import post_to_discord
    
    # Test dry run
    result = post_to_discord("Test message", dry_run=True)
    assert result is True
    
    # Test with disabled flag
    import os
    os.environ["ENABLE_DISCORD_PUBLISHING"] = "false"
    result = post_to_discord("Test message")
    assert result is False

def test_webhook_validation():
    """Test webhook URL validation."""
    import os
    from scripts.post_to_discord import post_to_discord
    
    # Test with invalid webhook
    os.environ["DISCORD_WEBHOOK_URL"] = "invalid_url"
    result = post_to_discord("Test message")
    assert result is False
```

### Integration Tests

```python
def test_discord_integration():
    """Test actual Discord integration."""
    import os
    from scripts.post_to_discord import post_to_discord
    
    # Set up test webhook
    os.environ["ENABLE_DISCORD_PUBLISHING"] = "true"
    os.environ["DISCORD_WEBHOOK_URL"] = "YOUR_TEST_WEBHOOK_URL"
    
    # Test actual publishing
    result = post_to_discord("Integration test message")
    assert result is True
```

## Monitoring

### Metrics

Track Discord publishing metrics:

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

metrics = get_metrics()

def track_discord_publish(success: bool, tenant: str = "default"):
    """Track Discord publishing metrics."""
    metrics.counter(
        "discord_publish_total",
        labels={
            "success": str(success).lower(),
            "tenant": tenant
        }
    ).inc()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def publish_with_logging(message: str, tenant: str) -> bool:
    """Publish with comprehensive logging."""
    logger.info(f"Publishing message for tenant {tenant}")
    
    try:
        success = post_to_discord(message)
        
        if success:
            logger.info(f"Successfully published message for tenant {tenant}")
        else:
            logger.warning(f"Failed to publish message for tenant {tenant}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error publishing message for tenant {tenant}: {e}")
        return False
```

## Best Practices

1. **Use feature flags** - Control publishing with `ENABLE_DISCORD_PUBLISHING`
2. **Test with dry run** - Always test before actual publishing
3. **Handle errors gracefully** - Provide fallbacks for failed publishing
4. **Use tenant isolation** - Separate webhooks for different tenants
5. **Monitor publishing** - Track success/failure rates
6. **Format messages well** - Use Discord markdown for better readability
7. **Keep messages concise** - Discord has message length limits
8. **Use appropriate channels** - Choose the right channel for the message type

## Troubleshooting

### Common Issues

1. **Publishing disabled**

   ```bash
   # Check if publishing is enabled
   echo $ENABLE_DISCORD_PUBLISHING
   
   # Enable publishing
   export ENABLE_DISCORD_PUBLISHING=true
   ```

2. **Webhook URL not set**

   ```bash
   # Check webhook URL
   echo $DISCORD_WEBHOOK_URL
   
   # Set webhook URL
   export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
   ```

3. **Network issues**

   ```python
   # Test webhook connectivity
   import requests
   
   webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
   try:
       response = requests.get(webhook_url, timeout=5)
       print(f"Webhook status: {response.status_code}")
   except Exception as e:
       print(f"Webhook error: {e}")
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed publishing information
post_to_discord("Debug message", dry_run=True)
```

## Security

### Webhook Security

- **Use HTTPS** - Always use secure webhook URLs
- **Rotate tokens** - Change webhook tokens regularly
- **Limit permissions** - Use webhooks only for necessary channels
- **Monitor usage** - Track webhook usage for anomalies

### Message Security

- **Sanitize content** - Remove sensitive information from messages
- **Use PII filtering** - Filter out personal information
- **Validate input** - Check message content before publishing
- **Rate limiting** - Limit publishing frequency

## Conclusion

The Discord publisher system provides a secure and flexible way to publish messages to Discord channels with proper tenant isolation and feature flag control. Following this guide will ensure reliable and secure Discord integration for your application.
