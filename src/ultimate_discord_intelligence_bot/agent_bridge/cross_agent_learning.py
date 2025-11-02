"""Cross-Agent Learning System - Adaptive intelligence sharing

This service enables agents to learn from each other's successes and failures,
building collective intelligence that improves over time.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning patterns"""
    SUCCESS_PATTERN = 'success_pattern'
    FAILURE_PATTERN = 'failure_pattern'
    OPTIMIZATION_PATTERN = 'optimization_pattern'
    ADAPTATION_PATTERN = 'adaptation_pattern'
    COLLABORATION_PATTERN = 'collaboration_pattern'

class LearningSource(Enum):
    """Sources of learning"""
    DIRECT_EXPERIENCE = 'direct_experience'
    OBSERVED_BEHAVIOR = 'observed_behavior'
    SHARED_INSIGHT = 'shared_insight'
    VALIDATED_OUTCOME = 'validated_outcome'
    COLLECTIVE_INTELLIGENCE = 'collective_intelligence'

@dataclass
class LearningPattern:
    """A learned pattern from agent experiences"""
    pattern_id: str
    learning_type: LearningType
    source: LearningSource
    agent_type: str
    context: dict[str, Any]
    pattern_data: dict[str, Any]
    success_rate: float
    confidence: float
    validation_count: int
    last_updated: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class LearningRequest:
    """Request for learning patterns"""
    requesting_agent_id: str
    agent_type: str
    context: dict[str, Any]
    learning_types: list[LearningType]
    min_confidence: float = 0.6
    max_patterns: int = 20
    tenant_id: str | None = None
    workspace_id: str | None = None

@dataclass
class LearningResponse:
    """Response with relevant learning patterns"""
    patterns: list[LearningPattern]
    recommendations: list[dict[str, Any]]
    adaptation_suggestions: list[str]
    confidence_scores: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CrossAgentLearningConfig:
    """Configuration for cross-agent learning"""
    enable_learning: bool = True
    enable_pattern_extraction: bool = True
    enable_adaptive_learning: bool = True
    enable_collaborative_learning: bool = True
    min_pattern_confidence: float = 0.5
    pattern_extraction_threshold: int = 5
    learning_rate: float = 0.1
    adaptation_rate: float = 0.05
    max_patterns_per_type: int = 1000
    pattern_retention_days: int = 90
    validation_threshold: int = 3
    pattern_cache_ttl: int = 600
    learning_batch_size: int = 50

