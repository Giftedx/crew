# OpenAI Integration Features

This document describes the OpenAI integration features available in the Ultimate Discord Intelligence Bot.

## Overview

The OpenAI integration provides advanced AI capabilities including structured outputs, function calling, streaming, voice processing, vision analysis, and multimodal content analysis. These features enhance the bot's ability to analyze and process content with state-of-the-art AI models.

## Features

### 1. Structured Outputs

Generate structured, validated responses from OpenAI models using JSON schemas.

**Service**: `OpenAIStructuredOutputsService`

**Key Methods**:

- `generate_structured_response()` - Generate structured responses with schema validation
- `analyze_content_structured()` - Analyze content with structured output format

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService

service = OpenAIStructuredOutputsService()
result = await service.analyze_content_structured(
    content="This is a debate about climate change",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 2. Function Calling

Enable OpenAI models to call custom functions during conversation.

**Service**: `OpenAIFunctionCallingService`

**Key Methods**:

- `register_function()` - Register a custom function for OpenAI to call
- `call_with_functions()` - Make requests with function calling enabled

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_function_calling import OpenAIFunctionCallingService

service = OpenAIFunctionCallingService()

def analyze_sentiment(text: str):
    return {"sentiment": "positive", "confidence": 0.8}

service.register_function(
    "analyze_sentiment",
    {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"}
            }
        }
    },
    analyze_sentiment
)
```

### 3. Streaming

Stream responses from OpenAI models for real-time processing.

**Service**: `OpenAIStreamingService`

**Key Methods**:

- `stream_content_analysis()` - Stream content analysis results
- `stream_enhanced_analysis()` - Stream enhanced analysis with multiple capabilities

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_streaming import OpenAIStreamingService

service = OpenAIStreamingService()
async for result in service.stream_content_analysis(
    content="Debate content",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
):
    if result.success:
        print(f"Streamed: {result.data['content']}")
```

### 4. Voice Processing

Convert between text and speech using OpenAI's voice models.

**Service**: `OpenAIVoiceService`

**Key Methods**:

- `text_to_speech()` - Convert text to speech
- `speech_to_text()` - Convert speech to text
- `process_voice_command()` - Process voice commands end-to-end

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_voice import OpenAIVoiceService

service = OpenAIVoiceService()

