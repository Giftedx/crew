# Basic Usage Examples

## Overview

This document provides practical examples of using the Ultimate Discord Intelligence Bot's multi-agent orchestration system.

## Quick Start

### 1. Basic Pipeline Usage

```python
import asyncio
from ultimate_discord_intelligence_bot.services.unified_pipeline import PipelineConfig, UnifiedPipeline

async def basic_example():
    # Configure the pipeline
    config = PipelineConfig(
        enable_vector_memory=True,
        enable_rl_routing=True,
        enable_mcp_tools=True,
        enable_prompt_optimization=True,
        enable_discord_publishing=True,
    )
    
    # Initialize the pipeline
    pipeline = UnifiedPipeline(config)
    await pipeline.initialize()
    
    # Process content
    result = await pipeline.process_content(
        content="Analyze this debate about climate change",
        content_type="analysis",
        tenant="user123",
        workspace="workspace1",
    )
    
    if result.success:
        print(f"Processing completed: {result.data}")
    else:
        print(f"Processing failed: {result.error}")
    
    # Cleanup
    await pipeline.shutdown()

# Run the example
asyncio.run(basic_example())
```

### 2. Crew Integration

```python
import asyncio
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

async def crew_example():
    # Initialize the crew
    crew = UltimateDiscordIntelligenceBotCrew()
    
    # Setup Discord integration
    crew.setup_discord_integration(
        webhook_url="https://discord.com/api/webhooks/...",
    )
    
    # Initialize MCP tools
    await crew._initialize_mcp_tools()
    
    # Run crew analysis
    inputs = {
        "url": "https://youtube.com/watch?v=example",
        "tenant": "user123",
        "workspace": "workspace1",
    }
    
    result = crew.crew().kickoff(inputs=inputs)
    
    # Publish results
    await crew.publish_crew_results(
        crew_result=result,
        tenant="user123",
        workspace="workspace1",
    )

# Run the example
asyncio.run(crew_example())
```

## Advanced Examples

### 1. Custom Vector Memory Operations

```python
import asyncio
from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.services.embedding_service import EmbeddingService

async def vector_memory_example():
    # Initialize services
    embedding_service = EmbeddingService()
    memory_service = MemoryService()
    
    # Store content in vector memory
    content = "This is important information about machine learning"
    result = await memory_service.add(
        text=content,
        tenant="user123",
        workspace="workspace1",
    )
    
    if result.success:
        print("Content stored successfully")
    
    # Search for similar content
    search_result = await memory_service.search(
        query="machine learning algorithms",
        tenant="user123",
        workspace="workspace1",
        limit=5,
    )
    
    if search_result.success:
        print(f"Found {len(search_result.data)} similar items")
        for item in search_result.data:
            print(f"- {item['text'][:100]}...")

# Run the example
asyncio.run(vector_memory_example())
```

### 2. RL Routing with Feedback

```python
import asyncio
from ultimate_discord_intelligence_bot.services.routing_service import RoutingService
from ultimate_discord_intelligence_bot.services.bandit_policy import BanditPolicy
from ultimate_discord_intelligence_bot.services.context_service import ContextService
from ultimate_discord_intelligence_bot.services.observability_service import ObservabilityService

async def rl_routing_example():
    # Initialize services
    context_service = ContextService()
    obs_service = ObservabilityService()
    
    # Create routing service
    routing_service = RoutingService(
        context_service=context_service,
        obs_service=obs_service,
        available_providers=["openai", "anthropic", "cohere"],
    )
    
    # Select provider
    selection_result = await routing_service.select_llm_provider({
        "tenant": "user123",
        "workspace": "workspace1",
        "content_type": "analysis",
    })
    
    if selection_result.success:
        selected_provider = selection_result.data
        print(f"Selected provider: {selected_provider}")
        
        # Simulate processing and record feedback
        # (In real usage, this would be based on actual results)
        feedback_result = await routing_service.record_provider_feedback(
            provider=selected_provider,
            reward=0.8,  # 0.0 to 1.0 scale
            request_context={
                "tenant": "user123",
                "workspace": "workspace1",
            },
        )
        
        if feedback_result.success:
            print("Feedback recorded successfully")
    
    # Get provider statistics
    stats_result = routing_service.get_provider_stats()
    if stats_result.success:
        print(f"Provider stats: {stats_result.data}")

# Run the example
asyncio.run(rl_routing_example())
```

