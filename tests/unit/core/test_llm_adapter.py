"""Tests for the LLM adapter."""

from platform.core.routing.base_router import UnifiedRouter
from platform.core.routing.llm_adapter import RouterLLMAdapter, create_router_llm


class TestRouterLLMAdapter:
    """Test RouterLLMAdapter implementation."""

    def test_adapter_creation(self) -> None:
        """Test adapter creation."""
        adapter = RouterLLMAdapter()
        assert adapter.model_name == "unified-router"
        assert isinstance(adapter.router, UnifiedRouter)

    def test_adapter_with_custom_router(self) -> None:
        """Test adapter with custom router."""
        router = UnifiedRouter()
        adapter = RouterLLMAdapter(router)
        assert adapter.router is router

    def test_messages_to_prompt(self) -> None:
        """Test message conversion to prompt."""
        adapter = RouterLLMAdapter()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        prompt = adapter._messages_to_prompt(messages)
        expected = "user: Hello\nassistant: Hi there!\nuser: How are you?"
        assert prompt == expected

    def test_extract_constraints(self) -> None:
        """Test constraint extraction from kwargs."""
        adapter = RouterLLMAdapter()
        kwargs = {"temperature": 0.9, "max_tokens": 500}
        constraints = adapter._extract_constraints(kwargs)
        assert constraints["min_quality"] == 0.8
        kwargs = {"minimize_cost": True, "max_cost": 0.01, "max_latency": 2.0}
        constraints = adapter._extract_constraints(kwargs)
        assert constraints["minimize_cost"] is True
        assert constraints["max_cost"] == 0.01
        assert constraints["max_latency"] == 2.0

    def test_invoke_success(self) -> None:
        """Test successful invoke."""
        adapter = RouterLLMAdapter()
        messages = [{"role": "user", "content": "Test message"}]
        result = adapter.invoke(messages)
        assert "content" in result
        assert "model" in result
        assert "usage" in result
        assert "routing_info" in result
        assert "Mock response" in result["content"]

    def test_invoke_with_constraints(self) -> None:
        """Test invoke with constraints."""
        adapter = RouterLLMAdapter()
        messages = [{"role": "user", "content": "Test message"}]
        kwargs = {"minimize_cost": True, "tenant": "test_tenant"}
        result = adapter.invoke(messages, **kwargs)
        assert "content" in result
        assert "routing_info" in result
        assert "strategy" in result["routing_info"]

    def test_get_stats(self) -> None:
        """Test getting router statistics."""
        adapter = RouterLLMAdapter()
        stats = adapter.get_stats()
        assert "cache_size" in stats
        assert "available_strategies" in stats
        assert "default_strategy" in stats

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        adapter = RouterLLMAdapter()
        messages = [{"role": "user", "content": "Test message"}]
        adapter.invoke(messages)
        adapter.invoke(messages)
        adapter.clear_cache()
        stats = adapter.get_stats()
        assert stats["cache_size"] == 0


class TestCreateRouterLLM:
    """Test create_router_llm function."""

    def test_create_with_default_router(self) -> None:
        """Test creating adapter with default router."""
        adapter = create_router_llm()
        assert isinstance(adapter, RouterLLMAdapter)
        assert isinstance(adapter.router, UnifiedRouter)

    def test_create_with_custom_router(self) -> None:
        """Test creating adapter with custom router."""
        router = UnifiedRouter()
        adapter = create_router_llm(router)
        assert adapter.router is router
