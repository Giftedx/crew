# OpenAI Integration

*Last updated: 2025-01-22*

## Overview

The Ultimate Discord Intelligence Bot includes comprehensive OpenAI integration providing advanced AI capabilities for content analysis, multimodal processing, and enhanced user interactions.

## Features

### Core Capabilities

- **Structured Outputs**: Schema-validated responses for consistent data processing
- **Function Calling**: Tool integration for complex analysis workflows
- **Streaming**: Real-time response streaming for better user experience
- **Voice**: Text-to-speech and speech-to-text capabilities
- **Vision**: Image analysis and multimodal content processing
- **Cost Monitoring**: Usage tracking and cost optimization

### Service Architecture

```
OpenAIServiceFacade
├── StructuredOutputsService
├── FunctionCallingService
├── StreamingService
├── VoiceService
├── VisionService
├── MultimodalService
└── CostMonitoringService
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_api_key_here

# Optional
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# Feature Flags
ENABLE_OPENAI_STRUCTURED_OUTPUTS=true
ENABLE_OPENAI_STREAMING=true
ENABLE_OPENAI_VOICE=false
ENABLE_OPENAI_VISION=false
ENABLE_OPENAI_MULTIMODAL=false
ENABLE_OPENAI_FUNCTION_CALLING=true
ENABLE_OPENAI_FALLBACK=true
```

### Service Initialization

```python
from ultimate_discord_intelligence_bot.services.openai_service_facade import OpenAIServiceFacade

# Initialize with default configuration
service = OpenAIServiceFacade()

# Or with custom configuration
from ultimate_discord_intelligence_bot.config.base import BaseConfig
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags

config = BaseConfig.from_env()
flags = FeatureFlags.from_env()
service = OpenAIServiceFacade(config=config, feature_flags=flags)
```

## Usage Examples

### Structured Analysis

```python
# Analyze content with structured outputs
result = await service.analyze_content_structured(
    content="Debate transcript content...",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)

if result.success:
    analysis_data = result.data
    print(f"Score: {analysis_data['score']}")
    print(f"Confidence: {analysis_data['confidence']}")
```

### Multimodal Analysis

```python
# Analyze text and images together
result = await service.analyze_multimodal_content(
    text="Content description",
    images=[image_bytes_1, image_bytes_2],
    audio_data=audio_bytes,  # Optional
    tenant="tenant_id",
    workspace="workspace_id"
)

if result.success:
    analysis = result.data['multimodal_analysis']
    print(f"Analysis: {analysis}")
```

### Voice Processing

```python
# Convert text to speech
tts_result = await service.text_to_speech(
    text="Hello, this is a test",
    voice="alloy",
    tenant="tenant_id",
    workspace="workspace_id"
)

if tts_result.success:
    audio_data = tts_result.data['audio_data']
    # Use audio_data for Discord voice messages

# Convert speech to text
stt_result = await service.speech_to_text(
    audio_data=audio_bytes,
    tenant="tenant_id",
    workspace="workspace_id"
)

if stt_result.success:
    transcribed_text = stt_result.data['text']
    print(f"Transcribed: {transcribed_text}")
```

### Streaming Analysis

```python
# Stream analysis results in real-time
async for result in service.stream_content_analysis(
    content="Long content to analyze...",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
):
    if result.success and result.data.get("streaming"):
        print(f"Streaming: {result.data['content']}")
    elif result.success and result.data.get("complete"):
        print("Analysis complete!")
```

## Discord Commands

### Available Commands

- `!openai-enhanced-analysis <content>` - Analyze content with OpenAI capabilities
- `!openai-stream <content>` - Stream analysis results in real-time
- `!openai-voice <text>` - Convert text to speech
- `!openai-vision` - Analyze attached images
- `!openai-multimodal <content>` - Analyze text and images together
- `!openai-costs [timeframe]` - Show API usage and costs
- `!openai-health` - Check service health status

### Example Usage

```
!openai-enhanced-analysis This is a debate about climate change policy
!openai-stream Analyze this political speech for bias and logical fallacies
!openai-voice Hello, welcome to our debate analysis bot
!openai-vision [attach image]
!openai-multimodal This image shows a political rally [attach image]
!openai-costs today
!openai-health
```

