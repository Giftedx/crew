from __future__ import annotations

from uuid import uuid4

from domains.memory.embedding_service import EmbeddingResult, EmbeddingService


def _stub_generate(service: EmbeddingService, call_counter: list[int]) -> None:
    def _fake_generate(text: str, model_name: str) -> EmbeddingResult:
        call_counter[0] += 1
        return EmbeddingResult(embedding=[0.1, 0.2, 0.3], model=model_name, dimension=3)

    service._select_model = lambda alias: "stub-model"  # type: ignore[assignment]
    service._generate_embedding = _fake_generate  # type: ignore[assignment]


def test_embed_text_uses_cache() -> None:
    service = EmbeddingService()
    calls = [0]
    _stub_generate(service, calls)

    text = f"cache-test-{uuid4()}"

    first = service.embed_text(text)
    second = service.embed_text(text)

    assert calls[0] == 1, "embedding generator should be invoked once due to caching"
    assert (first.metadata or {}).get("cache_hit") is False
    assert (second.metadata or {}).get("cache_hit") is True


def test_embed_text_bypass_cache_with_flag() -> None:
    service = EmbeddingService()
    calls = [0]
    _stub_generate(service, calls)

    text = f"cache-bypass-{uuid4()}"

    service.embed_text(text, use_cache=False)
    service.embed_text(text, use_cache=False)
    service.embed_text(text)

    # Each call should execute the embedding generator because caching was bypassed
    assert calls[0] == 3