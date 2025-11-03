from __future__ import annotations

import logging
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics

from llmlingua import PromptCompressor

from app.config.settings import Settings
from ultimate_discord_intelligence_bot.tools._base import BaseTool


logger = logging.getLogger(__name__)


class PromptCompressionTool(BaseTool[dict]):
    """Compress prompts using Microsoft's LLMLingua."""

    name: str = "prompt_compression"
    description: str = "Reduces token count in long prompts while preserving meaning"

    def __init__(self):
        super().__init__()
        settings = Settings()
        self._enabled = settings.enable_prompt_compression
        if self._enabled:
            try:
                self._compressor = PromptCompressor(
                    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank", device_map="auto"
                )
                logger.info("LLMLingua compressor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LLMLingua: {e}")
                self._compressor = None
                self._enabled = False
        else:
            self._compressor = None

    def _run(
        self,
        contexts: list[str],
        instruction: str = "",
        question: str = "",
        target_token: int = 2000,
        compression_ratio: float = 0.5,
    ) -> StepResult:
        """
        Compress prompt contexts to reduce token usage.

        Args:
            contexts: List of context strings to compress
            instruction: High-priority instruction text (compressed less aggressively)
            question: High-priority question text (compressed less aggressively)
            target_token: Target token count for compressed output
            compression_ratio: Target compression ratio (0.5 = 50% reduction)

        Returns:
            StepResult with compressed prompt and metrics
        """
        if not self._enabled or not self._compressor:
            return StepResult.skip(
                step="prompt_compression", reason="ENABLE_PROMPT_COMPRESSION not set or initialization failed"
            )
        try:
            compressed = self._compressor.compress_prompt(
                contexts,
                instruction=instruction,
                question=question,
                target_token=target_token,
                ratio=compression_ratio,
                condition_compare=True,
                condition_in_question="after",
                rank_method="longllmlingua",
                use_sentence_level_filter=False,
                context_budget="+100",
                dynamic_context_compression_ratio=0.4,
                reorder_context="sort",
            )
            origin_tokens = compressed.get("origin_tokens", 0)
            compressed_tokens = compressed.get("compressed_tokens", 0)
            tokens_saved = origin_tokens - compressed_tokens
            actual_ratio = compressed.get("ratio", 0)
            get_metrics().histogram(
                "prompt_compression_ratio", actual_ratio, labels={"tool": self.name, "outcome": "success"}
            )
            get_metrics().counter("tokens_saved_total", tokens_saved, labels={"tool": self.name})
            get_metrics().counter("tool_runs_total", 1, labels={"tool": self.name, "outcome": "success"})
            logger.info(f"Compressed prompt: {tokens_saved} tokens saved ({actual_ratio:.2%} reduction)")
            return StepResult.ok(
                result={
                    "compressed_prompt": compressed["compressed_prompt"],
                    "origin_tokens": origin_tokens,
                    "compressed_tokens": compressed_tokens,
                    "tokens_saved": tokens_saved,
                    "compression_ratio": actual_ratio,
                }
            )
        except Exception as e:
            get_metrics().counter("tool_runs_total", 1, labels={"tool": self.name, "outcome": "error"})
            logger.error(f"Prompt compression failed: {e}")
            return StepResult.fail(error=str(e), step="prompt_compression")


__all__ = ["PromptCompressionTool"]
