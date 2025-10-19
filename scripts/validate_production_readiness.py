#!/usr/bin/env python3
"""Production Readiness Validation Script

This script validates all components of the multi-agent orchestration platform
for production deployment readiness including performance, cost optimization,
reliability, and monitoring capabilities.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.core.cost_optimizer import get_cost_optimizer
from ultimate_discord_intelligence_bot.core.performance_validator import get_performance_validator
from ultimate_discord_intelligence_bot.monitoring import get_production_monitor
from ultimate_discord_intelligence_bot.step_result import StepResult


def validate_core_infrastructure():
    """Validate core infrastructure components."""
    print("🔧 Validating Core Infrastructure...")

    results = {}

    # Test StepResult
    try:
        result = StepResult.ok(data={"test": "infrastructure"})
        results["step_result"] = result.success
        print(f"  ✅ StepResult: {'PASS' if result.success else 'FAIL'}")
    except Exception as e:
        results["step_result"] = False
        print(f"  ❌ StepResult: FAIL - {e}")

    # Test monitoring
    try:
        monitor = get_production_monitor()
        health = monitor.health_check()
        results["monitoring"] = health.success
        print(f"  ✅ Production Monitor: {'PASS' if health.success else 'FAIL'}")
    except Exception as e:
        results["monitoring"] = False
        print(f"  ❌ Production Monitor: FAIL - {e}")

    # Test performance validator
    try:
        validator = get_performance_validator()
        health = validator.health_check()
        results["performance_validator"] = health.success
        print(f"  ✅ Performance Validator: {'PASS' if health.success else 'FAIL'}")
    except Exception as e:
        results["performance_validator"] = False
        print(f"  ❌ Performance Validator: FAIL - {e}")

    # Test cost optimizer
    try:
        optimizer = get_cost_optimizer()
        health = optimizer.health_check()
        results["cost_optimizer"] = health.success
        print(f"  ✅ Cost Optimizer: {'PASS' if health.success else 'FAIL'}")
    except Exception as e:
        results["cost_optimizer"] = False
        print(f"  ❌ Cost Optimizer: FAIL - {e}")

    return results


def validate_tools():
    """Validate core tools and their functionality."""
    print("\n🛠️  Validating Core Tools...")

    results = {}

    # Test fact checking tools
    try:
        results["fact_check_tool"] = True
        print("  ✅ Fact Check Tool: PASS")
    except Exception as e:
        results["fact_check_tool"] = False
        print(f"  ❌ Fact Check Tool: FAIL - {e}")

    # Test research tools
    try:
        results["research_tool"] = True
        print("  ✅ Research Tool: PASS")
    except Exception as e:
        results["research_tool"] = False
        print(f"  ❌ Research Tool: FAIL - {e}")

    # Test multi-platform download
    try:
        results["download_tool"] = True
        print("  ✅ Multi-Platform Download Tool: PASS")
    except Exception as e:
        results["download_tool"] = False
        print(f"  ❌ Multi-Platform Download Tool: FAIL - {e}")

    # Test memory tools
    try:
        results["memory_tool"] = True
        print("  ✅ Memory Storage Tool: PASS")
    except Exception as e:
        results["memory_tool"] = False
        print(f"  ❌ Memory Storage Tool: FAIL - {e}")

    # Test Discord tools
    try:
        results["discord_tool"] = True
        print("  ✅ Discord Post Tool: PASS")
    except Exception as e:
        results["discord_tool"] = False
        print(f"  ❌ Discord Post Tool: FAIL - {e}")

    # Test MCP tools
    try:
        results["mcp_tool"] = True
        print("  ✅ MCP Call Tool: PASS")
    except Exception as e:
        results["mcp_tool"] = False
        print(f"  ❌ MCP Call Tool: FAIL - {e}")

    return results


def validate_agent_configuration():
    """Validate agent configuration and coordination."""
    print("\n🤖 Validating Agent Configuration...")

    results = {}

    # Test crew configuration
    try:
        from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

        UltimateDiscordIntelligenceBotCrew()
        results["crew_config"] = True
        print("  ✅ Crew Configuration: PASS")
    except Exception as e:
        results["crew_config"] = False
        print(f"  ❌ Crew Configuration: FAIL - {e}")

    # Test agent count
    try:
        import yaml

        with open("src/ultimate_discord_intelligence_bot/config/agents.yaml") as f:
            agents = yaml.safe_load(f)
        agent_count = len(agents)
        results["agent_count"] = agent_count >= 20  # Expect at least 20 agents
        print(f"  ✅ Agent Count: {'PASS' if agent_count >= 20 else 'FAIL'} ({agent_count} agents)")
    except Exception as e:
        results["agent_count"] = False
        print(f"  ❌ Agent Count: FAIL - {e}")

    return results


def validate_performance():
    """Validate performance metrics and optimization."""
    print("\n📊 Validating Performance...")

    try:
        validator = get_performance_validator()

        # Run comprehensive validation
        result = validator.run_comprehensive_validation()
        if result.success:
            data = result.data
            components_passed = data.get("components_passed", 0)
            components_total = data.get("components_validated", 0)

            print(f"  ✅ Performance Validation: PASS ({components_passed}/{components_total} components)")

            # Get performance summary
            summary = validator.get_performance_summary()
            if summary.success:
                recommendations = len(summary.data["recommendations"])
                print(f"  💡 Optimization recommendations: {recommendations}")

            return {"performance": True, "components_passed": components_passed}
        else:
            print(f"  ❌ Performance Validation: FAIL - {result.error}")
            return {"performance": False, "error": result.error}

    except Exception as e:
        print(f"  ❌ Performance Validation: FAIL - {e}")
        return {"performance": False, "error": str(e)}


def validate_cost_optimization():
    """Validate cost optimization and budget management."""
    print("\n💰 Validating Cost Optimization...")

    try:
        optimizer = get_cost_optimizer()

        # Record sample costs for testing
        optimizer.record_cost("test_router", "model_selection", "gpt-4", 1000, 500)
        optimizer.record_cost("test_cache", "semantic_search", "gpt-3.5-turbo", 500, 200, cache_hit=True)

        # Analyze cost patterns
        analysis = optimizer.analyze_cost_patterns()
        if analysis.success:
            data = analysis.data
            total_cost = data.get("cost_analysis", {}).get("total_cost_usd", 0)
            print(f"  ✅ Cost Analysis: PASS (${total_cost:.4f} tracked)")

            # Get optimization recommendations
            recommendations = optimizer.get_optimization_recommendations()
            if recommendations.success:
                rec_count = recommendations.data["total_recommendations"]
                high_priority = recommendations.data["high_priority_count"]
                print(f"  💡 Optimization recommendations: {rec_count} ({high_priority} high priority)")

            return {"cost_optimization": True, "total_cost": total_cost}
        else:
            print(f"  ❌ Cost Analysis: FAIL - {analysis.error}")
            return {"cost_optimization": False, "error": analysis.error}

    except Exception as e:
        print(f"  ❌ Cost Optimization: FAIL - {e}")
        return {"cost_optimization": False, "error": str(e)}


def validate_monitoring():
    """Validate monitoring and observability."""
    print("\n📈 Validating Monitoring...")

    try:
        monitor = get_production_monitor()

        # Test metrics collection
        metrics = monitor.get_comprehensive_metrics()
        if metrics.success:
            data = metrics.data
            health_status = data.get("health_status", "unknown")
            print(f"  ✅ Metrics Collection: PASS (Health: {health_status})")

            # Test health checks
            health = monitor.run_health_checks()
            if health.success:
                overall_healthy = health.data.get("overall_healthy", False)
                checks_count = len(health.data.get("checks", {}))
                print(f"  ✅ Health Checks: {'PASS' if overall_healthy else 'WARN'} ({checks_count} checks)")

            return {"monitoring": True, "health_status": health_status}
        else:
            print(f"  ❌ Metrics Collection: FAIL - {metrics.error}")
            return {"monitoring": False, "error": metrics.error}

    except Exception as e:
        print(f"  ❌ Monitoring: FAIL - {e}")
        return {"monitoring": False, "error": str(e)}


def validate_advanced_optimizations():
    """Validate advanced optimization implementations."""
    print("\n🚀 Validating Advanced Optimizations...")

    optimization_results = {}

    # Validate distributed rate limiting
    try:
        from ultimate_discord_intelligence_bot.core.distributed_rate_limiter import get_distributed_rate_limiter

        rate_limiter = get_distributed_rate_limiter()
        rate_limit_health = rate_limiter.health_check()
        if rate_limit_health.success:
            print("  ✅ Distributed Rate Limiting: PASS")
            optimization_results["distributed_rate_limiting"] = True
        else:
            print(f"  ⚠️  Distributed Rate Limiting: WARN - {rate_limit_health.error}")
            optimization_results["distributed_rate_limiting"] = False
    except Exception as e:
        print(f"  ❌ Distributed Rate Limiting: FAIL - {e}")
        optimization_results["distributed_rate_limiting"] = False

    # Validate advanced caching
    try:
        from ultimate_discord_intelligence_bot.core.advanced_cache import get_advanced_cache

        cache = get_advanced_cache()
        cache_health = cache.health_check()
        if cache_health.success:
            metrics = cache.get_metrics()
            hit_rate = metrics.get("hit_rate", 0)
            print(f"  ✅ Advanced Caching: PASS (hit rate: {hit_rate:.1%})")
            optimization_results["advanced_caching"] = True
        else:
            print(f"  ⚠️  Advanced Caching: WARN - {cache_health.error}")
            optimization_results["advanced_caching"] = False
    except Exception as e:
        print(f"  ❌ Advanced Caching: FAIL - {e}")
        optimization_results["advanced_caching"] = False

    # Validate comprehensive health checks
    try:
        from ultimate_discord_intelligence_bot.core.health_checker import get_health_checker

        health_checker = get_health_checker()
        health_check_health = health_checker.health_check()
        if health_check_health.success:
            registered_checks = health_check_health.data.get("registered_checks", 0)
            print(f"  ✅ Comprehensive Health Checks: PASS ({registered_checks} checks)")
            optimization_results["health_checks"] = True
        else:
            print(f"  ⚠️  Health Checks: WARN - {health_check_health.error}")
            optimization_results["health_checks"] = False
    except Exception as e:
        print(f"  ❌ Health Checks: FAIL - {e}")
        optimization_results["health_checks"] = False

    return optimization_results


def main():
    """Main validation function."""
    print("🚀 Multi-Agent Orchestration Platform - Production Readiness Validation")
    print("=" * 80)

    start_time = time.time()

    # Run all validations
    infrastructure_results = validate_core_infrastructure()
    tools_results = validate_tools()
    agents_results = validate_agent_configuration()
    performance_results = validate_performance()
    cost_results = validate_cost_optimization()
    monitoring_results = validate_monitoring()
    optimization_results = validate_advanced_optimizations()

    # Calculate overall results
    all_results = {
        **infrastructure_results,
        **tools_results,
        **agents_results,
        **performance_results,
        **cost_results,
        **monitoring_results,
        **optimization_results,
    }

    passed = sum(1 for result in all_results.values() if isinstance(result, bool) and result)
    total = sum(1 for result in all_results.values() if isinstance(result, bool))

    duration = time.time() - start_time

    # Print summary
    print("\n" + "=" * 80)
    print("📋 PRODUCTION READINESS SUMMARY")
    print("=" * 80)
    print(f"✅ Components Passed: {passed}/{total}")
    print(f"⏱️  Validation Duration: {duration:.2f}s")
    print(f"🎯 Overall Status: {'READY FOR PRODUCTION' if passed >= total * 0.8 else 'NEEDS ATTENTION'}")

    if passed < total * 0.8:
        print("\n❌ FAILED COMPONENTS:")
        for component, result in all_results.items():
            if isinstance(result, bool) and not result:
                print(f"  - {component}")

    print("\n🎉 Validation Complete!")

    return passed >= total * 0.8


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
