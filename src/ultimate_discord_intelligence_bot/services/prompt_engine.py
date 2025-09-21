"""Utilities for building prompts and counting tokens.

The :class:`PromptEngine` centralises prompt construction and token counting so
any agent, tool or workflow can consistently prepare requests for large
language models. Token counting is provider aware: ``tiktoken`` powers OpenAI
model estimates, ``transformers`` tokenizers cover other providers and a simple
whitespace split acts as a final fallback.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from obs import metrics

try:  # lightweight tracing shim available in repo
    from opentelemetry import trace
except Exception:  # pragma: no cover - fallback to local noop-like tracer

    class _NoopSpan:
        def set_attribute(self, *_a, **_k):
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_a, **_k):  # noqa: D401 - simple context manager
            class _Ctx:
                def __enter__(self):
                    return _NoopSpan()

                def __exit__(self, *_):
                    return False

            return _Ctx()

    class _NoopTraceAPI:
        def get_tracer(self, *_a, **_k):  # noqa: D401 - return noop tracer
            return _NoopTracer()

    trace = _NoopTraceAPI()

try:
    from core.settings import get_settings
except Exception:  # pragma: no cover - defensive fallback

    def get_settings() -> Any:  # broad return type for fallback stub
        class _S:
            enable_prompt_compression = False
            prompt_compression_max_repeated_blank_lines = 1

        return _S()


from .memory_service import MemoryService

try:  # pragma: no cover - optional heavy dependency (performance tokenization fallback)
    import tiktoken as _tiktoken  # noqa: F401
except Exception:  # pragma: no cover
    _tiktoken = None

# Use a separate alias variable to avoid reassigning imported module symbol directly.
tiktoken = _tiktoken  # may be None at runtime

try:  # pragma: no cover - optional dependency (covered by mypy ignore-missing-imports override)
    from transformers import AutoTokenizer  # noqa: F401
except Exception:  # pragma: no cover
    AutoTokenizer = None  # noqa: N816 (capitalised from external lib convention, fallback sentinel)


@dataclass
class PromptEngine:
    """Generate prompts and estimate token usage."""

    memory: MemoryService | None = None
    _tokenizers: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def generate(self, template: str, variables: dict[str, Any]) -> str:
        """Fill ``template`` with ``variables`` using ``str.format``."""
        return template.format(**variables)

    def count_tokens(self, text: str, model: str | None = None) -> int:
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
                except Exception:  # pragma: no cover - best effort token counting
                    logging.getLogger(__name__).debug("tiktoken model lookup failed", exc_info=True)
            if AutoTokenizer:
                try:
                    tokenizer = self._tokenizers.get(model)
                    if tokenizer is None:
                        tokenizer = AutoTokenizer.from_pretrained(model)
                        self._tokenizers[model] = tokenizer
                    return len(tokenizer.encode(text))
                except Exception:  # pragma: no cover - optional tokenizer path
                    logging.getLogger(__name__).debug("transformers tokenization failed", exc_info=True)
            if tiktoken:
                enc = tiktoken.get_encoding("cl100k_base")
                return len(enc.encode(text))
        # Basic whitespace fallback. This can drastically under-estimate for very
        # long contiguous strings without spaces (e.g. "x" * 50000) which show up
        # in budget enforcement tests to simulate large prompts. If the split
        # yields <= 1 token yet the raw character length is large, apply a
        # heuristic approximation assuming ~4 characters per token (roughly in
        # line with common GPT tokenisation averages for English). This keeps
        # cost estimation conservative enough to trigger budget guards without
        # requiring heavyweight tokenizer dependencies.
        tokens = len(text.split())
        heuristic_min_unbroken_len = 200  # threshold for applying contiguous text heuristic
        if tokens <= 1 and len(text) > heuristic_min_unbroken_len:  # large unbroken text heuristic
            approx = max(1, len(text) // 4)
            tokens = approx
        return tokens

    def optimise(self, prompt: str, target_token_reduction: float = 0.0, max_tokens: int | None = None) -> str:
        """Return an optimised variant of ``prompt`` with intelligent context trimming.

        This implementation performs multiple passes of compression techniques to achieve
        the target token reduction while preserving important information:

        1. Basic compression (blank lines, deduplication, whitespace)
        2. Context-aware section summarisation (only if target_token_reduction > 0)
        3. Intelligent truncation with fallback strategies (only if max_tokens specified)

        Parameters
        ----------
        prompt:
            The input prompt text to optimize
        target_token_reduction:
            Target reduction ratio (0.15 = 15% reduction). If 0, only basic compression.
        max_tokens:
            Optional hard limit on output token count

        Compression enablement
        ----------------------
        Controlled by the following environment and settings flags:

        - ENABLE_PROMPT_COMPRESSION (env bool): primary switch when source is 'env'
        - settings.enable_prompt_compression / settings.enable_prompt_compression_flag
        - PROMPT_COMPRESSION_SOURCE (env str): 'env' | 'settings' | 'both'

        Semantics:
        - 'env' (default, backward compatible): enabled if env is truthy; if the
          env var exists but is falsy, settings may enable it. If the env var is
          absent, settings are ignored (historical behavior to avoid lru-cached
          settings making tests order-dependent).
        - 'settings': enabled only by settings flags (env ignored).
        - 'both': enabled if either env or settings enable it.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("prompt.optimise") as span:
            if span:
                try:
                    span.set_attribute("target_token_reduction", float(target_token_reduction))
                    span.set_attribute("max_tokens", int(max_tokens) if max_tokens is not None else -1)
                except Exception:
                    pass

            original = prompt
            text = original  # preserve internal structure initially
            settings = get_settings()

        # Determine compression enablement per configurable source policy.
        # Default preserves historical semantics: prefer ENV and ignore settings
        # unless the env var is present (even if falsy), to avoid lru-cached
        # settings causing order-dependent behavior.
        env_present = "ENABLE_PROMPT_COMPRESSION" in os.environ
        env_enabled = os.getenv("ENABLE_PROMPT_COMPRESSION", "").lower() in {"1", "true", "yes", "on"}
        settings_enabled = bool(getattr(settings, "enable_prompt_compression", False)) or bool(
            getattr(settings, "enable_prompt_compression_flag", False)
        )
        source_policy = os.getenv("PROMPT_COMPRESSION_SOURCE", "env").strip().lower()
        if source_policy == "settings":
            effective_enabled = settings_enabled
        elif source_policy == "both":
            effective_enabled = env_enabled or settings_enabled
        else:  # "env" (default): env governs; settings only if env var is present
            effective_enabled = env_enabled or (env_present and settings_enabled)
        try:
            # Add attributes for observability
            span.set_attribute("prompt_compression.source_policy", source_policy)
            span.set_attribute("prompt_compression.env_present", bool(env_present))
            span.set_attribute("prompt_compression.env_enabled", bool(env_enabled))
            span.set_attribute("prompt_compression.settings_enabled", bool(settings_enabled))
            span.set_attribute("prompt_compression.enabled", bool(effective_enabled))
        except Exception:
            pass
        if not effective_enabled:
            return original.strip()

        lbl = metrics.label_ctx()

        # Phase 1: Basic compression (always applied when compression is enabled)
        with tracer.start_as_current_span("prompt.compress.basic"):
            text = self._apply_basic_compression(text, settings)

        # Phase 2: Intelligent context trimming (only if target reduction specified)
        if target_token_reduction > 0:
            original_tokens = self.count_tokens(original)
            target_tokens = int(original_tokens * (1.0 - target_token_reduction))
            if max_tokens:
                target_tokens = min(target_tokens, max_tokens)
            if span:
                try:
                    span.set_attribute("prompt.tokens.original", int(original_tokens))
                    span.set_attribute("prompt.tokens.target", int(target_tokens))
                except Exception:
                    pass

            current_tokens = self.count_tokens(text)
            if current_tokens > target_tokens:
                with tracer.start_as_current_span("prompt.compress.context_trimming") as subspan:
                    if subspan:
                        try:
                            subspan.set_attribute("current_tokens", int(current_tokens))
                            subspan.set_attribute("target_tokens", int(target_tokens))
                        except Exception:
                            pass
                    text = self._apply_context_trimming(text, target_tokens, current_tokens)

        # Phase 3: Emergency truncation if hard limit specified and still over
        if max_tokens:
            current_tokens = self.count_tokens(text)
            if current_tokens > max_tokens:
                with tracer.start_as_current_span("prompt.compress.emergency_truncation") as subspan:
                    if subspan:
                        try:
                            subspan.set_attribute("current_tokens", int(current_tokens))
                            subspan.set_attribute("max_tokens", int(max_tokens))
                        except Exception:
                            pass
                    text = self._apply_emergency_truncation(text, max_tokens)

        try:  # metrics emission best-effort
            original_tokens = max(1, self.count_tokens(original))
            final_tokens = max(1, self.count_tokens(text))
            ratio = final_tokens / original_tokens
            reduction_achieved = 1.0 - ratio

            metrics.PROMPT_COMPRESSION_RATIO.labels(lbl["tenant"], lbl["workspace"], "optimise").observe(ratio)

            # Track if we achieved target reduction (only if target was set)
            if target_token_reduction > 0 and hasattr(metrics, "PROMPT_COMPRESSION_TARGET_MET"):
                target_met = reduction_achieved >= (target_token_reduction * 0.9)  # 90% of target
                if target_met:
                    metrics.PROMPT_COMPRESSION_TARGET_MET.labels(lbl["tenant"], lbl["workspace"]).inc()

            # Add span attributes
            if span:
                try:
                    span.set_attribute("prompt.tokens.final", int(final_tokens))
                    span.set_attribute("prompt.compress.ratio", float(ratio))
                    span.set_attribute("prompt.compress.reduction_achieved", float(reduction_achieved))
                except Exception:
                    pass
        except Exception:
            pass

        return text

    def _apply_basic_compression(self, text: str, settings: Any) -> str:
        """Apply basic compression techniques (existing optimise logic)."""
        # 1. Collapse excessive blank lines (configurable)
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

        # 2. Deduplicate consecutive identical lines (helps noisy logs / transcripts)
        deduped: list[str] = []
        prev: str | None = None
        for ln in text.splitlines():
            if ln == prev:
                continue
            deduped.append(ln)
            prev = ln
        text = "\n".join(deduped)

        # 3. Trim repeated spaces within lines while preserving indentation inside code fences
        def _squeeze_spaces(line: str) -> str:
            if line.startswith("    ") or line.startswith("\t"):
                return line  # assume preformatted/code
            return re.sub(r"\s{2,}", " ", line)

        text = "\n".join(_squeeze_spaces(line) for line in text.splitlines())

        # 4. Section summarisation for very long contiguous blocks
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
                        omitted = len(current) - (HEAD_TAIL_KEEP * 2)
                        current = head + [f"...[omitted {omitted} lines]..."] + tail
                    compressed_sections.append("\n".join(current))
                    current = []
                compressed_sections.append("")
            else:
                current.append(ln)
        if current:
            if len(current) > MAX_SECTION_LINES:
                head = current[:HEAD_TAIL_KEEP]
                tail = current[-HEAD_TAIL_KEEP:]
                omitted = len(current) - (HEAD_TAIL_KEEP * 2)
                current = head + [f"...[omitted {omitted} lines]..."] + tail
            compressed_sections.append("\n".join(current))
        text = "\n".join(compressed_sections).strip()

        return text

    def _apply_context_trimming(self, text: str, target_tokens: int, current_tokens: int) -> str:
        """Apply intelligent context trimming strategies."""
        lines = text.splitlines()
        if not lines:
            return text

        # Strategy 1: Remove low-value lines (empty, short, repetitive)
        line_values = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            value_score = 0

            # Higher value for longer, information-dense lines
            if len(stripped) > 10:
                value_score += 1
            if len(stripped) > 50:
                value_score += 1

            # Higher value for lines with specific markers
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

            # Lower value for very short or repetitive content
            if len(stripped) < 5:
                value_score -= 1
            if stripped.count(".") > 5 or stripped.count("-") > 5:
                value_score -= 1  # likely noise or formatting

            line_values.append((value_score, i, line))

        # Sort by value and keep highest-value lines
        line_values.sort(reverse=True)

        # Keep lines until we hit target token count
        kept_lines: list[str] = [""] * len(lines)
        running_tokens = 0

        for value_score, original_index, line in line_values:
            line_tokens = self.count_tokens(line)
            if running_tokens + line_tokens <= target_tokens:
                kept_lines[original_index] = line
                running_tokens += line_tokens
            else:
                # Try truncating this line if it's high value
                if value_score > 0 and running_tokens < target_tokens:
                    remaining_tokens = target_tokens - running_tokens
                    truncated = self._truncate_line_to_tokens(line, remaining_tokens)
                    if truncated:
                        kept_lines[original_index] = truncated
                        break
                else:
                    break

        # Reconstruct text preserving order
        result_lines = [line for line in kept_lines if line is not None]
        return "\n".join(result_lines)

    def _truncate_line_to_tokens(self, line: str, max_tokens: int) -> str:
        """Truncate a line to approximately max_tokens while preserving meaning."""
        if self.count_tokens(line) <= max_tokens:
            return line

        words = line.split()
        if not words:
            return ""

        # Binary search for optimal word count
        left, right = 0, len(words)
        best_result = ""

        while left <= right:
            mid = (left + right) // 2
            candidate = " ".join(words[:mid])

            if self.count_tokens(candidate) <= max_tokens:
                best_result = candidate
                left = mid + 1
            else:
                right = mid - 1

        # Add ellipsis if we truncated
        if best_result and best_result != line:
            # Try to add ellipsis if there's room
            with_ellipsis = best_result + "..."
            if self.count_tokens(with_ellipsis) <= max_tokens:
                return with_ellipsis

        return best_result

    def _apply_emergency_truncation(self, text: str, max_tokens: int) -> str:
        """Apply emergency truncation when all else fails."""
        if self.count_tokens(text) <= max_tokens:
            return text

        # count truncation occurrence for observability
        try:
            lbl = metrics.label_ctx()
            if hasattr(metrics, "PROMPT_EMERGENCY_TRUNCATIONS"):
                metrics.PROMPT_EMERGENCY_TRUNCATIONS.labels(lbl["tenant"], lbl["workspace"]).inc()
        except Exception:
            pass

        lines = text.splitlines()
        if not lines:
            return text

        # For very small token limits, return a minimal response
        if max_tokens <= 2:
            return "[truncated]" if max_tokens >= 1 else ""

        # Keep first and last portions, omit middle
        total_lines = len(lines)
        if total_lines <= 6:
            # For very short texts, just truncate words
            words = text.split()
            for i in range(len(words), 0, -1):
                candidate = " ".join(words[:i])
                if self.count_tokens(candidate) <= max_tokens:
                    return candidate + "..." if i < len(words) else candidate
            # Fallback for extreme cases
            return "[content omitted due to length]"[: max_tokens * 4] if max_tokens > 0 else ""

        # For longer texts, keep beginning and end
        keep_start = total_lines // 3
        keep_end = total_lines // 3

        while keep_start + keep_end > 0:
            start_lines = lines[:keep_start]
            end_lines = lines[-keep_end:] if keep_end > 0 else []

            if start_lines and end_lines:
                candidate_lines = (
                    start_lines + [f"...[omitted {total_lines - keep_start - keep_end} lines]..."] + end_lines
                )
            elif start_lines:
                candidate_lines = start_lines + [f"...[omitted {total_lines - keep_start} lines]..."]
            else:
                candidate_lines = [f"...[omitted {total_lines - keep_end} lines]..."] + end_lines

            candidate = "\n".join(candidate_lines)
            if self.count_tokens(candidate) <= max_tokens:
                return candidate

            # Reduce keep amounts
            if keep_start > keep_end:
                keep_start -= 1
            else:
                keep_end -= 1

        # Last resort: just return truncated beginning
        words = text.split()
        for i in range(len(words), 0, -1):
            candidate = " ".join(words[:i]) + "..."
            if self.count_tokens(candidate) <= max_tokens:
                return candidate

        return "[content omitted due to length]" if max_tokens > 0 else ""

    def build_with_context(
        self,
        instruction: str,
        query: str,
        k: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> str:
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
