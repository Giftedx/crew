from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "path, required_keys",
    [
        ("docs/a2a_postman_collection.json", ["A2A_BASE_URL", "A2A_API_KEY", "A2A_TENANT_ID", "A2A_WORKSPACE_ID"]),
        ("docs/a2a_insomnia_collection.json", ["A2A_BASE_URL", "A2A_API_KEY", "A2A_TENANT_ID", "A2A_WORKSPACE_ID"]),
    ],
)
def test_collections_parse_and_variables(path: str, required_keys: list[str]) -> None:
    p = Path(path)
    assert p.exists(), f"Missing collection file: {path}"

    raw = p.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, dict), "Collection should be a JSON object"

    # Postman uses top-level 'variable'; Insomnia uses resources with an environment entry
    keys_found: set[str] = set()

    # Postman
    variables = data.get("variable")
    if isinstance(variables, list):
        for v in variables:
            if isinstance(v, dict):
                k = v.get("key")
                if isinstance(k, str):
                    keys_found.add(k)

    # Insomnia
    resources = data.get("resources")
    if isinstance(resources, list):
        for r in resources:
            if isinstance(r, dict) and r.get("_type") == "environment":
                env_data = r.get("data") or {}
                if isinstance(env_data, dict):
                    keys_found.update(k for k in env_data.keys() if isinstance(k, str))

    missing = [k for k in required_keys if k not in keys_found]
    assert not missing, f"Missing environment variables in collections: {missing}"

    # Quick sanity: ensure we have requests to both discovery endpoints and jsonrpc path
    text = raw
    assert "/a2a/agent-card" in text
    assert "/a2a/skills" in text
    assert "/a2a/jsonrpc" in text
