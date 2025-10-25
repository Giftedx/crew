"""Example: Advanced feedback loop integration."""

import asyncio
import random
from typing import Any

from src.ai.integration.ai_ml_rl_integration import get_ai_integration


class MockTaskExecutor:
    """Mock task executor to demonstrate feedback loop."""

    def __init__(self, ai_system):
        """Initialize executor with AI system."""
        self.ai_system = ai_system
        self.execution_count = 0

    async def execute_analysis_task(self, content: str, complexity: float, required_accuracy: float) -> dict[str, Any]:
        """Execute an analysis task using AI routing."""
        self.execution_count += 1

        # Use AI system to select best tool
        tool_result = await self.ai_system.route_tool(
            task_description=f"Analyze content: {content[:50]}...",
            context={
                "complexity": complexity,
                "data_size": len(content),
                "required_accuracy": required_accuracy,
                "urgency": 0.5,
            },
            task_type="analysis",
        )

        if not tool_result.success:
            return {"success": False, "error": "Failed to route tool"}

        tool_selection = tool_result.data

        # Simulate tool execution
        execution_time = random.uniform(500, 2000)  # ms
        quality = random.uniform(0.7, 0.95)
        success = quality > 0.75

        # Submit feedback
        self.ai_system.submit_tool_feedback(
            tool_id=tool_selection.tool_id,
            context={"complexity": complexity},
            success=success,
            latency_ms=execution_time,
            quality_score=quality,
        )

        return {
            "success": success,
            "tool_used": tool_selection.tool_id,
            "execution_time_ms": execution_time,
            "quality_score": quality,
        }

    async def execute_verification_task(self, claims: list, urgency: float) -> dict[str, Any]:
        """Execute a verification task using AI routing."""
        self.execution_count += 1

        # Use AI system to select best agent
        agent_result = await self.ai_system.route_agent(
            task_description=f"Verify {len(claims)} claims",
            context={
                "complexity": 0.8,
                "urgency": urgency,
                "required_accuracy": 0.95,
                "data_volume": len(claims) / 10.0,
            },
            task_type="verification",
        )

        if not agent_result.success:
            return {"success": False, "error": "Failed to route agent"}

        agent_selection = agent_result.data

        # Simulate agent execution
        duration = random.uniform(30, 90)  # seconds
        quality = random.uniform(0.8, 0.98)
        success = quality > 0.85

        # Submit feedback
        self.ai_system.submit_agent_feedback(
            agent_id=agent_selection.agent_id,
            context={"urgency": urgency},
            success=success,
            duration_s=duration,
            quality_score=quality,
        )

        return {
            "success": success,
            "agent_used": agent_selection.agent_id,
            "duration_s": duration,
            "quality_score": quality,
            "verified_claims": len(claims),
        }


async def run_continuous_feedback_loop():
    """Demonstrate continuous feedback loop with adaptive routing."""
    # Initialize system
    ai_system = get_ai_integration()
    await ai_system.start()
    executor = MockTaskExecutor(ai_system)

    print("Starting Continuous Feedback Loop Demo")
    print("=" * 60)

    # Run multiple iterations
    for iteration in range(10):
        print(f"\nIteration {iteration + 1}/10")
        print("-" * 60)

        # Execute various tasks
        tasks = []

        # Analysis tasks with varying complexity
        for _ in range(2):
            complexity = random.uniform(0.4, 0.9)
            task = executor.execute_analysis_task(
                content="Sample content " * 100, complexity=complexity, required_accuracy=0.85
            )
            tasks.append(task)

        # Verification tasks
        task = executor.execute_verification_task(
            claims=["claim1", "claim2", "claim3"], urgency=random.uniform(0.5, 0.9)
        )
        tasks.append(task)

        # Execute all tasks
        results = await asyncio.gather(*tasks)

        # Print results
        for i, result in enumerate(results):
            if result["success"]:
                tool_or_agent = result.get("tool_used") or result.get("agent_used")
                quality = result["quality_score"]
                print(f"  Task {i + 1}: {tool_or_agent[:20]:20} | Quality: {quality:.2f}")
            else:
                print(f"  Task {i + 1}: FAILED - {result.get('error')}")

        # Let system process feedback
        await asyncio.sleep(1)

        # Every 3 iterations, show metrics
        if (iteration + 1) % 3 == 0:
            print("\n  Current Metrics:")
            metrics = await ai_system.get_aggregate_metrics()

            if "orchestrator" in metrics:
                orch_metrics = metrics["orchestrator"]
                print(f"    Signals processed: {orch_metrics.get('signals_processed', 0)}")
                print(f"    Consolidations: {orch_metrics.get('consolidations_triggered', 0)}")

            if "tool_router" in metrics:
                tool_metrics = metrics["tool_router"]
                print(f"    Total tools: {tool_metrics.get('total_tools', 0)}")

    print("\n" + "=" * 60)
    print(f"Total tasks executed: {executor.execution_count}")
    print("\nFinal Metrics:")
    final_metrics = await ai_system.get_aggregate_metrics()

    for component, comp_metrics in final_metrics.items():
        if isinstance(comp_metrics, dict):
            print(f"\n{component}:")
            for key, value in comp_metrics.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")

    # Cleanup
    await ai_system.stop()
    print("\nSystem stopped successfully!")


if __name__ == "__main__":
    asyncio.run(run_continuous_feedback_loop())
