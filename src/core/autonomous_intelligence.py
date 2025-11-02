"""Autonomous Intelligence system for self-improving agents and adaptive routing.

This module provides advanced autonomous capabilities including:
- Self-improving agent training and adaptation
- Dynamic model selection based on performance and context
- Reinforcement learning for optimal decision-making
- Autonomous task prioritization and resource allocation
- Continuous learning from feedback and outcomes
"""
from __future__ import annotations
import logging
import random
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for agent evaluation and improvement."""
    agent_id: str
    task_type: str
    success_rate: float
    average_response_time: float
    error_rate: float
    user_satisfaction: float
    cost_efficiency: float
    context_adherence: float
    timestamp: float = field(default_factory=time.time)

    def get_overall_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        weights = {'success_rate': 0.25, 'response_time': 0.2, 'error_rate': 0.2, 'user_satisfaction': 0.2, 'cost_efficiency': 0.1, 'context_adherence': 0.05}
        normalized_response_time = max(0, 1 - self.average_response_time / 10.0)
        normalized_error_rate = max(0, 1 - self.error_rate)
        scores = {'success_rate': self.success_rate, 'response_time': normalized_response_time, 'error_rate': normalized_error_rate, 'user_satisfaction': self.user_satisfaction, 'cost_efficiency': self.cost_efficiency, 'context_adherence': self.context_adherence}
        overall_score = sum((scores[metric] * weight for metric, weight in weights.items()))
        return min(overall_score * 100, 100.0)

@dataclass
class ModelPerformanceData:
    """Performance data for model evaluation and selection."""
    model_name: str
    provider: str
    task_types: list[str]
    performance_history: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    cost_history: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    usage_count: int = 0
    last_used: float = field(default_factory=time.time)

    def get_average_performance(self) -> float:
        """Get average performance score."""
        return statistics.mean(self.performance_history) if self.performance_history else 0.5

    def get_average_cost(self) -> float:
        """Get average cost per use."""
        return statistics.mean(self.cost_history) if self.cost_history else 0.0

    def get_performance_trend(self) -> float:
        """Calculate performance trend (positive = improving)."""
        if len(self.performance_history) < 5:
            return 0.0
        recent = list(self.performance_history)[-5:]
        older = list(self.performance_history)[:-5]
        if not older:
            return 0.0
        recent_avg = statistics.mean(recent)
        older_avg = statistics.mean(older)
        return recent_avg - older_avg

class AutonomousLearningEngine:
    """Autonomous learning engine for self-improving agents."""

    def __init__(self, learning_rate: float=0.1, exploration_rate: float=0.1):
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.agent_metrics: dict[str, deque[AgentPerformanceMetrics]] = defaultdict(lambda: deque(maxlen=200))
        self.model_data: dict[str, ModelPerformanceData] = {}
        self.adaptation_history: list[dict[str, Any]] = []
        self.last_adaptation: float = 0
        self.feedback_buffer: deque[dict[str, Any]] = deque(maxlen=1000)

    def record_agent_performance(self, metrics: AgentPerformanceMetrics) -> None:
        """Record agent performance metrics."""
        self.agent_metrics[metrics.agent_id].append(metrics)
        if len(self.agent_metrics[metrics.agent_id]) >= 10:
            self._adapt_agent_strategy(metrics.agent_id)

    def record_model_performance(self, model_name: str, provider: str, performance_score: float, cost: float, task_type: str) -> None:
        """Record model performance data."""
        model_key = f'{provider}:{model_name}'
        if model_key not in self.model_data:
            self.model_data[model_key] = ModelPerformanceData(model_name=model_name, provider=provider, task_types=[task_type])
        elif task_type not in self.model_data[model_key].task_types:
            self.model_data[model_key].task_types.append(task_type)
        model_data = self.model_data[model_key]
        model_data.performance_history.append(performance_score)
        model_data.cost_history.append(cost)
        model_data.usage_count += 1
        model_data.last_used = time.time()

    def select_optimal_model(self, task_type: str, context: dict[str, Any] | None=None, tenant_id: str | None=None) -> dict[str, Any]:
        """Select optimal model for a task using multi-armed bandit approach."""
        available_models = self._get_available_models_for_task(task_type)
        if not available_models:
            return {'model': 'gpt-3.5-turbo', 'provider': 'openrouter', 'reasoning': 'No performance data available, using default'}
        if random.random() < self.exploration_rate:
            selected_model = random.choice(available_models)
            reasoning = f'Exploration: randomly selected {selected_model['key']}'
        else:
            selected_model = self._select_best_model(available_models, task_type, context)
            reasoning = f'Exploitation: selected {selected_model['key']} (score: {selected_model['score']:.3f})'
        return {'model': selected_model['model_name'], 'provider': selected_model['provider'], 'reasoning': reasoning, 'confidence': selected_model['confidence'], 'estimated_cost': selected_model['estimated_cost']}

    def _get_available_models_for_task(self, task_type: str) -> list[dict[str, Any]]:
        """Get available models that can handle the task type."""
        candidates = []
        for model_key, model_data in self.model_data.items():
            if task_type in model_data.task_types and model_data.usage_count >= 3:
                avg_performance = model_data.get_average_performance()
                avg_cost = model_data.get_average_cost()
                candidates.append({'key': model_key, 'model_name': model_data.model_name, 'provider': model_data.provider, 'performance': avg_performance, 'cost': avg_cost, 'usage_count': model_data.usage_count, 'trend': model_data.get_performance_trend()})
        return candidates

    def _select_best_model(self, candidates: list[dict[str, Any]], task_type: str, context: dict[str, Any] | None=None) -> dict[str, Any]:
        """Select the best model using multi-criteria optimization."""
        if not candidates:
            return {'key': 'unknown', 'model_name': 'gpt-3.5-turbo', 'provider': 'openrouter', 'score': 0.5, 'confidence': 0.0, 'estimated_cost': 0.01}
        best_model = None
        best_score = -1
        for candidate in candidates:
            performance_weight = 0.4
            cost_weight = 0.3
            trend_weight = 0.2
            usage_weight = 0.1
            performance_score = candidate['performance']
            cost_score = 1 - min(candidate['cost'] / 0.1, 1.0)
            trend_score = (candidate['trend'] + 1) / 2
            usage_score = min(candidate['usage_count'] / 50, 1.0)
            composite_score = performance_score * performance_weight + cost_score * cost_weight + trend_score * trend_weight + usage_score * usage_weight
            if composite_score > best_score:
                best_score = composite_score
                best_model = candidate
        if best_model:
            return {'key': best_model['key'], 'model_name': best_model['model_name'], 'provider': best_model['provider'], 'score': best_score, 'confidence': min(best_model['usage_count'] / 10, 1.0), 'estimated_cost': best_model['cost']}
        fallback = candidates[0]
        return {'key': fallback['key'], 'model_name': fallback['model_name'], 'provider': fallback['provider'], 'score': fallback['performance'], 'confidence': 0.5, 'estimated_cost': fallback['cost']}

    def _adapt_agent_strategy(self, agent_id: str) -> None:
        """Adapt agent strategy based on recent performance."""
        metrics_list = list(self.agent_metrics[agent_id])
        if len(metrics_list) < 10:
            return
        recent_metrics = metrics_list[-10:]
        older_metrics = metrics_list[-20:-10] if len(metrics_list) >= 20 else metrics_list[:10]
        recent_avg = statistics.mean((m.overall_score() for m in recent_metrics))
        older_avg = statistics.mean((m.overall_score() for m in older_metrics))
        performance_trend = recent_avg - older_avg
        adaptation = {'agent_id': agent_id, 'timestamp': time.time(), 'performance_trend': performance_trend, 'recent_performance': recent_avg, 'strategy_changes': []}
        if performance_trend < -0.1:
            adaptation['strategy_changes'].append('reduce_complexity')
            adaptation['strategy_changes'].append('increase_validation')
            logger.warning(f'Agent {agent_id} performance declining, applying conservative strategies')
        elif performance_trend > 0.1:
            adaptation['strategy_changes'].append('increase_autonomy')
            adaptation['strategy_changes'].append('expand_capabilities')
            logger.info(f'Agent {agent_id} performance improving, enabling advanced features')
        self.adaptation_history.append(adaptation)
        self.last_adaptation = time.time()

    def process_feedback(self, feedback_data: dict[str, Any]) -> None:
        """Process user feedback for learning."""
        self.feedback_buffer.append({**feedback_data, 'processed_at': time.time()})
        if len(self.feedback_buffer) >= 50:
            self._analyze_feedback_patterns()

    def _analyze_feedback_patterns(self) -> None:
        """Analyze feedback patterns for learning opportunities."""
        recent_feedback = list(self.feedback_buffer)[-50:]
        satisfaction_scores = [f.get('satisfaction', 0.5) for f in recent_feedback]
        _ = statistics.mean(satisfaction_scores)
        low_satisfaction_feedback = [f for f in recent_feedback if f.get('satisfaction', 0.5) < 0.3]
        if low_satisfaction_feedback:
            common_issues = self._identify_common_issues(low_satisfaction_feedback)
            for issue in common_issues:
                logger.info(f'Identified learning opportunity: {issue}')

    def _identify_common_issues(self, feedback: list[dict[str, Any]]) -> list[str]:
        """Identify common issues from low-satisfaction feedback."""
        issues = []
        feedback_texts = [f.get('comments', '') for f in feedback if f.get('comments')]
        if feedback_texts:
            all_text = ' '.join(feedback_texts).lower()
            issue_keywords = ['slow', 'inaccurate', 'irrelevant', 'confusing', 'incomplete', 'wrong', 'not helpful', 'unclear']
            found_issues = [keyword for keyword in issue_keywords if keyword in all_text]
            issues.extend(found_issues)
        return issues

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learning progress and adaptations."""
        total_agents = len(self.agent_metrics)
        total_models = len(self.model_data)
        recent_adaptations = [a for a in self.adaptation_history if time.time() - a['timestamp'] < 24 * 3600]
        return {'agents_tracked': total_agents, 'models_tracked': total_models, 'total_adaptations': len(self.adaptation_history), 'recent_adaptations': len(recent_adaptations), 'feedback_processed': len(self.feedback_buffer), 'learning_rate': self.learning_rate, 'exploration_rate': self.exploration_rate, 'last_adaptation': self.last_adaptation}

    def export_learning_data(self) -> dict[str, Any]:
        """Export learning data for analysis and backup."""
        return {'agent_metrics': {agent_id: [metrics.__dict__ for metrics in metrics_list] for agent_id, metrics_list in self.agent_metrics.items()}, 'model_data': {model_key: {'model_name': data.model_name, 'provider': data.provider, 'task_types': data.task_types, 'performance_history': list(data.performance_history), 'cost_history': list(data.cost_history), 'usage_count': data.usage_count, 'last_used': data.last_used} for model_key, data in self.model_data.items()}, 'adaptation_history': self.adaptation_history[-50:], 'feedback_buffer': list(self.feedback_buffer)[-100:], 'exported_at': time.time()}

