import sys
import types
from types import SimpleNamespace
import pytest
from platform.core.step_result import StepResult

class DummyEmbeddingService:

    def __init__(self, dim: int=8) -> None:
        self._dim = dim

    def get_embedding_dimension(self) -> int:
        return self._dim

    async def generate_embedding(self, text: str, tenant: str, workspace: str) -> StepResult:
        return StepResult.ok(data=[0.1] * self._dim)

class DummyPoint:

    def __init__(self, pid: int, text: str, score: float) -> None:
        self.id = pid
        self.score = score
        self.payload = {'content': text, 'metadata': {}}

class DummyQdrant:

    def __init__(self) -> None:
        self._collections: set[str] = set()

    def get_collections(self):
        return SimpleNamespace(collections=[SimpleNamespace(name='default')])

    def create_collection(self, **kwargs):
        self._collections.add(kwargs.get('collection_name', 'default'))

    def search(self, collection_name: str, query_vector, limit: int, score_threshold: float, with_payload: bool):
        return [DummyPoint(1, 'A first doc', 0.91), DummyPoint(2, 'B second doc', 0.89)]

@pytest.mark.asyncio
async def test_retrieve_context_rerank_applied(monkeypatch):

    class DummyConfig:
        enable_reranker = True
        rerank_provider = 'cohere'

        def get_setting(self, key, default=None):
            return getattr(self, key, default)
    monkeypatch.setattr('core.secure_config.get_config', lambda: DummyConfig(), raising=False)
    from analysis import rerank as rerank_mod

    def fake_rerank(query: str, docs: list[str], provider: str, top_n: int):

        class R:
            indexes = list(reversed(range(len(docs))))
            scores = [1.0] * len(docs)
        return R()
    monkeypatch.setattr(rerank_mod, 'rerank', fake_rerank, raising=True)
    stub_mod = types.ModuleType('ultimate_discord_intelligence_bot.services.embedding_service')

    class _StubEmbeddingService:
        pass

    def _stub_create_embedding_service(*args, **kwargs):
        return _StubEmbeddingService()
    stub_mod.EmbeddingService = _StubEmbeddingService
    stub_mod.create_embedding_service = _stub_create_embedding_service
    sys.modules['ultimate_discord_intelligence_bot.services.embedding_service'] = stub_mod
    from domains.memory.vector_store import MemoryService
    svc = MemoryService(qdrant_client=DummyQdrant(), embedding_service=DummyEmbeddingService())
    res = await svc.retrieve_context('query', top_k=2, tenant='t1', workspace='w1')
    assert isinstance(res, StepResult)
    assert res.success
    assert res.data.get('reranked') is True
    assert res.data.get('rerank_provider') == 'cohere'
    items = res.data.get('data', [])
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]['id'] == 2
    assert items[1]['id'] == 1