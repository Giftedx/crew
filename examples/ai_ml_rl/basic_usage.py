"""Example: Basic usage of AI/ML/RL integration system."""

import asyncio

from src.ai.integration.ai_ml_rl_integration import get_ai_integration


async def main():
    """Demonstrate basic usage of AI/ML/RL system."""
    # Get integration instance
    ai_system = get_ai_integration()

    # Start the system (initializes all components and background tasks)
    await ai_system.start()

    print("AI/ML/RL System Started")
    print("=" * 60)

    # Example 1: Route a tool request
    print("\n1. Routing tool request...")
    tool_result = await ai_system.route_tool(
        task_description="Analyze sentiment of social media posts",
        context={"complexity": 0.7, "data_size": 5000, "urgency": 0.6, "required_accuracy": 0.9},
        task_type="analysis",
    )

    if tool_result.success:
        selection = tool_result.data
        print(f"   Selected tool: {selection.tool_id}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reasoning: {selection.reasoning}")

    # Example 2: Route an agent request
    print("\n2. Routing agent request...")
    agent_result = await ai_system.route_agent(
        task_description="Verify claims in a political article",
        context={"complexity": 0.8, "urgency": 0.7, "required_accuracy": 0.95, "data_volume": 0.6},
        task_type="verification",
    )

    if agent_result.success:
        selection = agent_result.data
        print(f"   Selected agent: {selection.agent_id}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Current load: {selection.current_load}/{selection.max_parallel_tasks}")

    # Example 3: Select a prompt variant
    print("\n3. Selecting optimal prompt...")
    prompt_result = await ai_system.select_prompt(
        prompt_type="analysis",
        context={"complexity": 0.7, "required_accuracy": 0.9, "budget_limit": 0.5},
        optimization_target="balanced",
    )

    if prompt_result.success:
        selection = prompt_result.data
        print(f"   Selected variant: {selection.variant_id[:12]}...")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Variables: {selection.variables}")

    # Example 4: Submit feedback
    print("\n4. Submitting feedback...")

    # Simulate tool execution feedback
    ai_system.submit_tool_feedback(
        tool_id="sentiment_tool", context={"complexity": 0.7}, success=True, latency_ms=850, quality_score=0.91
    )
    print("   Tool feedback submitted")

    # Simulate agent execution feedback
    ai_system.submit_agent_feedback(
        agent_id="verification_analyst", context={"urgency": 0.7}, success=True, duration_s=42.5, quality_score=0.94
    )
    print("   Agent feedback submitted")

    # Simulate RAG retrieval feedback
    ai_system.submit_rag_feedback(
        query_id="query_123",
        query_text="What is the capital of France?",
        retrieved_chunks=[
            {"id": "chunk_1", "content": "Paris is the capital of France."},
            {"id": "chunk_2", "content": "France is a country in Europe."},
        ],
        relevance_scores=[0.95, 0.72],
    )
    print("   RAG feedback submitted")

    # Example 5: Get aggregate metrics
    print("\n5. Collecting metrics...")
    metrics = await ai_system.get_aggregate_metrics()

    print("\n   System Metrics:")
    for component, component_metrics in metrics.items():
        print(f"\n   {component}:")
        for key, value in component_metrics.items():
            if isinstance(value, (int, float)) or (isinstance(value, dict) and len(value) < 5):
                print(f"     {key}: {value}")

    # Let system run for a bit to process feedback
    print("\n6. Processing feedback...")
    await asyncio.sleep(2)

    # Stop the system
    print("\nStopping AI/ML/RL System...")
    await ai_system.stop()
    print("System stopped successfully!")


if __name__ == "__main__":
    asyncio.run(main())
