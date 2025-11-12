"""Agent pooling for performance optimization.

This module implements agent instance pooling to reduce startup time and improve
performance by reusing pre-warmed agent instances across requests.

Key Features:
- Pre-warmed agent instances ready for immediate use
- Configurable pool size and TTL
- Tenant-aware isolation
- Automatic cleanup of stale instances
- Metrics integration for monitoring

Usage:
    from platform.cache.agent_pool import AgentPool

    pool = AgentPool(max_size=10, warmup=True)

    async with pool.acquire("analyst_agent") as agent:
        result = await agent.execute(task)
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import structlog

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from crewai import Agent
logger = structlog.get_logger(__name__)


class PooledAgent:
    """Wrapper for pooled agent instances with metadata tracking.

    This class wraps agent instances with creation time, usage count,
    and health status for pool management.
    """

    def __init__(self, agent: Agent, agent_type: str, tenant_id: str):
        """Initialize pooled agent.

        Args:
            agent: The CrewAI agent instance
            agent_type: Type/name of the agent (e.g., "analyst_agent")
            tenant_id: Tenant identifier for isolation
        """
        self.agent = agent
        self.agent_type = agent_type
        self.tenant_id = tenant_id
        self.created_at = time.time()
        self.last_used = time.time()
        self.usage_count = 0
        self.is_healthy = True

    def mark_used(self) -> None:
        """Mark agent as recently used."""
        self.last_used = time.time()
        self.usage_count += 1

    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if agent is stale and should be replaced.

        Args:
            max_age_seconds: Maximum age before considering stale

        Returns:
            True if agent should be replaced
        """
        return (time.time() - self.created_at) > max_age_seconds

    def time_since_used(self) -> float:
        """Get seconds since last use.

        Returns:
            Seconds since last usage
        """
        return time.time() - self.last_used


