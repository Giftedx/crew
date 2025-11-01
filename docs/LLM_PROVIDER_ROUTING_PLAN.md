## Addendum — Mission API, Provider Registry, and Learning Loop (Quality‑first)

Date: 2025-10-29

This addendum extends the provider routing plan with a cohesive, quality‑first integration across all entry points, enabling “all major providers,” continual learning, and consistent observability without touching restricted directories.

Summary:

1. Unify invocation behind a single Mission API entrypoint used by Discord, API, and Crew.
1. Introduce an LLM Provider Registry with adapters for OpenRouter, OpenAI, Anthropic, Google (Gemini), Cohere, Mistral, Azure OpenAI, AWS Bedrock, Groq/Together/Fireworks (Llama, Mixtral, etc.), Perplexity, xAI (Grok), DeepSeek — each tagged by capabilities (function_calling, vision, audio, json_schema, long_context).
1. Implement hierarchical routing (provider+model arms) via a router adapter that maps to Thompson Sampling (QUALITY_FIRST by default; also COST_AWARE and LATENCY_AWARE policies).
1. Add post‑analysis evaluation (LangSmith evaluator) and deterministic backstop retry with a curated top‑tier model when confidence is low.
1. Enrich StepResult metadata and Prometheus metrics with provider/model/cost/latency/eval_score, and enforce tenancy and HTTP guardrails.

New steps (superset of the plan below):

1. Mission API (single entrypoint)
   - Add `src/ultimate_discord_intelligence_bot/mission_api.py::run_mission(inputs, tenant_ctx)` delegating to `pipeline_components/orchestrator.py`, returning `step_result.StepResult`.
   - Refactor `src/server/app.py`, Discord command handlers, and `src/ultimate_discord_intelligence_bot/crew.py` to call this API for identical routing/fallbacks.

1. Provider Registry and Router Adapter
   - Create `services/llm_provider_registry.py` with `ProviderAdapter` and provider adapters listed above; include capability tags and cost/context metadata.
   - Create `services/llm_router_adapter.py` to present provider:model arms to `ai/routing/thompson_sampling_router.py` (no edits in restricted dirs). Policies: `QUALITY_FIRST` (default), `COST_AWARE`, `LATENCY_AWARE`.

1. Evaluation and Learning Hooks
   - After analysis, call `ai/evaluation/langsmith_evaluator.py` (shadow first) and transform scores into rewards; update the TS router via the adapter.
   - If confidence < threshold (default 0.7), retry once with a curated top‑tier model (Claude 3.5 Sonnet, GPT‑4.1/4o, Gemini 1.5 Pro) then return.

1. Retrieval Service Facade (optional)
   - Add `memory/retrieval_service.py` to centralize retrieval and enable `memory/hybrid_retriever.py` behind a flag; ensure `memory/qdrant_provider.py` handles sparse schema safely.

1. Tool Taxonomy and Registry (incremental)
   - Add `tools/base_types.py` (DownloaderTool, TranscriberTool, AnalyzerTool) and `tools/registry.py` for capability lookup and auto‑instrumentation.

1. Flags, Observability, and Compliance
   - Unify flags in `settings.py`/`core/secure_config.py` with `.env.example`: add `LLM_PROVIDER_ALLOWLIST`, `ROUTER_POLICY`, `QUALITY_FIRST_TASKS`, and per‑tenant overrides.
   - Enrich `StepResult.metadata` with `provider`, `model`, `capabilities`, `policy`, `cost_usd`, `latency_ms`, `eval_score`; add metrics for selections/rewards/failures/cost by provider/model/task.
   - Enforce `core/http_utils.py` (no direct `requests.*`), `with_tenant(...)`, and exports/instrumentation for all tools.

Rollout and flags:

- Default policies: `ROUTER_POLICY=QUALITY_FIRST`; `QUALITY_FIRST_TASKS="analysis,verification"`.
- Provider enablement via `LLM_PROVIDER_ALLOWLIST` and per‑tenant overrides.
- Evaluations in shadow mode first (use existing `ENABLE_TRAJECTORY_EVALUATION` or `ENABLE_SELF_EVAL_GATES` depending on module availability), then activate.
- Hybrid retrieval behind a feature flag; reversible.

Acceptance criteria:

- All surfaces call Mission API; identical StepResult shape and metadata.
- Provider registry enumerates providers and capabilities; router adapter selects provider:model arms; selections logged with cost/latency/eval.
- Evaluation rewards update TS posteriors; low‑confidence deterministic retry occurs once; outcomes recorded.
- Metrics present for selections_total, reward, failures_total, and cost buckets by provider/model/task.
- No direct `requests.*`; tenancy wrappers around storage/cache/metrics; tools exported and instrumented.

Risks and dependencies:

- Credentials for additional providers (Anthropic, Google, Cohere, Mistral, Azure, Bedrock, Groq/Together/Fireworks, Perplexity, xAI, DeepSeek).
- Qdrant sparse vector schema upgrade for hybrid retrieval.
- Rate limits and regional compliance (Azure/Bedrock) — treat via allowlists and tenant policy.
- Cost exposure — guard with per‑tenant budgets and policy caps.

---

## Plan: Quality‑first, provider‑agnostic routing

Unify model choice across all entry points with a provider registry and adapters, route through a single Mission API, and use hierarchical routing (provider+model) with evaluation‑driven rewards. Default to “most powerful” per task while exploring alternatives, with strict fallbacks and observability.

**Steps:**