### 3. MCP Tools Usage

```python
import asyncio
from ultimate_discord_intelligence_bot.services.mcp_client import MCPClient, create_default_mcp_tools

async def mcp_tools_example():
    # Initialize MCP client
    mcp_client = MCPClient(
        base_url="https://api.mcp.io",
        api_key="your_mcp_api_key",
    )
    
    # Register default tools
    default_tools = create_default_mcp_tools()
    for tool in default_tools:
        result = await mcp_client.register_tool(tool)
        if result.success:
            print(f"Registered tool: {tool.name}")
    
    # Execute web search
    search_result = await mcp_client.execute_tool(
        tool_name="web_search",
        parameters={"query": "latest AI developments"},
        tenant="user123",
        workspace="workspace1",
    )
    
    if search_result.success:
        print(f"Search results: {search_result.data}")
    
    # Execute image analysis
    image_result = await mcp_client.execute_tool(
        tool_name="image_analysis",
        parameters={"image_url": "https://example.com/image.jpg"},
        tenant="user123",
        workspace="workspace1",
    )
    
    if image_result.success:
        print(f"Image analysis: {image_result.data}")
    
    # Get client statistics
    stats_result = await mcp_client.get_stats()
    if stats_result.success:
        print(f"MCP client stats: {stats_result.data}")

# Run the example
asyncio.run(mcp_tools_example())
```

### 4. Prompt Optimization

```python
import asyncio
from ultimate_discord_intelligence_bot.services.prompt_compressor import PromptCompressor, CompressionConfig
from ultimate_discord_intelligence_bot.services.optimization_pipeline import OptimizationPipeline

async def prompt_optimization_example():
    # Initialize compressor
    compression_config = CompressionConfig(
        target_compression_ratio=0.5,
        min_quality_threshold=0.8,
        preserve_structure=True,
    )
    compressor = PromptCompressor(compression_config)
    
    # Initialize optimization pipeline
    optimization_pipeline = OptimizationPipeline(compressor=compressor)
    
    # Optimize a prompt
    original_prompt = """
    Please analyze the following content and provide a comprehensive summary
    of the key points, main arguments, and any potential biases or inaccuracies
    that you can identify. Be thorough and detailed in your analysis.
    """
    
    result = await optimization_pipeline.optimize_prompt(
        prompt=original_prompt,
        prompt_id="prompt_001",
        tenant="user123",
        workspace="workspace1",
    )
    
    if result.success:
        optimized_prompt = result.data["optimized_prompt"]
        metrics = result.data["metrics"]
        
        print(f"Original tokens: {metrics['original_tokens']}")
        print(f"Optimized tokens: {metrics['optimized_tokens']}")
        print(f"Compression ratio: {metrics['compression_ratio']:.2f}")
        print(f"Quality score: {metrics['quality_score']:.2f}")
        print(f"Cost savings: ${metrics['cost_savings']:.4f}")
        print(f"Optimized prompt: {optimized_prompt}")
    
    # Get optimization statistics
    stats_result = optimization_pipeline.get_optimization_stats()
    if stats_result.success:
        print(f"Optimization stats: {stats_result.data}")

# Run the example
asyncio.run(prompt_optimization_example())
```

### 5. Discord Artifact Publishing

