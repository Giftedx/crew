"""Optional LLMLingua prompt compression adapter.

This module provides a tiny wrapper around microsoft/llmlingua's
PromptCompressor. Import is lazy and guarded so the project works
without the dependency. Use via the convenience function
``maybe_compress_prompt`` which respects the feature flag
ENABLE_PROMPT_COMPRESSION and returns the original string on any
errors or when the dependency is missing.

Contracts:
- Input: prompt string and optional target token count (int)
- Output: compressed string (or original on fallback)
- No exceptions bubble up to callers.
"""

from __future__ import annotations

import os
from typing import Any

_COMPRESSOR: Any | None = None
_IMPORT_TRIED = False


def _get_compressor() -> Any | None:
    global _COMPRESSOR, _IMPORT_TRIED  # noqa: PLW0603
    if _COMPRESSOR is not None:
        return _COMPRESSOR
    if _IMPORT_TRIED:
        return None
    _IMPORT_TRIED = True
    try:  # optional dependency path
        from llmlingua import PromptCompressor  # type: ignore

        _COMPRESSOR = PromptCompressor()
        return _COMPRESSOR
    except Exception:
        _COMPRESSOR = None
        return None


def maybe_compress_prompt(prompt: str, *, target_tokens: int | None = None) -> str:
    """Return a compressed version of ``prompt`` when enabled and available.

    Behavior:
    - If ENABLE_PROMPT_COMPRESSION != "1": return original prompt.
    - If llmlingua is unavailable or any error occurs: return original prompt.
    - Otherwise, use PromptCompressor.compress_prompt with a conservative
      target size, preserving semantics as much as possible.
    """
    try:
        flag = os.getenv("ENABLE_PROMPT_COMPRESSION", "").strip().lower()
        if flag not in {"1", "true", "yes", "on"}:
            return prompt
        comp = _get_compressor()
        if comp is None:
            return prompt
        # Default target ~700 tokens if not provided (safe for most prompts)
        tgt = int(target_tokens) if target_tokens is not None else 700
        res = comp.compress_prompt(prompt, instruction="", question="", target_token=tgt)
        out = res.get("compressed_prompt") if isinstance(res, dict) else None
        return str(out) if isinstance(out, str) and out.strip() else prompt
    except Exception:
        return prompt


__all__ = ["maybe_compress_prompt"]
