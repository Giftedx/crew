import pytest

from ultimate_discord_intelligence_bot.services import MemoryService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


@pytest.mark.parametrize(
    "strict_flag,expect_raise",
    [
        ("0", False),
        ("", False),
        ("1", True),
    ],
)
def test_memory_service_strict_mode_behavior(monkeypatch, strict_flag, expect_raise):
    # Ensure ingest strict is off to avoid interference; test the new flag
    monkeypatch.setenv("ENABLE_INGEST_STRICT", "0")
    if strict_flag:
        monkeypatch.setenv("ENABLE_TENANCY_STRICT", strict_flag)
    else:
        monkeypatch.delenv("ENABLE_TENANCY_STRICT", raising=False)

    memory = MemoryService()

    if expect_raise:
        with pytest.raises(RuntimeError):
            memory.add("hello")
        with pytest.raises(RuntimeError):
            memory.retrieve("hello")
    else:
        # Non-strict should fallback and not raise
        memory.add("hello")
        assert memory.retrieve("hello") == [{"text": "hello", "metadata": {}}]


def test_memory_service_with_explicit_tenant(monkeypatch):
    # Enable strict to prove that explicit tenant context works
    monkeypatch.setenv("ENABLE_TENANCY_STRICT", "1")

    memory = MemoryService()
    ctx = TenantContext("t1", "w1")
    with with_tenant(ctx):
        memory.add("alpha", {"k": "v"})
        assert memory.retrieve("alpha") == [{"text": "alpha", "metadata": {"k": "v"}}]


def test_memory_service_isolation_between_tenants(monkeypatch):
    monkeypatch.setenv("ENABLE_TENANCY_STRICT", "1")

    memory = MemoryService()
    with with_tenant(TenantContext("t1", "w1")):
        memory.add("data1")
    with with_tenant(TenantContext("t2", "w2")):
        memory.add("data2")

    with with_tenant(TenantContext("t1", "w1")):
        assert memory.retrieve("data") == [{"text": "data1", "metadata": {}}]
    with with_tenant(TenantContext("t2", "w2")):
        assert memory.retrieve("data") == [{"text": "data2", "metadata": {}}]
