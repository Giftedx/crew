# Agent / Automated Assistant Extended Reference

This file complements `.github/copilot-instructions.md` (kept lean for fast model ingestion). It expands on operational patterns that are *enforced by tests or code paths today*.

## 1. StepResult Semantics
`StepResult` normalizes tool outcomes. It exposes:

- `success`: boolean success flag
- `data`: dict payload (tool-specific fields)
- `error`: optional error string

When converted to a dict (legacy callers), a `status` key is emitted as `"success"` or `"error"` for compatibility.
Prefer `StepResult.ok(...)` / `StepResult.fail(err, ...)` in new code.

## 2. Config Knob Lifecycle
1. Add key to the appropriate config YAML (e.g., `config/ingest.yaml`).
2. Load via existing loader (no bespoke parsers). Provide in‑code default.
3. Document in `docs/configuration.md` (and subsystem doc if applicable).
4. Add/adjust test covering both default & overridden behavior.
5. Run `make docs && pytest` (sync + validation).

## 3. In‑Memory Qdrant Fallback
Factory `memory.qdrant_provider.get_qdrant_client()` returns a stub when:
- `QDRANT_URL` unset, empty, equals `:memory:` or starts with `memory://`.
Use only for unit tests / quick dev. Do *not* benchmark recall. New vector features must degrade gracefully (avoid advanced filters unsupported in the stub).

## 4. Knowledge Graph (KG) & Plugins
- KG code lives under `kg/`. Relation strings must use **active voice** (`Creator collaborated_with Guest`).
- Add new relation types only with accompanying tests if surfaced externally.
- Plugins are tenant‑scoped sandboxes; register capabilities in manifest and validate with:
```bash
python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin <module>
```
- Always pass tenancy + run policy / security checks before persisting plugin outputs.

Example KG relation insertion in a test:
```python
from kg.store import KGStore
store = KGStore()
store.add_relation(tenant="default", workspace="main", rel_type="collaborated_with", a="hasan", b="h3_podcast")
rels = store.get_relations(a="hasan")
assert any(r.type == "collaborated_with" and r.b == "h3_podcast" for r in rels)
```

## 5. Discord CDN Archiver
Location: default `data/archive_manifest.db` (migrates from legacy root `archive_manifest.db` if present). Override with `ARCHIVE_DB_PATH`.
Workflow: Input CDN URL -> size/policy validation -> optional compression -> dedupe via manifest (checksum) -> stored object metadata returned.
Return shape must preserve stable keys: `id`, `original_url`, `stored_url`, `checksum`.

## 6. Observability & Metrics
- Use `obs.tracing` (init once) and `metrics` helpers. No `print` debugging.
- Extend metric enums sparingly; reuse label builders to keep cardinality bounded.

## 7. Timezone & Determinism
- Always timezone‑aware UTC. Use helpers (e.g. `ensure_utc`).
- Inject time / randomness providers into logic influencing tests.
- Ripgrep audits: `rg utcnow src`, `rg "datetime.now()" src` should stay empty.

## 8. Ripgrep Fast Discovery
```bash
rg StepResult src            # return patterns
rg "ENABLE_" -t py          # feature flags
rg VectorStore.namespace src # tenancy namespaces
rg "LearningEngine.record"   # RL reward hooks
rg "\[\d+\]" tests        # citation assertions
```

## 9. RL Reward Recording (Deterministic Pattern)
```python
from prompt_engine import PromptEngine
from core.learning_engine import LearningEngine
prompt = PromptEngine().build("routing_eval", user_query)
resp = router.route(prompt)

def score(r):
    base = 1.0 if r.data.get("had_citations") else 0.5
    return base / max(r.metrics.get("latency_ms", 1), 1)

LearningEngine.record(model=resp.model, reward=score(resp))
```

## 10. Pre‑PR Self‑Check (Fast Gate)
```bash
make format
make lint
pytest -k agent_config_audit
python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json
./scripts/dev.sh type-changed  # ensure no new type regressions
```
Optional deeper sweep before large merges:
```bash
pytest -q
make docs
```

## 11. Mypy Baseline Strategy
- Use `./scripts/dev.sh type-changed` for incremental checks.
- If total errors drop below baseline (`./scripts/dev.sh type-baseline`), update baseline via `./scripts/dev.sh type-baseline-update` in a dedicated `chore:` commit.
- Never increase baseline error count; fix or narrow types instead.

## 12. Anti‑Patterns (Enforced / Tested)
| Anti‑Pattern | Corrective Action |
|--------------|------------------|
| Raw provider SDK call | Use router / `OpenRouterService` + `TokenMeter` |
| Missing feature flag | Add `ENABLE_<AREA>_<FEATURE>` guard |
| Tenant omitted | Thread `(tenant, workspace)` or wrap with `with_tenant` |
| Silent swallow (no StepResult) | Return `StepResult(status=..., error=...)` or raise bug |
| Uncited grounded answer | Append ordered `[n]` tokens matching retrieval |
| Naive timestamp | Use UTC helper |
| New global singleton | Inject / pass dependency |

## 13. Minimal Tool Skeleton (Reference)
```python
class MyTool:
    name = "my_tool"
    def run(self, url: str) -> StepResult:
        if not url.startswith("https://"):
            return StepResult(error="invalid_url", status="bad_request")
        # ... logic ...
        return StepResult(data={"ok": True})
```

## 14. Citation Enforcement
Grounded response synthesis *must* append sequential bracket markers:
```python
cited_answer = answer + " " + "".join(f"[{i+1}]" for i, _ in enumerate(retrieved_docs))
```
Tests may assert the presence of `[1]` for at least one source.

## 15. Troubleshooting Ladder
1. Feature flag active? (`env | grep ENABLE_`)
2. Tenancy consistent? (namespace generation matches expected)
3. Vector store populated? (list points / log count)
4. Citations appended? (regex `\[[0-9]+\]` in answer)
5. Config/agent sync? (`pytest -k agent_config_audit`)
6. Cost guard triggered? (inspect `TokenMeter` logs / budgets)
7. Cache key canonical? (prompt build stable ordering)

---
**Edit Scope Reminder:** If a change touches multiple areas (routing + memory + grounding) prefer incremental PRs unless atomic.

*End of extended reference.*
