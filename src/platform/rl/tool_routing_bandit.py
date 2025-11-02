"""Tool Routing Bandit - Contextual bandit for intelligent tool selection

Extends RLModelRouter patterns to all 50+ tools with:
- Health monitoring
- Performance tracking
- Dynamic selection based on context
- Integration with UnifiedFeedbackOrchestrator
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
class ToolCapability:
    """Represents a tool and its capabilities"""
    tool_id: str
    tool_name: str
    category: str
    average_latency_ms: float = 1000.0
    success_rate: float = 0.95
    cost_score: float = 0.5
    capabilities: list[str] = field(default_factory=list)
    requirements: dict[str, Any] = field(default_factory=dict)
    health_score: float = 1.0
    last_used: float = field(default_factory=time.time)

@dataclass
class ToolSelection:
    """Result of tool selection"""
    tool_id: str
    confidence: float
    expected_success: float
    expected_latency_ms: float
    reasoning: str
    alternatives: list[tuple[str, float]] = field(default_factory=list)

class ToolContextualBandit:
    """Contextual bandit for tool routing"""

    def __init__(self, tools: list[ToolCapability], context_dim: int=15):
        self.tools = {tool.tool_id: tool for tool in tools}
        self.context_dim = context_dim
        self.tool_parameters = {tool_id: np.random.randn(context_dim) * 0.01 for tool_id in self.tools}
        self.tool_counts: defaultdict[str, int] = defaultdict(int)
        self.tool_rewards: defaultdict[str, list[float]] = defaultdict(list)
        self.context_history: list[list[float]] = []
        self.reward_history: list[float] = []
        self.recent_performance: dict[str, deque[float]] = {tool_id: deque(maxlen=50) for tool_id in self.tools}

    def select_tool(self, context: np.ndarray, task_type: str, required_capabilities: list[str] | None=None) -> StepResult:
        """Select best tool for given context"""
        try:
            if len(context) != self.context_dim:
                context = self._pad_context(context)
            candidate_tools = self._filter_tools(task_type, required_capabilities)
            if not candidate_tools:
                return StepResult.fail(f'No tools available for task_type={task_type}, capabilities={required_capabilities}')
            expected_rewards = {}
            for tool_id in candidate_tools:
                params = self.tool_parameters[tool_id]
                expected_reward = np.dot(params, context)
                tool = self.tools[tool_id]
                expected_reward *= tool.health_score
                expected_reward *= tool.success_rate
                expected_rewards[tool_id] = expected_reward
            selected_tool_id = max(expected_rewards, key=lambda k: expected_rewards[k])
            selected_tool = self.tools[selected_tool_id]
            sorted_rewards = sorted(expected_rewards.values(), reverse=True)
            confidence = 0.9
            if len(sorted_rewards) > 1:
                gap = sorted_rewards[0] - sorted_rewards[1]
                confidence = min(0.99, 0.5 + gap / 2.0)
            alternatives = sorted([(tid, reward) for tid, reward in expected_rewards.items() if tid != selected_tool_id], key=lambda x: x[1], reverse=True)[:3]
            selection = ToolSelection(tool_id=selected_tool_id, confidence=confidence, expected_success=selected_tool.success_rate, expected_latency_ms=selected_tool.average_latency_ms, reasoning=f'Selected {selected_tool.tool_name} for {task_type} (confidence={confidence:.2f}, success_rate={selected_tool.success_rate:.2f})', alternatives=alternatives)
            return StepResult.ok(data=selection)
        except Exception as e:
            logger.error(f'Tool selection failed: {e}')
            return StepResult.fail(f'Selection failed: {e}')

    def update(self, tool_id: str, context: np.ndarray, reward: float, latency_ms: float | None=None, success: bool=True) -> None:
        """Update tool parameters based on observed reward"""
        if tool_id not in self.tools:
            logger.warning(f'Unknown tool: {tool_id}')
            return
        if len(context) != self.context_dim:
            context = self._pad_context(context)
        self.tool_counts[tool_id] += 1
        self.tool_rewards[tool_id].append(reward)
        self.recent_performance[tool_id].append(reward)
        self.context_history.append(context.copy())
        self.reward_history.append(reward)
        learning_rate = 1.0 / (1.0 + self.tool_counts[tool_id] ** 0.5)
        prediction = np.dot(self.tool_parameters[tool_id], context)
        error = reward - prediction
        self.tool_parameters[tool_id] += learning_rate * error * context
        tool = self.tools[tool_id]
        tool.success_rate = 0.9 * tool.success_rate + 0.1 * (1.0 if success else 0.0)
        if latency_ms:
            tool.average_latency_ms = 0.9 * tool.average_latency_ms + 0.1 * latency_ms
        tool.last_used = time.time()
        if len(self.context_history) > 10000:
            self.context_history = self.context_history[-5000:]
            self.reward_history = self.reward_history[-5000:]

    def _filter_tools(self, task_type: str, required_capabilities: list[str] | None=None) -> list[str]:
        """Filter tools by task type and capabilities"""
        candidates = []
        for tool_id, tool in self.tools.items():
            if tool.health_score < 0.3:
                continue
            if task_type and task_type not in tool.category:
                continue
            if required_capabilities and (not all(cap in tool.capabilities for cap in required_capabilities)):
                continue
            candidates.append(tool_id)
        return candidates

    def _pad_context(self, context: np.ndarray) -> np.ndarray:
        """Pad or trim context to required dimension"""
        if len(context) < self.context_dim:
            padded = np.zeros(self.context_dim)
            padded[:len(context)] = context
            return padded
        return context[:self.context_dim]

    def get_tool_statistics(self) -> dict[str, Any]:
        """Get statistics for all tools"""
        stats = {}
        for tool_id, tool in self.tools.items():
            rewards = self.tool_rewards.get(tool_id, [])
            recent = list(self.recent_performance.get(tool_id, []))
            stats[tool_id] = {'tool_name': tool.tool_name, 'category': tool.category, 'usage_count': self.tool_counts.get(tool_id, 0), 'success_rate': tool.success_rate, 'health_score': tool.health_score, 'average_latency_ms': tool.average_latency_ms, 'average_reward': np.mean(rewards) if rewards else 0.0, 'recent_performance': np.mean(recent) if recent else 0.0, 'last_used': tool.last_used}
        return stats

class ToolRoutingBandit:
    """Main tool routing system with contextual bandit"""

    def __init__(self, enable_auto_discovery: bool=True):
        self.enable_auto_discovery = enable_auto_discovery
        self.tools = self._discover_tools() if enable_auto_discovery else []
        self.bandit = ToolContextualBandit(self.tools)
        self.feedback_queue: deque[dict[str, Any]] = deque(maxlen=1000)
        logger.info(f'Tool routing bandit initialized with {len(self.tools)} tools')

    def _discover_tools(self) -> list[ToolCapability]:
        """Auto-discover available tools"""
        discovered_tools = []
        try:
            from ultimate_discord_intelligence_bot.tools import TOOL_MAPPING
            for tool_name, module_path in TOOL_MAPPING.items():
                capability = ToolCapability(tool_id=tool_name, tool_name=tool_name, category=self._infer_category(module_path), capabilities=[])
                discovered_tools.append(capability)
        except Exception as e:
            logger.warning(f'Tool discovery failed: {e}')
        return discovered_tools

    def _infer_category(self, module_path: str) -> str:
        """Infer tool category from module path"""
        if 'analysis' in module_path:
            return 'analysis'
        if 'verification' in module_path:
            return 'verification'
        if 'memory' in module_path:
            return 'memory'
        if 'acquisition' in module_path:
            return 'acquisition'
        if 'discord' in module_path:
            return 'discord'
        if 'social' in module_path:
            return 'social'
        if 'observability' in module_path:
            return 'observability'
        return 'general'

    async def route_tool_request(self, task_description: str, context: dict[str, Any], task_type: str='general', required_capabilities: list[str] | None=None) -> StepResult:
        """Route a tool request to the best tool"""
        try:
            context_vec = self._extract_context_vector(context)
            result = self.bandit.select_tool(context_vec, task_type, required_capabilities)
            if not result.success:
                return result
            selection: ToolSelection = result.data
            logger.info(f'Tool routed: {task_type} → {selection.tool_id} (confidence={selection.confidence:.2f})')
            return StepResult.ok(data=selection)
        except Exception as e:
            logger.error(f'Tool routing failed: {e}')
            return StepResult.fail(f'Routing failed: {e}')

    def submit_tool_feedback(self, tool_id: str, context: dict[str, Any], success: bool, latency_ms: float, quality_score: float | None=None) -> StepResult:
        """Submit feedback for a tool execution"""
        try:
            reward = 0.0
            if success:
                reward += 0.6
                if quality_score is not None:
                    reward += 0.4 * quality_score
                if latency_ms > 5000:
                    reward -= 0.2 * min((latency_ms - 5000) / 10000, 0.5)
            self.feedback_queue.append({'tool_id': tool_id, 'context': context, 'reward': reward, 'success': success, 'latency_ms': latency_ms})
            return StepResult.ok(message='Feedback queued', reward=reward)
        except Exception as e:
            logger.error(f'Failed to submit tool feedback: {e}')
            return StepResult.fail(f'Feedback submission failed: {e}')

    def process_feedback_batch(self, batch_size: int=20) -> StepResult:
        """Process queued feedback signals"""
        try:
            processed = 0
            while self.feedback_queue and processed < batch_size:
                feedback = self.feedback_queue.popleft()
                context_vec = self._extract_context_vector(feedback['context'])
                self.bandit.update(tool_id=feedback['tool_id'], context=context_vec, reward=feedback['reward'], latency_ms=feedback.get('latency_ms'), success=feedback.get('success', True))
                processed += 1
            return StepResult.ok(message=f'Processed {processed} feedback signals', processed=processed, remaining=len(self.feedback_queue))
        except Exception as e:
            logger.error(f'Feedback processing failed: {e}')
            return StepResult.fail(f'Processing failed: {e}')

    def _extract_context_vector(self, context: dict[str, Any]) -> np.ndarray:
        """Extract feature vector from context"""
        features = []
        features.append(context.get('complexity', 0.5))
        features.append(context.get('data_size', 1000) / 10000.0)
        features.append(context.get('urgency', 0.5))
        features.append(context.get('required_accuracy', 0.8))
        features.append(context.get('required_speed', 0.5))
        features.append(context.get('budget_usd', 0.01) * 100)
        features.append(context.get('max_latency_ms', 5000) / 10000.0)
        features.append(1.0 if context.get('has_video') else 0.0)
        features.append(1.0 if context.get('has_audio') else 0.0)
        features.append(1.0 if context.get('has_text') else 0.0)
        features.append(context.get('user_priority', 0.5))
        features.append(context.get('historical_success', 0.8))
        features.append(len(context.get('tags', [])) / 10.0)
        features.append(context.get('time_of_day', 12) / 24.0)
        features.append(context.get('day_of_week', 3) / 7.0)
        return np.array(features[:15], dtype=float)

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive routing statistics"""
        return {'tool_statistics': self.bandit.get_tool_statistics(), 'total_tools': len(self.tools), 'feedback_queue_size': len(self.feedback_queue)}
_tool_router: ToolRoutingBandit | None = None

def get_tool_router(auto_create: bool=True) -> ToolRoutingBandit | None:
    """Get global tool router instance"""
    global _tool_router
    if _tool_router is None and auto_create:
        _tool_router = ToolRoutingBandit()
    return _tool_router

def set_tool_router(router: ToolRoutingBandit) -> None:
    """Set global tool router instance"""
    global _tool_router
    _tool_router = router
__all__ = ['ToolCapability', 'ToolContextualBandit', 'ToolRoutingBandit', 'ToolSelection', 'get_tool_router', 'set_tool_router']
