# 🔧 Copilot Quick Reference

Concise operational cheat sheet distilled from full `copilot-instructions.md`. Use this for fast editing decisions; consult the full doc for rationale.

## Core Pillars
- Tenant isolation everywhere (`TenantContext`, metrics labels, vector namespaces).
- Feature flags gate all new subsystems (`ENABLE_<AREA>_<FEATURE>`).
- Determinism: UTC aware timestamps, stable ordering/case.
- Observability: tracing spans + metrics; no `print` for runtime signals.
- Cost & routing: Only through PromptEngine → OpenRouterService → TokenMeter → LearningEngine.

## Golden Flow
URL → `multi_platform_download_tool` → transcription → analysis (sentiment/claims/fallacies/emotion?) → grounding (citations) → Discord delivery.
Each step returns `StepResult` or legacy dict with `status`.

## StepResult Patterns
- Success: `StepResult.ok(data={...})`
- Skipped (flag off/lightweight): `StepResult(status="skipped")`
- Recoverable error: `StepResult.fail(error="invalid_url", detail=...)`
- Programmer error: raise (tests should catch).

## Citations
Append numeric bracketed citations sequentially: `... [1][2]`. Missing citation is a warning + potential reward penalty.

## Model Routing & RL
Flow: PromptEngine.build → filter (capability, cost, context) → ε‑greedy explore → OpenRouterService (TokenMeter guard) → reward 0–1 (neg only for policy/safety) → LearningEngine.record(model, reward, cached=bool). Always record failures with reward=0; cached hits still recorded.

## Scheduler
Priority queue for ingestion/analysis; deterministic job key (URL + bucket) dedupes. Backpressure: drop lowest‑priority future jobs when queue exceeds limit → emit `scheduler_dropped_total{reason="backpressure"}`. Profiles metadata (from `profiles.yaml`) attached to enrich jobs.

## Observability Snippets
 
```python
with tracing.start_span("grounded_answer", tenant=t, workspace=w) as span:
    metrics.qa_requests_total.labels(tenant=t).inc()
```

Record reward:

```python
LearningEngine.record(model=chosen, reward=score)
```
Guidelines: one span per logical op; avoid high‑cardinality labels (truncate/hash user text); define counters centrally, not inline inside loops.

## Feature Flag Categories
 
| Area | Examples |
|------|----------|
| Ingestion | ENABLE_INGEST_YOUTUBE / _TWITCH |
| RAG / Grounding | ENABLE_RAG_CONTEXT, ENABLE_GROUNDING |
| RL / Routing | ENABLE_RL_GLOBAL, ENABLE_RL_ROUTING |
| Discord | ENABLE_DISCORD_COMMANDS |
| Security | ENABLE_CONTENT_MODERATION |
| Observability | ENABLE_TRACING, ENABLE_METRICS |
| HTTP | ENABLE_HTTP_RETRY (legacy ENABLE_ANALYSIS_HTTP_RETRY honored) |

## Quick Commands
 
| Task | Command |
|------|---------|
| Install dev | `pip install -e .[dev]` |
| Lint+format | `make format lint` |
| Type check | `make type` |
| Unit tests | `pytest -q` |
| Single test | `pytest tests/test_retry_precedence_scaffold.py::test_explicit_arg_wins` |
| Eval harness | `make eval` |
| Full systems | `python test_all_systems.py` |
| Lightweight import | `LIGHTWEIGHT_IMPORT=1 python start_full_bot.py --dry-run` |
| Retry audit | `pytest -k retry_precedence` |
| Find utcnow | `rg "utcnow\(" src` |

## Troubleshooting Ladder
 
1. Flag enabled?
2. Tenant context present?
3. Vector namespace populated?
4. Citations appended?
5. Agent/task config sync error?
6. Cost budget exceeded?
7. Cache key canonical?
8. Moderation/policy block?

## Anti‑Patterns
 
Raw model calls, unguarded features, tenant leakage, ad‑hoc prints, broad `Any`, silent except pass, duplicate ingestion logic.

## Add a Tool (Template)
 
```python
class MyTool(BaseTool):
    name = "my_tool"
    def _run(self, url: str):
        if not url.startswith("https://"):
            return {"status": "error", "error": "invalid_url"}
        return {"status": "success", "data": {"ok": True}}
```
Flag guard:
 
```python
if not os.getenv("ENABLE_ANALYSIS_MY_FEATURE"):
    return {"status": "skipped"}
```

Refer to: `copilot-instructions.md` for sections 13–16 deep dives.
