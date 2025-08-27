from ultimate_discord_intelligence_bot.services import MemoryService
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant, mem_ns


def test_mem_ns_composition():
    ctx = TenantContext("t1", "ws1")
    assert mem_ns(ctx, "x") == "t1:ws1:x"


def test_memory_isolation_between_tenants():
    service = MemoryService()
    ctx_a = TenantContext("tenantA", "main")
    ctx_b = TenantContext("tenantB", "main")
    with with_tenant(ctx_a):
        service.add("hello from A")
    with with_tenant(ctx_b):
        service.add("hello from B")
    with with_tenant(ctx_a):
        assert service.retrieve("hello") == [{"text": "hello from A", "metadata": {}}]
    with with_tenant(ctx_b):
        assert service.retrieve("hello") == [{"text": "hello from B", "metadata": {}}]
