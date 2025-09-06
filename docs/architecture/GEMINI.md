---
title: Gemini Integration Notes
origin: GEMINI.md (root)
status: migrated
last_moved: 2025-09-02
---

## Overview

This document captures integration considerations, limitations, and tuning guidance when using the Gemini model family within the system's unified LLM abstraction layer.

## Capabilities Snapshot

| Capability | Support | Notes |
|-----------|---------|-------|
| Text generation | Yes | Standard chat & completion styles |
| Multi-turn context | Yes | Conversation state length subject to token window |
| Tool / function calling | Partial | Requires schema adaptation layer |
| Image understanding | Model-dependent | Only enabled if vision flag on |
| Streaming tokens | Yes | Server-sent events pathway |
| System prompt | Yes | Prefixed; may be truncated near window limit |

## Configuration Parameters

| Parameter | Purpose | Guidance |
|-----------|---------|----------|
| model_id | Selects model variant | Use smallest variant that meets quality SLO |
| max_output_tokens | Upper bound on generated tokens | Set via budget function (cost guard) |
| temperature | Sampling diversity | 0.7 default; lower for deterministic eval harness |
| top_p | Nucleus sampling | Tune in tandem with temperature |
| safety_settings | Content filtering | Ensure alignment with moderation policy; log blocks |

## Prompt Assembly

````text
[system]
<system directives>
[user]
<user content>
[context]
<retrieved / tool output>
````

Guidelines:

1. Keep system directives concise; verbose instructions risk early truncation.
2. Insert tool outputs after user content with clear section delimiters.
3. Avoid nested markdown tables inside context block (token inflation & parsing ambiguity).

## Tool / Function Calling Layer

Gemini's tool invocation requires JSON schema adaptation. Approach:

1. Maintain internal Pydantic model definitions.
2. Derive JSON Schema; strip unsupported formats (e.g., `format: uuid`).
3. Inject `function_declarations` field with sanitized schema.
4. On model response with function call, map arguments back through Pydantic validation; surface errors with recovery suggestion.

Error Modes:

| Scenario | Example | Mitigation |
|----------|---------|------------|
| Missing required arg | `{"name": "fetch_user", "args": {}}` | Return validation error; ask model to supply missing fields |
| Type mismatch | `age: "twenty"` | Coerce simple primitives; else request correction |
| Hallucinated function | `name: delete_database` | Reject & restate available functions |

## Safety & Moderation

1. Apply pre-prompt normalization (trim excessive whitespace, collapse repeated punctuation) to reduce false-positive safety triggers.
2. Log safety blocks with category taxonomy (self-harm, violence, hate, sexual, other) for analytics.
3. Provide user-facing remediation message when content blocked; do not expose raw provider category codes.

## Streaming Considerations

| Aspect | Detail |
|--------|--------|
| Heartbeat | Expect events every <=5s; treat >15s gap as stalled stream |
| Buffering | Aggregate partial sentences before UI emit unless debug flag set |
| Cancellation | Support user abort; send cancel signal; ensure open HTTP response closed |

## Cost & Budgeting

| Metric | Approach |
|--------|----------|
| Token cost estimation | Use provider pricing sheet; maintain per-model dict |
| Budget enforcement | Pre-flight check: projected_prompt + max_output <= limit |
| Adaptive truncation | If over budget, reduce context section before system/user |

## Observability Hooks

Emit structured events:

````json
{"event":"gemini.request","model":"gemini-pro","tokens_in":1200,"functions":2}
{"event":"gemini.stream.start","id":"abc"}
{"event":"gemini.stream.delta","id":"abc","chars":42}
{"event":"gemini.stream.end","id":"abc","latency_ms":850}
````

Metrics:

| Metric | Type | Notes |
|--------|------|-------|
| gemini_tokens_in_total | Counter | Labeled by model |
| gemini_tokens_out_total | Counter | Labeled by model |
| gemini_stream_latency_seconds | Histogram | End - first byte per stream |
| gemini_function_call_failures_total | Counter | Validation or mapping errors |

## Failure Scenarios & Recovery

| Failure | Symptom | Recovery |
|---------|---------|----------|
| Timeout | No stream events >15s | Cancel & retry with backoff (max 2) |
| Rate limit | 429 error | Exponential backoff + jitter; respect Retry-After |
| Tool schema reject | Provider error on function_declarations | Remove optional fields; retry once |
| Invalid JSON in function args | Pydantic error | Ask model to resend only arguments JSON |

## Migration & Deprecation Plan

| Phase | Change | Action |
|-------|--------|--------|
| 1 | Introduce Gemini provider adapter | Feature flag default off |
| 2 | Add tool calling support | Compare quality vs baseline provider |
| 3 | Enable streaming in prod | Monitor latency & error budgets |
| 4 | Graduate flag (on by default) | Update docs & announce |

## Open Questions

1. Should we unify function calling schema across providers (adapter normalization) to simplify downstream parsing?
2. How do we reconcile provider-specific safety categories with internal moderation taxonomy (mapping table vs inline translation)?
3. Is adaptive truncation of context preferable to dynamic model downshift when near budget limits?

---
Generated 2025-09-02