# Convert text to speech
result = await service.text_to_speech(
    text="Hello, this is a test",
    voice="alloy",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Process voice command
result = await service.process_voice_command(
    audio_data=audio_bytes,
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 5. Vision Analysis

Analyze images and visual content using OpenAI's vision models.

**Service**: `OpenAIVisionService`

**Key Methods**:

- `analyze_image()` - Analyze single image
- `analyze_multiple_images()` - Analyze multiple images
- `extract_text_from_image()` - Extract text from images (OCR)
- `detect_bias_in_visual_content()` - Detect bias in visual content

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService

service = OpenAIVisionService()

# Analyze single image
result = await service.analyze_image(
    image_data=image_bytes,
    prompt="Analyze this image for key content",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Extract text from image
result = await service.extract_text_from_image(
    image_data=image_bytes,
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 6. Multimodal Analysis

Analyze content across multiple modalities (text, images, audio).

**Service**: `MultimodalAnalysisService`

**Key Methods**:

- `analyze_multimodal_content()` - Analyze content across modalities
- `analyze_debate_content_multimodal()` - Analyze debate content with multiple modalities
- `fact_check_multimodal()` - Fact-check using multiple modalities
- `detect_bias_multimodal()` - Detect bias across modalities

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_multimodal import MultimodalAnalysisService

service = MultimodalAnalysisService()

# Analyze multimodal content
result = await service.analyze_multimodal_content(
    text="Debate transcript",
    images=[image1_bytes, image2_bytes],
    audio_data=audio_bytes,
    tenant="tenant_id",
    workspace="workspace_id"
)

# Fact-check with images
result = await service.fact_check_multimodal(
    text="This claim is true",
    images=[evidence_image_bytes],
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 7. Integration Service

Main service that combines all OpenAI capabilities.

**Service**: `OpenAIIntegrationService`

**Key Methods**:

- `process_with_enhancements()` - Process content with multiple enhancements
- `stream_enhanced_analysis()` - Stream enhanced analysis
- `health_check()` - Check health of all services
- `get_available_enhancements()` - Get list of available enhancements

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService

service = OpenAIIntegrationService()

# Process with multiple enhancements
result = await service.process_with_enhancements(
    content="Debate content",
    enhancements=["structured_outputs", "function_calling", "vision"],
    tenant="tenant_id",
    workspace="workspace_id",
    images=[image_bytes]
)

# Check health
health = await service.health_check()
print(f"OpenAI available: {health.data['openai_available']}")
```

### 8. Cost Monitoring

Monitor OpenAI API usage and costs.

**Service**: `OpenAICostMonitoringService`

**Key Methods**:

- `record_request()` - Record API request for cost tracking
- `get_cost_summary()` - Get cost summary and projections
- `get_current_metrics()` - Get current usage metrics

**Example**:

```python
from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService

service = OpenAICostMonitoringService()

# Record a request
service.record_request(
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
    response_time=1.2,
    success=True
)

# Get cost summary
summary = service.get_cost_summary()
print(f"Total cost: ${summary['total_cost']:.4f}")
```

## Configuration

### Environment Variables

```bash
# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# Feature flags
ENABLE_OPENAI_STRUCTURED_OUTPUTS=true
ENABLE_OPENAI_STREAMING=true
ENABLE_OPENAI_VOICE=false
ENABLE_OPENAI_VISION=false
ENABLE_OPENAI_MULTIMODAL=false
ENABLE_OPENAI_FUNCTION_CALLING=true
ENABLE_OPENAI_FALLBACK=true
```

### Feature Flags

- `ENABLE_OPENAI_STRUCTURED_OUTPUTS` - Enable structured output generation
- `ENABLE_OPENAI_STREAMING` - Enable streaming responses
- `ENABLE_OPENAI_VOICE` - Enable voice processing capabilities
- `ENABLE_OPENAI_VISION` - Enable vision analysis capabilities
- `ENABLE_OPENAI_MULTIMODAL` - Enable multimodal analysis
- `ENABLE_OPENAI_FUNCTION_CALLING` - Enable function calling
- `ENABLE_OPENAI_FALLBACK` - Enable fallback to OpenRouter on failure

## Discord Commands

The integration includes several Discord commands for testing and using OpenAI features:

- `!openai-health` - Check OpenAI service health
- `!openai-analyze-structured <content>` - Perform structured analysis
- `!openai-analyze-multimodal <prompt>` - Analyze multimodal content (with image attachments)
- `!openai-voice-command` - Process voice commands (with audio attachments)

## CrewAI Integration

The OpenAI integration is available as a CrewAI tool:

**Tool**: `OpenAIEnhancedAnalysisTool`

**Key Methods**:

- `_run()` - Run enhanced analysis (synchronous for CrewAI)
- `stream_analysis()` - Stream analysis results
- `analyze_with_images()` - Analyze content with images
- `analyze_voice_content()` - Analyze voice content
- `fact_check_multimodal()` - Fact-check with multiple modalities
- `detect_bias_multimodal()` - Detect bias across modalities
- `generate_summary()` - Generate multimodal summary

## Error Handling

All services return `StepResult` objects for consistent error handling:

```python
result = await service.analyze_content_structured(...)
if result.success:
    data = result.data
else:
    error = result.error
    # Handle error
```

## Testing

Comprehensive tests are available in `tests/services/test_openai_integration_comprehensive.py`:

```bash
# Run OpenAI integration tests
pytest tests/services/test_openai_integration_comprehensive.py -v

# Run with coverage
pytest tests/services/test_openai_integration_comprehensive.py --cov=ultimate_discord_intelligence_bot.services.openai
```

## Examples

See `examples/openai_integration_example.py` for complete usage examples.

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure `OPENAI_API_KEY` environment variable is set
2. **Feature Disabled**: Check feature flags are enabled for desired capabilities
3. **Rate Limiting**: OpenAI has rate limits; consider implementing backoff
4. **Model Availability**: Some models may not be available in all regions

### Health Check

Use the health check to diagnose issues:

```python
service = OpenAIIntegrationService()
health = await service.health_check()
print(health.data)
```

### Fallback

If OpenAI is unavailable, the integration can fallback to OpenRouter:

```python
# Enable fallback in environment
ENABLE_OPENAI_FALLBACK=true
```

## Performance Considerations

- **Streaming**: Use streaming for long responses to improve perceived performance
- **Caching**: Consider caching results for repeated requests
- **Rate Limiting**: Implement appropriate rate limiting for production use
- **Cost Monitoring**: Monitor costs using the cost monitoring service

## Security

- **API Keys**: Store API keys securely and never commit them to version control
- **Input Validation**: Validate all inputs before sending to OpenAI
- **Output Sanitization**: Sanitize outputs before displaying to users
- **Rate Limiting**: Implement rate limiting to prevent abuse