## CrewAI Integration

### Tool Usage

The OpenAI integration is available as a CrewAI tool:

```python
from ultimate_discord_intelligence_bot.tools.analysis.openai_enhanced_analysis_tool import OpenAIEnhancedAnalysisTool

# Use in agent definition
tools = [
    OpenAIEnhancedAnalysisTool(),
    # ... other tools
]
```

### Agent Configuration

Add to your agent's `tool_guidelines`:

```yaml
tool_guidelines:
  - Use `openai_enhanced_analysis_tool` for advanced AI-powered analysis
  - Leverage structured outputs for consistent data processing
  - Apply multimodal analysis when images are available
  - Use function calling for complex analysis workflows
```

## Cost Monitoring

### Usage Tracking

```python
# Get current usage metrics
metrics = service.get_current_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Total tokens: {metrics['total_tokens']}")
print(f"Success rate: {metrics['success_rate']:.1%}")

# Get cost summary
costs = service.get_cost_summary()
print(f"Total cost: ${costs['total_cost']:.2f}")
print(f"Daily average: ${costs['daily_average_cost']:.2f}")
```

### Cost Optimization

- Use appropriate models for different tasks
- Implement caching for repeated requests
- Monitor usage patterns and optimize accordingly
- Set up alerts for cost thresholds

## Health Monitoring

### Service Health Check

```python
# Check overall service health
health_result = await service.health_check()

if health_result.success:
    health_data = health_result.data
    print(f"OpenAI Available: {health_data['openai_available']}")
    print(f"Services: {health_data['services']}")
    print(f"Features Enabled: {health_data['features_enabled']}")
```

### Status Monitoring

```python
# Get service status
status = service.get_service_status()
print(f"Services Available: {status['services_available']}")
print(f"Capabilities: {status['capabilities']}")
```

## Error Handling

### Fallback Strategy

The service includes automatic fallback to OpenRouter when OpenAI is unavailable:

```python
# Fallback is automatic when ENABLE_OPENAI_FALLBACK=true
result = await service.analyze_content_structured(
    content="content",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Check if fallback was used
if result.data.get("fallback"):
    print("Used OpenRouter fallback")
```

### Error Recovery

```python
try:
    result = await service.analyze_content_structured(...)
    if not result.success:
        # Handle specific error types
        if "rate_limit" in result.error:
            # Implement backoff strategy
            await asyncio.sleep(60)
        elif "invalid_api_key" in result.error:
            # Handle authentication error
            logger.error("Invalid OpenAI API key")
except Exception as e:
    logger.error(f"OpenAI service error: {e}")
```

## Best Practices

### Performance

- Use streaming for long content analysis
- Implement caching for repeated requests
- Batch similar requests when possible
- Monitor and optimize token usage

### Security

- Store API keys securely
- Implement rate limiting
- Validate input data
- Use tenant isolation

### Reliability

- Implement retry logic with exponential backoff
- Use fallback services when available
- Monitor service health regularly
- Handle errors gracefully

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key permissions and quotas

2. **Rate Limiting**
   - Implement exponential backoff
   - Consider upgrading API plan
   - Use fallback services

3. **Model Availability**
   - Check model availability in your region
   - Use alternative models when needed
   - Enable fallback to OpenRouter

4. **Feature Flags**
   - Verify feature flags are enabled
   - Check configuration values
   - Restart service after changes

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("ultimate_discord_intelligence_bot.services.openai").setLevel(logging.DEBUG)
```

## Migration Guide

### From Individual Services

If migrating from individual OpenAI services:

```python
# Old approach
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService

structured_service = OpenAIStructuredOutputsService()
vision_service = OpenAIVisionService()

# New approach
from ultimate_discord_intelligence_bot.services.openai_service_facade import OpenAIServiceFacade

service = OpenAIServiceFacade()
# All capabilities available through single interface
```

## Support

For issues and questions:

- Check the [main documentation](../README.md)
- Review [configuration guide](../configuration.md)
- See [troubleshooting guide](../operations/troubleshooting.md)
- Open an issue in the project repository
