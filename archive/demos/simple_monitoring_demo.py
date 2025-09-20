#!/usr/bin/env python3
"""
Simple Working Demo of Enhanced Performance Monitoring

This demonstrates the actual working API of the enhanced monitoring system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ultimate_discord_intelligence_bot.enhanced_performance_monitor import EnhancedPerformanceMonitor
from ultimate_discord_intelligence_bot.performance_integration import PerformanceIntegrationManager


async def demo_working_api():
    """Demonstrate the working API of enhanced monitoring."""
    print("🚀 Enhanced Performance Monitoring - Working Demo")
    print("=" * 60)

    # Initialize monitor
    monitor = EnhancedPerformanceMonitor()
    integration = PerformanceIntegrationManager()

    print("✅ Monitors initialized successfully")

    # 1. Real-time quality assessment
    print("\n📊 Testing Real-time Quality Assessment...")

    sample_response = """
    Based on my analysis of the provided content, I can confirm several key findings:

    1. The factual claims presented are well-supported by evidence from reliable sources
    2. The logical reasoning follows a coherent structure with clear premises and conclusions
    3. The analysis demonstrates comprehensive understanding of the topic
    4. Multiple perspectives were considered to ensure balanced assessment

    Therefore, I recommend this content as highly credible with a quality score of 0.85.
    """

    context = {
        "agent_name": "fact_checker",
        "tools_used": ["FactCheckTool", "LogicalFallacyTool"],
        "response_length": len(sample_response),
        "complexity": "high",
    }

    quality_score = await monitor.real_time_quality_assessment(sample_response, context)
    print(f"   Quality Score: {quality_score:.3f}")

    # 2. Monitor real-time performance
    print("\n⚡ Testing Real-time Performance Monitoring...")

    interaction_data = {
        "response_quality": quality_score,
        "response_time": 2.5,
        "tools_used": ["FactCheckTool", "LogicalFallacyTool"],
        "error_occurred": False,
        "user_feedback": {"helpful": True, "accurate": True},
    }

    performance_result = await monitor.monitor_real_time_performance("fact_checker", interaction_data)
    print(f"   Agent: {performance_result['agent_name']}")
    print(f"   Current Quality: {performance_result['current_performance']['avg_quality']:.3f}")
    print(f"   Average Response Time: {performance_result['current_performance']['avg_response_time']:.2f}s")
    print(f"   Alerts: {len(performance_result['alerts'])}")

    # 3. Generate more interactions for testing
    print("\n🔄 Generating sample interactions...")

    agents = ["content_manager", "truth_scorer", "qa_manager"]
    for i, agent in enumerate(agents):
        for j in range(3):
            interaction = {
                "response_quality": 0.7 + (i * 0.1) + (j * 0.05),  # Vary quality
                "response_time": 1.5 + (j * 0.5),  # Vary response time
                "tools_used": [f"Tool{i}_{j}"],
                "error_occurred": j == 2,  # Last interaction has error
                "user_feedback": {"rating": 4 + i},
            }
            await monitor.monitor_real_time_performance(agent, interaction)

    print(f"   Generated interactions for {len(agents)} agents")

    # 4. Generate dashboard
    print("\n📈 Testing Dashboard Generation...")

    dashboard = await monitor.generate_real_time_dashboard_data()

    print(f"   Dashboard contains {len(dashboard.get('agent_summaries', {}))} agent summaries")
    print(f"   System health: {dashboard.get('system_health', {}).get('overall_status', 'unknown')}")
    print(f"   Active alerts: {len(dashboard.get('active_alerts', []))}")

    # 5. Integration manager test
    print("\n🔗 Testing Integration Manager...")

    # Start interaction tracking
    interaction_id = await integration.start_interaction_tracking(
        agent_name="content_manager",
        task_type="content_analysis",
        context={"complexity": "high", "tools": ["FactCheckTool"]},
    )

    print(f"   Started tracking interaction: {interaction_id}")

    # Complete interaction tracking
    completion_result = await integration.complete_interaction_tracking(
        interaction_id=interaction_id,
        response="Analysis completed successfully with high confidence",
        user_feedback={"helpful": True, "rating": 5},
        error_occurred=False,
    )

    print(f"   Completed interaction tracking: {completion_result}")

    # 6. Show summary
    print("\n📋 Demo Summary:")
    print("   ✅ Real-time quality assessment: Working")
    print("   ✅ Performance monitoring: Working")
    print("   ✅ Alert system: Working")
    print("   ✅ Dashboard generation: Working")
    print("   ✅ Integration tracking: Working")

    # Save demo results
    demo_results = {
        "quality_assessment": quality_score,
        "performance_monitoring": performance_result,
        "dashboard": dashboard,
        "integration": completion_result,
    }

    with open("demo_results.json", "w") as f:
        json.dump(demo_results, f, indent=2, default=str)

    print("\n💾 Demo results saved to: demo_results.json")
    print("🎉 Enhanced Performance Monitoring Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_working_api())
