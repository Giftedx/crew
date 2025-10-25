"""Unit tests for LinUCBToolBandit integration with TaskRoutingTool."""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import numpy as np
import pytest

from ai.advanced_contextual_bandits import LinUCBToolBandit
from ultimate_discord_intelligence_bot.tools.observability.task_routing_tool import TaskRoutingTool


class TestLinUCBToolBandit:
    def test_select_and_update(self):
        arms = ["agent_a", "agent_b", "agent_c"]
        bandit = LinUCBToolBandit(arms=arms, context_dim=8, alpha=1.0)

        # Simple context vector
        x = np.array([0.8, 0.6, 0.7, 0.9, 0.8, 0.7, 1.0, 0.2])
        action = bandit.select_arm(x)

        assert action.arm_id in arms
        assert 0.0 <= action.confidence <= 1.0

        # Update with a reward and ensure internal state is updated
        before = bandit.counts[action.arm_id]
        bandit.update(action.arm_id, x, reward=0.85)
        assert bandit.counts[action.arm_id] == before + 1

    def test_context_extraction_defaults(self):
        features = {}
        x = LinUCBToolBandit.extract_context_vector(features, dim=8)
        assert len(x) == 8
        # Check reasonable default ranges
        assert 0.0 <= x[0] <= 1.0
        assert 0.0 <= x[1] <= 1.0


class TestTaskRoutingToolBanditIntegration:
    @pytest.fixture(autouse=True)
    def enable_bandit(self):
        os.environ["ENABLE_TOOL_ROUTING_BANDIT"] = "1"
        yield
        os.environ.pop("ENABLE_TOOL_ROUTING_BANDIT", None)

    def test_bandit_routing_path_basic(self):
        tool = TaskRoutingTool()

        workflow_execution = {
            "id": "wf_123",
            "tasks": [
                {
                    "id": "t1",
                    "name": "Analyze data",
                    "required_capabilities": ["analysis"],
                    "priority": 4,
                    "estimated_duration_minutes": 30,
                    "complexity_score": 0.7,
                }
            ],
            "execution_order": ["t1"],
        }

        now = time.time()
        available_agents = [
            {
                "id": "agent_a",
                "name": "Alpha",
                "capabilities": ["analysis", "summarization"],
                "current_load": 0.2,
                "max_concurrent_tasks": 3,
                "average_task_duration_minutes": 25,
                "success_rate": 0.92,
                "cost_per_task": 0.05,
                "latency_ms": 800,
            },
            {
                "id": "agent_b",
                "name": "Beta",
                "capabilities": ["analysis"],
                "current_load": 0.6,
                "max_concurrent_tasks": 5,
                "average_task_duration_minutes": 35,
                "success_rate": 0.88,
                "cost_per_task": 0.03,
                "latency_ms": 1200,
            },
        ]

        res = tool._run(workflow_execution, available_agents, tenant="t", workspace="w")
        assert res.success
        data = res.data
        assert data["status"] == "routed"
        assert data["assignments"][0]["agent_id"] in {"agent_a", "agent_b"}

    @patch(
        "ultimate_discord_intelligence_bot.tools.observability.task_routing_tool.TaskRoutingTool._calculate_agent_score"
    )
    def test_bandit_learns_from_heuristic_reward(self, mock_score):
        # Make the heuristic strongly favor agent_a so the bandit learns to pick it
        mock_score.side_effect = lambda t, a: 0.95 if a.agent_id == "agent_a" else 0.5
        tool = TaskRoutingTool()

        workflow_execution = {
            "id": "wf_456",
            "tasks": [
                {
                    "id": "t1",
                    "name": "Analyze data",
                    "required_capabilities": ["analysis"],
                    "priority": 5,
                    "estimated_duration_minutes": 20,
                    "complexity_score": 0.6,
                }
            ],
            "execution_order": ["t1"],
        }

        available_agents = [
            {
                "id": "agent_a",
                "name": "Alpha",
                "capabilities": ["analysis", "summarization"],
                "current_load": 0.2,
                "max_concurrent_tasks": 3,
                "average_task_duration_minutes": 25,
                "success_rate": 0.92,
                "cost_per_task": 0.05,
                "latency_ms": 800,
            },
            {
                "id": "agent_b",
                "name": "Beta",
                "capabilities": ["analysis"],
                "current_load": 0.6,
                "max_concurrent_tasks": 5,
                "average_task_duration_minutes": 35,
                "success_rate": 0.88,
                "cost_per_task": 0.03,
                "latency_ms": 1200,
            },
        ]

        # First run - learn
        os.environ["ENABLE_TOOL_ROUTING_BANDIT"] = "1"
        res1 = tool._run(workflow_execution, available_agents, tenant="t", workspace="w")
        assert res1.success

        # Second run - should prefer agent_a due to learned reward
        res2 = tool._run(workflow_execution, available_agents, tenant="t", workspace="w")
        assert res2.success
        assign_agent = res2.data["assignments"][0]["agent_id"]
        assert assign_agent == "agent_a"
