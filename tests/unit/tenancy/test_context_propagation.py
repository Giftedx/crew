"""Tests for async-safe TenantContext propagation."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from ultimate_discord_intelligence_bot.tenancy.context import (
    TenantContext,
    current_tenant,
    require_tenant,
    run_with_tenant_context,
    with_tenant,
)


def test_basic_context_propagation():
    """Test basic context set/get in sync code."""
    ctx = TenantContext("test_tenant", "test_workspace")
    
    assert current_tenant() is None
    
    with with_tenant(ctx):
        assert current_tenant() == ctx
        assert current_tenant().tenant_id == "test_tenant"
        assert current_tenant().workspace_id == "test_workspace"
    
    assert current_tenant() is None


def test_nested_context_propagation():
    """Test nested context managers restore correctly."""
    ctx1 = TenantContext("tenant1", "workspace1")
    ctx2 = TenantContext("tenant2", "workspace2")
    
    with with_tenant(ctx1):
        assert current_tenant().tenant_id == "tenant1"
        
        with with_tenant(ctx2):
            assert current_tenant().tenant_id == "tenant2"
        
        assert current_tenant().tenant_id == "tenant1"
    
    assert current_tenant() is None


@pytest.mark.asyncio
async def test_async_task_propagation():
    """Test context propagates to async tasks automatically."""
    ctx = TenantContext("async_tenant", "async_workspace")
    
    async def check_context():
        await asyncio.sleep(0.01)
        tenant = current_tenant()
        assert tenant is not None
        assert tenant.tenant_id == "async_tenant"
        return tenant.workspace_id
    
    with with_tenant(ctx):
        # Create multiple concurrent tasks
        tasks = [asyncio.create_task(check_context()) for _ in range(5)]
        results = await asyncio.gather(*tasks)
    
    assert all(ws == "async_workspace" for ws in results)
    assert current_tenant() is None


@pytest.mark.asyncio
async def test_async_isolation():
    """Test different async tasks can have isolated contexts."""
    async def task_with_context(tenant_id: str, workspace_id: str):
        ctx = TenantContext(tenant_id, workspace_id)
        with with_tenant(ctx):
            await asyncio.sleep(0.01)
            tenant = current_tenant()
            assert tenant.tenant_id == tenant_id
            assert tenant.workspace_id == workspace_id
            return tenant_id
    
    # Run tasks concurrently with different contexts
    tasks = [
        task_with_context(f"tenant_{i}", f"workspace_{i}")
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)
    
    assert results == [f"tenant_{i}" for i in range(10)]


def test_thread_pool_propagation():
    """Test context propagates to thread pool executors."""
    ctx = TenantContext("thread_tenant", "thread_workspace")
    
    def check_context():
        tenant = current_tenant()
        assert tenant is not None
        return tenant.tenant_id
    
    with with_tenant(ctx):
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit tasks with context propagation (decorator pattern)
            futures = [
                executor.submit(run_with_tenant_context(check_context))
                for _ in range(10)
            ]
            results = [f.result() for f in futures]
    
    assert all(tid == "thread_tenant" for tid in results)


def test_require_tenant_strict_mode():
    """Test require_tenant raises when context not set in strict mode."""
    # No context set
    assert current_tenant() is None
    
    # Strict mode should raise
    with pytest.raises(RuntimeError, match="TenantContext required"):
        require_tenant(strict=True)
    
    # Non-strict returns default
    ctx = require_tenant(strict=False)
    assert ctx.tenant_id == "default"
    assert ctx.workspace_id == "main"


def test_require_tenant_with_context():
    """Test require_tenant returns context when set."""
    ctx = TenantContext("req_tenant", "req_workspace")
    
    with with_tenant(ctx):
        result = require_tenant(strict=True)
        assert result == ctx


def test_backward_compat_aliases():
    """Test backward-compatible tenant/workspace aliases."""
    # Old style with tenant= and workspace=
    ctx = TenantContext(tenant="old_tenant", workspace="old_workspace")
    assert ctx.tenant_id == "old_tenant"
    assert ctx.workspace_id == "old_workspace"
    assert ctx.tenant == "old_tenant"  # alias property
    assert ctx.workspace == "old_workspace"  # alias property
    
    # New style
    ctx2 = TenantContext("new_tenant", "new_workspace")
    assert ctx2.tenant == "new_tenant"
    assert ctx2.workspace == "new_workspace"


@pytest.mark.asyncio
async def test_mixed_async_sync():
    """Test context works across async/sync boundaries."""
    ctx = TenantContext("mixed_tenant", "mixed_workspace")
    
    def sync_check():
        return current_tenant().tenant_id
    
    async def async_check():
        await asyncio.sleep(0.01)
        # Call sync function from async
        result = await asyncio.to_thread(run_with_tenant_context, sync_check)
        return result
    
    with with_tenant(ctx):
        result = await async_check()
    
    assert result == "mixed_tenant"
