from __future__ import annotations

from platform.core.llm_client import LLMClient


class _Provider:
    def __init__(self):
        self.calls = 0

    def __call__(self, messages):
        self.calls += 1
        return {"output": f"resp-{self.calls}"}


def test_llm_client_cache_hit(monkeypatch):
    monkeypatch.setenv("ENABLE_SEMANTIC_LLM_CACHE", "1")
    provider = _Provider()
    client = LLMClient(provider, model="test-model")
    msgs = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "How can I help?"},
        {"role": "user", "content": "Tell me a joke"},
    ]
    r1 = client.chat(msgs)
    r2 = client.chat(msgs)
    assert r1.response != r2.response
    assert provider.calls == 1
    assert r2.cached is True


def test_llm_client_budget_guard(monkeypatch):
    monkeypatch.delenv("ENABLE_SEMANTIC_LLM_CACHE", raising=False)
    provider = _Provider()
    client = LLMClient(provider, model="gpt-3.5")
    msgs = [{"role": "user", "content": "x" * 40}]
    res = client.chat(msgs)
    assert res.response["output"].startswith("resp-1")
    assert provider.calls == 1
