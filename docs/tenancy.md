# Tenancy

This project supports hosting multiple communities on a single deployment. Each
Discord guild is mapped to a workspace which in turn belongs to a tenant. The
`tenancy` module provides a light set of primitives so core services can remain
shared while data and configuration stay isolated.

## Adding a Tenant

1. Create a directory under `tenants/<slug>/`.
2. Add `tenants/<slug>/tenant.yaml` describing the tenant and its workspaces with Discord guild
   IDs.
3. (Optional) Provide `tenants/<slug>/routing.yaml`, `tenants/<slug>/budgets.yaml`, `tenants/<slug>/policy_overrides.yaml`
   and other configuration files for custom behaviour.

During runtime the `TenantRegistry` loads these files and resolves incoming
Discord requests to a `TenantContext` which carries the tenant and workspace
identifiers through the system.

### Routing Profiles and Budgets

If `tenants/<slug>/routing.yaml` is present it may define an `allowed_models` list limiting
which LLMs the router can select for that tenant.  `tenants/<slug>/budgets.yaml` configures
`daily_cap_usd` and `max_per_request` so costs are tracked per tenant rather
than globally.

## Memory Namespaces

The in-memory store and other persistence layers must prefix all namespaces with
`<tenant>:<workspace>:`. Utility :func:`tenancy.context.mem_ns` constructs these
prefixes and the `MemoryService` validates them to prevent cross-tenant access.

## Service Behavior: OpenRouter Tenancy

The `OpenRouterService` resolves the active tenant via `current_tenant()` and applies it to
model routing, budget evaluation, and cache namespacing. Behavior is guarded by flags:

- Strict mode: when `ENABLE_TENANCY_STRICT=1` (or `ENABLE_INGEST_STRICT=1`), calling `route()`
   without an active `TenantContext` raises `RuntimeError`.
- Non‑strict mode: if no tenant is set, the service logs a warning and defaults to
   `TenantContext("default", "main")`. A counter increments for visibility:

  - `tenancy_fallback_total{tenant,workspace,component}` with `component="openrouter_service"`.

Verification:

1. Unit test: `tests/test_openrouter_tenancy.py` validates both strict and non‑strict paths.
1. Metrics: render or scrape and inspect the counter.

    Example (pseudo‑code):

    ```python
    from obs import metrics
    print(metrics.render().decode("utf-8"))  # look for tenancy_fallback_total{...,component="openrouter_service"}
    ```

Notes:

- Provider preferences and model overrides come from `TenantRegistry`. Cache namespaces include
   `tenant` and `workspace` when the enhanced Redis cache is used.

### Metrics Labeling: Effective Context

LLM metrics (model selection, estimated cost, latency, cache hits) must be labeled with the
effective tenant/workspace even when callers forget to set a `TenantContext` in non‑strict mode.
To ensure this, the router computes an effective context at the start of each call and passes a
local label factory into all metric emissions. This avoids the "unknown" fallback from
`metrics.label_ctx()` while preserving strict mode semantics.

Implications:

- In strict mode, missing context still raises; no metrics are emitted for the failed call.
- In non‑strict mode, the effective `default:main` context is used for metrics and cache keys,
  and `tenancy_fallback_total{component="openrouter_service"}` is incremented once per call.

Tests: `tests/test_openrouter_metrics_labels.py` asserts that LLM metrics include
`tenant="default"` and `workspace="main"` labels in non‑strict mode when no context is set.