class AdaptiveTaskRouter:
    """Adaptive task routing system based on performance and context."""

    def __init__(self, learning_engine: AutonomousLearningEngine):
        self.learning_engine = learning_engine
        self.routing_cache: dict[str, dict[str, Any]] = {}
        try:
            from platform.cache.unified_config import get_unified_cache_config
            self.cache_ttl = get_unified_cache_config().get_ttl_for_domain('routing')
        except Exception:
            self.cache_ttl = 300

    def route_task(self, task_type: str, context: dict[str, Any], tenant_id: str | None=None, urgency: str='normal') -> dict[str, Any]:
        """Route task to optimal agent/model based on current conditions."""
        cache_key = f'{task_type}:{tenant_id}:{urgency}:{hash(str(context))}'
        if cache_key in self.routing_cache:
            cached_result = self.routing_cache[cache_key]
            if time.time() - cached_result['cached_at'] < self.cache_ttl:
                return cached_result['routing']
        model_selection = self.learning_engine.select_optimal_model(task_type, context, tenant_id)
        agent_assignment = self._select_optimal_agent(task_type, context, urgency)
        routing = {'task_type': task_type, 'agent_id': agent_assignment['agent_id'], 'model': model_selection['model'], 'provider': model_selection['provider'], 'priority': self._calculate_priority(urgency, context), 'estimated_duration': agent_assignment['estimated_duration'], 'confidence': min(model_selection['confidence'], agent_assignment['confidence']), 'reasoning': {'model_selection': model_selection['reasoning'], 'agent_selection': agent_assignment['reasoning']}}
        self.routing_cache[cache_key] = {'routing': routing, 'cached_at': time.time()}
        return routing

    def _select_optimal_agent(self, task_type: str, context: dict[str, Any], urgency: str) -> dict[str, Any]:
        """Select optimal agent for task execution."""
        agent_mapping = {'content_analysis': 'analysis_cartographer', 'fact_checking': 'verification_director', 'content_ingestion': 'acquisition_specialist', 'memory_storage': 'knowledge_integrator', 'discord_commands': 'discord_command_handler'}
        agent_id = agent_mapping.get(task_type, 'mission_orchestrator')
        if urgency == 'critical':
            agent_id = 'mission_orchestrator'
        agent_metrics = list(self.learning_engine.agent_metrics.get(agent_id, []))
        estimated_duration = 30.0
        confidence = 0.7
        if agent_metrics:
            recent_metrics = agent_metrics[-5:]
            avg_response_time = statistics.mean((m.average_response_time for m in recent_metrics))
            avg_success_rate = statistics.mean((m.success_rate for m in recent_metrics))
            estimated_duration = avg_response_time * 1.2
            confidence = avg_success_rate
        return {'agent_id': agent_id, 'estimated_duration': estimated_duration, 'confidence': confidence, 'reasoning': f'Selected {agent_id} based on task type and performance history'}

    def _calculate_priority(self, urgency: str, context: dict[str, Any]) -> int:
        """Calculate task priority based on urgency and context."""
        base_priority = {'low': 1, 'normal': 5, 'high': 8, 'critical': 10}.get(urgency, 5)
        if context.get('user_waiting', False):
            base_priority += 2
        if context.get('time_sensitive', False):
            base_priority += 1
        return min(base_priority, 10)

    def get_routing_stats(self) -> dict[str, Any]:
        """Get routing system statistics."""
        cache_hit_rate = 0.0
        if self.routing_cache:
            recent_entries = [entry for entry in self.routing_cache.values() if time.time() - entry['cached_at'] < 3600]
            cache_hit_rate = len(recent_entries) / len(self.routing_cache) if self.routing_cache else 0.0
        return {'cache_size': len(self.routing_cache), 'cache_hit_rate': cache_hit_rate, 'cache_ttl_seconds': self.cache_ttl}

