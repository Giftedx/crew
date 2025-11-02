"""Agent Routing Bandit - Intelligent routing across CrewAI agents

Contextual bandit for selecting the best agent for a given task based on:
- Historical performance
- Agent specialization
- Task requirements
- Resource constraints
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents an agent and its capabilities"""

    agent_id: str
    agent_name: str
    agent_type: str
    specializations: list[str] = field(default_factory=list)
    average_task_duration_s: float = 60.0
    success_rate: float = 0.9
    quality_score: float = 0.85
    max_parallel_tasks: int = 3
    current_load: int = 0
    health_score: float = 1.0
    last_used: float = field(default_factory=time.time)


@dataclass
class AgentSelection:
    """Result of agent selection"""

    agent_id: str
    confidence: float
    expected_success: float
    expected_duration_s: float
    reasoning: str
    alternatives: list[tuple[str, float]] = field(default_factory=list)


class AgentContextualBandit:
    """Contextual bandit for agent routing"""

    def __init__(self, agents: list[AgentCapability], context_dim: int = 12):
        self.agents = {agent.agent_id: agent for agent in agents}
        self.context_dim = context_dim
        self.agent_parameters = {agent_id: np.random.randn(context_dim) * 0.01 for agent_id in self.agents}
        self.learning_rate = 0.1
        self.agent_counts: defaultdict[str, int] = defaultdict(int)
        self.agent_rewards: defaultdict[str, list[float]] = defaultdict(list)
        self.recent_performance: dict[str, deque[float]] = {agent_id: deque(maxlen=30) for agent_id in self.agents}

    def select_agent(
        self, context: np.ndarray, task_type: str, required_specializations: list[str] | None = None
    ) -> StepResult:
        """Select best agent for given context"""
        try:
            if len(context) != self.context_dim:
                context = self._pad_context(context)
            candidate_agents = self._filter_agents(task_type, required_specializations)
            if not candidate_agents:
                return StepResult.fail(
                    f"No agents available for task_type={task_type}, specializations={required_specializations}"
                )
            expected_rewards = {}
            for agent_id in candidate_agents:
                params = self.agent_parameters[agent_id]
                expected_reward = np.dot(params, context)
                agent = self.agents[agent_id]
                expected_reward *= agent.health_score
                expected_reward *= agent.success_rate
                load_factor = 1.0 - agent.current_load / max(agent.max_parallel_tasks, 1)
                expected_reward *= load_factor
                expected_rewards[agent_id] = expected_reward
            selected_agent_id = max(expected_rewards, key=lambda k: expected_rewards[k])
            selected_agent = self.agents[selected_agent_id]
            sorted_rewards = sorted(expected_rewards.values(), reverse=True)
            confidence = 0.85
            if len(sorted_rewards) > 1:
                gap = sorted_rewards[0] - sorted_rewards[1]
                confidence = min(0.95, 0.5 + gap / 2.0)
            alternatives = sorted(
                [(aid, reward) for aid, reward in expected_rewards.items() if aid != selected_agent_id],
                key=lambda x: x[1],
                reverse=True,
            )[:2]
            selection = AgentSelection(
                agent_id=selected_agent_id,
                confidence=confidence,
                expected_success=selected_agent.success_rate,
                expected_duration_s=selected_agent.average_task_duration_s,
                reasoning=f"Selected {selected_agent.agent_name} for {task_type} (confidence={confidence:.2f}, load={selected_agent.current_load}/{selected_agent.max_parallel_tasks})",
                alternatives=alternatives,
            )
            return StepResult.ok(data=selection)
        except Exception as e:
            logger.error(f"Agent selection failed: {e}")
            return StepResult.fail(f"Selection failed: {e}")

    def update(
        self,
        agent_id: str,
        context: np.ndarray,
        reward: float,
        task_duration_s: float | None = None,
        success: bool = True,
    ) -> None:
        """Update agent parameters based on observed reward"""
        if agent_id not in self.agents:
            logger.warning(f"Unknown agent: {agent_id}")
            return
        if len(context) != self.context_dim:
            context = self._pad_context(context)
        self.agent_counts[agent_id] += 1
        self.agent_rewards[agent_id].append(reward)
        self.recent_performance[agent_id].append(reward)
        learning_rate = 1.0 / (1.0 + self.agent_counts[agent_id] ** 0.5)
        prediction = np.dot(self.agent_parameters[agent_id], context)
        error = reward - prediction
        self.agent_parameters[agent_id] += learning_rate * error * context
        agent = self.agents[agent_id]
        agent.success_rate = 0.9 * agent.success_rate + 0.1 * (1.0 if success else 0.0)
        if task_duration_s:
            agent.average_task_duration_s = 0.9 * agent.average_task_duration_s + 0.1 * task_duration_s
        agent.last_used = time.time()

    def _filter_agents(self, task_type: str, required_specializations: list[str] | None = None) -> list[str]:
        """Filter agents by task type and specializations"""
        candidates = []
        for agent_id, agent in self.agents.items():
            if agent.health_score < 0.4:
                continue
            if agent.current_load >= agent.max_parallel_tasks:
                continue
            if task_type and task_type not in agent.agent_type:
                continue
            if required_specializations and (
                not any(spec in agent.specializations for spec in required_specializations)
            ):
                continue
            candidates.append(agent_id)
        return candidates

    def _pad_context(self, context: np.ndarray) -> np.ndarray:
        """Pad or trim context to required dimension"""
        if len(context) < self.context_dim:
            padded = np.zeros(self.context_dim)
            padded[: len(context)] = context
            return padded
        return context[: self.context_dim]

    def get_agent_statistics(self) -> dict[str, Any]:
        """Get statistics for all agents"""
        stats = {}
        for agent_id, agent in self.agents.items():
            rewards = self.agent_rewards.get(agent_id, [])
            recent = list(self.recent_performance.get(agent_id, []))
            stats[agent_id] = {
                "agent_name": agent.agent_name,
                "agent_type": agent.agent_type,
                "usage_count": self.agent_counts.get(agent_id, 0),
                "success_rate": agent.success_rate,
                "quality_score": agent.quality_score,
                "health_score": agent.health_score,
                "average_duration_s": agent.average_task_duration_s,
                "current_load": agent.current_load,
                "max_parallel_tasks": agent.max_parallel_tasks,
                "average_reward": np.mean(rewards) if rewards else 0.0,
                "recent_performance": np.mean(recent) if recent else 0.0,
            }
        return stats


