import json
import os
import sys

import requests


def call_agent_execute(
    base_url: str,
    skill: str,
    args: dict,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    req_id: str = "1",
):
    url = base_url.rstrip("/") + "/a2a/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "agent.execute",
        "params": {"skill": skill, "args": args},
    }
    headers = {"Content-Type": "application/json"}
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id
    if workspace_id:
        headers["X-Workspace-Id"] = workspace_id
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def main():
    base_url = os.environ.get("A2A_BASE_URL", "http://localhost:8000")
    tenant = os.environ.get("A2A_TENANT_ID")
    workspace = os.environ.get("A2A_WORKSPACE_ID")
    skill = os.environ.get("A2A_SKILL", "tools.text_analyze")
    # Prefer explicit JSON args when provided
    raw_args = os.environ.get("A2A_ARGS_JSON")
    args: dict
    if raw_args:
        try:
            args = json.loads(raw_args)
        except Exception as exc:
            print(f"Invalid A2A_ARGS_JSON: {exc}", file=sys.stderr)
            sys.exit(2)
    else:
        # Convenience envs for common skills
        if skill == "tools.text_analyze":
            text = os.environ.get("A2A_TEXT", "hello from example client")
            args = {"text": text}
        elif skill == "tools.lc_summarize":
            text = os.environ.get("A2A_TEXT", "hello from example client")
            max_sentences = int(os.environ.get("A2A_MAX_SENTENCES", "3"))
            args = {"text": text, "max_sentences": max_sentences}
        elif skill == "tools.rag_query":
            query = os.environ.get("A2A_QUERY", "policy")
            docs_env = os.environ.get("A2A_DOCUMENTS_JSON", "[]")
            try:
                documents = json.loads(docs_env)
                if not isinstance(documents, list):
                    raise ValueError("A2A_DOCUMENTS_JSON must be a JSON array of strings")
            except Exception as exc:
                print(f"Invalid A2A_DOCUMENTS_JSON: {exc}", file=sys.stderr)
                sys.exit(2)
            top_k = int(os.environ.get("A2A_TOP_K", "3"))
            args = {"query": query, "documents": documents, "top_k": top_k}
        else:
            # Fallback
            text = os.environ.get("A2A_TEXT", "hello from example client")
            args = {"text": text}
    try:
        result = call_agent_execute(base_url, skill, args, tenant, workspace)
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