class AutonomousDecisionMaker:
    """Autonomous decision-making system for complex scenarios."""

    def __init__(self, learning_engine: AutonomousLearningEngine):
        self.learning_engine = learning_engine
        self.decision_history: list[dict[str, Any]] = []
        self.confidence_threshold = 0.7

    async def make_decision(self, decision_context: dict[str, Any], options: list[dict[str, Any]], decision_criteria: dict[str, float] | None=None) -> dict[str, Any]:
        """Make autonomous decision based on learning and context."""
        if not options:
            return {'decision': None, 'confidence': 0.0, 'reasoning': 'No options provided'}
        if decision_criteria is None:
            decision_criteria = {'performance': 0.4, 'cost': 0.3, 'reliability': 0.2, 'speed': 0.1}
        option_scores = []
        for option in options:
            score = await self._evaluate_option(option, decision_context, decision_criteria)
            option_scores.append((option, score))
        best_option, best_score = max(option_scores, key=lambda x: x[1])
        decision = {'selected_option': best_option, 'confidence': best_score, 'all_options_evaluated': len(options), 'decision_criteria': decision_criteria, 'reasoning': f'Selected option with score {best_score:.3f}', 'timestamp': time.time()}
        self.decision_history.append(decision)
        return decision

    async def _evaluate_option(self, option: dict[str, Any], context: dict[str, Any], criteria: dict[str, float]) -> float:
        """Evaluate a single option against decision criteria."""
        scores = {}
        task_type = option.get('task_type', context.get('task_type', 'unknown'))
        model_selection = self.learning_engine.select_optimal_model(task_type, context)
        scores['performance'] = model_selection.get('confidence', 0.5)
        estimated_cost = option.get('estimated_cost', 0.01)
        scores['cost'] = max(0, 1 - estimated_cost / 0.1)
        scores['reliability'] = option.get('reliability_score', 0.8)
        estimated_duration = option.get('estimated_duration', 30.0)
        scores['speed'] = max(0, 1 - estimated_duration / 60.0)
        total_score = sum((scores[metric] * weight for metric, weight in criteria.items()))
        return total_score

    def get_decision_summary(self, hours: int=24) -> dict[str, Any]:
        """Get summary of recent decisions."""
        cutoff_time = time.time() - hours * 3600
        recent_decisions = [d for d in self.decision_history if d['timestamp'] > cutoff_time]
        if not recent_decisions:
            return {'message': 'No decisions in the specified time period'}
        confidences = [d['confidence'] for d in recent_decisions]
        avg_confidence = statistics.mean(confidences)
        return {'total_decisions': len(recent_decisions), 'average_confidence': avg_confidence, 'high_confidence_decisions': sum((1 for d in recent_decisions if d['confidence'] > 0.8)), 'low_confidence_decisions': sum((1 for d in recent_decisions if d['confidence'] < 0.5)), 'decision_types': len({d.get('selected_option', {}).get('type', 'unknown') for d in recent_decisions})}
