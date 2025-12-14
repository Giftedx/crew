# MCP Tooling Strategy for CrewAI Integration

## 1. Specification and Reference Implementation Highlights

### 1.1 Protocol architecture and lifecycle

- **Client–host–server split** keeps hosts in control of security, while clients mediate stateful JSON-RPC sessions to focused servers. Servers expose resources, prompts, and tools but cannot access cross-server state without host mediation. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/architecture/index.mdx)
- **Initialization handshake** requires clients to send `initialize` with protocol version and capabilities; servers respond with their capabilities, and clients acknowledge with `notifications/initialized`. Only ping/log messages are allowed before initialization completes, preventing early tool execution. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/basic/lifecycle.mdx)
- **Capability negotiation** (e.g., `tools`, `resources`, `prompts`, `roots`, `sampling`) drives which protocol features each side can exercise. Optional flags like `listChanged` and `subscribe` govern notifications and streaming behavior. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/basic/lifecycle.mdx)
- **Tool invocation flow** uses `tools/list` for discovery, `tools/call` for execution, and optional `notifications/tools/list_changed` for dynamic catalogs. Responses wrap typed content payloads and surface `isError` for structured failure handling. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/server/tools.mdx)

### 1.2 Official SDK patterns

- **Python SDK (`mcp[cli]`)** offers FastMCP helpers for decorating tools/resources/prompts, supports stdio/SSE/HTTP transports, and bundles client utilities (context helpers, sampling, OAuth). Quickstart servers demonstrate additive tools, templated resources, and prompt registration. [Source](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md)
- **TypeScript SDK (`@modelcontextprotocol/sdk`)** mirrors the architecture with `McpServer`, zod schemas for typed input/output, and HTTP/stdio transports. Example servers show express-based wiring, structured tool outputs, and debounced notifications for efficiency. [Source](https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md)
- **Implementation guidance** from both SDKs emphasizes structured JSON schemas, streaming transports, and pluggable auth (OAuth helpers in Python, HTTP middleware hooks in TypeScript) that align with MCP’s capability negotiation model.

## 2. Patterns for Exposing External Services to CrewAI Agents

CrewAI integrations in this repo already treat MCP as the canonical bridge between external services and agents. Core patterns include:

1. **Safe in-process proxying (`MCPCallTool`)** – Wraps approved MCP modules/functions via a registry, returning `StepResult` objects so CrewAI agents can call MCP tools without a transport hop. Extending coverage means updating the allowlist with explicit namespace/function pairs and guarding metrics. 【F:src/ultimate_discord_intelligence_bot/tools/observability/mcp_call_tool.py†L1-L79】
2. **CrewAI tool wrappers (`MCPCallToolWrapper`)** – Adapts repository tools to CrewAI’s BaseTool interface, normalizing parameters, surfacing failures, and preserving shared context. Wrappers should catch exceptions, coerce outputs to `StepResult`, and provide default argument schemas when possible. 【F:src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py†L1205-L1242】
3. **Feature-flagged server mounts** – `docs/mcp.md` enumerates optional MCP servers (memory, routing, HTTP, KG, ingest, etc.) toggled via environment flags. Tool discovery in CrewAI is deterministic: enabling a server exposes its namespace and the CrewAI wrapper simply orchestrates the call. 【F:docs/mcp.md†L8-L78】
4. **Configuration-driven agent access** – Crew definitions pull tool availability from YAML and wrappers, letting us scope which agents see MCP capabilities. Use environment flags (e.g., `ENABLE_MCP_CALL_TOOL`) to add/remove tools per tenant or deployment. 【F:docs/mcp.md†L98-L134】【F:docs/crewai_integration.md†L1-L99】
5. **Transport-based integration** – For external platforms (Claude Desktop, VS Code, etc.), run `crew_mcp` via stdio/HTTP. CrewAI agents can either call the in-process bridge or hit remote MCP servers via FastMCP client tooling, depending on latency and security requirements. 【F:docs/mcp.md†L80-L111】

## 3. Authentication, Permissioning, and Sandbox Strategies

### 3.1 Protocol-level safeguards

