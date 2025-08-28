### GitHub Copilot / AI Agent Instructions (Concise)

Purpose: Enable an AI coding agent to make high‑quality, safe edits quickly in this multi‑tenant Discord intelligence / ingestion / grounding / RL routing platform.

1. Core layout: domain packages under `src/` (e.g. `ingest/`, `analysis/`, `grounding/`, `memory/`, `policy/`, `security/`, `scheduler/`, `archive/`, `debate/`, `obs/`), global Crew tooling under `src/ultimate_discord_intelligence_bot/` (agents, tools, services, tenancy helpers). Reuse instead of duplicating.
2. Tenancy: ALWAYS operate inside a `(tenant, workspace)` context. Utilities build collection / namespace keys via `VectorStore.namespace(tenant, workspace, source)` or a `TenantContext` helper. Never mix data across tenants; pass explicit tenant/workspace in new functions.
3. Ingestion pipeline: URL -> multi‑platform dispatcher (`multi_platform_download_tool.py`) -> platform downloader(s) (yt‑dlp based, optional `quality`) -> transcription -> segmentation/analysis -> grounding/fact checks -> Discord post. Wrap each stage return in a `StepResult` (pattern already used) for consistency.
4. Tools & agents: Add new tool in `.../tools/`; register in `crew.py`; update `config/agents.yaml` / `config/tasks.yaml`. AST sync tests (`test_agent_config_audit.py`) will fail if mismatched. Imitate existing tool signature & error handling.
5. Memory & grounding: Vector/RAG lives in `memory/` + Qdrant client; `MemoryService` defends against blank queries, enforces case‑insensitive metadata filters. Grounded answers MUST return citation tokens (numeric bracket style) if you extend grounding logic.
6. Cost & routing: `TokenMeter` enforces per‑request ceilings (`COST_MAX_PER_REQUEST`); `LearningEngine` uses epsilon‑greedy model selection; `LLMCache` caches prompt→response. When adding model calls, thread them through these services (do NOT call provider SDKs directly).
7. Feature flags: Subsystems gated by `ENABLE_*` env vars (ingest, RAG/context, cache, RL, Discord, security/privacy, observability). New features should ship behind a flag named consistently (`ENABLE_<AREA>_<FEATURE>` if granular).
8. Profiles & cross‑links: Creator/show/staff data + collaboration links defined in `profiles.yaml` and related store module. When enriching ingestion results, resolve handles through profile lookup utilities to maintain canonical IDs.
9. Privacy / policy: Before persisting or exposing user content, ensure policy & redaction passes (see `policy/` + `security/`). Follow existing PII detection hooks; mirror patterns rather than inventing new filters.
10. Observability: Use `obs/tracing` + `metrics` label helpers; never introduce ad‑hoc print debugging—emit structured metrics or spans. Extend existing enum/label sets instead of creating divergent names.
11. Testing workflow: Run `pytest` locally for every change. Golden eval & regression: `python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json`. Plugin capability testkit: `python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin ultimate_discord_intelligence_bot.plugins.example_summarizer` (swap plugin). Keep new tests fast; use fixtures in `conftest.py` for heavy deps.
12. Search & reuse: Use ripgrep patterns to locate precedent (`rg StepResult`, `rg VectorStore.namespace`). Implement extensions by copying nearest minimal pattern and adjusting—avoid sprawling new abstractions.
13. Config‑driven behavior: Add knobs in `config/*.yaml` instead of hard‑coding. Reflect new config fields in docs under `docs/` and ensure sync tests cover them if applicable.
14. Error handling: Prefer returning structured `StepResult(error=..., status=...)` rather than raising, unless truly fatal. Maintain consistent log / metric emission sites.
15. Security discipline: Validate external inputs (URLs, file paths, MIME types) mirroring existing validators; never trust user‑supplied paths; keep downloads sandboxed.
16. Commit style: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`). Small, incremental commits are preferred; no history rewrites.
17. Performance: Favor async & streaming where present; when adding parallel steps (e.g. transcription + upload) preserve ordering guarantees relied upon by downstream analysis.
18. Avoid anti‑patterns: Duplicated downloader logic, bypassing tenancy, raw model calls, unflagged new subsystems, new global singletons, unchecked environment access scattered across files.
19. When uncertain: Trace an existing end‑to‑end flow (e.g. ingestion test) and replicate structure; prefer incremental enhancement over refactor. Document deviations inline with a brief rationale.
20. Extended guidance lives in `AGENTS.md` & `README.md`; keep this file concise—update only with proven, enforced patterns (not aspirations).

#### Appendix: High‑Leverage Edit Recipes (quick reference)
Add a tool:
```python
# src/ultimate_discord_intelligence_bot/tools/my_new_tool.py
class MyNewTool:
	name = "my_new_tool"
	def run(self, url: str) -> StepResult:
		if not url.startswith("https://"): return StepResult(error="invalid_url")
		data = fetch(url)
		return StepResult(data=data)
# Register in crew.py & add to config/agents.yaml tool list; run test_agent_config_audit.py
```
Feature flag pattern:
```python
if not os.getenv("ENABLE_ANALYSIS_MY_FEATURE"): return StepResult(status="skipped")
```
Grounding citation transform:
```python
raw, sources = answer_text, retrieved_docs  # docs carry .id
cited = raw + " " + "".join(f"[{i+1}]" for i,_ in enumerate(sources))
```
RL reward hook:
```python
resp = router.route(prompt)
reward = score(resp)  # deterministic metric
learning_engine.record(model=resp.model, reward=reward)
```
Test a new tool (pytest):
```python
def test_my_new_tool(monkeypatch):
	tool = MyNewTool()
	r = tool.run("https://example.com")
	assert r.error is None and r.data
```
Error handling matrix (summary): user/input issues -> return StepResult(error=..., status="bad_request"); transient external -> StepResult(error=..., status="retryable"); internal bug -> raise then add test to cover.

#### Extended Appendix (Optional Patterns)
Security validation template:
```python
def _safe_url(url: str) -> str:
	if not url.startswith(("https://", "http://")): raise ValueError("scheme")
	if any(ch in url for ch in ['..', '\\']): raise ValueError("path_traversal")
	return url
```
Performance (controlled parallel step):
```python
transcription, upload = await asyncio.gather(
	transcribe(audio_path), upload_drive(audio_path)
)
# Keep ordering for downstream: pass both objects to analysis step
```
Config knob addition:
```yaml
# config/ingest.yaml
max_batch_size: 8  # NEW
```
```python
val = ingest_cfg.get("max_batch_size", 4)
```
Profile enrichment example:
```python
profile = store.lookup_handle(platform="youtube", handle=raw.channel)
if profile: event.profile_id = profile.id
```
Expanded error mapping:
```
bad input -> StepResult(status="bad_request")
rate limit / timeout -> StepResult(status="retryable")
upstream 5xx (repeat) -> escalate metric + retry policy
logic bug -> raise (add regression test)
partial data -> StepResult(status="partial")
```
Troubleshooting checklist:
1. Feature flag off? (`env | grep ENABLE_`)
2. Tenancy mismatch? (namespace keys consistent?)
3. Empty retrieval? (check vector count before grounding)
4. Missing citations? (ensure transform appended `[n]` tokens)
5. Config sync fail? (run `pytest -k agent_config_audit`)
6. Cost guard trips? (inspect `TokenMeter` ceiling + request size)
7. Cache not hit? (confirm canonical prompt build order)