#!/usr/bin/env python3
"""
Test Phase 2 Implementations - Comprehensive Validation

This script tests the Phase 2 implementations including:
- Executive Supervisor Agent
- Workflow Manager Agent
- Hierarchical Orchestrator
- RL Model Router
- RL Cache Optimizer
- Performance Learning Engine
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
from ultimate_discord_intelligence_bot.services.performance_learning_engine import (
    OptimizationGoal,
    OptimizationLevel,
    OptimizationRequest,
    PerformanceLearningEngine,
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class Phase2TestSuite:
    """Comprehensive test suite for Phase 2 implementations."""

    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {
            "executive_supervisor": {"passed": 0, "failed": 0, "tests": []},
            "workflow_manager": {"passed": 0, "failed": 0, "tests": []},
            "hierarchical_orchestrator": {"passed": 0, "failed": 0, "tests": []},
            "rl_model_router": {"passed": 0, "failed": 0, "tests": []},
            "rl_cache_optimizer": {"passed": 0, "failed": 0, "tests": []},
            "performance_learning_engine": {"passed": 0, "failed": 0, "tests": []},
        }

        # Initialize components
        self.executive_supervisor = ExecutiveSupervisorAgent()
        self.workflow_manager = WorkflowManagerAgent()
        self.orchestrator = HierarchicalOrchestrator()
        self.model_router = RLModelRouter()
        self.cache_optimizer = RLCacheOptimizer()
        self.performance_engine = PerformanceLearningEngine()

    async def run_all_tests(self):
        """Run all Phase 2 tests."""
        logger.info("Starting Phase 2 Implementation Tests")
        logger.info("=" * 60)

        # Test Executive Supervisor Agent
        await self.test_executive_supervisor()

        # Test Workflow Manager Agent
        await self.test_workflow_manager()

        # Test Hierarchical Orchestrator
        await self.test_hierarchical_orchestrator()

        # Test RL Model Router
        await self.test_rl_model_router()

        # Test RL Cache Optimizer
        await self.test_rl_cache_optimizer()

        # Test Performance Learning Engine
        await self.test_performance_learning_engine()

        # Generate final report
        self.generate_test_report()

    async def test_executive_supervisor(self):
        """Test Executive Supervisor Agent functionality."""
        logger.info("Testing Executive Supervisor Agent...")

        # Test 1: Strategic Planning
        try:
            mission_context = "Deploy enterprise intelligence platform with advanced agent orchestration"
            objectives = [
                {
                    "id": "obj_1",
                    "title": "Implement hierarchical orchestration",
                    "description": "Build supervisor-worker agent coordination",
                    "priority": 9,
                    "success_criteria": [
                        "95% task completion rate",
                        "Sub-second response times",
                    ],
                    "resource_requirements": {"cpu_cores": 8, "memory_gb": 16},
                    "timeline": "2 weeks",
                },
                {
                    "id": "obj_2",
                    "title": "Deploy RL optimization",
                    "description": "Implement reinforcement learning for model routing",
                    "priority": 8,
                    "success_criteria": ["30% cost reduction", "Improved accuracy"],
                    "resource_requirements": {"cpu_cores": 4, "memory_gb": 8},
                    "timeline": "1 week",
                },
            ]

            result = await self.executive_supervisor.execute_strategic_planning(
                mission_context, objectives, "test_tenant", "test_workspace"
            )

            if result.success and "strategic_plan" in result.data:
                self.test_results["executive_supervisor"]["passed"] += 1
                self.test_results["executive_supervisor"]["tests"].append(
                    {
                        "name": "Strategic Planning",
                        "status": "PASSED",
                        "details": f"Created plan with {len(result.data['strategic_plan']['objectives'])} objectives",
                    }
                )
            else:
                raise Exception(f"Strategic planning failed: {result.error}")

        except Exception as e:
            self.test_results["executive_supervisor"]["failed"] += 1
            self.test_results["executive_supervisor"]["tests"].append(
                {"name": "Strategic Planning", "status": "FAILED", "error": str(e)}
            )

        # Test 2: Resource Allocation
        try:
            allocation_requests = [
                {
                    "agent_id": "agent_1",
                    "cpu_cores": 4,
                    "memory_gb": 8,
                    "gpu_units": 1,
                    "network_bandwidth_mbps": 1000,
                    "storage_gb": 100,
                    "priority_level": 8,
                },
                {
                    "agent_id": "agent_2",
                    "cpu_cores": 2,
                    "memory_gb": 4,
                    "gpu_units": 0,
                    "network_bandwidth_mbps": 500,
                    "storage_gb": 50,
                    "priority_level": 6,
                },
            ]

            result = await self.executive_supervisor.allocate_resources(
                allocation_requests, "test_tenant", "test_workspace"
            )

            if result.success and "allocations" in result.data:
                self.test_results["executive_supervisor"]["passed"] += 1
                self.test_results["executive_supervisor"]["tests"].append(
                    {
                        "name": "Resource Allocation",
                        "status": "PASSED",
                        "details": f"Allocated resources for {len(result.data['allocations'])} agents",
                    }
                )
            else:
                raise Exception(f"Resource allocation failed: {result.error}")

        except Exception as e:
            self.test_results["executive_supervisor"]["failed"] += 1
            self.test_results["executive_supervisor"]["tests"].append(
                {"name": "Resource Allocation", "status": "FAILED", "error": str(e)}
            )

        # Test 3: Escalation Management
        try:
            escalation_context = "High error rate detected in model routing system"
            severity = "high"
            affected_components = ["model_router", "cache_optimizer"]

            result = await self.executive_supervisor.handle_escalation(
                escalation_context,
                severity,
                affected_components,
                "test_tenant",
                "test_workspace",
            )

            if result.success and "escalation_response" in result.data:
                self.test_results["executive_supervisor"]["passed"] += 1
                self.test_results["executive_supervisor"]["tests"].append(
                    {
                        "name": "Escalation Management",
                        "status": "PASSED",
                        "details": f"Handled {severity} escalation with {len(result.data['escalation_response']['response_actions'])} actions",
                    }
                )
            else:
                raise Exception(f"Escalation management failed: {result.error}")

        except Exception as e:
            self.test_results["executive_supervisor"]["failed"] += 1
            self.test_results["executive_supervisor"]["tests"].append(
                {"name": "Escalation Management", "status": "FAILED", "error": str(e)}
            )

    async def test_workflow_manager(self):
        """Test Workflow Manager Agent functionality."""
        logger.info("Testing Workflow Manager Agent...")

        # Test 1: Task Routing
        try:
            workflow_execution = {
                "id": "workflow_1",
                "name": "Content Analysis Workflow",
                "tasks": [
                    {
                        "id": "task_1",
                        "name": "Content Ingestion",
                        "description": "Ingest content from multiple sources",
                        "priority": 8,
                        "agent_type": "ingestion",
                        "estimated_duration_seconds": 120,
                        "resource_requirements": {"cpu_cores": 2, "memory_gb": 4},
                    },
                    {
                        "id": "task_2",
                        "name": "Content Analysis",
                        "description": "Analyze content for insights",
                        "priority": 9,
                        "agent_type": "analysis",
                        "estimated_duration_seconds": 300,
                        "resource_requirements": {"cpu_cores": 4, "memory_gb": 8},
                    },
                ],
            }

            available_agents = [
                {
                    "id": "agent_1",
                    "type": "ingestion",
                    "capabilities": ["content_ingestion", "data_processing"],
                    "current_load": 0.3,
                    "max_concurrent_tasks": 3,
                    "average_completion_time": 100.0,
                    "success_rate": 0.95,
                    "specializations": ["multi_source_ingestion"],
                },
                {
                    "id": "agent_2",
                    "type": "analysis",
                    "capabilities": ["content_analysis", "insight_extraction"],
                    "current_load": 0.2,
                    "max_concurrent_tasks": 2,
                    "average_completion_time": 250.0,
                    "success_rate": 0.92,
                    "specializations": ["deep_analysis"],
                },
            ]

            result = await self.workflow_manager.route_tasks(
                workflow_execution, available_agents, "test_tenant", "test_workspace"
            )

            if result.success and "routing_plan" in result.data:
                self.test_results["workflow_manager"]["passed"] += 1
                self.test_results["workflow_manager"]["tests"].append(
                    {
                        "name": "Task Routing",
                        "status": "PASSED",
                        "details": f"Routed {len(result.data['routing_plan']['assignments'])} tasks",
                    }
                )
            else:
                raise Exception(f"Task routing failed: {result.error}")

        except Exception as e:
            self.test_results["workflow_manager"]["failed"] += 1
            self.test_results["workflow_manager"]["tests"].append(
                {"name": "Task Routing", "status": "FAILED", "error": str(e)}
            )

        # Test 2: Dependency Resolution
        try:
            workflow_tasks = [
                {
                    "id": "task_1",
                    "name": "Data Preparation",
                    "priority": 7,
                    "dependencies": [],
                },
                {
                    "id": "task_2",
                    "name": "Data Processing",
                    "priority": 8,
                    "dependencies": ["task_1"],
                },
                {
                    "id": "task_3",
                    "name": "Data Analysis",
                    "priority": 9,
                    "dependencies": ["task_2"],
                },
            ]

            result = await self.workflow_manager.resolve_dependencies(workflow_tasks, "test_tenant", "test_workspace")

            if result.success and "dependency_resolution" in result.data:
                self.test_results["workflow_manager"]["passed"] += 1
                self.test_results["workflow_manager"]["tests"].append(
                    {
                        "name": "Dependency Resolution",
                        "status": "PASSED",
                        "details": f"Resolved dependencies for {len(result.data['dependency_resolution']['execution_order'])} tasks",
                    }
                )
            else:
                raise Exception(f"Dependency resolution failed: {result.error}")

        except Exception as e:
            self.test_results["workflow_manager"]["failed"] += 1
            self.test_results["workflow_manager"]["tests"].append(
                {"name": "Dependency Resolution", "status": "FAILED", "error": str(e)}
            )

        # Test 3: Workflow Optimization
        try:
            workflow_analysis = {
                "execution_phases": [
                    {
                        "phase_id": "phase_1",
                        "tasks": ["task_1", "task_2"],
                        "estimated_duration": "10 minutes",
                    }
                ]
            }

            optimization_goals = ["speed", "cost", "quality"]

            result = await self.workflow_manager.optimize_workflow(
                workflow_analysis, optimization_goals, "test_tenant", "test_workspace"
            )

            if result.success and "optimization_recommendations" in result.data:
                self.test_results["workflow_manager"]["passed"] += 1
                self.test_results["workflow_manager"]["tests"].append(
                    {
                        "name": "Workflow Optimization",
                        "status": "PASSED",
                        "details": f"Generated {len(result.data['optimization_recommendations']['recommendations'])} optimization recommendations",
                    }
                )
            else:
                raise Exception(f"Workflow optimization failed: {result.error}")

        except Exception as e:
            self.test_results["workflow_manager"]["failed"] += 1
            self.test_results["workflow_manager"]["tests"].append(
                {"name": "Workflow Optimization", "status": "FAILED", "error": str(e)}
            )

    async def test_hierarchical_orchestrator(self):
        """Test Hierarchical Orchestrator functionality."""
        logger.info("Testing Hierarchical Orchestrator...")

        # Test 1: Create Orchestration Session
        try:
            mission_context = "Deploy advanced agent orchestration system"
            objectives = [
                {
                    "id": "obj_1",
                    "title": "Setup hierarchical agents",
                    "description": "Configure supervisor-worker patterns",
                    "priority": 9,
                    "success_criteria": ["Agent coordination working"],
                    "resource_requirements": {"cpu_cores": 4},
                    "timeline": "1 week",
                }
            ]

            result = await self.orchestrator.create_orchestration_session(
                "Test Session",
                mission_context,
                objectives,
                "test_tenant",
                "test_workspace",
            )

            if result.success and "session_id" in result.data:
                session_id = result.data["session_id"]
                self.test_results["hierarchical_orchestrator"]["passed"] += 1
                self.test_results["hierarchical_orchestrator"]["tests"].append(
                    {
                        "name": "Create Orchestration Session",
                        "status": "PASSED",
                        "details": f"Created session {session_id} with {result.data['tasks_created']} tasks",
                    }
                )

                # Test 2: Execute Session
                try:
                    execution_result = await self.orchestrator.execute_orchestration_session(session_id)

                    if execution_result.success:
                        self.test_results["hierarchical_orchestrator"]["passed"] += 1
                        self.test_results["hierarchical_orchestrator"]["tests"].append(
                            {
                                "name": "Execute Orchestration Session",
                                "status": "PASSED",
                                "details": f"Executed session with {len(execution_result.data['execution_results'])} results",
                            }
                        )
                    else:
                        raise Exception(f"Session execution failed: {execution_result.error}")

                except Exception as e:
                    self.test_results["hierarchical_orchestrator"]["failed"] += 1
                    self.test_results["hierarchical_orchestrator"]["tests"].append(
                        {
                            "name": "Execute Orchestration Session",
                            "status": "FAILED",
                            "error": str(e),
                        }
                    )

                # Test 3: Monitor Session
                try:
                    monitoring_result = await self.orchestrator.monitor_orchestration_session(session_id)

                    if monitoring_result.success:
                        self.test_results["hierarchical_orchestrator"]["passed"] += 1
                        self.test_results["hierarchical_orchestrator"]["tests"].append(
                            {
                                "name": "Monitor Orchestration Session",
                                "status": "PASSED",
                                "details": f"Monitoring data collected with {len(monitoring_result.data['health_checks'])} health checks",
                            }
                        )
                    else:
                        raise Exception(f"Session monitoring failed: {monitoring_result.error}")

                except Exception as e:
                    self.test_results["hierarchical_orchestrator"]["failed"] += 1
                    self.test_results["hierarchical_orchestrator"]["tests"].append(
                        {
                            "name": "Monitor Orchestration Session",
                            "status": "FAILED",
                            "error": str(e),
                        }
                    )

            else:
                raise Exception(f"Session creation failed: {result.error}")

        except Exception as e:
            self.test_results["hierarchical_orchestrator"]["failed"] += 1
            self.test_results["hierarchical_orchestrator"]["tests"].append(
                {
                    "name": "Create Orchestration Session",
                    "status": "FAILED",
                    "error": str(e),
                }
            )

    async def test_rl_model_router(self):
        """Test RL Model Router functionality."""
        logger.info("Testing RL Model Router...")

        # Test 1: Model Routing
        try:
            context = RoutingContext(
                task_type="analysis",
                complexity=TaskComplexity.COMPLEX,
                token_estimate=2000,
                latency_requirement_ms=3000,
                cost_budget_usd=0.01,
                quality_requirement=0.9,
                tenant="test_tenant",
                workspace="test_workspace",
            )

            result = await self.model_router.route_request(context)

            if result.success and "model_selection" in result.data:
                self.test_results["rl_model_router"]["passed"] += 1
                self.test_results["rl_model_router"]["tests"].append(
                    {
                        "name": "Model Routing",
                        "status": "PASSED",
                        "details": f"Selected model {result.data['model_selection'].model_id} with confidence {result.data['model_selection'].confidence:.2f}",
                    }
                )
            else:
                raise Exception(f"Model routing failed: {result.error}")

        except Exception as e:
            self.test_results["rl_model_router"]["failed"] += 1
            self.test_results["rl_model_router"]["tests"].append(
                {"name": "Model Routing", "status": "FAILED", "error": str(e)}
            )

        # Test 2: Reward Update
        try:
            reward_data = {
                "reward": 0.8,
                "latency_ms": 1500.0,
                "cost_usd": 0.005,
                "quality_score": 0.92,
                "success": True,
                "context_features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            }

            result = await self.model_router.update_reward("gpt-4", "task_1", reward_data)

            if result.success:
                self.test_results["rl_model_router"]["passed"] += 1
                self.test_results["rl_model_router"]["tests"].append(
                    {
                        "name": "Reward Update",
                        "status": "PASSED",
                        "details": f"Updated reward for model with composite reward {result.data['composite_reward']:.2f}",
                    }
                )
            else:
                raise Exception(f"Reward update failed: {result.error}")

        except Exception as e:
            self.test_results["rl_model_router"]["failed"] += 1
            self.test_results["rl_model_router"]["tests"].append(
                {"name": "Reward Update", "status": "FAILED", "error": str(e)}
            )

        # Test 3: Routing Statistics
        try:
            result = self.model_router.get_routing_statistics()

            if result.success and "performance_metrics" in result.data:
                self.test_results["rl_model_router"]["passed"] += 1
                self.test_results["rl_model_router"]["tests"].append(
                    {
                        "name": "Routing Statistics",
                        "status": "PASSED",
                        "details": f"Retrieved statistics with {result.data['performance_metrics']['total_routes']} total routes",
                    }
                )
            else:
                raise Exception(f"Statistics retrieval failed: {result.error}")

        except Exception as e:
            self.test_results["rl_model_router"]["failed"] += 1
            self.test_results["rl_model_router"]["tests"].append(
                {"name": "Routing Statistics", "status": "FAILED", "error": str(e)}
            )

    async def test_rl_cache_optimizer(self):
        """Test RL Cache Optimizer functionality."""
        logger.info("Testing RL Cache Optimizer...")

        # Test 1: Cache Optimization
        try:
            context = CacheContext(
                key_pattern="user_preferences",
                access_frequency=5.0,
                data_size=10000,
                time_since_last_access=300.0,
                time_of_day=14,
                day_of_week=2,
                tenant="test_tenant",
                workspace="test_workspace",
            )

            result = await self.cache_optimizer.optimize_cache_operation(context, "store")

            if result.success and "optimized_action" in result.data:
                self.test_results["rl_cache_optimizer"]["passed"] += 1
                self.test_results["rl_cache_optimizer"]["tests"].append(
                    {
                        "name": "Cache Optimization",
                        "status": "PASSED",
                        "details": f"Optimized cache operation with confidence {result.data['confidence']:.2f}",
                    }
                )
            else:
                raise Exception(f"Cache optimization failed: {result.error}")

        except Exception as e:
            self.test_results["rl_cache_optimizer"]["failed"] += 1
            self.test_results["rl_cache_optimizer"]["tests"].append(
                {"name": "Cache Optimization", "status": "FAILED", "error": str(e)}
            )

        # Test 2: Performance Update
        try:
            from ultimate_discord_intelligence_bot.services.rl_cache_optimizer import (
                CacheAction,
                CacheStrategy,
            )

            action = CacheAction(
                action_type="store",
                key="test_key",
                ttl_seconds=3600,
                strategy=CacheStrategy.ADAPTIVE,
            )

            reward_data = {
                "hit": True,
                "latency_ms": 50.0,
                "cost_savings": 0.001,
                "quality_impact": 0.1,
                "context_features": [
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.8,
                    0.9,
                    1.0,
                    0.1,
                    0.2,
                ],
            }

            result = await self.cache_optimizer.update_cache_performance(action, reward_data)

            if result.success:
                self.test_results["rl_cache_optimizer"]["passed"] += 1
                self.test_results["rl_cache_optimizer"]["tests"].append(
                    {
                        "name": "Performance Update",
                        "status": "PASSED",
                        "details": f"Updated cache performance with composite reward {result.data['composite_reward']:.2f}",
                    }
                )
            else:
                raise Exception(f"Performance update failed: {result.error}")

        except Exception as e:
            self.test_results["rl_cache_optimizer"]["failed"] += 1
            self.test_results["rl_cache_optimizer"]["tests"].append(
                {"name": "Performance Update", "status": "FAILED", "error": str(e)}
            )

        # Test 3: Cache Statistics
        try:
            result = self.cache_optimizer.get_cache_statistics()

            if result.success and "cache_metrics" in result.data:
                self.test_results["rl_cache_optimizer"]["passed"] += 1
                self.test_results["rl_cache_optimizer"]["tests"].append(
                    {
                        "name": "Cache Statistics",
                        "status": "PASSED",
                        "details": f"Retrieved cache statistics with hit rate {result.data['cache_metrics']['hit_rate']:.2f}",
                    }
                )
            else:
                raise Exception(f"Statistics retrieval failed: {result.error}")

        except Exception as e:
            self.test_results["rl_cache_optimizer"]["failed"] += 1
            self.test_results["rl_cache_optimizer"]["tests"].append(
                {"name": "Cache Statistics", "status": "FAILED", "error": str(e)}
            )

    async def test_performance_learning_engine(self):
        """Test Performance Learning Engine functionality."""
        logger.info("Testing Performance Learning Engine...")

        # Test 1: Request Optimization
        try:
            request = OptimizationRequest(
                request_id="req_1",
                optimization_level=OptimizationLevel.REQUEST,
                goals=[OptimizationGoal.LATENCY, OptimizationGoal.COST],
                context={
                    "task_type": "analysis",
                    "complexity": "moderate",
                    "token_estimate": 1500,
                    "latency_requirement_ms": 2000,
                    "cost_budget_usd": 0.008,
                    "cache_key": "analysis_cache",
                    "access_frequency": 3.0,
                    "data_size": 5000,
                },
                priority=7,
                tenant="test_tenant",
                workspace="test_workspace",
            )

            result = await self.performance_engine.optimize_request(request)

            if result.success and "optimization_result" in result.data:
                self.test_results["performance_learning_engine"]["passed"] += 1
                self.test_results["performance_learning_engine"]["tests"].append(
                    {
                        "name": "Request Optimization",
                        "status": "PASSED",
                        "details": f"Optimized request with {len(result.data['optimization_result'].optimizations_applied)} optimizations",
                    }
                )
            else:
                raise Exception(f"Request optimization failed: {result.error}")

        except Exception as e:
            self.test_results["performance_learning_engine"]["failed"] += 1
            self.test_results["performance_learning_engine"]["tests"].append(
                {"name": "Request Optimization", "status": "FAILED", "error": str(e)}
            )

        # Test 2: Performance Feedback
        try:
            feedback_data = {
                "model_routing_feedback": {
                    "model_id": "gpt-4",
                    "task_id": "task_1",
                    "reward": 0.85,
                    "latency_ms": 1800.0,
                    "cost_usd": 0.006,
                    "quality_score": 0.94,
                    "success": True,
                    "context_features": [
                        0.1,
                        0.2,
                        0.3,
                        0.4,
                        0.5,
                        0.6,
                        0.7,
                        0.8,
                        0.9,
                        1.0,
                    ],
                },
                "cache_feedback": {
                    "action": {
                        "action_type": "store",
                        "key": "test_key",
                        "ttl_seconds": 3600,
                    },
                    "hit": True,
                    "latency_ms": 45.0,
                    "cost_savings": 0.002,
                    "quality_impact": 0.05,
                    "context_features": [
                        0.1,
                        0.2,
                        0.3,
                        0.4,
                        0.5,
                        0.6,
                        0.7,
                        0.8,
                        0.9,
                        1.0,
                        0.1,
                        0.2,
                    ],
                },
            }

            result = await self.performance_engine.update_performance_feedback(feedback_data)

            if result.success:
                self.test_results["performance_learning_engine"]["passed"] += 1
                self.test_results["performance_learning_engine"]["tests"].append(
                    {
                        "name": "Performance Feedback",
                        "status": "PASSED",
                        "details": f"Updated performance feedback with learning triggered: {result.data['learning_triggered']}",
                    }
                )
            else:
                raise Exception(f"Performance feedback failed: {result.error}")

        except Exception as e:
            self.test_results["performance_learning_engine"]["failed"] += 1
            self.test_results["performance_learning_engine"]["tests"].append(
                {"name": "Performance Feedback", "status": "FAILED", "error": str(e)}
            )

        # Test 3: Optimization Statistics
        try:
            result = self.performance_engine.get_optimization_statistics()

            if result.success and "engine_statistics" in result.data:
                self.test_results["performance_learning_engine"]["passed"] += 1
                self.test_results["performance_learning_engine"]["tests"].append(
                    {
                        "name": "Optimization Statistics",
                        "status": "PASSED",
                        "details": f"Retrieved engine statistics with {result.data['engine_statistics']['total_optimizations']} total optimizations",
                    }
                )
            else:
                raise Exception(f"Statistics retrieval failed: {result.error}")

        except Exception as e:
            self.test_results["performance_learning_engine"]["failed"] += 1
            self.test_results["performance_learning_engine"]["tests"].append(
                {"name": "Optimization Statistics", "status": "FAILED", "error": str(e)}
            )

    def generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2 IMPLEMENTATION TEST REPORT")
        logger.info("=" * 60)

        total_passed = 0
        total_failed = 0

        for component, results in self.test_results.items():
            component_passed = results["passed"]
            component_failed = results["failed"]
            total_passed += component_passed
            total_failed += component_failed

            logger.info(f"\n{component.upper().replace('_', ' ')}:")
            logger.info(f"  Passed: {component_passed}")
            logger.info(f"  Failed: {component_failed}")
            logger.info(f"  Success Rate: {(component_passed / (component_passed + component_failed) * 100):.1f}%")

            for test in results["tests"]:
                status_icon = "✅" if test["status"] == "PASSED" else "❌"
                logger.info(f"    {status_icon} {test['name']}")
                if test["status"] == "PASSED" and "details" in test:
                    logger.info(f"        {test['details']}")
                elif test["status"] == "FAILED" and "error" in test:
                    logger.info(f"        Error: {test['error']}")

        logger.info("\nOVERALL RESULTS:")
        logger.info(f"  Total Tests: {total_passed + total_failed}")
        logger.info(f"  Passed: {total_passed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Overall Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")

        # Save detailed report
        report_data = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "overall_results": {
                "total_tests": total_passed + total_failed,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": total_passed / (total_passed + total_failed) * 100,
            },
            "component_results": self.test_results,
        }

        report_file = f"docs/phase2_test_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"\nDetailed report saved to: {report_file}")

        if total_failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Phase 2 implementations are working correctly.")
        else:
            logger.info(f"\n⚠️  {total_failed} tests failed. Please review the errors above.")


async def main():
    """Main test execution function."""
    test_suite = Phase2TestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