1. Establish a provider registry and adapters.
   - Add `src/ultimate_discord_intelligence_bot/services/llm_provider_registry.py` defining a `ProviderAdapter` interface and adapters for: OpenRouter (meta‑provider), OpenAI, Anthropic, Google (Gemini), Cohere, Mistral, Azure OpenAI, AWS Bedrock, Meta Llama (via Groq/Together/Fireworks), Perplexity, xAI (Grok), DeepSeek. Include capability tags: text, function_calling, vision, audio, json_schema, long_context.

2. Integrate hierarchical routing with quality‑first policy.
   - In an adapter layer (outside `src/ai/routing/`), treat each provider:model as an “arm” for `ai/routing/thompson_sampling_router.py`; support policy toggles: QualityFirst (deterministic top tier), CostAware (reward penalizes spend), LatencyAware (p95 bound). Persist arm metadata in `StepResult.metadata` and Prometheus metrics.

3. Unify invocation via a Mission API.
   - Create `src/ultimate_discord_intelligence_bot/mission_api.py` with `run_mission(inputs, tenant_ctx)` to invoke `pipeline_components/orchestrator.py`. Refactor `src/server/app.py`, Discord command handlers, and `crew.py` to call this API so all surfaces use the same routing and fallbacks.

4. Wire evaluation and feedback loops.
   - Ensure post‑analysis evaluation with `ai/evaluation/langsmith_evaluator.py`; convert scores to rewards for the TS router. Add deterministic backstop: for critical tasks, always attempt a top‑tier retry (Claude 3.5 Sonnet, GPT‑4o/4.1, Gemini 1.5 Pro) when confidence < threshold, before returning.

5. Centralize credentials, flags, and fallbacks.
   - Extend `src/core/secure_config.py` and `env.example` with all provider keys (OpenAI, Anthropic, Google, Cohere, Mistral, Azure, Bedrock, Groq, Together, Fireworks, Perplexity, xAI, DeepSeek). Add `LLM_PROVIDER_ALLOWLIST`, `QUALITY_FIRST_TASKS`, `ROUTER_POLICY={quality_first|cost|latency}`, and per‑tenant overrides in `settings.py`.

6. Harden observability and safeguards.
   - Record `provider`, `model`, `capabilities`, `policy`, `cost_usd`, `latency_ms`, `eval_score` in `StepResult.metadata`. Add metrics: selections_total, reward, failures_total by provider/model, and cost buckets. Implement structured fallbacks: capability mismatch → retry best capable provider; timeout → lower‑latency provider; 429/5xx → alternate provider in same capability tier.

---

## Open Questions

1. Provider precedence defaults: Strictly quality‑first (Claude/GPT/Gemini) for all tasks, or only for specific tasks (analysis, verification) with exploration elsewhere?
2. Bedrock and Azure: enable via global flags or per‑tenant allowlist (due to region/data constraints)?
3. Capabilities policy: enforce JSON‑schema or tool‑use only when `inputs.requirements` demand it, or always prefer models that support them?

```markdown
## Plan: “All providers” quality‑first routing

Ensure every major LLM provider is selectable at runtime, with hierarchical routing that prefers the highest‑quality model for the task, while learning from evaluations and backing off gracefully.

**Steps:**
1. Introduce Provider Registry and adapters
   - Add `services/llm_provider_registry.py` with `ProviderAdapter` interface (`name`, `models()`, `capabilities`, `complete()`, `stream()`, `cost_estimator`).
   - Implement adapters for OpenRouter, OpenAI, Anthropic, Google (Gemini), Cohere, Mistral, Azure OpenAI, AWS Bedrock, Meta Llama (Groq/Together/Fireworks), Perplexity, xAI, DeepSeek.
   - Surface capability tags and per‑model metadata (context length, tool‑use, vision, audio).

2. Hierarchical routing with quality‑first policy
   - Create `services/llm_router_adapter.py` to map provider:model arms to `ai/routing/thompson_sampling_router.py`.
   - Policies: `QUALITY_FIRST` (deterministic shortlist + TS tie‑break), `COST_AWARE`, `LATENCY_AWARE`; configured in `settings.py` and overridable per tenant/task.

3. Single Mission API entrypoint
   - Add `mission_api.run_mission(inputs, tenant_ctx)` to call `pipeline_components/orchestrator.py`.
   - Update `server/app.py`, Discord commands, and `crew.py` to invoke `mission_api` so all routes share the same provider choice, fallbacks, and telemetry.

4. Evaluation‑driven learning and deterministic backstops
   - Plug in `ai/evaluation/langsmith_evaluator.py` post‑analysis; push reward to TS router.
   - If `eval_score < threshold`, retry once with a top‑tier provider from a curated list; annotate `StepResult.metadata` with both attempts.

5. Credentials, flags, and compliance
   - Extend `secure_config.py` and `.env.example` with union of provider keys; add `LLM_PROVIDER_ALLOWLIST`, `ROUTER_POLICY`, `QUALITY_FIRST_TASKS`, and per‑tenant overrides.
   - Ensure HTTP calls go through `core/http_utils.py` only; all surfaces return `StepResult`.

6. Observability, guardrails, and fallbacks
   - Add metrics for selections, rewards, costs, failures per provider/model; enrich `StepResult.metadata`.
   - Fallback cascade: capability mismatch → best capable provider; timeout → low‑latency provider; 429/5xx → alternate in capability tier; cost cap hit → shift to cheaper tier.
```