_autonomous_learning: AutonomousLearningEngine | None = None
_adaptive_router: AdaptiveTaskRouter | None = None
_decision_maker: AutonomousDecisionMaker | None = None

def get_autonomous_learning_engine() -> AutonomousLearningEngine:
    """Get or create the global autonomous learning engine."""
    global _autonomous_learning
    if _autonomous_learning is None:
        _autonomous_learning = AutonomousLearningEngine()
    return _autonomous_learning

def get_adaptive_router() -> AdaptiveTaskRouter:
    """Get or create the global adaptive task router."""
    learning_engine = get_autonomous_learning_engine()
    global _adaptive_router
    if _adaptive_router is None:
        _adaptive_router = AdaptiveTaskRouter(learning_engine)
    return _adaptive_router

def get_decision_maker() -> AutonomousDecisionMaker:
    """Get or create the global autonomous decision maker."""
    learning_engine = get_autonomous_learning_engine()
    global _decision_maker
    if _decision_maker is None:
        _decision_maker = AutonomousDecisionMaker(learning_engine)
    return _decision_maker

def record_agent_performance(agent_id: str, task_type: str, metrics: dict[str, float]) -> None:
    """Record agent performance for autonomous learning."""
    performance_metrics = AgentPerformanceMetrics(agent_id=agent_id, task_type=task_type, success_rate=metrics.get('success_rate', 0.0), average_response_time=metrics.get('response_time', 0.0), error_rate=metrics.get('error_rate', 0.0), user_satisfaction=metrics.get('satisfaction', 0.5), cost_efficiency=metrics.get('cost_efficiency', 0.5), context_adherence=metrics.get('context_adherence', 0.8))
    learning_engine = get_autonomous_learning_engine()
    learning_engine.record_agent_performance(performance_metrics)

