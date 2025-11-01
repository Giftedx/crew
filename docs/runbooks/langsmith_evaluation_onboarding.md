# LangSmith Evaluation Onboarding Playbook

**Updated:** October 28, 2025  
**Owner:** Observability & Reinforcement Learning Guild  
**Audience:** Tenant onboarding engineers, SRE rotations, evaluation operators

---

## 1. Purpose

This runbook describes how to provision LangSmith Evaluate for a new tenant and verify that automated trajectory grading is flowing into the unified feedback loop. Follow these steps whenever LangSmith grading is requested or when onboarding a new workspace to the Phase 1 evaluation enhancements.

---

## 2. Prerequisites

- **Tenant bootstrap completed.** The tenant must already exist under `crew_data/tenants/<slug>/` with a working `TenantContext` entry.
- **Secrets access.** You need permission to retrieve tenant-specific API keys from Vault or the secure secrets store.
- **LangSmith workspace.** The tenant (or our internal ops account) must have a LangSmith project with Evaluate enabled. Create a dedicated dataset for automated trajectories if one does not already exist.
- **Feature flag review.** Confirm that enabling LangSmith grading is approved for the tenant (see `docs/operations/feature_flags.md`).

---

## 3. Configuration Steps

### 3.1 SecureConfig entries

Populate the following keys in the tenant’s secure config source:

| Key | Location | Description |
| --- | --- | --- |
| `ENABLE_LANGSMITH_EVAL=true` | `.env` or `secure_config` | Turns on the evaluator bridge for this tenant. |
| `ENABLE_UNIFIED_FEEDBACK=true` | `.env` or `secure_config` | Required so LangSmith results are forwarded into the feedback loop. |
| `LANGSMITH_API_KEY=<tenant key>` | secrets store or `.env` | API token for Evaluate requests. |
| `LANGSMITH_PROJECT=<project>` | optional | Overrides the default `discord-intel-evals` project. |
| `LANGSMITH_EVALUATION_DATASET=<dataset>` | optional | Dataset name for LangSmith Evaluate (falls back to LangSmith defaults when empty). |
| `LANGSMITH_EVALUATION_NAME=<evaluation>` | optional | Custom evaluation config name; defaults to `trajectory-accuracy`. |

> **Tip:** For production tenants, prefer using Vault-backed entries (see `core/secure_config.get_config`). Use `.env` as a last resort for local debugging only.

### 3.2 Tenant secure config file

Update `crew_data/tenants/<slug>/secure_config.yaml` (or the JSON equivalent) with the keys above. Example:

```yaml
langsmith_api_key: ${vault://tenants/<slug>/langsmith_api_key}
langsmith_project: creator-observability
langsmith_evaluation_dataset: crew-trajectory-snapshots
enable_langsmith_eval: true
enable_unified_feedback: true
```

After editing, run `make secure-config-validate TENANT=<slug>` to confirm the schema passes validation.

### 3.3 Environment sanity check

- Restart any long-running workers (`make restart-workers`), or deploy the updated secure config through the orchestration pipeline.
- Ensure no stale environment variables override the intended tenant settings when using multi-tenant deployments (check `TenantContext` initialization logs).

---

## 4. Functional Verification

### 4.1 Dry run with synthetic trajectory

- Execute a pipeline run with `ENABLE_LANGSMITH_EVAL=1` set locally (for example, run `make run-crew TENANT=<slug>`).
- Verify logs include:
  - `LangSmithEvaluateAdapter.evaluate` success message.
  - `langsmith_trajectory_evaluator` metadata with `feedback_submitted=True`.
- Confirm the Prometheus counter `trajectory_evaluations_total{evaluator="langsmith"}` increments (use `make scrape-metrics` or check Grafana).

### 4.2 Unified feedback confirmation

- Inspect `UnifiedFeedbackOrchestrator` logs for `Trajectory feedback submitted` entries for the tenant.
- (Optional) Run the unit test to smoke-check feedback submission:

  ```bash
  pytest tests_new/unit/ai/test_langsmith_trajectory_evaluator.py -k submit_feedback
  ```

- (Optional) Run the focused tool performance tests to ensure no tool metrics regressions:

  ```bash
  pytest tests_new/unit/ai/test_unified_feedback_tool_performance.py
  ```

### 4.3 LangSmith UI validation

- Open the LangSmith Evaluate project and confirm that new evaluation runs appear in the dataset you configured.
- Ensure the evaluation status is `COMPLETED`. Investigate any `FAILED` runs via LangSmith logs (common causes are quota issues or malformed payloads).
## 5. Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `LangSmith evaluation disabled` StepResult. | Feature flag off or missing API key. | Re-check secure config entries; ensure tenant overrides are loaded. |
| `LangSmith evaluation returned no metrics`. | Evaluate configuration mis-specified dataset/evaluation name. | Validate dataset/evaluation name in LangSmith UI; update SecureConfig accordingly. |
| `orchestrator_unavailable` in metadata. | Unified feedback orchestrator not bootstrapped for this tenant. | Call `set_orchestrator(...)` during worker startup or enable feedback loop in deployment config. |
| LangSmith dashboards show runs but Prometheus counter flat. | Metrics module not imported or tenant omitted from `metrics.label_ctx`. | Confirm `LangSmithTrajectoryEvaluator` is part of the evaluation pipeline; check logs for counter increments. |

---

## 6. Rollback Plan

- Set `ENABLE_LANGSMITH_EVAL=false` for the tenant and redeploy secure config.
- Remove `langsmith_*` keys from tenant secrets if access must be revoked.
- Monitor the orchestrator metrics to ensure trajectory feedback falls back to the heuristic evaluator (logs should show `langsmith_eval_disabled`).

---

## 7. References

- `src/eval/langsmith_adapter.py`
- `src/ai/rl/langsmith_trajectory_evaluator.py`
- `src/ai/rl/unified_feedback_orchestrator.py`
- `AI_EVAL_ENHANCEMENT_ROADMAP_2025.md` (status updates)
- `docs/runbooks/rl_feedback_loop.md` (broader feedback orchestration guidance)
