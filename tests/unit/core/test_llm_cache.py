from __future__ import annotations

import time
from platform.core.llm_cache import get_llm_cache, reset_llm_cache_for_tests


def test_llm_cache_disabled_returns_none(monkeypatch):
    monkeypatch.delenv("ENABLE_SEMANTIC_LLM_CACHE", raising=False)
    cache = get_llm_cache()
    assert cache.get("hello", model="m") is None


def test_llm_cache_basic_put_get(monkeypatch):
    reset_llm_cache_for_tests()
    monkeypatch.setenv("ENABLE_SEMANTIC_LLM_CACHE", "1")
    cache = get_llm_cache()
    prompt = "What is the weather?"
    cache.put(prompt, "model-a", {"answer": "Sunny"})
    hit = cache.get(prompt, "model-a")
    assert hit == {"answer": "Sunny"}


def test_llm_cache_ttl_expiry(monkeypatch):
    reset_llm_cache_for_tests()
    monkeypatch.setenv("ENABLE_SEMANTIC_LLM_CACHE", "1")
    cache = get_llm_cache()
    prompt = "Short lived"
    cache.put(prompt, "model-a", "value", ttl_seconds=1)
    assert cache.get(prompt, "model-a") == "value"
    time.sleep(1.1)
    assert cache.get(prompt, "model-a") is None


def test_llm_cache_semantic_hit(monkeypatch):
    reset_llm_cache_for_tests()
    monkeypatch.setenv("ENABLE_SEMANTIC_LLM_CACHE", "1")
    monkeypatch.setenv("LLM_CACHE_SIMILARITY_THRESHOLD", "0.5")
    cache = get_llm_cache()
    base = "The capital of France is Paris"
    variant = "Capital of France?"
    cache.put(base, "model-a", "Paris")
    assert cache.get(variant, "model-a") == "Paris"
