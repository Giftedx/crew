"""Optional LLMLingua prompt compression adapter.

This module provides a tiny wrapper around microsoft/llmlingua's
``PromptCompressor`` that keeps the main code paths free from optional
dependency churn. Import is lazy and guarded so the project works without
the extra package installed. The convenience helpers implemented here
offer two primary entry points:

``maybe_compress_prompt``
    Backward-compatible API returning only the compressed string (or the
    original prompt when disabled/unavailable/errors occur). Existing
    callers continue to function exactly as before.

``compress_prompt_with_details``
    Extended API that also returns metadata about whether compression was
    attempted, which options were applied, and any diagnostic context that
    higher layers may wish to surface (e.g. observability, RouteState).

The helpers never raise; on any failure they simply return the original
prompt alongside metadata describing the fallback reason.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from typing import Any

_COMPRESSOR: Any | None = None
_IMPORT_TRIED = False
_SIGNATURE_CACHE: inspect.Signature | None = None


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


def _get_signature(compressor: Any) -> inspect.Signature | None:
    global _SIGNATURE_CACHE  # noqa: PLW0603
    if _SIGNATURE_CACHE is not None:
        return _SIGNATURE_CACHE
    try:
        method = getattr(compressor, "compress_prompt", None)
        if method is None:
            return None
        _SIGNATURE_CACHE = inspect.signature(method)
    except Exception:
        _SIGNATURE_CACHE = None
    return _SIGNATURE_CACHE


TruthPredicate = Callable[[str], bool]


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_kwargs(
    *,
    signature: inspect.Signature | None,
    target_tokens: int | None,
    ratio: float | None,
    extra: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    params = signature.parameters if signature is not None else {}
    kwargs: dict[str, Any] = {}
    accepted: dict[str, Any] = {}

    def _maybe_set(key: str, value: Any) -> None:
        if signature is None or key in params:
            kwargs[key] = value
            accepted[key] = value

    # Common optional parameters supported by PromptCompressor
    _maybe_set("instruction", "")
    _maybe_set("question", "")
    if target_tokens is not None:
        for cand in ("target_token", "target_tokens", "max_tokens", "target_length"):
            if signature is None or cand in params:
                kwargs[cand] = int(target_tokens)
                accepted[cand] = int(target_tokens)
                break
    if ratio is not None:
        for cand in ("compression_ratio", "ratio", "target_ratio"):
            if signature is None or cand in params:
                kwargs[cand] = float(ratio)
                accepted[cand] = float(ratio)
                break
    if extra:
        for key, value in extra.items():
            if signature is None or key in params:
                kwargs[key] = value
                accepted[key] = value
    return kwargs, accepted


def _extract_text(result: Any) -> str | None:
    if isinstance(result, dict):
        text = result.get("compressed_prompt")
        if isinstance(text, str) and text.strip():
            return text
        return None
    if isinstance(result, str) and result.strip():
        return result
    return None


def compress_prompt_with_details(
    prompt: str,
    *,
    enabled: bool | None = None,
    target_tokens: int | None = None,
    ratio: float | None = None,
    truthy: TruthPredicate | None = None,
    extra_kwargs: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Compress ``prompt`` when enabled, returning (text, metadata).

    Parameters
    ----------
    prompt:
        Input text to compress.
    enabled:
        Optional override for enablement. ``True`` forces compression,
        ``False`` forces bypass, ``None`` falls back to the environment flag.
    target_tokens:
        Desired token budget passed to the compressor when supported.
    ratio:
        Desired compression ratio (0-1). Only applied if the compressor
        signature exposes a compatible parameter.
    truthy:
        Optional predicate used to parse env strings (defaults to
        ``_is_truthy``).
    extra_kwargs:
        Additional keyword arguments forwarded to ``compress_prompt`` when
        recognised by the underlying signature (e.g. ``stage``, ``device``).

    Returns
    -------
    tuple[str, dict[str, Any]]
        Compressed text (or original) and metadata describing execution.
    """

    truthy = truthy or _is_truthy
    try:
        if enabled is None:
            flag = os.getenv("ENABLE_PROMPT_COMPRESSION", "")
            if not truthy(flag):
                return prompt, {"applied": False, "reason": "disabled"}
        elif enabled is False:
            return prompt, {"applied": False, "reason": "disabled"}

        compressor = _get_compressor()
        if compressor is None:
            return prompt, {"applied": False, "reason": "unavailable"}

        signature = _get_signature(compressor)
        kwargs, accepted = _build_kwargs(
            signature=signature,
            target_tokens=target_tokens,
            ratio=ratio,
            extra=extra_kwargs,
        )

        result = compressor.compress_prompt(prompt, **kwargs)
        compressed = _extract_text(result)
        if not compressed:
            return prompt, {"applied": False, "reason": "no_output", "kwargs": accepted}

        metadata: dict[str, Any] = {"applied": True, "reason": "applied", "kwargs": accepted}
        if isinstance(result, dict):
            for key in ("compression_ratio", "original_tokens", "compressed_tokens", "removed_tokens"):
                if key in result:
                    metadata[key] = result[key]
        return compressed, metadata
    except Exception as exc:
        return prompt, {"applied": False, "reason": "error", "error": str(exc)}


def maybe_compress_prompt(
    prompt: str,
    *,
    target_tokens: int | None = None,
    enabled: bool | None = None,
    ratio: float | None = None,
    extra_kwargs: dict[str, Any] | None = None,
) -> str:
    """Return a compressed version of ``prompt`` when enabled and available.

    Behavior:
    - If ENABLE_PROMPT_COMPRESSION != "1": return original prompt.
    - If llmlingua is unavailable or any error occurs: return original prompt.
    - Otherwise, use PromptCompressor.compress_prompt with a conservative
      target size, preserving semantics as much as possible.
    """
    compressed, _meta = compress_prompt_with_details(
        prompt,
        enabled=enabled,
        target_tokens=target_tokens,
        ratio=ratio,
        extra_kwargs=extra_kwargs,
    )
    return compressed


__all__ = ["maybe_compress_prompt", "compress_prompt_with_details"]
