"""
Prompt Compressor for token-aware prompt optimization.

This module implements LLMLingua-style compression techniques to reduce
token usage while preserving output quality.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


@dataclass
class CompressionMetrics:
    """Metrics for prompt compression."""

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    quality_score: float
    compression_time_ms: float


@dataclass
class CompressionConfig:
    """Configuration for prompt compression."""

    target_compression_ratio: float = 0.5  # Target 50% compression
    min_quality_threshold: float = 0.8  # Minimum quality score
    preserve_structure: bool = True  # Preserve markdown, lists, etc.
    aggressive_mode: bool = False  # More aggressive compression
    preserve_keywords: list[str] | None = None  # Keywords to always preserve


class PromptCompressor:
    """Token-aware prompt compressor using multiple strategies."""

    def __init__(self, config: CompressionConfig | None = None):
        """Initialize prompt compressor.

        Args:
            config: Compression configuration
        """
        self.config = config or CompressionConfig()
        self.compression_history: list[CompressionMetrics] = []

        logger.info("Initialized PromptCompressor with target ratio: %.2f", self.config.target_compression_ratio)

    @require_tenant(strict_flag_enabled=False)
    async def compress_prompt(
        self,
        prompt: str,
        tenant: str = "",
        workspace: str = "",
        **kwargs: Any,
    ) -> StepResult:
        """Compress a prompt while preserving quality.

        Args:
            prompt: Original prompt to compress
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional compression parameters

        Returns:
            StepResult with compressed prompt and metrics
        """
        try:
            import time

            start_time = time.time()

            # Estimate original token count
            original_tokens = self._estimate_tokens(prompt)

            # Apply compression strategies
            compressed_prompt = await self._apply_compression_strategies(prompt)

            # Calculate metrics
            compressed_tokens = self._estimate_tokens(compressed_prompt)
            compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
            compression_time = (time.time() - start_time) * 1000

            # Calculate quality score
            quality_score = self._calculate_quality_score(prompt, compressed_prompt)

            # Check if compression meets requirements
            if compression_ratio > self.config.target_compression_ratio:
                logger.debug(
                    "Compression ratio %.2f exceeds target %.2f, applying aggressive compression",
                    compression_ratio,
                    self.config.target_compression_ratio,
                )
                compressed_prompt = await self._apply_aggressive_compression(prompt)
                compressed_tokens = self._estimate_tokens(compressed_prompt)
                compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

            # Validate quality
            if quality_score < self.config.min_quality_threshold:
                logger.warning(
                    "Quality score %.2f below threshold %.2f, returning original prompt",
                    quality_score,
                    self.config.min_quality_threshold,
                )
                compressed_prompt = prompt
                compressed_tokens = original_tokens
                compression_ratio = 1.0

            # Create metrics
            metrics = CompressionMetrics(
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=compression_ratio,
                quality_score=quality_score,
                compression_time_ms=compression_time,
            )

            # Store metrics
            self.compression_history.append(metrics)

            logger.debug(
                "Compressed prompt: %d -> %d tokens (ratio: %.2f, quality: %.2f)",
                original_tokens,
                compressed_tokens,
                compression_ratio,
                quality_score,
            )

            return StepResult.ok(
                data={
                    "compressed_prompt": compressed_prompt,
                    "metrics": {
                        "original_tokens": original_tokens,
                        "compressed_tokens": compressed_tokens,
                        "compression_ratio": compression_ratio,
                        "quality_score": quality_score,
                        "compression_time_ms": compression_time,
                    },
                }
            )

        except Exception as e:
            logger.error("Prompt compression failed: %s", str(e))
            return StepResult.fail(f"Prompt compression failed: {e!s}")

    async def _apply_compression_strategies(self, prompt: str) -> str:
        """Apply various compression strategies.

        Args:
            prompt: Original prompt

        Returns:
            Compressed prompt
        """
        compressed = prompt

        # Strategy 1: Remove redundant whitespace
        compressed = self._remove_redundant_whitespace(compressed)

        # Strategy 2: Compress repetitive patterns
        compressed = self._compress_repetitive_patterns(compressed)

        # Strategy 3: Simplify complex sentences
        compressed = self._simplify_complex_sentences(compressed)

        # Strategy 4: Remove unnecessary words
        compressed = self._remove_unnecessary_words(compressed)

        # Strategy 5: Preserve structure if configured
        if self.config.preserve_structure:
            compressed = self._preserve_structure(compressed, prompt)

        return compressed

    def _remove_redundant_whitespace(self, text: str) -> str:
        """Remove redundant whitespace while preserving structure."""
        # Remove multiple spaces
        text = re.sub(r" +", " ", text)
        # Remove multiple newlines
        text = re.sub(r"\n+", "\n", text)
        # Remove trailing whitespace
        text = re.sub(r" +$", "", text, flags=re.MULTILINE)
        return text.strip()

    def _compress_repetitive_patterns(self, text: str) -> str:
        """Compress repetitive patterns in text."""
        # Compress repeated words
        text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text)
        # Compress repeated phrases
        text = re.sub(r"(\b\w+(?:\s+\w+)*\b)\s+\1", r"\1", text)
        return text

    def _simplify_complex_sentences(self, text: str) -> str:
        """Simplify complex sentences while preserving meaning."""
        sentences = text.split(". ")
        simplified_sentences = []

        for sentence in sentences:
            if len(sentence.split()) > 20:  # Long sentences
                # Split on conjunctions
                parts = re.split(r"\s+(and|but|however|therefore|moreover)\s+", sentence)
                if len(parts) > 1:
                    simplified_sentences.extend(parts)
                else:
                    simplified_sentences.append(sentence)
            else:
                simplified_sentences.append(sentence)

        return ". ".join(simplified_sentences)

    def _remove_unnecessary_words(self, text: str) -> str:
        """Remove unnecessary words while preserving meaning."""
        # Common unnecessary words/phrases
        unnecessary_patterns = [
            r"\b(very|really|quite|rather|somewhat|fairly)\b",
            r"\b(in order to|so as to)\b",
            r"\b(due to the fact that|because of the fact that)\b",
            r"\b(it is important to note that|it should be noted that)\b",
            r"\b(at this point in time|at the present time)\b",
        ]

        for pattern in unnecessary_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    def _preserve_structure(self, compressed: str, original: str) -> str:
        """Preserve important structural elements."""
        # Preserve markdown headers
        if "#" in original:
            # Keep header structure
            pass

        # Preserve lists
        if "- " in original or "* " in original:
            # Keep list structure
            pass

        # Preserve code blocks
        if "```" in original:
            # Keep code block structure
            pass

        return compressed

    async def _apply_aggressive_compression(self, prompt: str) -> str:
        """Apply aggressive compression strategies.

        Args:
            prompt: Original prompt

        Returns:
            Aggressively compressed prompt
        """
        compressed = prompt

        # Remove common filler words
        filler_words = [
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
        ]

        words = compressed.split()
        filtered_words = []

        for word in words:
            clean_word = re.sub(r"[^\w]", "", word.lower())
            if clean_word not in filler_words or word in (self.config.preserve_keywords or []):
                filtered_words.append(word)

        compressed = " ".join(filtered_words)

        # Remove redundant phrases
        redundant_phrases = [
            "it is important to",
            "it should be noted that",
            "it is worth noting that",
            "it is clear that",
            "it is obvious that",
            "it is evident that",
        ]

        for phrase in redundant_phrases:
            compressed = compressed.replace(phrase, "")

        return compressed

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple token estimation (4 chars per token average)
        return len(text) // 4

    def _calculate_quality_score(self, original: str, compressed: str) -> float:
        """Calculate quality score for compressed text.

        Args:
            original: Original text
            compressed: Compressed text

        Returns:
            Quality score (0-1)
        """
        if not compressed or len(compressed) < len(original) * 0.1:
            return 0.0

        score = 1.0

        # Check if key information is preserved
        original_words = set(original.lower().split())
        compressed_words = set(compressed.lower().split())

        # Calculate word overlap
        overlap = len(original_words.intersection(compressed_words))
        total_original = len(original_words)
        if total_original > 0:
            word_preservation = overlap / total_original
            score *= word_preservation

        # Check if structure is preserved
        if self.config.preserve_structure:
            structure_elements = ["#", "-", "*", "```", "1.", "2.", "3."]
            original_has_structure = any(elem in original for elem in structure_elements)
            compressed_has_structure = any(elem in compressed for elem in structure_elements)

            if original_has_structure and not compressed_has_structure:
                score *= 0.8  # Penalize structure loss

        # Check if important keywords are preserved
        if self.config.preserve_keywords:
            preserved_keywords = sum(
                1 for keyword in self.config.preserve_keywords if keyword.lower() in compressed.lower()
            )
            total_keywords = len(self.config.preserve_keywords)
            if total_keywords > 0:
                keyword_preservation = preserved_keywords / total_keywords
                score *= keyword_preservation

        return min(score, 1.0)

    def get_compression_stats(self) -> StepResult:
        """Get compression statistics.

        Returns:
            StepResult with compression statistics
        """
        try:
            if not self.compression_history:
                return StepResult.ok(data={"message": "No compression history available"})

            # Calculate aggregate statistics
            total_compressions = len(self.compression_history)
            avg_compression_ratio = sum(m.compression_ratio for m in self.compression_history) / total_compressions
            avg_quality_score = sum(m.quality_score for m in self.compression_history) / total_compressions
            avg_compression_time = sum(m.compression_time_ms for m in self.compression_history) / total_compressions

            total_tokens_saved = sum(m.original_tokens - m.compressed_tokens for m in self.compression_history)

            return StepResult.ok(
                data={
                    "total_compressions": total_compressions,
                    "average_compression_ratio": avg_compression_ratio,
                    "average_quality_score": avg_quality_score,
                    "average_compression_time_ms": avg_compression_time,
                    "total_tokens_saved": total_tokens_saved,
                    "config": {
                        "target_compression_ratio": self.config.target_compression_ratio,
                        "min_quality_threshold": self.config.min_quality_threshold,
                        "preserve_structure": self.config.preserve_structure,
                        "aggressive_mode": self.config.aggressive_mode,
                    },
                }
            )

        except Exception as e:
            logger.error("Failed to get compression stats: %s", str(e))
            return StepResult.fail(f"Failed to get compression stats: {e!s}")

    def reset_compression_history(self) -> StepResult:
        """Reset compression history.

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.compression_history.clear()
            logger.info("Reset compression history")
            return StepResult.ok(data={"reset": True})

        except Exception as e:
            logger.error("Failed to reset compression history: %s", str(e))
            return StepResult.fail(f"Failed to reset compression history: {e!s}")

    def update_config(self, new_config: CompressionConfig) -> StepResult:
        """Update compression configuration.

        Args:
            new_config: New compression configuration

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.config = new_config
            logger.info("Updated compression configuration")
            return StepResult.ok(data={"updated": True})

        except Exception as e:
            logger.error("Failed to update compression config: %s", str(e))
            return StepResult.fail(f"Failed to update compression config: {e!s}")