```python
import asyncio
from ultimate_discord_intelligence_bot.services.artifact_publisher import ArtifactPublisher, ArtifactMetadata, DiscordConfig

async def discord_publishing_example():
    # Configure Discord
    discord_config = DiscordConfig(
        webhook_url="https://discord.com/api/webhooks/...",
        enable_embeds=True,
        max_message_length=2000,
    )
    
    # Initialize publisher
    publisher = ArtifactPublisher(discord_config)
    
    # Create artifact metadata
    metadata = ArtifactMetadata(
        artifact_id="analysis_001",
        title="Content Analysis Results",
        description="Comprehensive analysis of the provided content",
        content_type="analysis",
        tenant="user123",
        workspace="workspace1",
        created_at=time.time(),
        source_url="https://example.com/source",
        tags=["analysis", "content", "ai"],
    )
    
    # Prepare artifact data
    artifact_data = {
        "summary": "This content discusses important topics...",
        "key_findings": [
            "Finding 1: Important point about topic A",
            "Finding 2: Significant insight about topic B",
        ],
        "confidence_score": 0.85,
        "source_url": "https://example.com/source",
    }
    
    # Publish artifact
    result = await publisher.publish_artifact(
        artifact_data=artifact_data,
        metadata=metadata,
        tenant="user123",
        workspace="workspace1",
    )
    
    if result.success:
        print(f"Artifact published successfully: {result.data}")
    else:
        print(f"Publishing failed: {result.error}")
    
    # Get publishing statistics
    stats_result = publisher.get_publishing_stats()
    if stats_result.success:
        print(f"Publishing stats: {stats_result.data}")

# Run the example
asyncio.run(discord_publishing_example())
```

## Integration Examples

### 1. Complete Workflow

```python
import asyncio
from ultimate_discord_intelligence_bot.services.unified_pipeline import PipelineConfig, UnifiedPipeline

async def complete_workflow_example():
    # Configure pipeline with all features
    config = PipelineConfig(
        enable_vector_memory=True,
        enable_rl_routing=True,
        enable_mcp_tools=True,
        enable_prompt_optimization=True,
        enable_discord_publishing=True,
        enable_observability=True,
        qdrant_url="http://localhost:6333",
        available_providers=["openai", "anthropic"],
        discord_webhook_url="https://discord.com/api/webhooks/...",
    )
    
    # Initialize pipeline
    pipeline = UnifiedPipeline(config)
    init_result = await pipeline.initialize()
    
    if not init_result.success:
        print(f"Initialization failed: {init_result.error}")
        return
    
    print("Pipeline initialized successfully")
    
    # Process multiple content items
    content_items = [
        "Analyze this debate about renewable energy",
        "Summarize the key points in this article",
        "Fact-check these claims about climate change",
    ]
    
    for i, content in enumerate(content_items):
        print(f"\nProcessing item {i+1}: {content[:50]}...")
        
        result = await pipeline.process_content(
            content=content,
            content_type="analysis",
            tenant=f"user_{i}",
            workspace="workspace1",
        )
        
        if result.success:
            print(f"✓ Processing completed in {result.data['processing_time_ms']:.1f}ms")
        else:
            print(f"✗ Processing failed: {result.error}")
    
    # Get comprehensive statistics
    stats_result = await pipeline.get_pipeline_stats()
    if stats_result.success:
        print(f"\nPipeline Statistics:")
        print(f"- Components: {stats_result.data['components']}")
        print(f"- Config: {stats_result.data['config']}")
    
    # Perform health check
    health_result = await pipeline.health_check()
    if health_result.success:
        print(f"\nHealth Status: {health_result.data['overall_health']}")
        for component, status in health_result.data['components'].items():
            print(f"- {component}: {status['status']}")
    
    # Shutdown pipeline
    shutdown_result = await pipeline.shutdown()
    if shutdown_result.success:
        print("\nPipeline shutdown completed")

# Run the complete example
asyncio.run(complete_workflow_example())
```

### 2. Error Handling and Recovery

