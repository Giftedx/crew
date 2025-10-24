from ultimate_discord_intelligence_bot.marketplace.trust import (
    clamp_capabilities,
    clamp_resources,
)


def test_clamp_capabilities_respects_tier():
    requested = ["rag.read", "tool.exec"]
    allowed = clamp_capabilities(requested, "community")
    assert allowed == ["rag.read"], "community tier should drop disallowed capabilities"


def test_clamp_resources_limits_by_tier():
    res = clamp_resources(cpu_ms=1000, memory_mb=1024, tier="community")
    assert res["cpu_ms"] == 500
    assert res["memory_mb"] == 256
