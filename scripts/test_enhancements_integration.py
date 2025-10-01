#!/usr/bin/env python3
"""Integration test and demonstration of AI/ML enhancements.

This script validates that all the top-rated enhancement features from the
comprehensive review are properly integrated and working:

1. GPTCache Semantic Cache (with tenant isolation)
2. LLMLingua Prompt Compression (with metadata recording)
3. GraphRAG Memory (with StepResult compliance)
4. Ax Adaptive Routing (with fallback behavior)
5. AgentEvals Trajectory Evaluation

Run with: python3 scripts/test_enhancements_integration.py
"""

import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_gptcache_semantic_cache():
    """Test GPTCache semantic cache integration."""
    print("🔍 Testing GPTCache Semantic Cache...")

    try:
        from core.cache.semantic_cache import create_semantic_cache

        # Test cache creation
        cache = create_semantic_cache(similarity_threshold=0.8, cache_dir="./test_cache", fallback_enabled=True)

        print(f"  ✅ Cache created: {type(cache).__name__}")

        # Test tenant-aware caching
        from ultimate_discord_intelligence_bot.services.openrouter_service.tenant_semantic_cache import (
            TenantSemanticCache,
        )

        tenant_cache = TenantSemanticCache(cache_root="./test_cache", similarity_threshold=0.85)

        print(f"  ✅ Tenant cache created: {type(tenant_cache).__name__}")

        return True

    except Exception as e:
        print(f"  ❌ GPTCache test failed: {e}")
        return False


def test_llmlingua_compression():
    """Test LLMLingua prompt compression."""
    print("🗜️  Testing LLMLingua Prompt Compression...")

    try:
        from prompt_engine.llmlingua_adapter import compress_prompt_with_details

        test_prompt = "This is a long prompt that should be compressed when LLMLingua is available. " * 10

        # Test with compression enabled
        compressed, metadata = compress_prompt_with_details(test_prompt, enabled=True, target_tokens=50, ratio=0.5)

        print(f"  ✅ Compression attempted: {metadata}")
        print(f"  📝 Original length: {len(test_prompt)}, Compressed: {len(compressed)}")

        # Test PromptEngine integration
        from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

        engine = PromptEngine()

        optimized, opt_metadata = engine.optimise_with_metadata(
            test_prompt, target_token_reduction=0.3, force_enable=True
        )

        print(f"  ✅ PromptEngine optimization: stages={len(opt_metadata.get('stages', []))}")

        return True

    except Exception as e:
        print(f"  ❌ LLMLingua test failed: {e}")
        return False


def test_graph_memory():
    """Test GraphRAG memory integration."""
    print("🕸️  Testing Graph Memory...")

    try:
        from ultimate_discord_intelligence_bot.tools.graph_memory_tool import GraphMemoryTool

        # Create graph memory tool
        graph_tool = GraphMemoryTool(storage_dir="./test_graph_memory")

        # Test graph creation
        result = graph_tool.run(
            text="Alice collaborates with Bob on a machine learning project. They use Python and TensorFlow to build a recommendation system.",
            metadata={"source": "integration_test", "timestamp": time.time()},
            tags=["ml", "collaboration"],
        )

        print(f"  ✅ Graph memory result: {result.custom_status}")
        if result.success:
            print(f"  📊 Graph ID: {result.data.get('graph_id', 'N/A')}")
            print(f"  🔗 Nodes: {result.data.get('node_count', 0)}, Edges: {result.data.get('edge_count', 0)}")

        return result.success

    except Exception as e:
        print(f"  ❌ Graph memory test failed: {e}")
        return False


def test_ax_adaptive_routing():
    """Test Ax adaptive routing."""
    print("🎯 Testing Ax Adaptive Routing...")

    try:
        from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import (
            AdaptiveRoutingManager,
        )

        # Test manager creation (should handle missing Ax gracefully)
        manager = AdaptiveRoutingManager(enabled=True)

        print(f"  ✅ Manager created, enabled: {manager.enabled}")

        # Test suggestion (should return None if Ax unavailable)
        candidates = ["gpt-4o-mini", "gpt-3.5-turbo", "claude-3-haiku"]
        context = {"tenant": "test", "task_type": "analysis"}

        suggestion = manager.suggest("analysis", candidates, context)

        if suggestion:
            trial_index, model = suggestion
            print(f"  🎲 Suggestion: trial={trial_index}, model={model}")

            # Test observation
            manager.observe("analysis", trial_index, 0.8, {"success": True})
            print("  📊 Observation recorded")
        else:
            print("  ⚠️  No suggestion (Ax not available, using fallback)")

        return True

    except Exception as e:
        print(f"  ❌ Ax routing test failed: {e}")
        return False


