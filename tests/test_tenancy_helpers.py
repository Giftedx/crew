from ultimate_discord_intelligence_bot.tenancy.context import (
    TenantContext,
    current_tenant,
    mem_ns,
    with_tenant,
)
from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool


class _DummyConfig:
    def get_setting(self, _key):  # pragma: no cover - trivial stub
        return None


class _FakeQdrantClient:
    def __init__(self):
        self.created = []
        self.upserts = []

    def get_collection(self, name):  # pragma: no cover - always missing
        raise RuntimeError("missing")

    def recreate_collection(self, name, *, vectors_config):
        self.created.append((name, vectors_config))

    def upsert(self, *, collection_name, points):
        self.upserts.append((collection_name, points))


def _stub_config(monkeypatch):
    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_config",
        lambda: _DummyConfig(),
    )


def test_with_tenant_restores_previous_context():
    base = TenantContext("tenant", "workspace")
    with with_tenant(base):
        assert current_tenant() == base
        nested = TenantContext("nested", "inner")
        with with_tenant(nested):
            assert current_tenant() == nested
        assert current_tenant() == base
    assert current_tenant() is None


def test_mem_ns_composes_and_physical_name(monkeypatch):
    _stub_config(monkeypatch)
    tenant_ctx = TenantContext("alpha", "beta")
    logical = mem_ns(tenant_ctx, "collection")
    assert logical == "alpha:beta:collection"
    physical = MemoryStorageTool._physical_name(logical)
    assert ":" not in physical
    assert physical == "alpha__beta__collection"


def test_memory_storage_uses_tenant_namespace(monkeypatch):
    _stub_config(monkeypatch)
    client = _FakeQdrantClient()
    tool = MemoryStorageTool(client=client, collection="analysis", embedding_fn=lambda text: [float(len(text))])

    tenant_ctx = TenantContext("tenant", "space")
    with with_tenant(tenant_ctx):
        ns = tool._get_tenant_collection()
        assert ns == "tenant:space:analysis"
        result = tool.run("hello", {"topic": "testing"})

    assert result.success
    assert client.upserts, "upsert should be invoked"
    collection_name, _ = client.upserts[-1]
    assert collection_name == MemoryStorageTool._physical_name("tenant:space:analysis")
    assert ":" not in collection_name