```python
import asyncio
from ultimate_discord_intelligence_bot.services.unified_pipeline import PipelineConfig, UnifiedPipeline

async def error_handling_example():
    # Configure pipeline with error-prone settings
    config = PipelineConfig(
        enable_vector_memory=True,
        enable_rl_routing=True,
        enable_mcp_tools=True,
        enable_prompt_optimization=True,
        enable_discord_publishing=True,
        # Use invalid URLs to test error handling
        qdrant_url="http://invalid-url:6333",
        discord_webhook_url="https://invalid-webhook.com",
    )
    
    pipeline = UnifiedPipeline(config)
    
    try:
        # Attempt initialization
        init_result = await pipeline.initialize()
        
        if not init_result.success:
            print(f"Initialization failed (expected): {init_result.error}")
            
            # Try with fallback configuration
            config.qdrant_url = "http://localhost:6333"
            config.discord_webhook_url = None  # Disable Discord publishing
            
            pipeline = UnifiedPipeline(config)
            init_result = await pipeline.initialize()
            
            if init_result.success:
                print("Pipeline initialized with fallback configuration")
            else:
                print(f"Fallback initialization also failed: {init_result.error}")
                return
        
        # Process content with error handling
        result = await pipeline.process_content(
            content="Test content for error handling",
            content_type="analysis",
            tenant="user123",
            workspace="workspace1",
        )
        
        if result.success:
            print("Content processed successfully")
        else:
            print(f"Content processing failed: {result.error}")
            
            # Try with simplified configuration
            print("Attempting with simplified configuration...")
            # ... implement fallback logic
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    finally:
        # Always cleanup
        try:
            await pipeline.shutdown()
            print("Pipeline shutdown completed")
        except Exception as e:
            print(f"Shutdown error: {e}")

# Run the error handling example
asyncio.run(error_handling_example())
```

## Best Practices

### 1. Resource Management

```python
# Always use context managers or try/finally for cleanup
async def resource_management_example():
    pipeline = None
    try:
        pipeline = UnifiedPipeline(config)
        await pipeline.initialize()
        # ... use pipeline
    finally:
        if pipeline:
            await pipeline.shutdown()
```

### 2. Error Handling

```python
# Always check results and handle errors gracefully
async def error_handling_example():
    result = await pipeline.process_content(content)
    
    if not result.success:
        logger.error(f"Processing failed: {result.error}")
        # Implement fallback logic
        return
    
    # Process successful result
    data = result.data
```

### 3. Performance Monitoring

```python
# Monitor performance and adjust configuration
async def performance_monitoring_example():
    start_time = time.time()
    
    result = await pipeline.process_content(content)
    
    processing_time = time.time() - start_time
    
    if processing_time > 5.0:  # 5 seconds threshold
        logger.warning(f"Slow processing: {processing_time:.2f}s")
        # Consider adjusting configuration
```

### 4. Configuration Management

```python
# Use environment-specific configurations
import os

def get_config():
    env = os.getenv('APP_ENV', 'development')
    
    if env == 'production':
        return PipelineConfig(
            enable_observability=True,
            qdrant_url=os.getenv('QDRANT_URL'),
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL'),
        )
    else:
        return PipelineConfig(
            enable_observability=False,
            qdrant_url='http://localhost:6333',
            discord_webhook_url=None,
        )
```

## Troubleshooting

### Common Issues

1. **Initialization Failures**: Check environment variables and service connectivity
2. **Processing Errors**: Verify content format and service availability
3. **Performance Issues**: Monitor resource usage and adjust configuration
4. **Memory Leaks**: Ensure proper cleanup and resource management

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debug configuration
config = PipelineConfig(
    enable_observability=True,
    # ... other settings
)
```

### Health Monitoring

```python
# Regular health checks
async def health_monitoring():
    health_result = await pipeline.health_check()
    
    if health_result.data['overall_health'] != 'healthy':
        logger.warning(f"Pipeline health issues: {health_result.data}")
        # Implement recovery logic
```