class AgentRoutingBandit:
    """Main agent routing system"""

    def __init__(self):
        self.agents = self._discover_agents()
        self.bandit = AgentContextualBandit(self.agents)
        self.feedback_queue: deque[dict[str, Any]] = deque(maxlen=500)
        logger.info(f"Agent routing bandit initialized with {len(self.agents)} agents")

    def _discover_agents(self) -> list[AgentCapability]:
        """Auto-discover available CrewAI agents"""
        discovered_agents = []
        try:
            from domains.orchestration.agents.registry import AGENT_DEFINITIONS

            for agent_def in AGENT_DEFINITIONS.values():
                capability = AgentCapability(
                    agent_id=agent_def.get("id", "unknown"),
                    agent_name=agent_def.get("role", "Unknown Agent"),
                    agent_type=self._infer_agent_type(agent_def.get("role", "")),
                    specializations=agent_def.get("tools", []),
                )
                discovered_agents.append(capability)
        except Exception as e:
            logger.warning(f"Agent discovery failed: {e}, using defaults")
            default_agents = [
                AgentCapability(
                    agent_id="acquisition_specialist",
                    agent_name="Acquisition Specialist",
                    agent_type="acquisition",
                    specializations=["download", "transcription"],
                ),
                AgentCapability(
                    agent_id="verification_analyst",
                    agent_name="Verification Analyst",
                    agent_type="verification",
                    specializations=["fact_check", "truth_scoring"],
                ),
                AgentCapability(
                    agent_id="deep_content_analyst",
                    agent_name="Deep Content Analyst",
                    agent_type="analysis",
                    specializations=["sentiment", "narrative", "claims"],
                ),
                AgentCapability(
                    agent_id="intelligence_coordinator",
                    agent_name="Intelligence Coordinator",
                    agent_type="intelligence",
                    specializations=["synthesis", "strategy"],
                ),
            ]
            discovered_agents.extend(default_agents)
        return discovered_agents

    def _infer_agent_type(self, role: str) -> str:
        """Infer agent type from role"""
        role_lower = role.lower()
        if "acquisition" in role_lower or "download" in role_lower:
            return "acquisition"
        if "verification" in role_lower or "fact" in role_lower:
            return "verification"
        if "analysis" in role_lower or "analyst" in role_lower:
            return "analysis"
        if "intelligence" in role_lower or "coordinator" in role_lower:
            return "intelligence"
        if "monitor" in role_lower or "tracking" in role_lower:
            return "monitoring"
        return "general"

    async def route_agent_task(
        self,
        task_description: str,
        context: dict[str, Any],
        task_type: str = "general",
        required_specializations: list[str] | None = None,
    ) -> StepResult:
        """Route a task to the best agent"""
        try:
            context_vec = self._extract_context_vector(context)
            result = self.bandit.select_agent(context_vec, task_type, required_specializations)
            if not result.success:
                return result
            selection: AgentSelection = result.data
            agent = self.bandit.agents.get(selection.agent_id)
            if agent:
                agent.current_load += 1
            logger.info(f"Agent routed: {task_type} → {selection.agent_id} (confidence={selection.confidence:.2f})")
            return StepResult.ok(data=selection)
        except Exception as e:
            logger.error(f"Agent routing failed: {e}")
            return StepResult.fail(f"Routing failed: {e}")

    def complete_agent_task(
        self,
        agent_id: str,
        context: dict[str, Any],
        success: bool,
        task_duration_s: float,
        quality_score: float | None = None,
    ) -> StepResult:
        """Mark task completion and submit feedback"""
        try:
            agent = self.bandit.agents.get(agent_id)
            if agent and agent.current_load > 0:
                agent.current_load -= 1
            reward = 0.0
            if success:
                reward += 0.5
                if quality_score is not None:
                    reward += 0.5 * quality_score
                expected_duration = agent.average_task_duration_s if agent else 60.0
                if task_duration_s > expected_duration * 2:
                    reward -= 0.2
            self.feedback_queue.append(
                {
                    "agent_id": agent_id,
                    "context": context,
                    "reward": reward,
                    "success": success,
                    "task_duration_s": task_duration_s,
                }
            )
            return StepResult.ok(message="Task completed, feedback queued", reward=reward)
        except Exception as e:
            logger.error(f"Failed to complete agent task: {e}")
            return StepResult.fail(f"Task completion failed: {e}")

    def process_feedback_batch(self, batch_size: int = 10) -> StepResult:
        """Process queued feedback signals"""
        try:
            processed = 0
            while self.feedback_queue and processed < batch_size:
                feedback = self.feedback_queue.popleft()
                context_vec = self._extract_context_vector(feedback["context"])
                self.bandit.update(
                    agent_id=feedback["agent_id"],
                    context=context_vec,
                    reward=feedback["reward"],
                    task_duration_s=feedback.get("task_duration_s"),
                    success=feedback.get("success", True),
                )
                processed += 1
            return StepResult.ok(
                message=f"Processed {processed} feedback signals",
                processed=processed,
                remaining=len(self.feedback_queue),
            )
        except Exception as e:
            logger.error(f"Feedback processing failed: {e}")
            return StepResult.fail(f"Processing failed: {e}")

    def _extract_context_vector(self, context: dict[str, Any]) -> np.ndarray:
        """Extract feature vector from context"""
        features = []
        features.append(context.get("complexity", 0.5))
        features.append(context.get("urgency", 0.5))
        features.append(context.get("data_volume", 1000) / 10000.0)
        features.append(context.get("required_accuracy", 0.9))
        features.append(context.get("required_depth", 0.7))
        features.append(context.get("max_duration_s", 300) / 600.0)
        features.append(context.get("budget_usd", 0.05) * 20)
        features.append(1.0 if context.get("has_multimodal") else 0.0)
        features.append(1.0 if context.get("requires_verification") else 0.0)
        features.append(context.get("num_agents_involved", 1) / 5.0)
        features.append(context.get("priority", 5) / 10.0)
        features.append(context.get("historical_success", 0.8))
        return np.array(features[:12], dtype=float)

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive routing statistics"""
        return {
            "agent_statistics": self.bandit.get_agent_statistics(),
            "total_agents": len(self.agents),
            "feedback_queue_size": len(self.feedback_queue),
        }


_agent_router: AgentRoutingBandit | None = None


def get_agent_router(auto_create: bool = True) -> AgentRoutingBandit | None:
    """Get global agent router instance"""
    global _agent_router
    if _agent_router is None and auto_create:
        _agent_router = AgentRoutingBandit()
    return _agent_router


def set_agent_router(router: AgentRoutingBandit) -> None:
    """Set global agent router instance"""
    global _agent_router
    _agent_router = router


__all__ = [
    "AgentCapability",
    "AgentContextualBandit",
    "AgentRoutingBandit",
    "AgentSelection",
    "get_agent_router",
    "set_agent_router",
]