class CrossAgentLearningService:
    """Cross-agent learning and pattern recognition service"""

    def __init__(self, config: CrossAgentLearningConfig | None=None):
        self.config = config or CrossAgentLearningConfig()
        self._initialized = False
        self._patterns: dict[str, LearningPattern] = {}
        self._agent_patterns: dict[str, set[str]] = {}
        self._pattern_cache: dict[str, Any] = {}
        self._learning_history: dict[str, list[dict[str, Any]]] = {}
        self._success_tracker: dict[str, list[dict[str, Any]]] = {}
        self._failure_tracker: dict[str, list[dict[str, Any]]] = {}
        self._initialize_learning()

    def _initialize_learning(self) -> None:
        """Initialize the cross-agent learning service"""
        try:
            self._initialized = True
            logger.info('Cross-Agent Learning Service initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize Cross-Agent Learning Service: {e}')
            self._initialized = False

    async def learn_from_experience(self, agent_id: str, agent_type: str, experience_type: LearningType, context: dict[str, Any], outcome: dict[str, Any], success: bool, metadata: dict[str, Any] | None=None, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Learn from an agent's experience"""
        try:
            if not self._initialized:
                return StepResult.fail('Cross-Agent Learning Service not initialized')
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, 'tenant_id', 'default') if ctx else 'default'
            if workspace_id is None:
                workspace_id = getattr(ctx, 'workspace_id', 'main') if ctx else 'main'
            experience_record = {'agent_id': agent_id, 'agent_type': agent_type, 'experience_type': experience_type.value, 'context': context, 'outcome': outcome, 'success': success, 'timestamp': datetime.now(timezone.utc).isoformat(), 'tenant_id': tenant_id, 'workspace_id': workspace_id, 'metadata': metadata or {}}
            if agent_id not in self._learning_history:
                self._learning_history[agent_id] = []
            self._learning_history[agent_id].append(experience_record)
            if success:
                if agent_id not in self._success_tracker:
                    self._success_tracker[agent_id] = []
                self._success_tracker[agent_id].append(experience_record)
            else:
                if agent_id not in self._failure_tracker:
                    self._failure_tracker[agent_id] = []
                self._failure_tracker[agent_id].append(experience_record)
            patterns_extracted = await self._extract_patterns(agent_id, agent_type)
            updated_patterns = await self._update_patterns(agent_id, experience_record)
            logger.info(f'Experience learned from {agent_id}: {experience_type.value}, success={success}')
            return StepResult.ok(data={'learned': True, 'patterns_extracted': patterns_extracted, 'patterns_updated': updated_patterns, 'experience_type': experience_type.value, 'success': success})
        except Exception as e:
            logger.error(f'Error learning from experience: {e}', exc_info=True)
            return StepResult.fail(f'Experience learning failed: {e!s}')

    async def get_learning_patterns(self, requesting_agent_id: str, agent_type: str, context: dict[str, Any], learning_types: list[LearningType], min_confidence: float=0.6, max_patterns: int=20, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Get relevant learning patterns for an agent"""
        try:
            if not self._initialized:
                return StepResult.fail('Cross-Agent Learning Service not initialized')
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, 'tenant_id', 'default') if ctx else 'default'
            if workspace_id is None:
                workspace_id = getattr(ctx, 'workspace_id', 'main') if ctx else 'main'
            relevant_patterns = await self._search_patterns(context=context, learning_types=learning_types, min_confidence=min_confidence, requesting_agent_type=agent_type, max_patterns=max_patterns)
            recommendations = await self._generate_recommendations(patterns=relevant_patterns, context=context, agent_type=agent_type)
            adaptation_suggestions = await self._generate_adaptation_suggestions(patterns=relevant_patterns, context=context, agent_type=agent_type)
            confidence_scores = self._calculate_confidence_scores(relevant_patterns)
            response = LearningResponse(patterns=relevant_patterns, recommendations=recommendations, adaptation_suggestions=adaptation_suggestions, confidence_scores=confidence_scores, metadata={'requesting_agent': requesting_agent_id, 'agent_type': agent_type, 'context_keys': list(context.keys()), 'learning_types': [lt.value for lt in learning_types], 'tenant_id': tenant_id, 'workspace_id': workspace_id})
            logger.info(f'Learning patterns requested by {requesting_agent_id}: {len(relevant_patterns)} patterns found')
            return StepResult.ok(data=response)
        except Exception as e:
            logger.error(f'Error getting learning patterns: {e}', exc_info=True)
            return StepResult.fail(f'Learning pattern retrieval failed: {e!s}')

    async def validate_pattern(self, pattern_id: str, validating_agent_id: str, validation_context: dict[str, Any], success: bool, feedback: str | None=None, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Validate a learning pattern based on new experience"""
        try:
            if not self._initialized:
                return StepResult.fail('Cross-Agent Learning Service not initialized')
            if pattern_id not in self._patterns:
                return StepResult.fail(f'Pattern {pattern_id} not found')
            pattern = self._patterns[pattern_id]
            {'validating_agent': validating_agent_id, 'validation_context': validation_context, 'success': success, 'feedback': feedback, 'validated_at': datetime.now(timezone.utc).isoformat(), 'tenant_id': tenant_id, 'workspace_id': workspace_id}
            pattern.validation_count += 1
            if success:
                pattern.success_rate = (pattern.success_rate * (pattern.validation_count - 1) + 1.0) / pattern.validation_count
            else:
                pattern.success_rate = (pattern.success_rate * (pattern.validation_count - 1) + 0.0) / pattern.validation_count
            pattern.confidence = (pattern.confidence + pattern.success_rate) / 2
            pattern.last_updated = datetime.now(timezone.utc)
            self._patterns[pattern_id] = pattern
            cache_key = f'pattern:{pattern_id}'
            if cache_key in self._pattern_cache:
                self._pattern_cache[cache_key] = pattern
            logger.info(f'Pattern {pattern_id} validated by {validating_agent_id}: success={success}')
            return StepResult.ok(data={'validated': True, 'pattern_id': pattern_id, 'validation_count': pattern.validation_count, 'success_rate': pattern.success_rate, 'updated_confidence': pattern.confidence})
        except Exception as e:
            logger.error(f'Error validating pattern: {e}', exc_info=True)
            return StepResult.fail(f'Pattern validation failed: {e!s}')

    async def get_agent_learning_summary(self, agent_id: str, days: int=30) -> StepResult:
        """Get learning summary for a specific agent"""
        try:
            if not self._initialized:
                return StepResult.fail('Cross-Agent Learning Service not initialized')
            if agent_id not in self._learning_history:
                return StepResult.ok(data={'agent_id': agent_id, 'summary': 'No learning history found'})
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            recent_experiences = [exp for exp in self._learning_history[agent_id] if datetime.fromisoformat(exp['timestamp']) > cutoff_date]
            if not recent_experiences:
                return StepResult.ok(data={'agent_id': agent_id, 'summary': 'No recent learning history'})
            total_experiences = len(recent_experiences)
            successful_experiences = len([exp for exp in recent_experiences if exp['success']])
            success_rate = successful_experiences / total_experiences if total_experiences > 0 else 0
            experience_types = {}
            for exp in recent_experiences:
                exp_type = exp['experience_type']
                if exp_type not in experience_types:
                    experience_types[exp_type] = {'total': 0, 'successful': 0}
                experience_types[exp_type]['total'] += 1
                if exp['success']:
                    experience_types[exp_type]['successful'] += 1
            learning_trends = self._calculate_learning_trends(recent_experiences)
            agent_patterns = []
            for pattern_id in self._agent_patterns.get(agent_id.split(':')[0], []):
                if pattern_id in self._patterns:
                    agent_patterns.append(self._patterns[pattern_id])
            return StepResult.ok(data={'agent_id': agent_id, 'summary': {'total_experiences': total_experiences, 'successful_experiences': successful_experiences, 'success_rate': success_rate, 'experience_types': experience_types, 'learning_trends': learning_trends, 'relevant_patterns': len(agent_patterns), 'pattern_confidence_avg': sum((p.confidence for p in agent_patterns)) / max(len(agent_patterns), 1)}})
        except Exception as e:
            logger.error(f'Error getting agent learning summary: {e}', exc_info=True)
            return StepResult.fail(f'Learning summary retrieval failed: {e!s}')

    async def _extract_patterns(self, agent_id: str, agent_type: str) -> int:
        """Extract learning patterns from agent experiences"""
        try:
            patterns_extracted = 0
            if agent_id in self._success_tracker and len(self._success_tracker[agent_id]) >= self.config.pattern_extraction_threshold:
                success_patterns = await self._analyze_success_patterns(agent_id, agent_type)
                patterns_extracted += len(success_patterns)
            if agent_id in self._failure_tracker and len(self._failure_tracker[agent_id]) >= self.config.pattern_extraction_threshold:
                failure_patterns = await self._analyze_failure_patterns(agent_id, agent_type)
                patterns_extracted += len(failure_patterns)
            return patterns_extracted
        except Exception as e:
            logger.error(f'Error extracting patterns: {e}')
            return 0

    async def _analyze_success_patterns(self, agent_id: str, agent_type: str) -> list[LearningPattern]:
        """Analyze and extract success patterns"""
        try:
            patterns = []
            successes = self._success_tracker[agent_id]
            success_groups = self._group_similar_experiences(successes)
            for group in success_groups:
                if len(group) >= self.config.pattern_extraction_threshold:
                    pattern = await self._create_pattern_from_group(group=group, learning_type=LearningType.SUCCESS_PATTERN, agent_type=agent_type)
                    if pattern:
                        patterns.append(pattern)
            return patterns
        except Exception as e:
            logger.error(f'Error analyzing success patterns: {e}')
            return []

    async def _analyze_failure_patterns(self, agent_id: str, agent_type: str) -> list[LearningPattern]:
        """Analyze and extract failure patterns"""
        try:
            patterns = []
            failures = self._failure_tracker[agent_id]
            failure_groups = self._group_similar_experiences(failures)
            for group in failure_groups:
                if len(group) >= self.config.pattern_extraction_threshold:
                    pattern = await self._create_pattern_from_group(group=group, learning_type=LearningType.FAILURE_PATTERN, agent_type=agent_type)
                    if pattern:
                        patterns.append(pattern)
            return patterns
        except Exception as e:
            logger.error(f'Error analyzing failure patterns: {e}')
            return []

    def _group_similar_experiences(self, experiences: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Group similar experiences together"""
        try:
            groups = []
            for experience in experiences:
                added_to_group = False
                for group in groups:
                    if self._experiences_similar(experience, group[0]):
                        group.append(experience)
                        added_to_group = True
                        break
                if not added_to_group:
                    groups.append([experience])
            return groups
        except Exception as e:
            logger.error(f'Error grouping experiences: {e}')
            return []

    def _experiences_similar(self, exp1: dict[str, Any], exp2: dict[str, Any]) -> bool:
        """Check if two experiences are similar"""
        try:
            context1 = exp1.get('context', {})
            context2 = exp2.get('context', {})
            common_keys = set(context1.keys()).intersection(set(context2.keys()))
            if len(common_keys) < 3:
                return False
            similar_values = 0
            for key in common_keys:
                if context1[key] == context2[key]:
                    similar_values += 1
            similarity_ratio = similar_values / len(common_keys)
            return similarity_ratio >= 0.7
        except Exception:
            return False

    async def _create_pattern_from_group(self, group: list[dict[str, Any]], learning_type: LearningType, agent_type: str) -> LearningPattern | None:
        """Create a learning pattern from a group of similar experiences"""
        try:
            common_context = self._extract_common_context(group)
            common_outcomes = self._extract_common_outcomes(group)
            success_count = len([exp for exp in group if exp['success']])
            success_rate = success_count / len(group)
            confidence = min(0.9, success_rate + len(group) / 100)
            pattern_id = f'{agent_type}:{learning_type.value}:{int(datetime.now().timestamp())}'
            pattern = LearningPattern(pattern_id=pattern_id, learning_type=learning_type, source=LearningSource.DIRECT_EXPERIENCE, agent_type=agent_type, context=common_context, pattern_data={'common_outcomes': common_outcomes, 'experience_count': len(group), 'success_rate': success_rate}, success_rate=success_rate, confidence=confidence, validation_count=0, last_updated=datetime.now(timezone.utc), metadata={'created_from': 'experience_analysis', 'source_experiences': len(group)})
            self._patterns[pattern_id] = pattern
            if agent_type not in self._agent_patterns:
                self._agent_patterns[agent_type] = set()
            self._agent_patterns[agent_type].add(pattern_id)
            logger.info(f'Created pattern {pattern_id} from {len(group)} experiences')
            return pattern
        except Exception as e:
            logger.error(f'Error creating pattern from group: {e}')
            return None

    def _extract_common_context(self, experiences: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common context elements from experiences"""
        try:
            if not experiences:
                return {}
            all_keys = set()
            for exp in experiences:
                all_keys.update(exp.get('context', {}).keys())
            common_context = {}
            for key in all_keys:
                values = [exp.get('context', {}).get(key) for exp in experiences]
                most_common = max(set(values), key=values.count)
                if values.count(most_common) >= len(values) * 0.7:
                    common_context[key] = most_common
            return common_context
        except Exception as e:
            logger.error(f'Error extracting common context: {e}')
            return {}

    def _extract_common_outcomes(self, experiences: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common outcome elements from experiences"""
        try:
            if not experiences:
                return {}
            all_keys = set()
            for exp in experiences:
                all_keys.update(exp.get('outcome', {}).keys())
            common_outcomes = {}
            for key in all_keys:
                values = [exp.get('outcome', {}).get(key) for exp in experiences]
                most_common = max(set(values), key=values.count)
                if values.count(most_common) >= len(values) * 0.7:
                    common_outcomes[key] = most_common
            return common_outcomes
        except Exception as e:
            logger.error(f'Error extracting common outcomes: {e}')
            return {}

    async def _search_patterns(self, context: dict[str, Any], learning_types: list[LearningType], min_confidence: float, requesting_agent_type: str, max_patterns: int) -> list[LearningPattern]:
        """Search for relevant learning patterns"""
        try:
            candidate_patterns = []
            for pattern in self._patterns.values():
                if pattern.learning_type not in learning_types:
                    continue
                if pattern.confidence < min_confidence:
                    continue
                candidate_patterns.append(pattern)
            scored_patterns = []
            for pattern in candidate_patterns:
                score = self._calculate_pattern_relevance(pattern, context, requesting_agent_type)
                scored_patterns.append((score, pattern))
            scored_patterns.sort(key=lambda x: x[0], reverse=True)
            return [pattern for score, pattern in scored_patterns[:max_patterns]]
        except Exception as e:
            logger.error(f'Error searching patterns: {e}')
            return []

    def _calculate_pattern_relevance(self, pattern: LearningPattern, context: dict[str, Any], requesting_agent_type: str) -> float:
        """Calculate relevance score for a pattern"""
        try:
            score = 0.0
            score += pattern.confidence * 0.4
            if pattern.agent_type == requesting_agent_type:
                score += 0.3
            elif self._agent_types_compatible(pattern.agent_type, requesting_agent_type):
                score += 0.2
            context_similarity = self._context_similarity(context, pattern.context)
            score += context_similarity * 0.2
            if pattern.validation_count > 0:
                score += min(0.1, pattern.validation_count / 10)
            score += pattern.success_rate * 0.1
            return min(1.0, score)
        except Exception as e:
            logger.error(f'Error calculating pattern relevance: {e}')
            return 0.0

    def _agent_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two agent types are compatible for learning"""
        try:
            common_prefixes = ['mission', 'executive', 'workflow', 'analysis']
            return any((prefix in type1.lower() and prefix in type2.lower() for prefix in common_prefixes))
        except Exception:
            return False

    def _context_similarity(self, context1: dict[str, Any], context2: dict[str, Any]) -> float:
        """Calculate context similarity"""
        try:
            if not context1 or not context2:
                return 0.0
            common_keys = set(context1.keys()).intersection(set(context2.keys()))
            if not common_keys:
                return 0.0
            matches = 0
            for key in common_keys:
                if context1[key] == context2[key]:
                    matches += 1
            return matches / len(common_keys)
        except Exception:
            return 0.0

    async def _generate_recommendations(self, patterns: list[LearningPattern], context: dict[str, Any], agent_type: str) -> list[dict[str, Any]]:
        """Generate recommendations based on patterns"""
        try:
            recommendations = []
            for pattern in patterns:
                if pattern.learning_type == LearningType.SUCCESS_PATTERN:
                    recommendations.append({'type': 'success_strategy', 'pattern_id': pattern.pattern_id, 'confidence': pattern.confidence, 'suggestion': f'Apply success pattern from {pattern.agent_type}: {pattern.pattern_data.get('common_outcomes', {})}', 'context_requirements': pattern.context})
                elif pattern.learning_type == LearningType.FAILURE_PATTERN:
                    recommendations.append({'type': 'avoidance_strategy', 'pattern_id': pattern.pattern_id, 'confidence': pattern.confidence, 'suggestion': f'Avoid failure pattern from {pattern.agent_type}: {pattern.pattern_data.get('common_outcomes', {})}', 'context_requirements': pattern.context})
            return recommendations
        except Exception as e:
            logger.error(f'Error generating recommendations: {e}')
            return []

    async def _generate_adaptation_suggestions(self, patterns: list[LearningPattern], context: dict[str, Any], agent_type: str) -> list[str]:
        """Generate adaptation suggestions based on patterns"""
        try:
            suggestions = []
            for pattern in patterns:
                if pattern.learning_type == LearningType.ADAPTATION_PATTERN:
                    suggestions.append(f'Consider adapting strategy based on {pattern.agent_type} experience')
                elif pattern.learning_type == LearningType.OPTIMIZATION_PATTERN:
                    suggestions.append(f'Optimize approach using {pattern.agent_type} optimization pattern')
                elif pattern.learning_type == LearningType.COLLABORATION_PATTERN:
                    suggestions.append(f'Collaborate with {pattern.agent_type} for better outcomes')
            return suggestions
        except Exception as e:
            logger.error(f'Error generating adaptation suggestions: {e}')
            return []

    def _calculate_confidence_scores(self, patterns: list[LearningPattern]) -> dict[str, float]:
        """Calculate confidence scores for patterns"""
        try:
            scores = {}
            for pattern in patterns:
                scores[pattern.pattern_id] = pattern.confidence
            return scores
        except Exception as e:
            logger.error(f'Error calculating confidence scores: {e}')
            return {}

    def _calculate_learning_trends(self, experiences: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate learning trends from experiences"""
        try:
            if len(experiences) < 2:
                return {'trend': 'insufficient_data'}
            sorted_experiences = sorted(experiences, key=lambda x: x['timestamp'])
            recent_successes = len([exp for exp in sorted_experiences[-5:] if exp['success']])
            recent_total = min(5, len(sorted_experiences))
            recent_success_rate = recent_successes / recent_total if recent_total > 0 else 0
            earlier_successes = len([exp for exp in sorted_experiences[:-5] if exp['success']])
            earlier_total = max(0, len(sorted_experiences) - 5)
            earlier_success_rate = earlier_successes / earlier_total if earlier_total > 0 else 0
            if recent_success_rate > earlier_success_rate + 0.1:
                trend = 'improving'
            elif recent_success_rate < earlier_success_rate - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
            return {'trend': trend, 'recent_success_rate': recent_success_rate, 'overall_success_rate': len([exp for exp in experiences if exp['success']]) / len(experiences)}
        except Exception as e:
            logger.error(f'Error calculating learning trends: {e}')
            return {'trend': 'error'}

    async def _update_patterns(self, agent_id: str, experience_record: dict[str, Any]) -> int:
        """Update existing patterns based on new experience"""
        try:
            updated_count = 0
            for pattern_id, pattern in self._patterns.items():
                if pattern.agent_type == experience_record['agent_type'] and self._experience_matches_pattern(experience_record, pattern):
                    pattern.validation_count += 1
                    if experience_record['success']:
                        pattern.success_rate = (pattern.success_rate * (pattern.validation_count - 1) + 1.0) / pattern.validation_count
                    else:
                        pattern.success_rate = (pattern.success_rate * (pattern.validation_count - 1) + 0.0) / pattern.validation_count
                    pattern.confidence = (pattern.confidence + pattern.success_rate) / 2
                    pattern.last_updated = datetime.now(timezone.utc)
                    self._patterns[pattern_id] = pattern
                    updated_count += 1
            return updated_count
        except Exception as e:
            logger.error(f'Error updating patterns: {e}')
            return 0

    def _experience_matches_pattern(self, experience: dict[str, Any], pattern: LearningPattern) -> bool:
        """Check if an experience matches a pattern"""
        try:
            context_similarity = self._context_similarity(experience.get('context', {}), pattern.context)
            return context_similarity >= 0.7
        except Exception:
            return False

    def get_learning_status(self) -> dict[str, Any]:
        """Get learning service status"""
        return {'initialized': self._initialized, 'total_patterns': len(self._patterns), 'total_agents': len(self._agent_patterns), 'total_experiences': sum((len(exp_list) for exp_list in self._learning_history.values())), 'success_tracker_entries': sum((len(exp_list) for exp_list in self._success_tracker.values())), 'failure_tracker_entries': sum((len(exp_list) for exp_list in self._failure_tracker.values())), 'config': {'enable_learning': self.config.enable_learning, 'enable_pattern_extraction': self.config.enable_pattern_extraction, 'enable_adaptive_learning': self.config.enable_adaptive_learning, 'min_pattern_confidence': self.config.min_pattern_confidence}}