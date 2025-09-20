from __future__ import annotations

import json
import os

from client.a2a_client import A2AClient, A2AClientConfig


def main() -> None:
    base_url = os.getenv("A2A_BASE_URL", "http://localhost:8000")
    api_key = os.getenv("A2A_API_KEY")
    enable_retry = os.getenv("A2A_ENABLE_RETRY", "0").lower() in ("1", "true", "yes", "on")
    tenant_id = os.getenv("A2A_TENANT_ID")
    workspace_id = os.getenv("A2A_WORKSPACE_ID")

    client = A2AClient(
        A2AClientConfig(
            base_url=base_url,
            api_key=api_key,
            enable_retry=enable_retry,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )
    )

    print("# Agent Card")
    print(json.dumps(client.get_agent_card(), indent=2))

    print("\n# Skills")
    print(json.dumps(client.get_skills(), indent=2))

    print("\n# RPC: tools.text_analyze")
    res = client.call("tools.text_analyze", {"text": "Hello A2A world"})
    print(json.dumps(res, indent=2))

    print("\n# RPC Batch")
    batch = [
        ("tools.text_analyze", {"text": "alpha"}, 1),
        ("agent.execute", {"skill": "tools.lc_summarize", "args": {"text": "one. two. three.", "max_sentences": 2}}, 2),
    ]
    res_b = client.call_batch(batch)
    print(json.dumps(res_b, indent=2))


if __name__ == "__main__":
    main()
