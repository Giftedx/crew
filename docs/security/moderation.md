# Content Moderation

The moderation system provides multi-layered content safety screening before content is posted to Discord or other channels.

## Overview

Two moderation layers:

1. **Rule-Based Moderation** (`security.moderation`): Simple text filtering using banned terms
2. **OpenAI Moderation API** (`security.openai_moderation`): AI-powered content classification

## OpenAI Moderation Integration

### Features

- Multi-category detection: hate, violence, sexual content, self-harm
- Confidence scoring for each category
- Batch processing support
- Graceful fallback when API unavailable

### Categories Detected

- **Hate**: Hateful content targeting protected groups
- **Hate/Threatening**: Threatening content
- **Self-Harm**: Content promoting self-harm
- **Sexual**: Sexual content
- **Sexual/Minors**: Sexual content involving minors
- **Violence**: Violent content
- **Violence/Graphic**: Graphic violent content

### Configuration

```bash
# Enable OpenAI moderation
OPENAI_API_KEY=your_openai_api_key

# Optional: Configure thresholds
OPENAI_MODERATION_ENABLED=true
```

### Usage

```python
from src.security.openai_moderation import OpenAIModerationService

service = OpenAIModerationService()

# Check single content
result = service.check_content("content to check")
if result.flagged:
    print(f"Content blocked: {result.categories}")
    print(f"Action: {result.action}")

# Check multiple contents
results = service.check_batch(["content1", "content2"])
for result in results:
    if result.flagged:
        print(f"Blocked: {result.categories}")
```

## Pre-Publication Filter

The `ContentFilter` class provides a pre-publication screen before Discord posting:

```python
from src.discord.content_filter import ContentFilter

filter = ContentFilter()

# Check content before posting
result = filter.check_content("content to post", trusted_source=False)

if result.success and result.data["action"] == "allow":
    # Post content
    await channel.send(result.data["content"])
else:
    # Content blocked
    print(f"Content blocked: {result.error}")
```

### Features

- Automatic content screening
- Trusted source override
- Batch content checking
- Fail-safe: allows content on error (configurable)

## Integration with Discord

The filter integrates with Discord posting workflows:

```python
# Before posting any content
result = content_filter.check_content(message_content)

if result.success:
    # Content passed moderation
    await channel.send(result.data["content"])
else:
    # Content blocked - log and skip
    logger.warning(f"Content blocked: {result.error}")
```

## Metrics

Moderation operations are tracked with Prometheus metrics:

- `moderation_checks_total`: Total moderation checks
- `moderation_blocks_total`: Content blocked count
- `moderation_latency_seconds`: Moderation check latency

## Error Handling

### API Failures

On OpenAI API failure, content is **allowed** by default (fail-safe):

```python
# Fallback behavior
if not service.client:
    return ModerationResult(
        flagged=False,
        action="allow"  # Fail-safe
    )
```

### Configuration Failures

If moderation is unavailable:
- Content proceeds without filtering
- Warning logged
- No user impact

## Best Practices

1. **Always use moderation**: Enable for all user-generated content
2. **Trusted sources**: Use `trusted_source=True` for verified creators
3. **Batch processing**: Use `check_batch()` for multiple items
4. **Monitor metrics**: Track moderation stats and adjust thresholds
5. **Logging**: Log all blocked content for review
6. **Error handling**: Gracefully handle API failures

## Troubleshooting

### Moderation Not Working

- Check `OPENAI_API_KEY` is set
- Verify OpenAI API accessibility
- Review service logs for errors

### Too Many False Positives

- Review category scores
- Adjust thresholds if needed
- Use trusted source override

### API Rate Limits

- Implement request throttling
- Use batch processing efficiently
- Monitor API usage

## See Also

- [OpenAI Moderation API Docs](https://platform.openai.com/docs/guides/moderation)
- [Configuration Guide](../configuration.md)
- [Security Operations](./ops.md)
