# Tenancy

This project supports hosting multiple communities on a single deployment. Each
Discord guild is mapped to a workspace which in turn belongs to a tenant. The
`tenancy` module provides a light set of primitives so core services can remain
shared while data and configuration stay isolated.

## Adding a Tenant

1. Create a directory under `tenants/<slug>/`.
2. Add `tenant.yaml` describing the tenant and its workspaces with Discord guild
   IDs.
3. (Optional) Provide `routing.yaml`, `budgets.yaml`, `policy_overrides.yaml`
   and other configuration files for custom behaviour.

During runtime the `TenantRegistry` loads these files and resolves incoming
Discord requests to a `TenantContext` which carries the tenant and workspace
identifiers through the system.

## Memory Namespaces

The in-memory store and other persistence layers must prefix all namespaces with
`<tenant>:<workspace>:`. Utility :func:`tenancy.context.mem_ns` constructs these
prefixes and the `MemoryService` validates them to prevent cross-tenant access.
