# OpenAI Integration for Ultimate Discord Intelligence Bot

This document provides a comprehensive guide to the OpenAI integration features added to the Ultimate Discord Intelligence Bot.

## Overview

The OpenAI integration adds advanced AI capabilities to the bot, including:
- **Structured Outputs**: JSON schema validation for reliable data processing
- **Function Calling**: Enhanced tool integration with OpenAI's native function calling
- **Streaming Responses**: Real-time response streaming for better user experience
- **Voice Capabilities**: Speech-to-speech processing for voice interactions
- **Vision Analysis**: Image and video content analysis
- **Multimodal Analysis**: Combined text, image, and audio analysis
- **Cost Monitoring**: Usage tracking and cost management

## Quick Start

### 1. Environment Setup

Add the following environment variables to your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
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

### 2. Install Dependencies

```bash
pip install openai>=1.0.0
```

### 3. Basic Usage

```python
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService

# Initialize the service
openai_service = OpenAIIntegrationService()

# Analyze content with OpenAI enhancements
result = await openai_service.process_with_enhancements(
    content="Your content here",
    enhancements=["structured_outputs", "function_calling"],
    tenant="your_tenant",
    workspace="your_workspace",
    analysis_type="debate"
)

if result.success:
    print(f"Analysis: {result.data}")
else:
    print(f"Error: {result.error}")
```

## Services

### 1. OpenAI Integration Service

The main service that combines all OpenAI capabilities.

```python
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService

service = OpenAIIntegrationService()

# Get available enhancements
enhancements = service.get_available_enhancements()

# Process content with enhancements
result = await service.process_with_enhancements(
    content="Content to analyze",
    enhancements=enhancements,
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 2. Structured Outputs Service

Provides JSON schema validation for reliable data processing.

```python
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService

service = OpenAIStructuredOutputsService()

# Define schema
schema = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 10},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["score", "confidence"]
}

