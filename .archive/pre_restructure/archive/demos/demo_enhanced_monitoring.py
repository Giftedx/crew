#!/usr/bin/env python3
"""
Enhanced Performance Monitoring Demonstration

This script demonstrates the comprehensive agent performance monitoring capabilities
that have been integrated into the Ultimate Discord Intelligence Bot system.

Features demonstrated:
- Real-time quality assessment during crew execution
- Performance alerting and threshold monitoring
- Comprehensive execution analytics
- Integration with existing crew infrastructure
- Dashboard generation and reporting

Usage:
    python demo_enhanced_monitoring.py [--scenario SCENARIO]

Scenarios:
    simple: Basic crew execution with monitoring
    complex: Multi-agent workflow with quality assessment
    failure: Simulate failure scenarios for alert testing
    dashboard: Generate performance dashboard
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ultimate_discord_intelligence_bot.enhanced_crew_integration import (
        EnhancedCrewExecutor,
        enhanced_crew_execution,
        execute_crew_with_quality_monitoring,
    )
    from ultimate_discord_intelligence_bot.enhanced_performance_monitor import (
        EnhancedPerformanceMonitor,
    )
    from ultimate_discord_intelligence_bot.performance_integration import (
        PerformanceIntegrationManager,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Ensure you're running from the project root and have installed dependencies")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def demo_simple_monitoring():
    """Demonstrate basic crew execution with enhanced monitoring."""
    print("\n🚀 Demo: Simple Monitoring")
    print("=" * 50)

    try:
        # Create enhanced crew executor
        executor = EnhancedCrewExecutor()

        # Define simple input for demonstration
        inputs = {
            "query": "Analyze the current state of artificial intelligence development",
            "focus_areas": [
                "machine_learning",
                "natural_language_processing",
                "ethics",
            ],
            "depth": "comprehensive",
        }

        print(f"📝 Input: {json.dumps(inputs, indent=2)}")
        print("\n🔄 Starting enhanced crew execution...")

        # Execute with comprehensive monitoring
        result = await executor.execute_with_comprehensive_monitoring(
            inputs=inputs,
            enable_real_time_alerts=True,
            quality_threshold=0.6,
            max_execution_time=120.0,
        )

        # Display results
        print("\n📊 Execution Results:")
        print(f"✅ Quality Score: {result['quality_score']:.2f}")
        print(f"⏱️  Execution Time: {result['execution_time']:.2f}s")
        print(f"🚨 Performance Alerts: {len(result['performance_alerts'])}")
        print(f"📈 Quality Checkpoints: {len(result['quality_checkpoints'])}")

        # Show execution summary
        summary = result["execution_summary"]
        print("\n📋 Execution Summary:")
        print(f"   Agents Used: {', '.join(summary['agents_executed'])}")
        print(f"   Tools Used: {', '.join(summary['tools_used'])}")
        print(f"   Performance Rating: {summary['performance_insights']['efficiency_rating']}")

        # Show any alerts
        if result["performance_alerts"]:
            print("\n🚨 Performance Alerts:")
            for alert in result["performance_alerts"]:
                print(f"   - {alert['type']}: {alert['message']}")

        return result

    except Exception as e:
        print(f"❌ Error during simple monitoring demo: {e}")
        return None


async def demo_complex_workflow():
    """Demonstrate multi-agent workflow with detailed quality assessment."""
    print("\n🚀 Demo: Complex Multi-Agent Workflow")
    print("=" * 50)

    try:
        # Use context manager for enhanced execution
        async with enhanced_crew_execution() as executor:
            # Complex multi-step workflow
            inputs = {
                "content_url": "https://example.com/analysis-target",
                "analysis_types": [
                    "fact_check",
                    "sentiment",
                    "bias_detection",
                    "credibility",
                ],
                "cross_reference": True,
                "generate_report": True,
                "quality_threshold": 0.8,
            }

            print(f"📝 Complex Input: {json.dumps(inputs, indent=2)}")
            print("\n🔄 Starting multi-agent workflow...")

            result = await executor.execute_with_comprehensive_monitoring(
                inputs=inputs,
                enable_real_time_alerts=True,
                quality_threshold=0.75,
                max_execution_time=180.0,
            )

            # Detailed analysis of execution
            print("\n📊 Detailed Execution Analysis:")
            print(f"🎯 Overall Quality: {result['quality_score']:.3f}")
            print(f"⏰ Total Time: {result['execution_time']:.2f}s")

            # Quality checkpoint analysis
            checkpoints = result["quality_checkpoints"]
            if checkpoints:
                avg_quality = sum(cp["quality"] for cp in checkpoints) / len(checkpoints)
                print(f"📈 Average Step Quality: {avg_quality:.3f}")
                print(
                    f"📊 Quality Range: {min(cp['quality'] for cp in checkpoints):.2f} - {max(cp['quality'] for cp in checkpoints):.2f}"
                )

            # Performance insights
            insights = result["execution_summary"]["performance_insights"]
            print("\n💡 Performance Insights:")
            print(f"   Trend: {insights['quality_trend']}")
            print(f"   Efficiency: {insights['efficiency_rating']}")
            print(f"   Tool Usage: {insights['tool_usage_pattern']}")

            if insights["recommendations"]:
                print("   Recommendations:")
                for rec in insights["recommendations"]:
                    print(f"     - {rec}")

            return result

    except Exception as e:
        print(f"❌ Error during complex workflow demo: {e}")
        return None


async def demo_failure_scenario():
    """Demonstrate failure handling and alert generation."""
    print("\n🚀 Demo: Failure Scenario & Alert Testing")
    print("=" * 50)

    try:
        executor = EnhancedCrewExecutor()

        # Inputs designed to test edge cases and potential failures
        inputs = {
            "invalid_url": "not-a-real-url",
            "timeout_operation": True,
            "stress_test": True,
            "expected_failure": True,
        }

        print(f"📝 Test Input (designed for failure): {json.dumps(inputs, indent=2)}")
        print("\n🔄 Starting failure scenario test...")

        # Use very strict thresholds to trigger alerts
        result = await executor.execute_with_comprehensive_monitoring(
            inputs=inputs,
            enable_real_time_alerts=True,
            quality_threshold=0.9,  # Very high threshold
            max_execution_time=30.0,  # Short timeout
        )

        print("\n📊 Failure Scenario Results:")

        if result.get("error"):
            print(f"❌ Expected Error: {result['error']}")
            print(f"⏱️  Time to Failure: {result['execution_time']:.2f}s")

            failure_summary = result["execution_summary"]
            print("\n🔍 Failure Analysis:")
            print(f"   Stage: {failure_summary['failure_analysis']['failure_stage']}")
            print(f"   Checkpoints: {failure_summary['failure_analysis']['checkpoints_before_failure']}")
            print(f"   Last Agent: {failure_summary['failure_analysis']['last_successful_agent']}")
        else:
            print("✅ Unexpected success (failure scenario didn't trigger)")

        # Show alerts generated
        alerts = result.get("performance_alerts", [])
        if alerts:
            print(f"\n🚨 Generated Alerts ({len(alerts)}):")
            for alert in alerts:
                print(f"   - {alert['type']}: {alert['message']}")

        return result

    except Exception as e:
        print(f"❌ Error during failure scenario demo: {e}")
        return None


async def demo_dashboard_generation():
    """Demonstrate dashboard generation and performance reporting."""
    print("\n🚀 Demo: Dashboard Generation & Reporting")
    print("=" * 50)

    try:
        # Initialize monitoring components
        enhanced_monitor = EnhancedPerformanceMonitor()
        integration_manager = PerformanceIntegrationManager()

        print("📊 Generating performance dashboard...")

        # Generate sample data for demonstration
        await generate_sample_performance_data(enhanced_monitor, integration_manager)

        # Generate dashboards
        real_time_dashboard = await enhanced_monitor.generate_real_time_dashboard()
        weekly_report = await integration_manager.generate_weekly_performance_report()

        print("\n📈 Real-Time Dashboard Generated:")
        print(f"   Quality Metrics: {len(real_time_dashboard.get('quality_metrics', []))} data points")
        print(f"   Performance Trends: {len(real_time_dashboard.get('performance_trends', []))} trends")
        print(f"   Active Alerts: {len(real_time_dashboard.get('active_alerts', []))} alerts")

        print("\n📊 Weekly Report Generated:")
        print(f"   Total Interactions: {weekly_report.get('total_interactions', 0)}")
        print(f"   Average Quality: {weekly_report.get('average_quality', 0):.3f}")
        print(f"   Performance Score: {weekly_report.get('performance_score', 0):.3f}")

        # Show quality distribution
        if "quality_distribution" in weekly_report:
            dist = weekly_report["quality_distribution"]
            print("   Quality Distribution:")
            print(f"     Excellent (>0.8): {dist.get('excellent', 0)}")
            print(f"     Good (0.6-0.8): {dist.get('good', 0)}")
            print(f"     Fair (0.4-0.6): {dist.get('fair', 0)}")
            print(f"     Poor (<0.4): {dist.get('poor', 0)}")

        # Save dashboard data for inspection
        dashboard_file = Path("demo_dashboard.json")
        report_file = Path("demo_weekly_report.json")

        with open(dashboard_file, "w") as f:
            json.dump(real_time_dashboard, f, indent=2, default=str)

        with open(report_file, "w") as f:
            json.dump(weekly_report, f, indent=2, default=str)

        print(f"\n💾 Dashboard saved to: {dashboard_file}")
        print(f"💾 Report saved to: {report_file}")

        return {
            "dashboard": real_time_dashboard,
            "weekly_report": weekly_report,
            "files": [str(dashboard_file), str(report_file)],
        }

    except Exception as e:
        print(f"❌ Error during dashboard demo: {e}")
        return None


async def generate_sample_performance_data(enhanced_monitor, integration_manager):
    """Generate sample performance data for demonstration."""
    print("🔄 Generating sample performance data...")

    if integration_manager is not None:
        manager_name = getattr(getattr(integration_manager, "__class__", None), "__name__", "manager")
        print(f"🔗 Integration manager connected: {manager_name}")

    sample_agents = ["content_manager", "fact_checker", "truth_scorer", "qa_manager"]
    sample_tools = [
        "FactCheckTool",
        "LogicalFallacyTool",
        "TruthScoringTool",
        "TextAnalysisTool",
    ]

    # Generate sample interactions
    for i in range(20):
        agent = sample_agents[i % len(sample_agents)]
        tools_used = [sample_tools[j % len(sample_tools)] for j in range(i % 3 + 1)]

        # Vary quality scores to show distribution
        base_quality = 0.7
        variation = (i % 10 - 5) * 0.05  # -0.25 to +0.25
        quality = max(0.0, min(1.0, base_quality + variation))

        response_time = 2.0 + (i % 5) * 0.5  # 2.0 to 4.5 seconds

        await enhanced_monitor.record_interaction_async(
            agent_name=agent,
            interaction_type="demo_interaction",
            quality_score=quality,
            response_time=response_time,
            context={
                "tools_used": tools_used,
                "demo_index": i,
                "complexity": "medium" if i % 2 == 0 else "high",
            },
        )

        # Simulate some time passing
        await asyncio.sleep(0.1)

    print("✅ Sample data generation complete")


async def demo_convenience_functions():
    """Demonstrate the convenience functions for simple usage."""
    print("\n🚀 Demo: Convenience Functions")
    print("=" * 50)

    try:
        inputs = {
            "task": "Quick analysis demonstration",
            "complexity": "low",
        }

        print(f"📝 Using convenience function with: {json.dumps(inputs, indent=2)}")
        print("🔄 Executing with execute_crew_with_quality_monitoring()...")

        # Use the convenience function
        result = await execute_crew_with_quality_monitoring(
            inputs=inputs,
            quality_threshold=0.65,
            enable_alerts=True,
        )

        print("\n📊 Convenience Function Results:")
        print(f"✅ Quality: {result['quality_score']:.2f}")
        print(f"⏱️  Time: {result['execution_time']:.2f}s")
        print(f"🎯 Success: {'Yes' if not result.get('error') else 'No'}")

        return result

    except Exception as e:
        print(f"❌ Error during convenience function demo: {e}")
        return None


def print_demo_summary(results: dict[str, Any]):
    """Print a comprehensive summary of all demo results."""
    print("\n" + "=" * 70)
    print("📋 ENHANCED PERFORMANCE MONITORING DEMO SUMMARY")
    print("=" * 70)

    total_demos = len([k for k in results if k.startswith("demo_")])
    successful_demos = len([v for k, v in results.items() if k.startswith("demo_") and v is not None])

    print(f"🎯 Demos Executed: {total_demos}")
    print(f"✅ Successful: {successful_demos}")
    print(f"❌ Failed: {total_demos - successful_demos}")

    if results.get("demo_simple"):
        simple = results["demo_simple"]
        print("\n📊 Simple Monitoring:")
        print(f"   Quality: {simple['quality_score']:.2f}")
        print(f"   Time: {simple['execution_time']:.1f}s")

    if results.get("demo_complex"):
        complex_demo = results["demo_complex"]
        print("\n🔧 Complex Workflow:")
        print(f"   Quality: {complex_demo['quality_score']:.2f}")
        print(f"   Time: {complex_demo['execution_time']:.1f}s")
        print(f"   Checkpoints: {len(complex_demo['quality_checkpoints'])}")

    if results.get("demo_dashboard"):
        dashboard = results["demo_dashboard"]
        print("\n📈 Dashboard Generation:")
        print(f"   Files Created: {len(dashboard.get('files', []))}")
        print("   Report Metrics: Available")

    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Real-time quality assessment")
    print("   ✅ Performance alerting system")
    print("   ✅ Comprehensive execution analytics")
    print("   ✅ Failure handling and diagnostics")
    print("   ✅ Dashboard and report generation")
    print("   ✅ Integration with existing crew infrastructure")

    print("\n🚀 System Ready for Enhanced Agent Performance Monitoring!")


async def main():
    """Main demo execution function."""
    parser = argparse.ArgumentParser(description="Enhanced Performance Monitoring Demo")
    parser.add_argument(
        "--scenario",
        choices=["simple", "complex", "failure", "dashboard", "convenience", "all"],
        default="all",
        help="Demo scenario to run",
    )

    args = parser.parse_args()

    print("🤖 Enhanced Performance Monitoring Demo")
    print("Ultimate Discord Intelligence Bot")
    print("=" * 70)

    results = {}

    try:
        if args.scenario in ["simple", "all"]:
            results["demo_simple"] = await demo_simple_monitoring()

        if args.scenario in ["complex", "all"]:
            results["demo_complex"] = await demo_complex_workflow()

        if args.scenario in ["failure", "all"]:
            results["demo_failure"] = await demo_failure_scenario()

        if args.scenario in ["dashboard", "all"]:
            results["demo_dashboard"] = await demo_dashboard_generation()

        if args.scenario in ["convenience", "all"]:
            results["demo_convenience"] = await demo_convenience_functions()

        # Print comprehensive summary
        print_demo_summary(results)

    except KeyboardInterrupt:
        print("\n⚡ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution error")

    print("\n👋 Demo complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