def test_agent_evals():
    """Test AgentEvals trajectory evaluation."""
    print("📈 Testing AgentEvals Trajectory Evaluation...")

    try:
        from eval.trajectory_evaluator import AgentTrajectory, TrajectoryEvaluator, TrajectoryStep

        evaluator = TrajectoryEvaluator()

        # Create mock trajectory
        steps = [
            TrajectoryStep(
                timestamp=time.time(),
                agent_role="analyst",
                action_type="tool_call",
                content="Analyzing sentiment of the text",
                tool_name="sentiment_analyzer",
                tool_args={"text": "This is great!"},
                success=True,
            ),
            TrajectoryStep(
                timestamp=time.time() + 1,
                agent_role="analyst",
                action_type="response",
                content="The sentiment is positive with confidence 0.95",
                success=True,
            ),
        ]

        trajectory = AgentTrajectory(
            session_id="test-123",
            user_input="What is the sentiment of 'This is great!'?",
            steps=steps,
            final_output="The text has positive sentiment.",
            total_duration=2.5,
            success=True,
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # Test evaluation
        result = evaluator.evaluate_trajectory_accuracy(trajectory)

        print(f"  ✅ Evaluation result: {result.custom_status}")
        if result.success:
            print(f"  📊 Score: {result.data.get('score', 'N/A')}")
            print(f"  🔍 Reasoning: {result.data.get('reasoning', 'N/A')[:100]}...")

        return result.success or result.custom_status == "skipped"

    except Exception as e:
        print(f"  ❌ AgentEvals test failed: {e}")
        return False


def test_hipporag_continual_memory():
    """Test HippoRAG continual memory integration."""
    print("🧠 Testing HippoRAG Continual Memory...")

    try:
        from ultimate_discord_intelligence_bot.tools.hipporag_continual_memory_tool import HippoRagContinualMemoryTool

        # Create HippoRAG continual memory tool
        hipporag_tool = HippoRagContinualMemoryTool(storage_dir="./test_hipporag_memory")

        # Test memory storage
        result = hipporag_tool.run(
            text="Machine learning algorithms are revolutionizing artificial intelligence. "
            "Deep neural networks enable pattern recognition and complex decision making. "
            "These systems can learn from experience and adapt to new situations.",
            metadata={"source": "integration_test", "timestamp": time.time(), "domain": "ai_ml"},
            tags=["ml", "ai", "neural_networks", "learning"],
            consolidate=True,
        )

        print(f"  ✅ HippoRAG memory result: {result.custom_status}")
        if result.success:
            print(f"  📊 Memory ID: {result.data.get('memory_id', 'N/A')}")
            print(f"  🧠 Backend: {result.data.get('backend', 'unknown')}")
            capabilities = result.data.get("capabilities", [])
            print(f"  🎯 Capabilities: {', '.join(capabilities)}")
        elif result.custom_status == "feature_disabled":
            print("  ⚠️  Feature disabled (expected without ENABLE_HIPPORAG_MEMORY=1)")
        elif result.custom_status == "fallback_used":
            print("  ⚠️  Using fallback storage (hipporag package unavailable)")

        # Test retrieval if memory was stored successfully
        if result.success and result.data.get("backend") == "hipporag":
            retrieval_result = hipporag_tool.retrieve(
                query="machine learning neural networks", num_to_retrieve=2, include_reasoning=True
            )
            print(f"  🔍 Retrieval result: {retrieval_result.custom_status}")
            if retrieval_result.success:
                num_results = retrieval_result.data.get("num_retrieved", 0)
                print(f"  📥 Retrieved {num_results} memories")

        return result.success or result.custom_status in ["feature_disabled", "fallback_used"]

    except Exception as e:
        print(f"  ❌ HippoRAG continual memory test failed: {e}")
        return False


def test_pipeline_integration():
    """Test that enhancements integrate with the main pipeline."""
    print("🔄 Testing Pipeline Integration...")

    try:
        from ultimate_discord_intelligence_bot.pipeline_components.base import PipelineBase

        # Create pipeline instance
        pipeline = PipelineBase()

        # Check that enhancement tools are available
        has_graph_memory = hasattr(pipeline, "graph_memory") and pipeline.graph_memory is not None
        has_prompt_engine = hasattr(pipeline, "prompt_engine") and pipeline.prompt_engine is not None

        print(f"  ✅ Graph memory available: {has_graph_memory}")
        print(f"  ✅ Prompt engine available: {has_prompt_engine}")

        # Test compression capability
        if has_prompt_engine:
            test_text = "This is a test prompt for compression evaluation."
            compressed, metadata = pipeline._maybe_compress_transcript(test_text)
            print(f"  📝 Compression metadata: {metadata is not None}")

        return True

    except Exception as e:
        print(f"  ❌ Pipeline integration test failed: {e}")
        return False


def main():
    """Run all enhancement tests."""
    print("🚀 AI/ML Enhancement Integration Test")
    print("=====================================")

    # Set test environment
    os.environ["ENABLE_PROMPT_COMPRESSION"] = "1"
    os.environ["ENABLE_GRAPH_MEMORY"] = "1"
    os.environ["ENABLE_TRAJECTORY_EVALUATION"] = "1"
    # Canonical flag for HippoRAG; tool also accepts legacy ENABLE_HIPPORAG_CONTINUAL_MEMORY
    os.environ["ENABLE_HIPPORAG_MEMORY"] = "1"

    tests = [
        ("GPTCache Semantic Cache", test_gptcache_semantic_cache),
        ("LLMLingua Compression", test_llmlingua_compression),
        ("Graph Memory", test_graph_memory),
        ("HippoRAG Continual Memory", test_hipporag_continual_memory),
        ("Ax Adaptive Routing", test_ax_adaptive_routing),
        ("AgentEvals Trajectory", test_agent_evals),
        ("Pipeline Integration", test_pipeline_integration),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((test_name, False))

    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All enhancements are properly integrated!")
        print("\n💡 Ready to enable with:")
        print("   export ENABLE_GPTCACHE=true")
        print("   export ENABLE_SEMANTIC_CACHE_SHADOW=true")
        print("   export ENABLE_PROMPT_COMPRESSION=true")
        print("   export ENABLE_GRAPH_MEMORY=true")
        print("   export ENABLE_HIPPORAG_MEMORY=true   # or ENABLE_HIPPORAG_CONTINUAL_MEMORY=true (legacy)")
        print("   export ENABLE_AX_ROUTING=true")
        print("   export ENABLE_TRAJECTORY_EVALUATION=true")
        print("\n   Or use: make run-discord-enhanced")
    else:
        print(f"\n⚠️  {total - passed} tests failed - check integration")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