# Generate structured response
result = await service.generate_structured_response(
    prompt="Analyze this content",
    schema=schema,
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 3. Function Calling Service

Enhanced tool integration with OpenAI's native function calling.

```python
from ultimate_discord_intelligence_bot.services.openai_function_calling import OpenAIFunctionCallingService

service = OpenAIFunctionCallingService()

# Register custom function
def my_handler(content: str, analysis_type: str):
    return {"result": "processed"}

service.register_function(
    "my_function",
    {
        "name": "my_function",
        "description": "My custom function",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "analysis_type": {"type": "string"}
            }
        }
    },
    my_handler
)

# Call with functions
result = await service.call_with_functions(
    prompt="Use my_function to process this",
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 4. Streaming Service

Real-time response streaming for better user experience.

```python
from ultimate_discord_intelligence_bot.services.openai_streaming import OpenAIStreamingService

service = OpenAIStreamingService()

# Stream analysis
async for chunk in service.stream_content_analysis(
    content="Content to analyze",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
):
    if chunk.success and chunk.data.get("streaming"):
        print(chunk.data["content"], end="", flush=True)
    elif chunk.success and chunk.data.get("complete"):
        print("\nAnalysis complete!")
        break
```

### 5. Voice Service

Speech-to-speech processing for voice interactions.

```python
from ultimate_discord_intelligence_bot.services.openai_voice import OpenAIVoiceService

service = OpenAIVoiceService()

# Text to speech
result = await service.text_to_speech(
    text="Hello, world!",
    voice="alloy",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Speech to text
result = await service.speech_to_text(
    audio_data=audio_bytes,
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

### 6. Vision Service

Image and video content analysis.

```python
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService

service = OpenAIVisionService()

# Analyze single image
result = await service.analyze_image(
    image_data=image_bytes,
    prompt="Analyze this image for bias indicators",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Analyze multiple images
result = await service.analyze_multiple_images(
    images=[image1_bytes, image2_bytes],
    prompt="Compare these images",
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 7. Multimodal Analysis Service

Combined text, image, and audio analysis.

```python
from ultimate_discord_intelligence_bot.services.openai_multimodal import MultimodalAnalysisService

service = MultimodalAnalysisService()

# Analyze multimodal content
result = await service.analyze_multimodal_content(
    text="Text content",
    images=[image1_bytes, image2_bytes],
    audio_data=audio_bytes,
    tenant="tenant_id",
    workspace="workspace_id"
)

# Fact-check with multimodal evidence
result = await service.fact_check_multimodal(
    text="Claim to fact-check",
    images=[evidence_image_bytes],
    tenant="tenant_id",
    workspace="workspace_id"
)
```

### 8. Cost Monitoring Service

Usage tracking and cost management.

```python
from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService

monitor = OpenAICostMonitoringService()

# Record usage
await monitor.record_request(
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
    response_time=1.2,
    success=True
)

# Get current metrics
metrics = monitor.get_current_metrics()
print(f"Total cost: ${metrics['total_cost']:.2f}")

# Get cost summary
summary = monitor.get_cost_summary()
print(f"Projected monthly cost: ${summary['projected_monthly_cost']:.2f}")
```

## Enhanced Analysis Tool

The enhanced analysis tool provides a simplified interface to all OpenAI capabilities.

```python
from ultimate_discord_intelligence_bot.tools.analysis.openai_enhanced_analysis_tool import OpenAIEnhancedAnalysisTool

tool = OpenAIEnhancedAnalysisTool()

# Basic analysis
result = await tool._run(
    content="Content to analyze",
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Multimodal analysis
result = await tool.analyze_with_images(
    content="Content with images",
    images=[image1_bytes, image2_bytes],
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)

# Voice analysis
result = await tool.analyze_voice_content(
    audio_data=audio_bytes,
    analysis_type="debate",
    tenant="tenant_id",
    workspace="workspace_id"
)
```

## Configuration

### Feature Flags

Control which OpenAI features are enabled:

```python
# In your .env file
ENABLE_OPENAI_STRUCTURED_OUTPUTS=true   # Enable structured outputs
ENABLE_OPENAI_STREAMING=true            # Enable streaming responses
ENABLE_OPENAI_VOICE=false               # Enable voice capabilities
ENABLE_OPENAI_VISION=false              # Enable vision analysis
ENABLE_OPENAI_MULTIMODAL=false          # Enable multimodal analysis
ENABLE_OPENAI_FUNCTION_CALLING=true     # Enable function calling
ENABLE_OPENAI_FALLBACK=true             # Enable OpenRouter fallback
```

### Model Configuration

Configure OpenAI models and parameters:

```python
# In your .env file
OPENAI_MAX_TOKENS=4000                  # Maximum tokens per request
OPENAI_TEMPERATURE=0.7                  # Response temperature
OPENAI_BASE_URL=https://api.openai.com/v1  # API base URL
```

## Error Handling

All services use the `StepResult` pattern for consistent error handling:

```python
result = await service.some_method()

if result.success:
    # Process successful result
    data = result.data
else:
    # Handle error
    error_message = result.error
    print(f"Error: {error_message}")
```

## Fallback Mechanisms

The integration includes fallback mechanisms to maintain reliability:

1. **OpenRouter Fallback**: If OpenAI is unavailable, services can fall back to OpenRouter
2. **Feature Flag Control**: Disable features that aren't working properly
3. **Error Handling**: Comprehensive error handling with meaningful error messages

## Cost Management

The cost monitoring service helps manage OpenAI usage:

1. **Real-time Tracking**: Track usage and costs in real-time
2. **Cost Alerts**: Get alerts when costs exceed thresholds
3. **Usage Analytics**: Detailed usage analytics and projections
4. **Budget Controls**: Set daily and monthly cost limits

## Testing

Run the tests to verify the integration:

```bash
pytest tests/services/test_openai_integration.py -v
```

## Examples

See `examples/openai_integration_example.py` for comprehensive usage examples.

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure `OPENAI_API_KEY` is set in your environment
2. **Feature Not Enabled**: Check that the appropriate feature flag is enabled
3. **Rate Limits**: OpenAI has rate limits; the service includes retry logic
4. **Cost Alerts**: Monitor costs to avoid unexpected charges

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify your OpenAI API key and configuration
3. Review the feature flags and ensure they're properly set
4. Check the cost monitoring service for usage patterns

## Migration from OpenRouter

The integration is designed to work alongside OpenRouter:

1. **Gradual Migration**: Enable OpenAI features gradually
2. **Fallback Support**: OpenRouter remains available as fallback
3. **Feature Parity**: OpenAI services provide enhanced capabilities
4. **Cost Comparison**: Monitor costs to ensure value

## Future Enhancements

Planned enhancements include:
1. **Advanced Caching**: Intelligent caching for cost optimization
2. **Batch Processing**: Batch requests for efficiency
3. **Custom Models**: Support for fine-tuned models
4. **Advanced Analytics**: Enhanced usage analytics and insights
