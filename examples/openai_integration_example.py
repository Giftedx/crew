"""Example usage of OpenAI integration services."""

import asyncio

from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService


async def main():
    """Example of using OpenAI integration services."""

    # Initialize services
    openai_service = OpenAIIntegrationService()
    cost_monitor = OpenAICostMonitoringService()

    # Example 1: Basic content analysis with structured outputs
    print("=== Example 1: Basic Content Analysis ===")
    content = """
    This is a debate about climate change. The speaker argues that human activity 
    is the primary cause of global warming, citing scientific studies and data 
    from the IPCC. They present evidence showing rising temperatures, melting ice caps, 
    and increased carbon dioxide levels in the atmosphere.
    """

    result = await openai_service.process_with_enhancements(
        content=content,
        enhancements=["structured_outputs", "function_calling"],
        tenant="example_tenant",
        workspace="example_workspace",
        analysis_type="debate",
    )

    if result.success:
        print("Analysis completed successfully!")
        print(f"Enhanced analysis: {result.data}")
    else:
        print(f"Analysis failed: {result.error}")

    # Example 2: Streaming analysis
    print("\n=== Example 2: Streaming Analysis ===")
    async for chunk in openai_service.stream_enhanced_analysis(
        content=content, analysis_type="debate", tenant="example_tenant", workspace="example_workspace"
    ):
        if chunk.success and chunk.data.get("streaming"):
            print(f"Streaming: {chunk.data['content']}", end="", flush=True)
        elif chunk.success and chunk.data.get("complete"):
            print("\nStreaming complete!")
            break
        elif not chunk.success:
            print(f"\nStreaming error: {chunk.error}")
            break

    # Example 3: Multimodal analysis (if images available)
    print("\n=== Example 3: Multimodal Analysis ===")
    # Note: In a real scenario, you would have actual image data
    fake_images = [b"fake_image_data_1", b"fake_image_data_2"]

    multimodal_result = await openai_service.process_with_enhancements(
        content=content,
        enhancements=["structured_outputs", "vision", "multimodal"],
        tenant="example_tenant",
        workspace="example_workspace",
        analysis_type="debate",
        images=fake_images,
    )

    if multimodal_result.success:
        print("Multimodal analysis completed!")
        print(f"Analysis includes: {multimodal_result.data['enhanced_analysis'].keys()}")
    else:
        print(f"Multimodal analysis failed: {multimodal_result.error}")

    # Example 4: Voice analysis (if audio available)
    print("\n=== Example 4: Voice Analysis ===")
    # Note: In a real scenario, you would have actual audio data
    fake_audio = b"fake_audio_data"

    voice_result = await openai_service.analyze_voice_content(
        audio_data=fake_audio, analysis_type="debate", tenant="example_tenant", workspace="example_workspace"
    )

    if voice_result.success:
        print("Voice analysis completed!")
        print(f"Voice analysis: {voice_result.data}")
    else:
        print(f"Voice analysis failed: {voice_result.error}")

    # Example 5: Fact-checking with multimodal evidence
    print("\n=== Example 5: Multimodal Fact-Checking ===")
    fact_check_result = await openai_service.fact_check_multimodal(
        text="The Earth's temperature has risen by 1.1°C since pre-industrial times.",
        images=fake_images,
        tenant="example_tenant",
        workspace="example_workspace",
    )

    if fact_check_result.success:
        print("Fact-checking completed!")
        print(f"Fact-check results: {fact_check_result.data}")
    else:
        print(f"Fact-checking failed: {fact_check_result.error}")

    # Example 6: Bias detection
    print("\n=== Example 6: Bias Detection ===")
    bias_result = await openai_service.detect_bias_multimodal(
        text="This biased statement clearly shows favoritism towards one side.",
        images=fake_images,
        tenant="example_tenant",
        workspace="example_workspace",
    )

    if bias_result.success:
        print("Bias detection completed!")
        print(f"Bias analysis: {bias_result.data}")
    else:
        print(f"Bias detection failed: {bias_result.error}")

    # Example 7: Generate summary
    print("\n=== Example 7: Generate Summary ===")
    summary_result = await openai_service.generate_multimodal_summary(
        text=content, images=fake_images, tenant="example_tenant", workspace="example_workspace"
    )

    if summary_result.success:
        print("Summary generation completed!")
        print(f"Summary: {summary_result.data}")
    else:
        print(f"Summary generation failed: {summary_result.error}")

    # Example 8: Health check
    print("\n=== Example 8: Health Check ===")
    health_result = await openai_service.health_check()

    if health_result.success:
        print("Health check completed!")
        print(f"OpenAI available: {health_result.data['openai_available']}")
        print(f"Features enabled: {health_result.data['features_enabled']}")
        print(f"Services status: {health_result.data['services']}")
    else:
        print(f"Health check failed: {health_result.error}")

    # Example 9: Cost monitoring
    print("\n=== Example 9: Cost Monitoring ===")

    # Record some example usage
    await cost_monitor.record_request(
        model="gpt-4o-mini", input_tokens=100, output_tokens=50, response_time=1.2, success=True
    )

    await cost_monitor.record_request(
        model="gpt-4o-mini", input_tokens=200, output_tokens=100, response_time=2.1, success=True
    )

    # Get current metrics
    metrics = cost_monitor.get_current_metrics()
    print(f"Current metrics: {metrics}")

    # Get cost summary
    cost_summary = cost_monitor.get_cost_summary()
    print(f"Cost summary: {cost_summary}")

    # Example 10: Get available enhancements
    print("\n=== Example 10: Available Enhancements ===")
    enhancements = openai_service.get_available_enhancements()
    print(f"Available enhancements: {enhancements}")


if __name__ == "__main__":
    asyncio.run(main())
