# A2A Adapter (JSON-RPC)

This service exposes a minimal Agent2Agent (A2A) compatible adapter over JSON-RPC 2.0 using FastAPI.

It provides discovery via an Agent Card and executes registered "skills" (tools) through a JSON-RPC endpoint.

## Enable

Set the environment flag before starting the API service:

```bash
export ENABLE_A2A_API=true
```

## Endpoints

- GET `/a2a/agent-card` – Agent Card with metadata and skill schemas
- GET `/a2a/skills` – minimal list of skills and input schemas
- POST `/a2a/jsonrpc` – JSON-RPC 2.0 execution endpoint

## Tenancy

Include headers to scope calls to a tenant workspace:

- `X-Tenant-Id: <tenant>`
- `X-Workspace-Id: <workspace>`

Alternatively, you can pass `tenant_id` and `workspace_id` inside `params`, but headers are preferred.

## JSON-RPC

Supports direct method calls and the convenience wrapper `agent.execute`.

### Direct method

Request:

```http
POST /a2a/jsonrpc
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools.text_analyze",
  "params": {"text": "hello from A2A"}
}
```

### agent.execute wrapper

Request:

```http
POST /a2a/jsonrpc
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "agent.execute",
  "params": {"skill": "tools.text_analyze", "args": {"text": "hello"}}
}
```

Example: lc_summarize

```http
POST /a2a/jsonrpc
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "agent.execute",
  "params": {
    "skill": "tools.lc_summarize",
    "args": {"text": "Long text here...", "max_sentences": 3}
  }
}
```

### Responses

- Success:

```json
{ "jsonrpc": "2.0", "id": "1", "result": {"status": "success", "data": {}, "error": null} }
```

- Error:

```json
{ "jsonrpc": "2.0", "id": "1", "error": {"code": -32601, "message": "Method not found"} }
```

Error codes follow JSON-RPC 2.0 conventions: -32601 (method not found), -32602 (invalid params), -32603 (internal error).

## Skills (Tools)

The adapter registers a small set of curated tools as skills. Out of the box, it exposes `tools.text_analyze` if available.

To add a new skill, register a callable that returns a `StepResult` in `src/server/a2a_router.py`:

```python
from some.module import MyTool

_my_tool = MyTool()
_TOOLS["tools.my_skill"] = lambda *, arg1, arg2=None: _my_tool.run(arg1=arg1, arg2=arg2)
```

## References

- Demo client: `scripts/a2a_client_demo.py`
  - Quick run (assuming server on localhost:8000 and A2A enabled):

```bash
export A2A_BASE_URL=http://localhost:8000
# Optional auth if enabled
export A2A_API_KEY=key1
# Optional tenancy
export A2A_TENANT_ID=default
export A2A_WORKSPACE_ID=main

# Run via Make target (preferred)
make run-a2a-client-demo

# Or directly
/home/crew/.venv/bin/python scripts/a2a_client_demo.py
```

- Collections (ready-to-import):
  - Postman: `docs/a2a_postman_collection.json`
  - Insomnia: `docs/a2a_insomnia_collection.json`
  - Includes a "JSON-RPC: batch (auth)" example with optional API key and tenancy headers

- Tests (A2A-only fast sweep):

```bash
make test-a2a
```

- A2A Protocol: <https://a2a-protocol.org/latest/>
- ADK docs: <https://google.github.io/adk-docs/>
- A2A repo: <https://github.com/a2aproject/A2A>
