"""Prompt Library with A/B Testing

Centralized prompt variants with performance tags → auto-select best examples
using bandit routing.
"""
from __future__ import annotations
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import numpy as np
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompts in the library"""
    ANALYSIS = 'analysis'
    VERIFICATION = 'verification'
    SYNTHESIS = 'synthesis'
    EXTRACTION = 'extraction'
    CLASSIFICATION = 'classification'
    GENERATION = 'generation'

@dataclass
class PromptVariant:
    """A variant of a prompt template"""
    variant_id: str
    prompt_type: PromptType
    template: str
    variables: list[str] = field(default_factory=list)
    performance_tags: dict[str, float] = field(default_factory=dict)
    usage_count: int = 0
    avg_quality: float = 0.5
    avg_latency_ms: float = 1000.0
    avg_cost_usd: float = 0.01
    success_rate: float = 0.9
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

@dataclass
class PromptSelection:
    """Result of prompt selection"""
    variant_id: str
    template: str
    confidence: float
    expected_quality: float
    reasoning: str

class PromptLibraryAB:
    """
    Prompt Library with A/B Testing

    Features:
    1. Store multiple variants for each prompt type
    2. Track performance metrics for each variant
    3. Use contextual bandit to select best variant
    4. Auto-generate new variants based on performance
    5. Prune low-performing variants
    """

    def __init__(self, context_dim: int=8):
        self.variants: dict[PromptType, list[PromptVariant]] = defaultdict(list)
        self.variant_parameters: dict[str, np.ndarray] = {}
        self.context_dim = context_dim
        self.feedback_queue: deque[dict[str, Any]] = deque(maxlen=1000)
        self.generation_history: list[dict[str, Any]] = []

    def register_variant(self, prompt_type: PromptType, template: str, performance_tags: dict[str, float] | None=None) -> StepResult:
        """Register a new prompt variant"""
        try:
            variant_id = self._generate_variant_id(prompt_type, template)
            if variant_id in self.variant_parameters:
                return StepResult.skip(reason='variant_already_exists', variant_id=variant_id)
            variables = self._extract_variables(template)
            variant = PromptVariant(variant_id=variant_id, prompt_type=prompt_type, template=template, variables=variables, performance_tags=performance_tags or {})
            self.variants[prompt_type].append(variant)
            self.variant_parameters[variant_id] = np.random.randn(self.context_dim) * 0.01
            logger.info(f'Registered prompt variant: {prompt_type.value}/{variant_id}')
            return StepResult.ok(message='Variant registered', variant_id=variant_id)
        except Exception as e:
            logger.error(f'Failed to register variant: {e}')
            return StepResult.fail(f'Registration failed: {e}')

    def select_prompt(self, prompt_type: PromptType, context: dict[str, Any], optimization_target: str='quality') -> StepResult:
        """Select best prompt variant for given context"""
        try:
            candidates = self.variants.get(prompt_type, [])
            if not candidates:
                return StepResult.fail(f'No variants available for {prompt_type.value}')
            context_vec = self._extract_context_features(context, optimization_target)
            expected_rewards = {}
            for variant in candidates:
                params = self.variant_parameters[variant.variant_id]
                expected_reward = np.dot(params, context_vec)
                if optimization_target == 'quality':
                    expected_reward *= variant.avg_quality
                elif optimization_target == 'speed':
                    expected_reward *= 1.0 / (1.0 + variant.avg_latency_ms / 1000.0)
                elif optimization_target == 'cost':
                    expected_reward *= 1.0 / (1.0 + variant.avg_cost_usd * 100)
                else:
                    expected_reward *= variant.avg_quality * 0.6
                    expected_reward *= 1.0 / (1.0 + variant.avg_latency_ms / 1000.0) * 0.2
                    expected_reward *= 1.0 / (1.0 + variant.avg_cost_usd * 100) * 0.2
                expected_reward *= variant.success_rate
                expected_rewards[variant.variant_id] = expected_reward
            selected_id = max(expected_rewards, key=lambda k: expected_rewards[k])
            selected_variant = next((v for v in candidates if v.variant_id == selected_id))
            selected_variant.usage_count += 1
            selected_variant.last_used = time.time()
            sorted_rewards = sorted(expected_rewards.values(), reverse=True)
            confidence = 0.8
            if len(sorted_rewards) > 1:
                gap = sorted_rewards[0] - sorted_rewards[1]
                confidence = min(0.95, 0.5 + gap / 2.0)
            selection = PromptSelection(variant_id=selected_id, template=selected_variant.template, confidence=confidence, expected_quality=selected_variant.avg_quality, reasoning=f'Selected variant {selected_id} for {prompt_type.value} optimizing for {optimization_target} (confidence={confidence:.2f})')
            logger.debug(f'Prompt selected: {prompt_type.value} → {selected_id}')
            return StepResult.ok(data=selection)
        except Exception as e:
            logger.error(f'Prompt selection failed: {e}')
            return StepResult.fail(f'Selection failed: {e}')

    def submit_feedback(self, variant_id: str, context: dict[str, Any], quality_score: float, latency_ms: float, cost_usd: float, success: bool=True) -> StepResult:
        """Submit performance feedback for a variant"""
        try:
            self.feedback_queue.append({'variant_id': variant_id, 'context': context, 'quality_score': quality_score, 'latency_ms': latency_ms, 'cost_usd': cost_usd, 'success': success, 'timestamp': time.time()})
            return StepResult.ok(message='Feedback queued')
        except Exception as e:
            logger.error(f'Failed to submit feedback: {e}')
            return StepResult.fail(f'Feedback submission failed: {e}')

    def process_feedback_batch(self, batch_size: int=20, optimization_target: str='quality') -> StepResult:
        """Process queued feedback signals"""
        try:
            processed = 0
            while self.feedback_queue and processed < batch_size:
                feedback = self.feedback_queue.popleft()
                variant_id = feedback['variant_id']
                variant = None
                for variants_list in self.variants.values():
                    variant = next((v for v in variants_list if v.variant_id == variant_id), None)
                    if variant:
                        break
                if not variant:
                    logger.warning(f'Variant not found: {variant_id}')
                    continue
                alpha = 0.2
                variant.avg_quality = (1 - alpha) * variant.avg_quality + alpha * feedback['quality_score']
                variant.avg_latency_ms = (1 - alpha) * variant.avg_latency_ms + alpha * feedback['latency_ms']
                variant.avg_cost_usd = (1 - alpha) * variant.avg_cost_usd + alpha * feedback['cost_usd']
                variant.success_rate = 0.9 * variant.success_rate + 0.1 * (1.0 if feedback['success'] else 0.0)
                context_vec = self._extract_context_features(feedback['context'], optimization_target)
                if optimization_target == 'quality':
                    reward = feedback['quality_score']
                elif optimization_target == 'speed':
                    reward = 1.0 / (1.0 + feedback['latency_ms'] / 1000.0)
                elif optimization_target == 'cost':
                    reward = 1.0 / (1.0 + feedback['cost_usd'] * 100)
                else:
                    reward = 0.6 * feedback['quality_score']
                    reward += 0.2 / (1.0 + feedback['latency_ms'] / 1000.0)
                    reward += 0.2 / (1.0 + feedback['cost_usd'] * 100)
                params = self.variant_parameters[variant_id]
                learning_rate = 0.01
                prediction = np.dot(params, context_vec)
                error = reward - prediction
                self.variant_parameters[variant_id] += learning_rate * error * context_vec
                processed += 1
            return StepResult.ok(message=f'Processed {processed} feedback signals', processed=processed)
        except Exception as e:
            logger.error(f'Feedback processing failed: {e}')
            return StepResult.fail(f'Processing failed: {e}')

    def _generate_variant_id(self, prompt_type: PromptType, template: str) -> str:
        """Generate unique variant ID"""
        hash_input = f'{prompt_type.value}:{template}'.encode()
        hash_digest = hashlib.md5(hash_input).hexdigest()
        return f'{prompt_type.value}_{hash_digest[:12]}'

    def _extract_variables(self, template: str) -> list[str]:
        """Extract variable names from template"""
        import re
        pattern = '\\{(\\w+)\\}'
        matches = re.findall(pattern, template)
        return list(set(matches))

    def _extract_context_features(self, context: dict[str, Any], optimization_target: str) -> np.ndarray:
        """Extract feature vector from context"""
        features = []
        features.append(context.get('complexity', 0.5))
        features.append(context.get('input_length', 100) / 1000.0)
        features.append(context.get('expected_output_length', 200) / 1000.0)
        features.append(context.get('required_accuracy', 0.9))
        features.append(context.get('budget_usd', 0.01) * 100)
        features.append(context.get('max_latency_ms', 2000) / 5000.0)
        features.append(1.0 if optimization_target == 'quality' else 0.0)
        features.append(1.0 if optimization_target == 'speed' else 0.0)
        return np.array(features[:8], dtype=float)

    def get_variant_statistics(self) -> dict[str, Any]:
        """Get statistics for all variants"""
        stats_by_type = {}
        for prompt_type, variants_list in self.variants.items():
            type_stats = []
            for variant in variants_list:
                type_stats.append({'variant_id': variant.variant_id, 'usage_count': variant.usage_count, 'avg_quality': variant.avg_quality, 'avg_latency_ms': variant.avg_latency_ms, 'avg_cost_usd': variant.avg_cost_usd, 'success_rate': variant.success_rate})
            stats_by_type[prompt_type.value] = type_stats
        return {'variants_by_type': stats_by_type, 'total_variants': sum((len(v) for v in self.variants.values())), 'feedback_queue_size': len(self.feedback_queue)}
_prompt_library: PromptLibraryAB | None = None

def get_prompt_library(auto_create: bool=True) -> PromptLibraryAB | None:
    """Get global prompt library instance"""
    global _prompt_library
    if _prompt_library is None and auto_create:
        _prompt_library = PromptLibraryAB()
    return _prompt_library

def set_prompt_library(library: PromptLibraryAB) -> None:
    """Set global prompt library instance"""
    global _prompt_library
    _prompt_library = library
__all__ = ['PromptLibraryAB', 'PromptSelection', 'PromptType', 'PromptVariant', 'get_prompt_library', 'set_prompt_library']