- **Host mediation**: Hosts control client creation and can gate sampling requests, enforce human-in-the-loop confirmations, and scope which servers are reachable. Architecture docs stress isolation between servers and limited context exposure. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/architecture/index.mdx)
- **Capability scoping**: Only negotiated features (e.g., tools with `listChanged`, resources with `subscribe`) are usable, preventing unauthorized operations. Enforce minimal capability sets during initialization to reduce attack surface. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/basic/lifecycle.mdx)
- **Human oversight**: Tool documentation explicitly recommends confirmation prompts, logging, and denial controls whenever models invoke high-risk tools. Implement UI/UX or CrewAI workflow steps that require human approval for destructive actions. [Source](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2024-11-05/server/tools.mdx)

### 3.2 Repository enforcement

- **Allowlists & sanitization**: HTTP MCP server enforces HTTPS-only URLs and host allowlists via `MCP_HTTP_ALLOWLIST`, truncates payloads, and uses cached/resilient fetch utilities to harden outbound calls. Extend allowlists per deployment, and consider per-tenant overrides to isolate data domains. 【F:src/mcp_server/http_server.py†L1-L126】
- **Namespace registries**: `MCPCallTool` exposes only curated functions, requiring code review for new additions. Maintain namespaces per service domain and apply feature flags for optional exposure. 【F:src/ultimate_discord_intelligence_bot/tools/observability/mcp_call_tool.py†L17-L63】
- **CrewAI gating flags**: Environment toggles (e.g., `ENABLE_CREW_CONFIG_VALIDATION`, `ENABLE_MCP_CALL_TOOL`) let operators enforce stricter validation, verbose logging, or disable tools in sensitive environments. Combine with tenant-aware config to restrict capabilities. 【F:docs/crewai_integration.md†L13-L59】【F:docs/mcp.md†L98-L134】
- **Observability hooks**: Metrics counters record tool usage and errors, enabling anomaly detection and automated throttling policies. Extend metrics labels with tenant/agent identifiers for granular auditing. 【F:src/ultimate_discord_intelligence_bot/tools/observability/mcp_call_tool.py†L41-L79】

### 3.3 Sandbox layering recommendations

- Run MCP servers in isolated processes or containers when exposing side-effectful tools, relying on FastMCP transports that support per-connection auth (e.g., API keys, OAuth tokens). Use SDK-provided middlewares to enforce token checks before accepting `initialize`.
- Combine CrewAI agent role definitions with tool wrappers that validate inputs (schema-driven) to prevent prompt-injection exploitation of tool parameters.
- For high-risk tools (ingest, HTTP fetch), implement rate limiting at the wrapper level and log structured audit events via the observability pipeline.

## 4. Extension Mechanisms for Custom Tooling

1. **New MCP servers/modules** – Follow `src/mcp_server/http_server.py` patterns: wrap functionality in pure functions, decorate with `@mcp.tool`/`@mcp.resource`, and gate mounting behind environment flags in `mcp_server/server.py`. Update tests (`tests/unit/core/test_mcp_imports.py`) to keep smoke coverage. 【F:src/mcp_server/http_server.py†L1-L126】【F:docs/mcp.md†L108-L134】
2. **CrewAI wrapper scaffolding** – Extend `CrewAIToolWrapper` derivatives to normalize parameters and provide default schemas, ensuring new tools integrate seamlessly with CrewAI’s argument validation. Use shared context fields to pass state between sequential tasks. 【F:src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py†L1205-L1320】
3. **In-process tool registry expansion** – Update `_SAFE_REGISTRY` with new namespace/function pairs and implement guardrails (input sanitization, metrics). Consider namespacing per tenant if multi-tenant security demands separate registries. 【F:src/ultimate_discord_intelligence_bot/tools/observability/mcp_call_tool.py†L17-L63】
4. **Transport adaptations** – Leverage SDK streamable HTTP transports to expose MCP servers behind API gateways. Use OAuth helpers (Python SDK) or middleware (TypeScript SDK) to enforce bearer tokens, enabling external partners to integrate while respecting CrewAI permission models. [Source](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md)
5. **Automation & validation** – Integrate new tools into validation scripts (`scripts/validate_mcp_tools.py`, `src/validation/mcp_tools_validator.py`) to ensure conformance and to catch regressions before production rollout. 【F:scripts/validate_mcp_tools.py†L1-L571】【F:src/validation/mcp_tools_validator.py†L1-L864】

---
Maintainers should update this strategy whenever the MCP specification revs, new SDK primitives land, or CrewAI introduces different tool interfaces.
