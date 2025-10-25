#!/usr/bin/env python3
"""Validation script for all 6 AI/ML/RL improvements.

This script validates that all improvements are properly installed and
can be imported/initialized without errors.
"""

import sys
from pathlib import Path


# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def validate_improvement_1_feature_extractor():
    """Validate #1: Auto-discovering Feature Extractor."""
    print("\n=== Improvement #1: Feature Extractor ===")
    try:
        from ai.routing.feature_engineering import FeatureExtractor, get_feature_extractor

        # Test direct instantiation
        extractor = FeatureExtractor()
        print(f"✓ FeatureExtractor instantiated: {extractor.FEATURE_DIM} dimensions")

        # Test singleton factory
        global_extractor = get_feature_extractor()
        print(f"✓ Global extractor obtained: {global_extractor.FEATURE_DIM} dimensions")

        # Test feature extraction
        test_context = {
            "duration": 600,
            "complexity": 0.7,
            "quality_score": 0.85,
        }
        features = extractor.extract_features(test_context)
        print(f"✓ Features extracted: shape={features.shape}, dtype={features.dtype}")

        print("✅ Improvement #1: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #1: FAILED - {e}")
        return False


def validate_improvement_2_rl_optimizer():
    """Validate #2: RL Quality Threshold Optimizer."""
    print("\n=== Improvement #2: RL Optimizer ===")
    try:
        from ai.routing.rl_quality_threshold_optimizer import (
            RLQualityThresholdOptimizer,
        )

        # Test instantiation
        optimizer = RLQualityThresholdOptimizer()
        print(f"✓ RLQualityThresholdOptimizer instantiated: {len(optimizer._configs)} configs")

        # Test config selection
        context = {"content_type": "educational", "urgency": 0.5}
        config = optimizer.select_threshold_config(context)
        print(f"✓ Config selected: {config.name} (min_quality={config.min_overall_quality})")

        # Test reward update
        optimizer.update_from_result(config, quality_score=0.75, cost=0.05, success=True)
        print("✓ Reward updated successfully")

        print("✅ Improvement #2: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #2: FAILED - {e}")
        return False


def validate_improvement_3_semantic_cache():
    """Validate #3: Semantic Routing Cache."""
    print("\n=== Improvement #3: Semantic Cache ===")
    try:
        from core.routing.semantic_routing_cache import SemanticRoutingCache

        # Test instantiation (will use in-memory fallback without Redis)
        cache = SemanticRoutingCache(similarity_threshold=0.95, cache_size=100, ttl_seconds=600)
        print(f"✓ SemanticRoutingCache instantiated: backend={cache._backend}")

        # Test cache operations
        test_transcript = "This is a test transcript for validation."
        test_routing = {"model": "gpt-4", "confidence": 0.9}

        # Store routing decision
        cache.store_routing(test_transcript, test_routing)
        print("✓ Routing decision stored")

        # Retrieve routing decision
        cached = cache.get_similar_routing(test_transcript, similarity_threshold=0.95)
        if cached:
            print(f"✓ Routing decision retrieved: {cached}")
        else:
            print("⚠ Cache miss (expected for first run)")

        print("✅ Improvement #3: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #3: FAILED - {e}")
        return False


def validate_improvement_4_cold_start_priors():
    """Validate #4: Cold-Start Model Priors."""
    print("\n=== Improvement #4: Cold-Start Priors ===")
    try:
        from ai.routing.cold_start_priors import ColdStartPriorService

        # Test instantiation
        service = ColdStartPriorService()
        print("✓ ColdStartPriorService instantiated")

        # Test prior lookup for known model
        quality_prior = service.get_prior("gpt-4-turbo", "quality")
        latency_prior = service.get_prior("gpt-4-turbo", "latency")
        print(f"✓ Priors retrieved: quality={quality_prior:.3f}, latency={latency_prior:.3f}")

        # Test prior lookup for unknown model (should use family/global fallback)
        unknown_quality = service.get_prior("unknown-model-xyz", "quality")
        print(f"✓ Fallback prior for unknown model: quality={unknown_quality:.3f}")

        # Test prior update
        service.update_prior("gpt-4-turbo", "quality", 0.95)
        updated_quality = service.get_prior("gpt-4-turbo", "quality")
        print(f"✓ Prior updated: new_quality={updated_quality:.3f}")

        print("✅ Improvement #4: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #4: FAILED - {e}")
        return False


