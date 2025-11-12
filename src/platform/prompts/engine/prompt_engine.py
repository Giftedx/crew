"""Utilities for building prompts and counting tokens.

The :class:`PromptEngine` centralises prompt construction and token counting so
any agent, tool or workflow can consistently prepare requests for large
language models. Token counting is provider aware: ``tiktoken`` powers OpenAI
model estimates, ``transformers`` tokenizers cover other providers and a simple
whitespace split acts as a final fallback.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.config.settings import Settings
from ultimate_discord_intelligence_bot.obs import metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .optimization_pipeline import OptimizationConfig, OptimizationPipeline
from .prompt_compressor import CompressionConfig, PromptCompressor


try:
    from platform import settings as core_settings
except Exception:
    core_settings = None


def get_settings() -> Settings:
    """Retrieve the active settings instance with fallbacks.

    Returns:
        Settings: Configured settings object. Falls back to constructing a new
        ``Settings`` instance if the shared ``core.settings`` facade is
        unavailable (e.g., in isolated test environments).
    """
    if core_settings is not None:
        try:
            return core_settings.get_settings()
        except Exception:
            return Settings()
    return Settings()


try:
    from opentelemetry import trace
except Exception:

    class _NoopSpan:
        def set_attribute(self, *_a, **_k):
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_a, **_k):
            class _Ctx:
                def __enter__(self):
                    return _NoopSpan()

                def __exit__(self, *_):
                    return False

            return _Ctx()

    class _NoopTraceAPI:
        def get_tracer(self, *_a, **_k):
            return _NoopTracer()

    trace = _NoopTraceAPI()
if TYPE_CHECKING:
    from .memory_service import MemoryService
try:
    from prompt_engine.llmlingua_adapter import compress_prompt_with_details
except Exception:

    def compress_prompt_with_details(prompt: str, **_: Any) -> StepResult:
        return (prompt, {"applied": False, "reason": "unavailable"})


try:
    import tiktoken as _tiktoken
except Exception:
    _tiktoken = None
tiktoken = _tiktoken
try:
    from transformers import AutoTokenizer
except Exception:
    AutoTokenizer = None


@dataclass
class PromptEngine:
    """Generate prompts and estimate token usage."""

    memory: MemoryService | None = None
    _tokenizers: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _optimization_pipeline: OptimizationPipeline | None = None
    _compression_enabled: bool = False

    def generate(self, template: str, variables: dict[str, Any]) -> StepResult:
        """Fill ``template`` with ``variables`` using ``str.format``."""
        return template.format(**variables)

    def enable_optimization(
        self, compression_config: CompressionConfig | None = None, optimization_config: OptimizationConfig | None = None
    ) -> None:
        """Enable prompt optimization.

        Args:
            compression_config: Compression configuration
            optimization_config: Optimization configuration
        """
        if compression_config is None:
            compression_config = CompressionConfig()
        if optimization_config is None:
            optimization_config = OptimizationConfig()
        self._optimization_pipeline = OptimizationPipeline(
            compressor=PromptCompressor(compression_config), config=optimization_config
        )
        self._compression_enabled = True
        logger = logging.getLogger(__name__)
        logger.info("Prompt optimization enabled")

    def disable_optimization(self) -> None:
        """Disable prompt optimization."""
        self._optimization_pipeline = None
        self._compression_enabled = False
        logger = logging.getLogger(__name__)
        logger.info("Prompt optimization disabled")

    async def generate_optimized(
        self,
        template: str,
        variables: dict[str, Any],
        prompt_id: str | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Generate and optimize a prompt.

        Args:
            template: Prompt template
            variables: Template variables
            prompt_id: Unique identifier for the prompt
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with optimized prompt and metrics
        """
        try:
            base_prompt = self.generate(template, variables)
            if not base_prompt.success:
                return base_prompt
            if not self._compression_enabled or self._optimization_pipeline is None:
                return StepResult.ok(
                    data={"prompt": base_prompt, "optimized": False, "metrics": {"optimization_disabled": True}}
                )
            optimization_result = await self._optimization_pipeline.optimize_prompt(
                prompt=base_prompt, prompt_id=prompt_id, tenant=tenant, workspace=workspace
            )
            if optimization_result.success:
                return StepResult.ok(
                    data={
                        "prompt": optimization_result.data["optimized_prompt"],
                        "optimized": True,
                        "metrics": optimization_result.data["metrics"],
                    }
                )
            else:
                logger = logging.getLogger(__name__)
                logger.warning("Prompt optimization failed, using original: %s", optimization_result.error)
                return StepResult.ok(
                    data={
                        "prompt": base_prompt,
                        "optimized": False,
                        "metrics": {"optimization_failed": True, "error": optimization_result.error},
                    }
                )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Optimized prompt generation failed: %s", str(e))
            return StepResult.fail(f"Optimized prompt generation failed: {e!s}")

    def get_optimization_stats(self) -> StepResult:
        """Get optimization statistics.

        Returns:
            StepResult with optimization statistics
        """
        if not self._compression_enabled or self._optimization_pipeline is None:
            return StepResult.ok(data={"optimization_disabled": True})
        return self._optimization_pipeline.get_optimization_stats()

    def count_tokens(self, text: str, model: str | None = None) -> StepResult:
        """Return an estimated token count for ``text``.

        Parameters
        ----------
        text:
            The prompt text to analyse.
        model:
            Optional model name. When supplied the engine attempts to use a
            provider-specific tokenizer: ``tiktoken`` for OpenAI models and
            ``transformers`` for others. If no specialised tokenizer is
            available a simple whitespace split provides a conservative
            fallback.
        """
        if model:
            if tiktoken:
                try:
                    enc = tiktoken.encoding_for_model(model)
                    return len(enc.encode(text))
                except Exception:
                    logging.getLogger(__name__).debug("tiktoken model lookup failed", exc_info=True)
            if AutoTokenizer:
                try:
                    tokenizer = self._tokenizers.get(model)
                    if tokenizer is None:
                        tokenizer = AutoTokenizer.from_pretrained(model)
                        self._tokenizers[model] = tokenizer
                    return len(tokenizer.encode(text))
                except Exception:
                    logging.getLogger(__name__).debug("transformers tokenization failed", exc_info=True)
            if tiktoken:
                enc = tiktoken.get_encoding("cl100k_base")
                return len(enc.encode(text))
        tokens = len(text.split())
        heuristic_min_unbroken_len = 200
        if tokens <= 1 and len(text) > heuristic_min_unbroken_len:
            approx = max(1, len(text) // 4)
            tokens = approx
        return tokens

    def optimise(
        self,
        prompt: str,
        target_token_reduction: float = 0.0,
        max_tokens: int | None = None,
        *,
        model: str | None = None,
        force_enable: bool = False,
    ) -> StepResult:
        text, _ = self.optimise_with_metadata(
            prompt,
            model=model,
            target_token_reduction=target_token_reduction,
            max_tokens=max_tokens,
            force_enable=force_enable,
        )
        return text

    def optimise_with_metadata(
        self,
        prompt: str,
        *,
        model: str | None = None,
        target_token_reduction: float = 0.0,
        max_tokens: int | None = None,
        llmlingua_ratio: float | None = None,
        force_enable: bool = False,
    ) -> StepResult:
        """Optimise ``prompt`` returning the compressed text and observability metadata."""
        truthy = {"1", "true", "yes", "on"}
        tracer = trace.get_tracer(__name__)
        metadata: dict[str, Any] = {"stages": []}
        settings = get_settings()
        with tracer.start_as_current_span("prompt.optimise") as span:
            original = prompt
            text = original
            default_reduction = float(getattr(settings, "prompt_compression_default_target", 0.0) or 0.0)
            if target_token_reduction <= 0 and default_reduction > 0:
                target_token_reduction = default_reduction
            if max_tokens is None:
                cfg_max_tokens = getattr(settings, "prompt_compression_max_tokens", None)
                if cfg_max_tokens not in (None, "", 0):
                    try:
                        max_tokens = int(cfg_max_tokens)
                    except Exception:
                        max_tokens = None
            if span:
                try:
                    span.set_attribute("target_token_reduction", float(target_token_reduction))
                    span.set_attribute("max_tokens", int(max_tokens) if max_tokens is not None else -1)
                except Exception:
                    pass
            env_present = "ENABLE_PROMPT_COMPRESSION" in os.environ
            env_enabled = os.getenv("ENABLE_PROMPT_COMPRESSION", "").lower() in truthy
            settings_enabled = bool(getattr(settings, "enable_prompt_compression", False)) or bool(
                getattr(settings, "enable_prompt_compression_flag", False)
            )
            source_policy = os.getenv("PROMPT_COMPRESSION_SOURCE", "env").strip().lower()
            if source_policy == "settings":
                effective_enabled = settings_enabled
            elif source_policy == "both":
                effective_enabled = env_enabled or settings_enabled
            else:
                effective_enabled = env_enabled or (env_present and settings_enabled)
            if force_enable:
                effective_enabled = True
            metadata.update(
                {
                    "source_policy": source_policy,
                    "env_present": bool(env_present),
                    "env_enabled": bool(env_enabled),
                    "settings_enabled": bool(settings_enabled),
                    "enabled": bool(effective_enabled),
                    "forced": bool(force_enable),
                    "target_token_reduction": float(target_token_reduction),
                    "max_tokens": int(max_tokens) if max_tokens is not None else None,
                }
            )
            if span:
                try:
                    span.set_attribute("prompt_compression.source_policy", source_policy)
                    span.set_attribute("prompt_compression.env_present", bool(env_present))
                    span.set_attribute("prompt_compression.env_enabled", bool(env_enabled))
                    span.set_attribute("prompt_compression.settings_enabled", bool(settings_enabled))
                    span.set_attribute("prompt_compression.enabled", bool(effective_enabled))
                    span.set_attribute("prompt_compression.forced", bool(force_enable))
                except Exception:
                    pass
            original_tokens = self.count_tokens(original, model)
            metadata["original_tokens"] = original_tokens
            if not effective_enabled:
                metadata["final_tokens"] = original_tokens
                metadata["reduction"] = 0.0
                if span:
                    with contextlib.suppress(Exception):
                        span.set_attribute("prompt.compress.forced", bool(force_enable))
                return (original.strip(), metadata)
            lbl = metrics.label_ctx()
            with tracer.start_as_current_span("prompt.compress.basic"):
                text = self._apply_basic_compression(text, settings)
            basic_tokens = self.count_tokens(text, model)
            metadata["stages"].append(
                {"stage": "basic", "before_tokens": original_tokens, "after_tokens": basic_tokens}
            )
            current_tokens = basic_tokens
            target_tokens = None
            if target_token_reduction > 0 and original_tokens > 0:
                target_tokens = int(original_tokens * (1.0 - target_token_reduction))
                if max_tokens is not None:
                    target_tokens = min(target_tokens, max_tokens)
                if span:
                    try:
                        span.set_attribute("prompt.tokens.original", int(original_tokens))
                        span.set_attribute("prompt.tokens.target", int(target_tokens))
                    except Exception:
                        pass
                metadata["target_tokens"] = target_tokens
                current_tokens = self.count_tokens(text, model)
                if current_tokens > target_tokens:
                    with tracer.start_as_current_span("prompt.compress.context_trimming") as subspan:
                        if subspan:
                            try:
                                subspan.set_attribute("current_tokens", int(current_tokens))
                                subspan.set_attribute("target_tokens", int(target_tokens))
                            except Exception:
                                pass
                        text = self._apply_context_trimming(text, target_tokens, current_tokens)
                    trimmed_tokens = self.count_tokens(text, model)
                    metadata["stages"].append(
                        {
                            "stage": "context_trim",
                            "before_tokens": current_tokens,
                            "after_tokens": trimmed_tokens,
                            "target_tokens": target_tokens,
                        }
                    )
                    current_tokens = trimmed_tokens
            if max_tokens is not None:
                current_tokens = self.count_tokens(text, model)
                if current_tokens > max_tokens:
                    with tracer.start_as_current_span("prompt.compress.emergency_truncation") as subspan:
                        if subspan:
                            try:
                                subspan.set_attribute("current_tokens", int(current_tokens))
                                subspan.set_attribute("max_tokens", int(max_tokens))
                            except Exception:
                                pass
                        text = self._apply_emergency_truncation(text, max_tokens)
                    emergency_tokens = self.count_tokens(text, model)
                    metadata["stages"].append(
                        {
                            "stage": "emergency_truncation",
                            "before_tokens": current_tokens,
                            "after_tokens": emergency_tokens,
                            "max_tokens": max_tokens,
                        }
                    )
                    current_tokens = emergency_tokens
            llmlingua_env_present = "ENABLE_LLMLINGUA" in os.environ
            llmlingua_env_enabled = os.getenv("ENABLE_LLMLINGUA", "").lower() in truthy
            llmlingua_shadow_env = os.getenv("ENABLE_LLMLINGUA_SHADOW", "")
            llmlingua_shadow_enabled = bool(getattr(settings, "enable_llmlingua_shadow", False)) or (
                bool(llmlingua_shadow_env) and llmlingua_shadow_env.lower() in truthy
            )
            if llmlingua_env_present:
                llmlingua_active = llmlingua_env_enabled
            else:
                llmlingua_active = bool(getattr(settings, "enable_llmlingua", False))
            llmlingua_mode = "disabled"
            if llmlingua_active:
                llmlingua_mode = "active"
            elif llmlingua_shadow_enabled:
                llmlingua_mode = "shadow"
            llmlingua_info: dict[str, Any] = {"mode": llmlingua_mode, "applied": False}
            metadata["llmlingua"] = llmlingua_info
            if llmlingua_mode != "disabled":
                before_tokens = self.count_tokens(text, model)
                llmlingua_info["before_tokens"] = before_tokens
                min_tokens = int(getattr(settings, "llmlingua_min_tokens", 600) or 600)
                if before_tokens >= max(1, min_tokens):
                    ratio_effective = (
                        llmlingua_ratio
                        if llmlingua_ratio is not None
                        else float(getattr(settings, "llmlingua_target_ratio", target_token_reduction or 0.0) or 0.0)
                    )
                    if ratio_effective <= 0 and target_token_reduction > 0:
                        ratio_effective = target_token_reduction
                    ratio_effective = max(0.05, min(0.95, ratio_effective or 0.35))
                    target_budget = getattr(settings, "llmlingua_target_tokens", None)
                    llmlingua_target_tokens = (
                        int(target_budget)
                        if target_budget not in (None, "", 0)
                        else int(before_tokens * (1.0 - ratio_effective))
                    )
                    if max_tokens is not None:
                        llmlingua_target_tokens = min(llmlingua_target_tokens, max_tokens)
                    extra_kwargs: dict[str, Any] = {}
                    stage = getattr(settings, "llmlingua_stage", None)
                    if stage:
                        extra_kwargs["stage"] = stage
                    device = getattr(settings, "llmlingua_device", None)
                    if device:
                        extra_kwargs["device"] = device
                    compressed, details = compress_prompt_with_details(
                        text,
                        enabled=True,
                        target_tokens=llmlingua_target_tokens,
                        ratio=ratio_effective,
                        extra_kwargs=extra_kwargs,
                    )
                    after_tokens_llm = self.count_tokens(compressed, model)
                    llmlingua_stage_meta: dict[str, Any] = {
                        "stage": "llmlingua",
                        "mode": llmlingua_mode,
                        "before_tokens": before_tokens,
                        "after_tokens": after_tokens_llm if llmlingua_mode == "active" else before_tokens,
                        "shadow_after_tokens": after_tokens_llm if llmlingua_mode == "shadow" else None,
                        "details": details,
                    }
                    metadata["stages"].append(llmlingua_stage_meta)
                    llmlingua_info.update(
                        {
                            "applied": bool(details.get("applied")),
                            "details": details,
                            "target_tokens": llmlingua_target_tokens,
                            "ratio": ratio_effective,
                            "after_tokens": after_tokens_llm,
                        }
                    )
                    if llmlingua_mode == "shadow":
                        llmlingua_info["shadow_after_tokens"] = after_tokens_llm
                    if llmlingua_mode == "active" and details.get("applied") and compressed.strip():
                        text = compressed
                        current_tokens = after_tokens_llm
                else:
                    llmlingua_info["reason"] = "below_min_tokens"
            final_tokens = self.count_tokens(text, model)
            metadata["final_tokens"] = final_tokens
            metadata["reduction"] = 0.0 if original_tokens == 0 else 1.0 - final_tokens / max(1, original_tokens)
            try:
                original_tokens_safe = max(1, original_tokens)
                final_tokens_safe = max(1, final_tokens)
                ratio = final_tokens_safe / original_tokens_safe
                reduction_achieved = 1.0 - ratio
                metrics.PROMPT_COMPRESSION_RATIO.labels(lbl["tenant"], lbl["workspace"], "optimise").observe(ratio)
                if target_token_reduction > 0 and hasattr(metrics, "PROMPT_COMPRESSION_TARGET_MET"):
                    target_met = reduction_achieved >= target_token_reduction * 0.9
                    if target_met:
                        metrics.PROMPT_COMPRESSION_TARGET_MET.labels(lbl["tenant"], lbl["workspace"]).inc()
                if span:
                    try:
                        span.set_attribute("prompt.tokens.final", int(final_tokens))
                        span.set_attribute("prompt.compress.ratio", float(ratio))
                        span.set_attribute("prompt.compress.reduction_achieved", float(reduction_achieved))
                    except Exception:
                        pass
            except Exception:
                pass
        return (text, metadata)

    def _apply_basic_compression(self, text: str, settings: Any) -> StepResult:
        """Apply basic compression techniques (existing optimise logic)."""
        max_blanks = int(getattr(settings, "prompt_compression_max_repeated_blank_lines", 1) or 1)
        lines: list[str] = []
        blank_run = 0
        for ln in text.splitlines():
            if ln.strip() == "":
                blank_run += 1
                if blank_run <= max_blanks:
                    lines.append("")
            else:
                blank_run = 0
                lines.append(ln.rstrip())
        text = "\n".join(lines).strip()
        deduped: list[str] = []
        prev: str | None = None
        for ln in text.splitlines():
            if ln == prev:
                continue
            deduped.append(ln)
            prev = ln
        text = "\n".join(deduped)

        def _squeeze_spaces(line: str) -> StepResult:
            if line.startswith(("    ", "\t")):
                return line
            return re.sub("\\s{2,}", " ", line)

        text = "\n".join(_squeeze_spaces(line) for line in text.splitlines())
        MAX_SECTION_LINES = 40
        HEAD_TAIL_KEEP = 5
        compressed_sections: list[str] = []
        current: list[str] = []
        for ln in text.splitlines():
            if ln.strip() == "":
                if current:
                    if len(current) > MAX_SECTION_LINES:
                        head = current[:HEAD_TAIL_KEEP]
                        tail = current[-HEAD_TAIL_KEEP:]
                        omitted = len(current) - HEAD_TAIL_KEEP * 2
                        current = [*head, f"...[omitted {omitted} lines]...", *tail]
                    compressed_sections.append("\n".join(current))
                    current = []
                compressed_sections.append("")
            else:
                current.append(ln)
        if current:
            if len(current) > MAX_SECTION_LINES:
                head = current[:HEAD_TAIL_KEEP]
                tail = current[-HEAD_TAIL_KEEP:]
                omitted = len(current) - HEAD_TAIL_KEEP * 2
                current = [*head, f"...[omitted {omitted} lines]...", *tail]
            compressed_sections.append("\n".join(current))
        text = "\n".join(compressed_sections).strip()
        return text

    def _apply_context_trimming(self, text: str, target_tokens: int, current_tokens: int) -> StepResult:
        """Apply intelligent context trimming strategies."""
        lines = text.splitlines()
        if not lines:
            return text
        line_values = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            value_score = 0
            if len(stripped) > 10:
                value_score += 1
            if len(stripped) > 50:
                value_score += 1
            if any(
                marker in stripped.lower()
                for marker in [
                    "error",
                    "warning",
                    "important",
                    "note:",
                    "question:",
                    "answer:",
                    "context:",
                    "summary:",
                    "conclusion:",
                    "result:",
                    "output:",
                ]
            ):
                value_score += 2
            if len(stripped) < 5:
                value_score -= 1
            if stripped.count(".") > 5 or stripped.count("-") > 5:
                value_score -= 1
            line_values.append((value_score, i, line))
        line_values.sort(reverse=True)
        kept_lines: list[str] = [""] * len(lines)
        running_tokens = 0
        for value_score, original_index, line in line_values:
            line_tokens = self.count_tokens(line)
            if running_tokens + line_tokens <= target_tokens:
                kept_lines[original_index] = line
                running_tokens += line_tokens
            elif value_score > 0 and running_tokens < target_tokens:
                remaining_tokens = target_tokens - running_tokens
                truncated = self._truncate_line_to_tokens(line, remaining_tokens)
                if truncated:
                    kept_lines[original_index] = truncated
                    break
            else:
                break
        result_lines = [line for line in kept_lines if line is not None]
        return "\n".join(result_lines)

    def _truncate_line_to_tokens(self, line: str, max_tokens: int) -> StepResult:
        """Truncate a line to approximately max_tokens while preserving meaning."""
        if self.count_tokens(line) <= max_tokens:
            return line
        words = line.split()
        if not words:
            return ""
        left, right = (0, len(words))
        best_result = ""
        while left <= right:
            mid = (left + right) // 2
            candidate = " ".join(words[:mid])
            if self.count_tokens(candidate) <= max_tokens:
                best_result = candidate
                left = mid + 1
            else:
                right = mid - 1
        if best_result and best_result != line:
            with_ellipsis = best_result + "..."
            if self.count_tokens(with_ellipsis) <= max_tokens:
                return with_ellipsis
        return best_result

    def _apply_emergency_truncation(self, text: str, max_tokens: int) -> StepResult:
        """Apply emergency truncation when all else fails."""
        if self.count_tokens(text) <= max_tokens:
            return text
        try:
            lbl = metrics.label_ctx()
            if hasattr(metrics, "PROMPT_EMERGENCY_TRUNCATIONS"):
                metrics.PROMPT_EMERGENCY_TRUNCATIONS.labels(lbl["tenant"], lbl["workspace"]).inc()
        except Exception:
            pass
        lines = text.splitlines()
        if not lines:
            return text
        if max_tokens <= 2:
            return "[truncated]" if max_tokens >= 1 else ""
        total_lines = len(lines)
        if total_lines <= 6:
            words = text.split()
            for i in range(len(words), 0, -1):
                candidate = " ".join(words[:i])
                if self.count_tokens(candidate) <= max_tokens:
                    return candidate + "..." if i < len(words) else candidate
            return "[content omitted due to length]"[: max_tokens * 4] if max_tokens > 0 else ""
        keep_start = total_lines // 3
        keep_end = total_lines // 3
        while keep_start + keep_end > 0:
            start_lines = lines[:keep_start]
            end_lines = lines[-keep_end:] if keep_end > 0 else []
            if start_lines and end_lines:
                candidate_lines = [
                    *start_lines,
                    f"...[omitted {total_lines - keep_start - keep_end} lines]...",
                    *end_lines,
                ]
            elif start_lines:
                candidate_lines = [*start_lines, f"...[omitted {total_lines - keep_start} lines]..."]
            else:
                candidate_lines = [f"...[omitted {total_lines - keep_end} lines]...", *end_lines]
            candidate = "\n".join(candidate_lines)
            if self.count_tokens(candidate) <= max_tokens:
                return candidate
            if keep_start > keep_end:
                keep_start -= 1
            else:
                keep_end -= 1
        words = text.split()
        for i in range(len(words), 0, -1):
            candidate = " ".join(words[:i]) + "..."
            if self.count_tokens(candidate) <= max_tokens:
                return candidate
        return "[content omitted due to length]" if max_tokens > 0 else ""

    def build_with_context(
        self, instruction: str, query: str, k: int = 3, metadata: dict[str, Any] | None = None
    ) -> StepResult:
        """Build a prompt that includes top-``k`` context snippets.

        ``metadata`` may be provided to scope memory lookups to a specific
        creator or source. Returned prompts list sources for traceability.
        """
        context_blocks = []
        sources = []
        if self.memory:
            hits = self.memory.retrieve(query, limit=k, metadata=metadata)
            for idx, hit in enumerate(hits, 1):
                context_blocks.append(f"[{idx}] {hit['text']}")
                meta = hit.get("metadata", {})
                src = meta.get("source")
                ts = meta.get("ts")
                if src:
                    if ts is not None:
                        sources.append(f"[{idx}] {src}#{ts}")
                    else:
                        sources.append(f"[{idx}] {src}")
        context_text = "\n".join(context_blocks) or "(no context)"
        sources_text = "\n".join(sources)
        return f"{instruction}\n\nContext:\n{context_text}\n\nSources:\n{sources_text}\n\nQuery: {query}"