class AgentPool:
    """Pool for managing reusable agent instances.

    This pool maintains pre-warmed agent instances to reduce startup time
    and improve performance by avoiding repeated agent initialization.

    Features:
    - Configurable pool size per agent type
    - Automatic cleanup of stale instances
    - Tenant-aware isolation
    - Health monitoring and metrics
    - Async context manager support
    """

    def __init__(
        self,
        max_size: int = 10,
        warmup: bool = True,
        max_age_seconds: float = 3600.0,  # 1 hour
        cleanup_interval: float = 300.0,  # 5 minutes
    ):
        """Initialize agent pool.

        Args:
            max_size: Maximum number of agents per type per tenant
            warmup: Whether to pre-warm agents on startup
            max_age_seconds: Maximum age before replacing agents
            cleanup_interval: How often to run cleanup (seconds)
        """
        self.max_size = max_size
        self.warmup = warmup
        self.max_age_seconds = max_age_seconds
        self.cleanup_interval = cleanup_interval

        # Pool structure: tenant_id -> agent_type -> list[PooledAgent]
        self._pools: dict[str, dict[str, list[PooledAgent]]] = defaultdict(lambda: defaultdict(list))

        # Agent creation functions: agent_type -> factory function
        self._factories: dict[str, callable] = {}

        self.metrics = get_metrics()
        self._cleanup_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

        logger.info(
            "agent_pool_initialized",
            max_size=max_size,
            warmup=warmup,
            max_age_seconds=max_age_seconds,
            cleanup_interval=cleanup_interval,
        )

        if warmup:
            # Start cleanup task only if we have a running event loop
            try:
                asyncio.get_running_loop()
                self._start_cleanup_task()
            except RuntimeError:
                # No event loop running, skip cleanup task for now
                # It will be started when acquire() is first called in async context
                logger.debug("skipping_cleanup_task_no_event_loop")

    def register_factory(self, agent_type: str, factory: callable) -> None:
        """Register an agent factory function.

        Args:
            agent_type: Type/name of the agent
            factory: Function that creates agent instances
        """
        self._factories[agent_type] = factory
        logger.info("agent_factory_registered", agent_type=agent_type)

        if self.warmup:
            # Pre-warm some instances
            try:
                task = asyncio.create_task(self._warmup_agents(agent_type))
                # Store task reference to prevent garbage collection
                if not hasattr(self, "_warmup_tasks"):
                    self._warmup_tasks = set()
                self._warmup_tasks.add(task)
                task.add_done_callback(self._warmup_tasks.discard)
            except RuntimeError:
                # No event loop running, skip warmup
                logger.debug("skipping_warmup_no_event_loop", agent_type=agent_type)

    async def _warmup_agents(self, agent_type: str, count: int = 3) -> None:
        """Pre-warm agent instances.

        Args:
            agent_type: Type of agent to warm up
            count: Number of instances to create
        """
        if agent_type not in self._factories:
            logger.warning("cannot_warmup_unknown_agent_type", agent_type=agent_type)
            return

        tenant_id = current_tenant()
        created = 0

        for _ in range(count):
            try:
                agent = await self._create_agent(agent_type, tenant_id)
                if agent:
                    self._add_to_pool(agent, agent_type, tenant_id)
                    created += 1
            except Exception as e:
                logger.warning("agent_warmup_failed", agent_type=agent_type, error=str(e))

        logger.info("agent_warmup_completed", agent_type=agent_type, created=created)

    async def _create_agent(self, agent_type: str, tenant_id: str) -> PooledAgent | None:
        """Create a new agent instance.

        Args:
            agent_type: Type of agent to create
            tenant_id: Tenant identifier

        Returns:
            PooledAgent instance or None if creation failed
        """
        if agent_type not in self._factories:
            logger.error("unknown_agent_type", agent_type=agent_type)
            return None

        start_time = time.time()
        try:
            factory = self._factories[agent_type]
            agent = await factory() if asyncio.iscoroutinefunction(factory) else factory()

            creation_time = time.time() - start_time
            self.metrics.observe_histogram(
                "agent_creation_duration_seconds",
                creation_time,
                labels={"agent_type": agent_type, "tenant_id": tenant_id},
            )

            pooled_agent = PooledAgent(agent, agent_type, tenant_id)
            logger.debug(
                "agent_created",
                agent_type=agent_type,
                tenant_id=tenant_id,
                creation_time_seconds=creation_time,
            )
            return pooled_agent

        except Exception as e:
            creation_time = time.time() - start_time
            logger.error(
                "agent_creation_failed",
                agent_type=agent_type,
                tenant_id=tenant_id,
                error=str(e),
                creation_time_seconds=creation_time,
            )
            self.metrics.increment_counter(
                "agent_creation_errors_total",
                labels={"agent_type": agent_type, "tenant_id": tenant_id, "error_type": type(e).__name__},
            )
            return None

    def _add_to_pool(self, agent: PooledAgent, agent_type: str, tenant_id: str) -> None:
        """Add agent to pool.

        Args:
            agent: PooledAgent instance
            agent_type: Type of agent
            tenant_id: Tenant identifier
        """
        pool = self._pools[tenant_id][agent_type]
        if len(pool) < self.max_size:
            pool.append(agent)
            self.metrics.gauge(
                "agent_pool_size",
                len(pool),
                labels={"agent_type": agent_type, "tenant_id": tenant_id},
            )
            logger.debug(
                "agent_added_to_pool",
                agent_type=agent_type,
                tenant_id=tenant_id,
                pool_size=len(pool),
            )
        else:
            logger.debug(
                "pool_full_discarding_agent",
                agent_type=agent_type,
                tenant_id=tenant_id,
                pool_size=len(pool),
            )

    @asynccontextmanager
    async def acquire(self, agent_type: str) -> AsyncGenerator[Agent, None]:
        """Acquire an agent from the pool.

        Args:
            agent_type: Type of agent to acquire

        Yields:
            Agent instance from pool

        Raises:
            RuntimeError: If no agent available and creation fails
        """
        tenant_id = current_tenant()
        agent = await self._acquire_agent(agent_type, tenant_id)

        if agent is None:
            raise RuntimeError(f"Failed to acquire agent of type: {agent_type}")

        try:
            agent.mark_used()
            self.metrics.increment_counter(
                "agent_acquisitions_total",
                labels={"agent_type": agent_type, "tenant_id": tenant_id},
            )
            yield agent.agent
        finally:
            # Return agent to pool
            self._return_agent(agent, agent_type, tenant_id)

    async def _acquire_agent(self, agent_type: str, tenant_id: str) -> PooledAgent | None:
        """Acquire an agent from the pool, creating if necessary.

        Args:
            agent_type: Type of agent to acquire
            tenant_id: Tenant identifier

        Returns:
            PooledAgent instance or None
        """
        async with self._lock:
            pool = self._pools[tenant_id][agent_type]

            # Try to find a healthy, non-stale agent
            for agent in pool:
                if agent.is_healthy and not agent.is_stale(self.max_age_seconds):
                    pool.remove(agent)
                    return agent

            # No suitable agent found, try to create one
            agent = await self._create_agent(agent_type, tenant_id)
            return agent

    def _return_agent(self, agent: PooledAgent, agent_type: str, tenant_id: str) -> None:
        """Return agent to pool.

        Args:
            agent: Agent to return
            agent_type: Type of agent
            tenant_id: Tenant identifier
        """
        # Only return healthy agents
        if agent.is_healthy:
            self._add_to_pool(agent, agent_type, tenant_id)
        else:
            logger.debug(
                "discarding_unhealthy_agent",
                agent_type=agent_type,
                tenant_id=tenant_id,
                usage_count=agent.usage_count,
            )

    def _start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up stale agents."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_stale_agents()
            except Exception as e:
                logger.error("cleanup_task_error", error=str(e))

    async def _cleanup_stale_agents(self) -> None:
        """Remove stale agents from all pools."""
        async with self._lock:
            cleaned_total = 0

            for tenant_id, tenant_pools in self._pools.items():
                for agent_type, pool in tenant_pools.items():
                    original_size = len(pool)
                    # Keep only healthy, non-stale agents
                    pool[:] = [agent for agent in pool if agent.is_healthy and not agent.is_stale(self.max_age_seconds)]
                    cleaned = original_size - len(pool)
                    if cleaned > 0:
                        cleaned_total += cleaned
                        self.metrics.gauge(
                            "agent_pool_size",
                            len(pool),
                            labels={"agent_type": agent_type, "tenant_id": tenant_id},
                        )
                        logger.debug(
                            "cleaned_stale_agents",
                            agent_type=agent_type,
                            tenant_id=tenant_id,
                            cleaned=cleaned,
                            remaining=len(pool),
                        )

            if cleaned_total > 0:
                logger.info("stale_agent_cleanup_completed", cleaned_total=cleaned_total)

    def get_stats(self, tenant_id: str | None = None) -> dict[str, Any]:
        """Get pool statistics.

        Args:
            tenant_id: Specific tenant to get stats for, or None for all

        Returns:
            Dictionary with pool statistics
        """
        stats = {
            "total_agents": 0,
            "pools": {},
            "tenants": list(self._pools.keys()) if tenant_id is None else [tenant_id],
        }

        tenants_to_check = [tenant_id] if tenant_id else self._pools.keys()

        for tid in tenants_to_check:
            if tid in self._pools:
                tenant_stats = {}
                for agent_type, pool in self._pools[tid].items():
                    tenant_stats[agent_type] = {
                        "count": len(pool),
                        "healthy": sum(1 for a in pool if a.is_healthy),
                        "stale": sum(1 for a in pool if a.is_stale(self.max_age_seconds)),
                        "avg_usage": sum(a.usage_count for a in pool) / len(pool) if pool else 0,
                        "oldest_age": max((time.time() - a.created_at for a in pool), default=0),
                    }
                    stats["total_agents"] += len(pool)
                stats["pools"][tid] = tenant_stats

        return stats

    async def shutdown(self) -> None:
        """Shutdown the agent pool and cleanup resources."""
        logger.info("agent_pool_shutdown_started")

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        # Clear all pools
        self._pools.clear()
        self._factories.clear()

        logger.info("agent_pool_shutdown_completed")


# Global agent pool instance
_pool: AgentPool | None = None


def get_agent_pool() -> AgentPool:
    """Get the global agent pool instance.

    Returns:
        The singleton AgentPool instance
    """
    global _pool
    if _pool is None:
        _pool = AgentPool()
    return _pool