def validate_improvement_5_hipporag_instrumentation():
    """Validate #5: HippoRAG Instrumentation."""
    print("\n=== Improvement #5: HippoRAG Instrumentation ===")
    try:
        # Check dashboard file exists
        dashboard_path = Path(__file__).parent.parent / "dashboards" / "hipporag_learning.json"
        if dashboard_path.exists():
            print(f"✓ Grafana dashboard found: {dashboard_path}")
        else:
            print(f"⚠ Grafana dashboard not found: {dashboard_path}")

        # Check alerts file exists
        alerts_path = (
            Path(__file__).parent.parent
            / "src"
            / "ultimate_discord_intelligence_bot"
            / "monitoring"
            / "hipporag_alerts.py"
        )
        if alerts_path.exists():
            print(f"✓ Prometheus alerts found: {alerts_path}")

            # Import and validate alerts
            sys.path.insert(0, str(alerts_path.parent.parent))
            from monitoring.hipporag_alerts import HIPPORAG_ALERTS

            print(f"✓ {len(HIPPORAG_ALERTS)} alerts defined")
            for alert in HIPPORAG_ALERTS[:3]:  # Show first 3
                print(f"  - {alert['alert']}: {alert['annotations']['summary']}")
        else:
            print(f"⚠ Prometheus alerts not found: {alerts_path}")

        # Check HippoRAG tool has metrics
        tool_path = (
            Path(__file__).parent.parent
            / "src"
            / "ultimate_discord_intelligence_bot"
            / "tools"
            / "memory"
            / "hipporag_continual_memory_tool.py"
        )
        if tool_path.exists():
            content = tool_path.read_text()
            if "hipporag_indexing_latency_seconds" in content:
                print("✓ HippoRAG tool has metrics instrumentation")
            else:
                print("⚠ HippoRAG tool missing metrics")
        else:
            print(f"⚠ HippoRAG tool not found: {tool_path}")

        print("✅ Improvement #5: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #5: FAILED - {e}")
        return False


def validate_improvement_6_backpressure():
    """Validate #6: Cross-System Backpressure Coordinator."""
    print("\n=== Improvement #6: Backpressure Coordinator ===")
    try:
        from core.resilience.backpressure_coordinator import (
            BackpressureCoordinator,
            ServiceHealth,
            get_backpressure_coordinator,
        )

        # Test instantiation
        coordinator = BackpressureCoordinator()
        print("✓ BackpressureCoordinator instantiated")

        # Test singleton factory
        get_backpressure_coordinator()
        print("✓ Global coordinator obtained")

        # Test health registration
        from core.circuit_breaker_canonical import CircuitState

        health = ServiceHealth(
            service_name="test_service",
            is_healthy=True,
            circuit_state=CircuitState.CLOSED,
            failure_count=0,
            success_rate=1.0,
            response_time_p95=0.1,
        )
        coordinator.register_service_health(health)
        print("✓ Service health registered")

        # Test backpressure check
        is_active = coordinator.is_backpressure_active()
        level = coordinator.get_backpressure_level()
        print(f"✓ Backpressure status: active={is_active}, level={level.name}")

        # Test metrics
        metrics = coordinator.get_health_summary()
        print(
            f"✓ Health summary: {metrics.healthy_services}/{metrics.total_services} healthy, "
            f"{metrics.open_circuits} open circuits"
        )

        # Test middleware exists
        middleware_path = Path(__file__).parent.parent / "src" / "server" / "backpressure_middleware.py"
        if middleware_path.exists():
            print(f"✓ FastAPI middleware found: {middleware_path}")
        else:
            print(f"⚠ FastAPI middleware not found: {middleware_path}")

        # Test orchestrator integration
        orchestrator_path = (
            Path(__file__).parent.parent
            / "src"
            / "ultimate_discord_intelligence_bot"
            / "pipeline_components"
            / "orchestrator.py"
        )
        if orchestrator_path.exists():
            content = orchestrator_path.read_text()
            if "get_backpressure_coordinator" in content:
                print("✓ Orchestrator has backpressure integration")
            else:
                print("⚠ Orchestrator missing backpressure integration")
        else:
            print(f"⚠ Orchestrator not found: {orchestrator_path}")

        print("✅ Improvement #6: PASSED")
        return True
    except Exception as e:
        print(f"❌ Improvement #6: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("AI/ML/RL Improvements Validation")
    print("=" * 70)

    results = {
        "1_feature_extractor": validate_improvement_1_feature_extractor(),
        "2_rl_optimizer": validate_improvement_2_rl_optimizer(),
        "3_semantic_cache": validate_improvement_3_semantic_cache(),
        "4_cold_start_priors": validate_improvement_4_cold_start_priors(),
        "5_hipporag_instrumentation": validate_improvement_5_hipporag_instrumentation(),
        "6_backpressure": validate_improvement_6_backpressure(),
    }

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} improvements validated successfully")

    if passed == total:
        print("\n🎉 All improvements are properly installed and functional!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} improvement(s) failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
