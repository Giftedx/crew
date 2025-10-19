#!/usr/bin/env python3
"""
Minimal Phase 2 Implementation Tests

This script provides minimal functionality tests for Phase 2 components
that actually exist and work.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.agents.workflow_manager import (
    WorkflowManagerAgent,
)
from ultimate_discord_intelligence_bot.services.rl_cache_optimizer import (
    CacheContext,
    RLCacheOptimizer,
)
from ultimate_discord_intelligence_bot.services.rl_model_router import (
    RLModelRouter,
    RoutingContext,
    TaskComplexity,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_workflow_manager():
    """Test Workflow Manager Agent with simple data."""
    logger.info("Testing Workflow Manager Agent...")

    manager = WorkflowManagerAgent()

    # Test task routing with simple data
    workflow_execution = {
        "tasks": [
            {
                "id": "task1",
                "name": "Test Task",
                "description": "Simple test task",
                "required_capabilities": ["test_capability"],
                "dependencies": [],
                "priority": 1,
            }
        ]
    }

    available_agents = [
        {
            "id": "agent1",
            "name": "Test Agent",
            "capabilities": ["test_capability"],
            "load": 0.1,
        }
    ]

    try:
        result = await manager.route_tasks(
            workflow_execution, available_agents, "test_tenant", "test_workspace"
        )
        if result.success:
            logger.info("✅ Task Routing - PASSED")
            return True
        else:
            logger.error(f"❌ Task Routing - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Task Routing - ERROR: {str(e)}")
        return False


async def test_rl_model_router():
    """Test RL Model Router with proper RoutingContext."""
    logger.info("Testing RL Model Router...")

    router = RLModelRouter()

    # Test model routing with proper RoutingContext
    context = RoutingContext(
        task_type="text_generation",
        complexity=TaskComplexity.MODERATE,
        token_estimate=1000,
        latency_requirement_ms=2000,
        cost_budget_usd=0.05,
        quality_requirement=0.8,
        tenant="test_tenant",
        workspace="test_workspace",
    )

    try:
        result = await router.route_request(context)
        if result.success:
            logger.info("✅ Model Routing - PASSED")
            return True
        else:
            logger.error(f"❌ Model Routing - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Model Routing - ERROR: {str(e)}")
        return False


async def test_rl_cache_optimizer():
    """Test RL Cache Optimizer with proper CacheContext."""
    logger.info("Testing RL Cache Optimizer...")

    optimizer = RLCacheOptimizer()

    # Test cache optimization with proper CacheContext
    context = CacheContext(
        key_pattern="test_key_*",
        access_frequency=0.8,
        data_size=1024,
        time_since_last_access=60.0,
        time_of_day=12,
        day_of_week=1,
        tenant="test_tenant",
        workspace="test_workspace",
    )

    try:
        result = await optimizer.optimize_cache_operation(context, "read")
        if result.success:
            logger.info("✅ Cache Optimization - PASSED")
            return True
        else:
            logger.error(f"❌ Cache Optimization - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Cache Optimization - ERROR: {str(e)}")
        return False


async def main():
    """Run all minimal tests."""
    logger.info("Starting Minimal Phase 2 Implementation Tests")
    logger.info("=" * 60)

    test_results = {}

    # Run tests for components that actually work
    test_results["workflow_manager"] = await test_workflow_manager()
    test_results["rl_model_router"] = await test_rl_model_router()
    test_results["rl_cache_optimizer"] = await test_rl_cache_optimizer()

    # Generate summary
    logger.info("\n" + "=" * 60)
    logger.info("MINIMAL PHASE 2 TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    for component, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{component.replace('_', ' ').title()}: {status}")

    logger.info(
        f"\nOverall: {passed}/{total} components passed ({passed / total * 100:.1f}%)"
    )

    # Save results
    report_path = f"docs/minimal_phase2_test_report_{int(time.time())}.json"
    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "test_results": test_results,
                "summary": {
                    "passed": passed,
                    "total": total,
                    "success_rate": passed / total * 100,
                },
            },
            f,
            indent=2,
        )

    logger.info(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
