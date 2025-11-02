"""Central LLM client wrapper.

Goals:
- Single entry point for chat completions with optional semantic cache
- Integrate token & cost estimation (`core.token_meter`) and budget guard
- Provide pluggable provider callable (dependency injection) for easy testing
- Preserve per-tenant isolation implicitly via underlying cache + budget store

Feature Flags:
- ENABLE_SEMANTIC_LLM_CACHE (handled by llm_cache internally)

This wrapper deliberately remains minimal until a full provider registry is
introduced. It focuses on safe, testable composition of caching and budgeting.
"""
from __future__ import annotations
import contextlib
from collections.abc import Callable, Sequence
from typing import Any
from platform.llm_cache import get_llm_cache
from platform.token_meter import cost_guard, estimate_tokens
from platform.observability.metrics import get_metrics
ProviderFn = Callable[[Sequence[dict[str, Any]]], Any]

class LLMCallResult:

    def __init__(self, response: Any | None=None, *, cached: bool=False, estimated_tokens: int=0, model: str='', **kwargs: Any) -> None:
        if response is None and 'output' in kwargs:
            response = kwargs.pop('output')
        if estimated_tokens == 0 and 'usage_tokens' in kwargs:
            with contextlib.suppress(Exception):
                estimated_tokens = int(kwargs.pop('usage_tokens'))
        self.response = response
        self.cached = bool(cached)
        self.estimated_tokens = int(estimated_tokens)
        self.model = model
        self.output = self.response

    def __repr__(self) -> str:
        return f'LLMCallResult(model={self.model!r}, cached={self.cached}, estimated_tokens={self.estimated_tokens}, response={str(self.response)[:40]!r})'

def build_llm_call_result(**kwargs: Any) -> LLMCallResult:
    """Backward-compatible builder mapping legacy test fixture kwargs.

    Accepted aliases:
      - output -> response
      - usage_tokens -> estimated_tokens (fallback default 0)
      - model (required)
      - cached (default False)
    Ignores: cost, latency_ms, any extra keys.
    """
    response = kwargs.pop('response', None)
    if response is None and 'output' in kwargs:
        response = kwargs.pop('output')
    estimated = kwargs.pop('estimated_tokens', None)
    if estimated is None and 'usage_tokens' in kwargs:
        estimated = kwargs.pop('usage_tokens')
    if estimated is None:
        estimated = 0
    model = kwargs.pop('model', 'unknown')
    cached = bool(kwargs.pop('cached', False))
    return LLMCallResult(response=response, cached=cached, estimated_tokens=int(estimated), model=model)

class LLMClient:

    def __init__(self, provider: ProviderFn, model: str):
        self.provider = provider
        self.model = model
        self._cache = get_llm_cache()
        try:
            self._metrics = get_metrics()
        except Exception:
            self._metrics = None

    def chat(self, messages: Sequence[dict[str, Any]]) -> LLMCallResult:
        """Execute chat call with semantic cache and budget protection.

        Steps:
        1. Normalize prompt (join user/assistant content fields) for cache key.
        2. Attempt semantic cache hit.
        3. If miss, estimate tokens & enforce budget via cost_guard.
        4. Call provider and store result (fire-and-forget on cache put failure).
        5. Return `LLMCallResult` with metadata.
        """
        normalized = self._normalize_messages(messages)
        cached_resp = self._cache.get(normalized, self.model)
        if cached_resp is not None:
            tokens = estimate_tokens(normalized)
            transformed = cached_resp
            try:
                if isinstance(cached_resp, dict):
                    if 'output' in cached_resp and isinstance(cached_resp['output'], str):
                        transformed = {**cached_resp, 'output': cached_resp['output'] + ' (cached)'}
                    elif 'response' in cached_resp and isinstance(cached_resp['response'], str):
                        transformed = {**cached_resp, 'response': cached_resp['response'] + ' (cached)'}
                elif isinstance(cached_resp, str):
                    transformed = cached_resp + ' (cached)'
            except Exception:
                transformed = cached_resp
            with contextlib.suppress(Exception):
                if self._metrics:
                    self._metrics.counter('llm_calls_total', labels={'model': self.model, 'cache': 'hit'}).inc()
                    self._metrics.counter('llm_tokens_estimated_total', labels={'model': self.model}).add(tokens)
            return LLMCallResult(response=transformed, cached=True, estimated_tokens=tokens, model=self.model)
        tokens = estimate_tokens(normalized)
        est_out = max(16, int(tokens * 0.25))
        with cost_guard(tokens, est_out, self.model):
            import time as _t
            _t0 = _t.monotonic()
            resp = self.provider(messages)
            duration = _t.monotonic() - _t0
            with contextlib.suppress(Exception):
                if self._metrics:
                    self._metrics.counter('llm_calls_total', labels={'model': self.model, 'cache': 'miss'}).inc()
                    self._metrics.counter('llm_tokens_estimated_total', labels={'model': self.model}).add(tokens + est_out)
                    self._metrics.histogram('llm_call_seconds', duration, labels={'model': self.model})
        with contextlib.suppress(Exception):
            self._cache.put(normalized, self.model, resp)
        return LLMCallResult(response=resp, cached=False, estimated_tokens=tokens + est_out, model=self.model)

    def _normalize_messages(self, messages: Sequence[dict[str, Any]]) -> str:
        parts: list[str] = []
        for m in messages:
            role = m.get('role', '')
            content = m.get('content', '')
            if content:
                parts.append(f'{role}:{content}')
            elif m.get('tool_calls'):
                parts.append(f'{role}:tool_calls')
        return '\n'.join(parts)
__all__ = ['LLMCallResult', 'LLMClient', 'ProviderFn', 'build_llm_call_result']