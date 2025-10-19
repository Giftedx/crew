#!/usr/bin/env python3
"""
Simple Phase 2 Implementation Tests

This script provides basic functionality tests for Phase 2 components
without complex data structures that may cause issues.
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

from ultimate_discord_intelligence_bot.agents.executive_supervisor import (
    ExecutiveSupervisorAgent,
)
from ultimate_discord_intelligence_bot.agents.workflow_manager import (
    WorkflowManagerAgent,
)
from ultimate_discord_intelligence_bot.services.hierarchical_orchestrator import (
    HierarchicalOrchestrator,
)
from ultimate_discord_intelligence_bot.services.rl_cache_optimizer import (
    RLCacheOptimizer,
)
from ultimate_discord_intelligence_bot.services.rl_model_router import RLModelRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_executive_supervisor():
    """Test Executive Supervisor Agent with simple data."""
    logger.info("Testing Executive Supervisor Agent...")

    supervisor = ExecutiveSupervisorAgent()

    # Test strategic planning with simple data
    mission_context = "Test mission for validation"
    objectives = [
        {
            "id": "obj1",
            "title": "Test Objective 1",
            "description": "Simple test objective",
            "priority": 1,
            "dependencies": [],
        }
    ]

    try:
        result = await supervisor.execute_strategic_planning(
            mission_context, objectives, "test_tenant", "test_workspace"
        )
        if result.success:
            logger.info("✅ Strategic Planning - PASSED")
            return True
        else:
            logger.error(f"❌ Strategic Planning - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Strategic Planning - ERROR: {str(e)}")
        return False


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


async def test_hierarchical_orchestrator():
    """Test Hierarchical Orchestrator with simple data."""
    logger.info("Testing Hierarchical Orchestrator...")

    orchestrator = HierarchicalOrchestrator()

    # Test mission creation with simple data
    mission_context = "Test orchestration mission"
    objectives = [
        {
            "id": "obj1",
            "title": "Test Objective",
            "description": "Simple test objective",
            "priority": 1,
            "dependencies": [],
        }
    ]

    available_agents = [
        {
            "id": "agent1",
            "name": "Test Agent",
            "capabilities": ["test_capability"],
            "load": 0.1,
        }
    ]

    available_resources = {"cpu_units": 100, "memory_mb": 8192, "gpu_hours": 10}

    try:
        result = await orchestrator.start_intelligence_mission(
            mission_context,
            objectives,
            available_agents,
            available_resources,
            "test_tenant",
            "test_workspace",
        )
        if result.success:
            logger.info("✅ Mission Orchestration - PASSED")
            return True
        else:
            logger.error(f"❌ Mission Orchestration - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Mission Orchestration - ERROR: {str(e)}")
        return False


async def test_rl_model_router():
    """Test RL Model Router with simple data."""
    logger.info("Testing RL Model Router...")

    router = RLModelRouter()

    # Test model routing with simple context
    task_context = {
        "task_complexity": 0.5,
        "latency_requirement": 1000,
        "cost_budget": 0.05,
        "security_level": 3,
    }

    try:
        result = await router.route_request(task_context)
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
    """Test RL Cache Optimizer with simple data."""
    logger.info("Testing RL Cache Optimizer...")

    optimizer = RLCacheOptimizer()

    # Test cache operations
    context = {"data_freshness_requirement": 0.8, "expected_access_frequency": 0.6}

    try:
        # Test cache set
        result = await optimizer.set("test_key", "test_value", context)
        if result.success:
            logger.info("✅ Cache Set - PASSED")

            # Test cache get
            result = await optimizer.get("test_key")
            if result.success:
                logger.info("✅ Cache Get - PASSED")
                return True
            else:
                logger.error(f"❌ Cache Get - FAILED: {result.error}")
                return False
        else:
            logger.error(f"❌ Cache Set - FAILED: {result.error}")
            return False
    except Exception as e:
        logger.error(f"❌ Cache Operations - ERROR: {str(e)}")
        return False


async def main():
    """Run all simple tests."""
    logger.info("Starting Simple Phase 2 Implementation Tests")
    logger.info("=" * 60)

    test_results = {}

    # Run tests
    test_results["executive_supervisor"] = await test_executive_supervisor()
    test_results["workflow_manager"] = await test_workflow_manager()
    test_results["hierarchical_orchestrator"] = await test_hierarchical_orchestrator()
    test_results["rl_model_router"] = await test_rl_model_router()
    test_results["rl_cache_optimizer"] = await test_rl_cache_optimizer()

    # Generate summary
    logger.info("\n" + "=" * 60)
    logger.info("SIMPLE PHASE 2 TEST SUMMARY")
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
    report_path = f"docs/simple_phase2_test_report_{int(time.time())}.json"
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
