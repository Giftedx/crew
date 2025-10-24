"""Enhanced prompt compression system with advanced optimization strategies.

This module provides comprehensive prompt compression capabilities that build
upon the existing PromptEngine and add advanced optimization techniques.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Available prompt compression strategies."""

    BASIC = "basic"
    CONTEXT_AWARE = "context_aware"
    SEMANTIC = "semantic"
    ADAPTIVE = "adaptive"
    AGGRESSIVE = "aggressive"


class CompressionLevel(Enum):
    """Compression intensity levels."""

    LIGHT = "light"  # 10-20% reduction
    MODERATE = "moderate"  # 20-40% reduction
    AGGRESSIVE = "aggressive"  # 40-60% reduction
    MAXIMUM = "maximum"  # 60-80% reduction


@dataclass
class CompressionResult:
    """Result of prompt compression operation."""

    original_prompt: str
    compressed_prompt: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: CompressionStrategy
    level: CompressionLevel
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "original_prompt": self.original_prompt,
            "compressed_prompt": self.compressed_prompt,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "strategy_used": self.strategy_used.value,
            "level": self.level.value,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class CompressionConfig:
    """Configuration for prompt compression."""

    # Strategy selection
    default_strategy: CompressionStrategy = CompressionStrategy.ADAPTIVE
    enable_semantic_compression: bool = True
    enable_context_aware: bool = True

    # Compression levels
    light_reduction_target: float = 0.15  # 15% reduction
    moderate_reduction_target: float = 0.30  # 30% reduction
    aggressive_reduction_target: float = 0.50  # 50% reduction
    maximum_reduction_target: float = 0.70  # 70% reduction

    # Quality preservation
    preserve_instructions: bool = True
    preserve_examples: bool = True
    preserve_formatting: bool = True
    min_compression_quality_score: float = 0.8

    # Performance limits
    max_processing_time_ms: float = 5000.0  # 5 seconds
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour


class AdvancedPromptCompressor:
    """Advanced prompt compression with multiple strategies and quality preservation."""

    def __init__(self, config: CompressionConfig | None = None):
        self.config = config or CompressionConfig()
        self._compression_cache: dict[str, CompressionResult] = {}
        self._cache_timestamps: dict[str, float] = {}

        # Initialize compression strategies
        self._strategies = {
            CompressionStrategy.BASIC: self._basic_compression,
            CompressionStrategy.CONTEXT_AWARE: self._context_aware_compression,
            CompressionStrategy.SEMANTIC: self._semantic_compression,
            CompressionStrategy.ADAPTIVE: self._adaptive_compression,
            CompressionStrategy.AGGRESSIVE: self._aggressive_compression,
        }

    def compress_prompt(
        self,
        prompt: str,
        target_level: CompressionLevel | None = None,
        strategy: CompressionStrategy | None = None,
        model: str | None = None,
        preserve_quality: bool = True,
    ) -> StepResult:
        """Compress a prompt using the specified strategy and level."""
        try:
            start_time = time.time()

            # Validate input
            if not prompt or not prompt.strip():
                return StepResult.fail("Empty prompt cannot be compressed")

            # Check cache first
            if self.config.enable_caching:
                cache_key = self._get_cache_key(prompt, target_level, strategy, model)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    return StepResult.ok(data=cached_result.to_dict())

            # Determine strategy and level
            effective_strategy = strategy or self.config.default_strategy
            effective_level = target_level or CompressionLevel.MODERATE

            # Get target reduction
            target_reduction = self._get_target_reduction(effective_level)

            # Count original tokens
            original_tokens = self._count_tokens(prompt, model)

            # Apply compression
            compressed_prompt, metadata = self._apply_compression_strategy(
                prompt, effective_strategy, target_reduction, model, preserve_quality
            )

            # Count compressed tokens
            compressed_tokens = self._count_tokens(compressed_prompt, model)

            # Calculate compression ratio
            compression_ratio = (original_tokens - compressed_tokens) / original_tokens if original_tokens > 0 else 0.0

            # Create result
            processing_time = (time.time() - start_time) * 1000

            result = CompressionResult(
                original_prompt=prompt,
                compressed_prompt=compressed_prompt,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=compression_ratio,
                strategy_used=effective_strategy,
                level=effective_level,
                metadata=metadata,
                processing_time_ms=processing_time,
            )

            # Cache result
            if self.config.enable_caching:
                self._cache_result(cache_key, result)

            return StepResult.ok(data=result.to_dict())

        except Exception as e:
            logger.error(f"Prompt compression failed: {e}")
            return StepResult.fail(f"Prompt compression failed: {e!s}")

    def _apply_compression_strategy(
        self,
        prompt: str,
        strategy: CompressionStrategy,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Apply the specified compression strategy."""
        strategy_func = self._strategies.get(strategy, self._basic_compression)
        return strategy_func(prompt, target_reduction, model, preserve_quality)

    def _basic_compression(
        self,
        prompt: str,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Basic compression using simple text processing."""
        metadata = {"strategy": "basic", "steps": []}

        # Step 1: Remove excessive whitespace
        compressed = re.sub(r"\n\s*\n\s*\n+", "\n\n", prompt)  # Max 2 newlines
        compressed = re.sub(r"[ \t]+", " ", compressed)  # Normalize spaces
        metadata["steps"].append("whitespace_normalization")

        # Step 2: Remove redundant phrases
        redundant_patterns = [
            r"\b(please|kindly|would you|could you)\b\s*",  # Polite filler words
            r"\b(I think|I believe|in my opinion|it seems)\b\s*",  # Opinion qualifiers
            r"\b(very|really|quite|rather|pretty)\s+(good|bad|important|useful)\b",  # Intensifiers
        ]

        for pattern in redundant_patterns:
            compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)
        metadata["steps"].append("redundant_phrase_removal")

        # Step 3: Simplify complex sentences
        if target_reduction > 0.3:  # Aggressive compression
            # Split long sentences
            sentences = compressed.split(".")
            simplified_sentences = []
            for sentence in sentences:
                if len(sentence.split()) > 20:  # Long sentence
                    # Keep only essential parts
                    words = sentence.split()
                    if len(words) > 15:
                        simplified = " ".join(words[:15]) + "..."
                        simplified_sentences.append(simplified)
                    else:
                        simplified_sentences.append(sentence)
                else:
                    simplified_sentences.append(sentence)
            compressed = ". ".join(simplified_sentences)
            metadata["steps"].append("sentence_simplification")

        return compressed.strip(), metadata

    def _context_aware_compression(
        self,
        prompt: str,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Context-aware compression that preserves important information."""
        metadata = {"strategy": "context_aware", "steps": []}

        # Start with basic compression
        compressed, basic_metadata = self._basic_compression(prompt, target_reduction, model, preserve_quality)
        metadata["steps"].extend(basic_metadata["steps"])

        # Step 1: Identify and preserve instruction blocks
        instruction_patterns = [
            r"(?i)(instructions?|directions?|steps?|requirements?):\s*([^\n]+(?:\n[^\n]+)*)",
            r"(?i)(task|goal|objective):\s*([^\n]+)",
            r"(?i)(please|kindly)\s+(do|perform|execute|complete)\s+([^\n]+)",
        ]

        preserved_instructions = []
        for pattern in instruction_patterns:
            matches = re.finditer(pattern, compressed)
            for match in matches:
                preserved_instructions.append(match.group(0))
        metadata["steps"].append(f"preserved_{len(preserved_instructions)}_instructions")

        # Step 2: Preserve examples if configured
        if self.config.preserve_examples:
            example_patterns = [
                r"(?i)(example|sample|demo):\s*([^\n]+(?:\n[^\n]+)*)",
                r"(?i)(for instance|for example|e\.g\.)\s*([^\n]+)",
            ]

            preserved_examples = []
            for pattern in example_patterns:
                matches = re.finditer(pattern, compressed)
                for match in matches:
                    preserved_examples.append(match.group(0))
            metadata["steps"].append(f"preserved_{len(preserved_examples)}_examples")

        # Step 3: Remove less important context
        context_removal_patterns = [
            r"(?i)(background|context|history|previously):\s*([^\n]+(?:\n[^\n]+)*)",
            r"(?i)(note|notice|important|remember):\s*([^\n]+)",
        ]

        for pattern in context_removal_patterns:
            if target_reduction > 0.4:  # Only for aggressive compression
                compressed = re.sub(pattern, "", compressed)
        metadata["steps"].append("context_reduction")

        return compressed.strip(), metadata

    def _semantic_compression(
        self,
        prompt: str,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Semantic compression using advanced techniques."""
        metadata = {"strategy": "semantic", "steps": []}

        # Start with context-aware compression
        compressed, context_metadata = self._context_aware_compression(
            prompt, target_reduction, model, preserve_quality
        )
        metadata["steps"].extend(context_metadata["steps"])

        # Step 1: Synonym replacement for common verbose phrases
        synonym_replacements = {
            r"\b(in order to|so as to)\b": "to",
            r"\b(due to the fact that|because of the fact that)\b": "because",
            r"\b(at this point in time|at the present time)\b": "now",
            r"\b(in the event that|in case)\b": "if",
            r"\b(with regard to|in relation to|concerning)\b": "about",
            r"\b(prior to|before the time that)\b": "before",
            r"\b(subsequent to|after the time that)\b": "after",
        }

        for pattern, replacement in synonym_replacements.items():
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
        metadata["steps"].append("synonym_replacement")

        # Step 2: Abbreviation for common terms
        if target_reduction > 0.3:
            abbreviations = {
                r"\b(application|applications)\b": "app(s)",
                r"\b(communication|communications)\b": "comm(s)",
                r"\b(documentation|documentations)\b": "docs",
                r"\b(information|informations)\b": "info",
                r"\b(management|managements)\b": "mgmt",
            }

            for pattern, replacement in abbreviations.items():
                compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
            metadata["steps"].append("abbreviation_replacement")

        # Step 3: Remove redundant explanations
        redundant_explanations = [
            r"(?i)(which means that|which is to say|in other words|that is to say)\s+([^\n]+)",
            r"(?i)(as mentioned earlier|as stated before|as previously mentioned)\s*[,.]?\s*",
        ]

        for pattern in redundant_explanations:
            compressed = re.sub(pattern, "", compressed)
        metadata["steps"].append("redundant_explanation_removal")

        return compressed.strip(), metadata

    def _adaptive_compression(
        self,
        prompt: str,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Adaptive compression that adjusts strategy based on content analysis."""
        metadata = {"strategy": "adaptive", "steps": []}

        # Analyze prompt characteristics
        analysis = self._analyze_prompt(prompt)
        metadata["analysis"] = analysis

        # Choose optimal strategy based on analysis
        if analysis["has_instructions"] and analysis["has_examples"]:
            # Use context-aware for structured prompts
            return self._context_aware_compression(prompt, target_reduction, model, preserve_quality)
        elif analysis["complexity_score"] > 0.7:
            # Use semantic for complex prompts
            return self._semantic_compression(prompt, target_reduction, model, preserve_quality)
        else:
            # Use basic for simple prompts
            return self._basic_compression(prompt, target_reduction, model, preserve_quality)

    def _aggressive_compression(
        self,
        prompt: str,
        target_reduction: float,
        model: str | None,
        preserve_quality: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Aggressive compression for maximum token reduction."""
        metadata = {"strategy": "aggressive", "steps": []}

        # Start with semantic compression
        compressed, semantic_metadata = self._semantic_compression(prompt, target_reduction, model, preserve_quality)
        metadata["steps"].extend(semantic_metadata["steps"])

        # Step 1: Remove all non-essential words
        non_essential_words = [
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
            "shall",
            "very",
            "really",
            "quite",
            "rather",
            "pretty",
            "somewhat",
            "fairly",
            "please",
            "kindly",
            "thank",
            "thanks",
            "appreciate",
        ]

        words = compressed.split()
        filtered_words = []
        for word in words:
            clean_word = re.sub(r"[^\w]", "", word.lower())
            if clean_word not in non_essential_words or len(word) > 4:
                filtered_words.append(word)

        compressed = " ".join(filtered_words)
        metadata["steps"].append("non_essential_word_removal")

        # Step 2: Aggressive sentence shortening
        sentences = compressed.split(".")
        shortened_sentences = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 10:  # Shorten long sentences
                # Keep first 8 words and last 2 words
                shortened = " ".join(words[:8]) + "..." + " ".join(words[-2:])
                shortened_sentences.append(shortened)
            else:
                shortened_sentences.append(sentence)

        compressed = ". ".join(shortened_sentences)
        metadata["steps"].append("aggressive_sentence_shortening")

        return compressed.strip(), metadata

    def _analyze_prompt(self, prompt: str) -> dict[str, Any]:
        """Analyze prompt characteristics to inform compression strategy."""
        analysis = {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "sentence_count": len([s for s in prompt.split(".") if s.strip()]),
            "has_instructions": bool(re.search(r"(?i)(instructions?|directions?|steps?)", prompt)),
            "has_examples": bool(re.search(r"(?i)(example|sample|demo)", prompt)),
            "has_formatting": bool(re.search(r"```|`|\*\*|\*|#+", prompt)),
            "complexity_score": 0.0,
        }

        # Calculate complexity score
        complexity_factors = [
            len(prompt) > 1000,  # Long prompt
            analysis["sentence_count"] > 10,  # Many sentences
            bool(re.search(r"(?i)(however|therefore|moreover|furthermore)", prompt)),  # Complex connectors
            bool(re.search(r"(?i)(because|since|although|unless)", prompt)),  # Conditional language
        ]

        analysis["complexity_score"] = sum(complexity_factors) / len(complexity_factors)

        return analysis

    def _get_target_reduction(self, level: CompressionLevel) -> float:
        """Get target reduction percentage for compression level."""
        reduction_map = {
            CompressionLevel.LIGHT: self.config.light_reduction_target,
            CompressionLevel.MODERATE: self.config.moderate_reduction_target,
            CompressionLevel.AGGRESSIVE: self.config.aggressive_reduction_target,
            CompressionLevel.MAXIMUM: self.config.maximum_reduction_target,
        }
        return reduction_map.get(level, self.config.moderate_reduction_target)

    def _count_tokens(self, text: str, model: str | None) -> int:
        """Count tokens in text using available tokenizers."""
        try:
            # Try to use existing PromptEngine token counting
            from ultimate_discord_intelligence_bot.services.prompt_engine import (
                PromptEngine,
            )

            engine = PromptEngine()
            return engine.count_tokens(text, model)
        except Exception:
            # Fallback to simple estimation
            return len(text.split()) * 1.3  # Rough approximation

    def _get_cache_key(
        self,
        prompt: str,
        level: CompressionLevel | None,
        strategy: CompressionStrategy | None,
        model: str | None,
    ) -> str:
        """Generate cache key for compression result."""
        import hashlib

        key_data = f"{prompt}:{level.value if level else 'default'}:{strategy.value if strategy else 'default'}:{model or 'default'}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()  # nosec B324 - cache key only

    def _get_cached_result(self, cache_key: str) -> CompressionResult | None:
        """Get cached compression result if available and not expired."""
        if cache_key not in self._compression_cache:
            return None

        # Check if cache entry is expired
        cache_time = self._cache_timestamps.get(cache_key, 0)
        if time.time() - cache_time > self.config.cache_ttl_seconds:
            del self._compression_cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None

        return self._compression_cache[cache_key]

    def _cache_result(self, cache_key: str, result: CompressionResult) -> None:
        """Cache compression result."""
        self._compression_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()

        # Clean up old cache entries
        current_time = time.time()
        expired_keys = [
            key
            for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self.config.cache_ttl_seconds
        ]

        for key in expired_keys:
            self._compression_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def get_compression_stats(self) -> StepResult:
        """Get statistics about compression operations."""
        try:
            return StepResult.ok(
                data={
                    "cache_size": len(self._compression_cache),
                    "cache_ttl_seconds": self.config.cache_ttl_seconds,
                    "available_strategies": [strategy.value for strategy in CompressionStrategy],
                    "available_levels": [level.value for level in CompressionLevel],
                    "config": {
                        "default_strategy": self.config.default_strategy.value,
                        "enable_semantic_compression": self.config.enable_semantic_compression,
                        "enable_caching": self.config.enable_caching,
                        "preserve_instructions": self.config.preserve_instructions,
                        "preserve_examples": self.config.preserve_examples,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Compression stats generation failed: {e}")
            return StepResult.fail(f"Compression stats failed: {e!s}")

    def clear_cache(self) -> StepResult:
        """Clear compression cache."""
        try:
            self._compression_cache.clear()
            self._cache_timestamps.clear()

            return StepResult.ok(data={"cache_cleared": True})

        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            return StepResult.fail(f"Cache clearing failed: {e!s}")


# Global prompt compressor instance
_prompt_compressor: AdvancedPromptCompressor | None = None


def get_prompt_compressor() -> AdvancedPromptCompressor:
    """Get the global prompt compressor instance."""
    global _prompt_compressor
    if _prompt_compressor is None:
        _prompt_compressor = AdvancedPromptCompressor()
    return _prompt_compressor


__all__ = [
    "AdvancedPromptCompressor",
    "CompressionConfig",
    "CompressionLevel",
    "CompressionResult",
    "CompressionStrategy",
    "get_prompt_compressor",
]
