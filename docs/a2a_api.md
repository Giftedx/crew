# A2A JSON-RPC Adapter

This service exposes a minimal Agent-to-Agent (A2A) adapter over HTTP using JSON-RPC 2.0.

- Base path: `/a2a`
- RPC endpoint: `POST /a2a/jsonrpc`
- Discovery:
  - `GET /a2a/agent-card`
  - `GET /a2a/skills`

## Enablement

The adapter is disabled by default. Enable via environment:

- `ENABLE_A2A_API=1`
- Optional API key protection: `ENABLE_A2A_API_KEY=1` and `A2A_API_KEY="key1,key2"`
- Optional streaming demo route: `ENABLE_A2A_STREAMING_DEMO=1`

Feature flags control exposure of individual tools at runtime (no restart required in tests):

- `ENABLE_A2A_SKILL_SUMMARIZE` (default: on)
- `ENABLE_A2A_SKILL_RAG_OFFLINE` (default: on)
- `ENABLE_A2A_SKILL_RAG_VECTOR` (default: on)
- `ENABLE_A2A_SKILL_RAG_INGEST` (default: off)
- `ENABLE_A2A_SKILL_RAG_INGEST_URL` (default: off)
- `ENABLE_A2A_SKILL_RAG_HYBRID` (default: on)
- `ENABLE_A2A_SKILL_RESEARCH_BRIEF` (default: on)
- `ENABLE_A2A_SKILL_RESEARCH_BRIEF_MULTI` or `ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI` (default: off)

## JSON-RPC Basics

Request (single):

```json
{
  "jsonrpc": "2.0",
  "id": "123",
  "method": "tools.lc_summarize",
  "params": { "text": "...", "max_sentences": 3 }
}
```

Request (batch):

```json
[
  { "jsonrpc": "2.0", "id": 1, "method": "tools.text_analyze", "params": {"text": "hello"} },
  { "jsonrpc": "2.0", "id": 2, "method": "agent.execute", "params": {"skill": "tools.rag_query", "args": {"query": "q", "documents": ["a", "b"]}} }
]
```

Response (success):

```json
{
  "jsonrpc": "2.0",
  "id": "123",
  "result": { "status": "success", "data": { /* tool-specific */ } }
}
```

Response (error):

```json
{
  "jsonrpc": "2.0",
  "id": "123",
  "error": { "code": -32602, "message": "Invalid params: ...", "data": { /* optional */ } }
}
```

Error codes:

- `-32600` Invalid Request
- `-32601` Method not found
- `-32602` Invalid params
- `-32603` Internal error

## Auth

If API key auth is enabled, provide the header `X-API-Key: <key>`.

## Tenancy

Optionally scope calls by including headers:

- `X-Tenant-Id: <tenant>`
- `X-Workspace-Id: <workspace>`

Some tools use tenant/workspace to select or create vector index namespaces.

## Tools

The `/a2a/skills` endpoint returns the currently enabled tool list with input schemas. Notable tools:

- `tools.text_analyze` — Simple text stats (length, word count)
- `tools.lc_summarize` — Extractive summarization; offline fallback available
- `tools.rag_query` — Offline ranking of provided documents
- `tools.rag_query_vs` — Tenant-scoped vector search (if available)
- `tools.rag_ingest`, `tools.rag_ingest_url` — Ingest content into vectors (optional)
- `tools.rag_hybrid` — Combine vector + offline heuristics
- `tools.research_and_brief` — Synthesize an outline and key findings from sources
- `tools.research_and_brief_multi` — Multi-agent variant (behind flag) with offline fallback

## Observability

- Latency histograms and counters are recorded when metrics are enabled.
- Tracing spans wrap each tool execution (one span per tool call).

## Examples

cURL (single):

```bash
curl -sS -X POST http://localhost:8000/a2a/jsonrpc \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: key1' \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools.text_analyze","params":{"text":"hello world"}}'
```

cURL (batch):

```bash
curl -sS -X POST http://localhost:8000/a2a/jsonrpc \
  -H 'Content-Type: application/json' \
  -d '[{"jsonrpc":"2.0","id":1,"method":"tools.text_analyze","params":{"text":"hello"}},{"jsonrpc":"2.0","id":2,"method":"agent.execute","params":{"skill":"tools.rag_query","args":{"query":"q","documents":["a","b"]}}}]'
```

### Python client

A small client is available at `src/client/a2a_client.py`:

```python
from client.a2a_client import A2AClient, A2AClientConfig

client = A2AClient(A2AClientConfig(base_url="http://localhost:8000", api_key=None, enable_retry=False))
print(client.get_agent_card())
print(client.get_skills())
print(client.call("tools.text_analyze", {"text": "hello"}))
```

There’s also a demo script: `scripts/a2a_client_demo.py` (configure A2A_BASE_URL and A2A_API_KEY as needed).

### Quick-run tips

- Run only A2A-related tests:

```bash
make test-a2a
```

- Import a ready-made Postman collection: `docs/a2a_postman_collection.json`

Note: The `make test-a2a` target also validates the Postman/Insomnia collection JSON and required variables.

## Using Postman/Insomnia collections

The demo also respects optional tenancy environment variables:

- `A2A_TENANT_ID`
- `A2A_WORKSPACE_ID`
You can exercise the API interactively using the provided collections:

- Postman: `docs/a2a_postman_collection.json`
- Insomnia: `docs/a2a_insomnia_collection.json`

Configure these environment variables after importing:

- A2A_BASE_URL: Base server URL (e.g., <http://localhost:8000>)
- A2A_API_KEY: API key value when `ENABLE_A2A_API_KEY=1` (optional)
- A2A_TENANT_ID: Tenant identifier (optional)
- A2A_WORKSPACE_ID: Workspace identifier (optional)

Notes

- The collections send `X-API-Key`, `X-Tenant-Id`, and `X-Workspace-Id` headers only when the corresponding variables are set.
- Start with the discovery requests (`GET /a2a/agent-card`, `GET /a2a/skills`), then try `POST /a2a/jsonrpc` using the provided examples.
- A ready-made "JSON-RPC: batch (auth)" request is included to quickly exercise batch calls with optional API key and tenancy headers.
