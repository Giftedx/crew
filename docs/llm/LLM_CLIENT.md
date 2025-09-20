# LLM Client Wrapper

A minimal central client for LLM chat calls that unifies:

- Semantic cache lookups (via `SemanticLLMCache`)
- Token/cost estimation & budget enforcement (`core.token_meter`)
- Pluggable provider injection for testing and multi-provider evolution

## Why

Prior to this wrapper, LLM calls would need to compose caching + budgeting manually. Centralizing reduces drift and enables future routing / metrics.

## Usage

```python
from core.llm_client import LLMClient

# Provider function signature: List[message] -> response
# Each message: {"role": "user|assistant|tool", "content": str, ...}

def provider(messages):
    # call real model here
    return {"output": "hello"}

client = LLMClient(provider, model="gpt-4o-mini")
result = client.chat([
    {"role": "user", "content": "Explain diffusion models simply."}
])
print(result.response, result.cached, result.estimated_tokens)
```

## Feature Flags

- `ENABLE_SEMANTIC_LLM_CACHE` (handled internally by cache module)

## Budget Enforcement

Uses `cost_guard(tokens_in, est_out, model)` with a conservative heuristic (output ≈ 25% of input, floor 16 tokens). Override logic later by extending the client or adding optional parameters.

## Cache Semantics

- Key: normalized concatenation of message `role:content` (tool call messages reduced to `role:tool_calls`).
- On cache hit: returns cached response (no provider call) and sets `cached=True`.
- On miss: provider called, response cached (fire-and-forget) and returned.

## Extensibility Roadmap

1. Multi-provider routing (bandit / cost-aware) injected at construction.
1. Observability hooks (cache_hit, cache_miss, budget_violation metrics).
1. Streaming interface for partial responses.
1. Prompt compression pre-pass.

## Testing

See `tests/test_llm_client.py` for examples covering cache hit and budget guard paths.