def select_optimal_model(task_type: str, context: dict[str, Any] | None=None, tenant_id: str | None=None) -> dict[str, Any]:
    """Select optimal model using autonomous learning."""
    learning_engine = get_autonomous_learning_engine()
    return learning_engine.select_optimal_model(task_type, context, tenant_id)

def route_task_adaptively(task_type: str, context: dict[str, Any], tenant_id: str | None=None, urgency: str='normal') -> dict[str, Any]:
    """Route task using adaptive routing."""
    router = get_adaptive_router()
    return router.route_task(task_type, context, tenant_id, urgency)

def process_user_feedback(feedback_data: dict[str, Any]) -> None:
    """Process user feedback for autonomous learning."""
    learning_engine = get_autonomous_learning_engine()
    learning_engine.process_feedback(feedback_data)

def get_autonomous_intelligence_summary() -> dict[str, Any]:
    """Get comprehensive autonomous intelligence summary."""
    learning_engine = get_autonomous_learning_engine()
    router = get_adaptive_router()
    decision_maker = get_decision_maker()
    return {'learning_engine': learning_engine.get_learning_summary(), 'routing_stats': router.get_routing_stats(), 'decision_maker': decision_maker.get_decision_summary(), 'total_components': 3}

def initialize_autonomous_intelligence() -> None:
    """Initialize autonomous intelligence systems."""
    learning_engine = get_autonomous_learning_engine()
    logger.info('Autonomous intelligence systems initialized')
    if not learning_engine.model_data:
        learning_engine.record_model_performance('gpt-3.5-turbo', 'openrouter', 0.75, 0.002, 'content_analysis')
        learning_engine.record_model_performance('gpt-4', 'openrouter', 0.85, 0.03, 'content_analysis')
        learning_engine.record_model_performance('claude-3', 'openrouter', 0.8, 0.015, 'fact_checking')
        logger.info('Initialized baseline model performance data')
__all__ = ['AdaptiveTaskRouter', 'AgentPerformanceMetrics', 'AutonomousDecisionMaker', 'AutonomousLearningEngine', 'ModelPerformanceData', 'get_adaptive_router', 'get_autonomous_intelligence_summary', 'get_autonomous_learning_engine', 'get_decision_maker', 'initialize_autonomous_intelligence', 'process_user_feedback', 'record_agent_performance', 'route_task_adaptively', 'select_optimal_model']