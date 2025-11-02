"""Async execution paths for OpenRouter routing.

This module provides async versions of the OpenRouter execution paths
for improved concurrency and performance.
"""
from __future__ import annotations
import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any
import aiohttp
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
if TYPE_CHECKING:
    from .service import OpenRouterService
    from .state import RouteState
log = logging.getLogger(__name__)

class AsyncConnectionPool:
    """Async HTTP connection pool for OpenRouter API requests."""

    def __init__(self, pool_size: int=10, timeout: int=30, max_retries: int=3) -> None:
        """Initialize async connection pool.

        Args:
            pool_size: Maximum number of connections
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self._pool_size = pool_size
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._max_retries = max_retries
        self._connector: aiohttp.TCPConnector | None = None
        self._session: aiohttp.ClientSession | None = None
        self._feature_flags = FeatureFlags()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create async HTTP session."""
        if self._session is None or self._session.closed:
            if self._feature_flags.ENABLE_OPENROUTER_CONNECTION_POOLING:
                self._connector = aiohttp.TCPConnector(limit=self._pool_size, limit_per_host=self._pool_size, keepalive_timeout=30, enable_cleanup_closed=True)
            else:
                self._connector = aiohttp.TCPConnector()
            self._session = aiohttp.ClientSession(connector=self._connector, timeout=self._timeout)
            log.debug('Created async HTTP session with connection pooling')
        return self._session

    async def post(self, url: str, headers: dict[str, str] | None=None, json_data: dict[str, Any] | None=None, **kwargs: Any) -> aiohttp.ClientResponse | None:
        """Make async POST request.

        Args:
            url: The URL to make the request to
            headers: HTTP headers
            json_data: JSON payload
            **kwargs: Additional request parameters

        Returns:
            Response object or None if request failed
        """
        session = await self._get_session()
        for attempt in range(self._max_retries + 1):
            try:
                async with session.post(url, headers=headers, json=json_data, **kwargs) as response:
                    if response.status < 400:
                        log.debug('Async request successful: %s', response.status)
                        return response
                    else:
                        log.warning('Async request failed: %s', response.status)
                        if attempt < self._max_retries:
                            await asyncio.sleep(0.3 * 2 ** attempt)
                            continue
                        return response
            except asyncio.TimeoutError:
                log.error('Async request timeout (attempt %d/%d)', attempt + 1, self._max_retries + 1)
                if attempt < self._max_retries:
                    await asyncio.sleep(0.3 * 2 ** attempt)
                    continue
                return None
            except aiohttp.ClientError as e:
                log.error('Async request client error: %s', e)
                if attempt < self._max_retries:
                    await asyncio.sleep(0.3 * 2 ** attempt)
                    continue
                return None
        return None

    async def close(self) -> None:
        """Close the async session and connector."""
        if self._session and (not self._session.closed):
            await self._session.close()
            self._session = None
            log.debug('Closed async HTTP session')
        if self._connector:
            await self._connector.close()
            self._connector = None

class AsyncExecutor:
    """Handles async execution of OpenRouter requests."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize async executor.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._connection_pool = AsyncConnectionPool()
        self._feature_flags = FeatureFlags()

    async def execute_online_async(self, state: RouteState) -> dict[str, Any]:
        """Execute online request asynchronously.

        Args:
            state: Route state containing request information

        Returns:
            Response dictionary
        """
        if not self._feature_flags.ENABLE_OPENROUTER_ASYNC_ROUTING:
            return self._execute_online_sync_fallback(state)
        try:
            payload = {'model': state.model, 'messages': [{'role': 'user', 'content': state.prompt}]}
            if state.provider_opts:
                payload['provider'] = state.provider_opts
            headers = {'Authorization': f'Bearer {self._service.api_key}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
            settings = self._service.get_settings()
            if hasattr(settings, 'openrouter_referer') and settings.openrouter_referer:
                headers['Referer'] = str(settings.openrouter_referer)
                headers['HTTP-Referer'] = str(settings.openrouter_referer)
            if hasattr(settings, 'openrouter_title') and settings.openrouter_title:
                headers['X-Title'] = str(settings.openrouter_title)
            response = await self._connection_pool.post(url='https://openrouter.ai/api/v1/chat/completions', headers=headers, json_data=payload)
            if response is None:
                return {'status': 'error', 'error': 'Request failed', 'model': state.model, 'tokens': state.tokens_in, 'provider': state.provider_opts}
            data = await response.json()
            message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            latency_ms = (time.perf_counter() - state.start_time) * 1000
            tokens_out = self._service.prompt_engine.count_tokens(message, state.model)
            self._update_learning_engine(state, latency_ms)
            result = {'status': 'success', 'model': state.model, 'response': message, 'tokens': state.tokens_in, 'provider': state.provider_opts}
            self._record_metrics(state, latency_ms, tokens_out, True)
            return result
        except Exception as e:
            log.error('Async execution failed: %s', e)
            return {'status': 'error', 'error': str(e), 'model': state.model, 'tokens': state.tokens_in, 'provider': state.provider_opts}

    def _execute_online_sync_fallback(self, state: RouteState) -> dict[str, Any]:
        """Fallback to synchronous execution when async is disabled."""
        from .execution import execute_online
        try:
            return execute_online(self._service, state)
        except Exception as e:
            log.error('Sync fallback execution failed: %s', e)
            return {'status': 'error', 'error': str(e), 'model': state.model, 'tokens': state.tokens_in, 'provider': state.provider_opts}

    def _update_learning_engine(self, state: RouteState, latency_ms: float) -> None:
        """Update the learning engine with performance metrics."""
        try:
            settings = self._service.get_settings()
            w_cost = getattr(settings, 'reward_cost_weight', 0.5)
            w_lat = getattr(settings, 'reward_latency_weight', 0.5)
            if w_cost == 0.0 and w_lat == 0.0:
                w_cost = w_lat = 0.5
            norm = w_cost + w_lat
            w_cost /= norm
            w_lat /= norm
            cost_norm = min(1.0, state.projected_cost / max(state.projected_cost, 1e-09))
            lat_window = getattr(settings, 'reward_latency_ms_window', 2000)
            lat_norm = min(1.0, latency_ms / max(lat_window, 1.0))
            reward = max(0.0, 1.0 - w_cost * cost_norm - w_lat * lat_norm)
            self._service.learning.update(state.task_type, state.model, reward=reward)
        except Exception as e:
            log.debug('Learning engine update failed: %s', e)

    def _record_metrics(self, state: RouteState, latency_ms: float, tokens_out: int, success: bool) -> None:
        """Record metrics for the request."""
        try:
            from platform.observability import metrics
            labels = state.labels()
            metrics.LLM_MODEL_SELECTED.labels(**labels, task=state.task_type, model=state.model, provider=state.provider_family).inc()
            metrics.LLM_ESTIMATED_COST.labels(**labels, model=state.model, provider=state.provider_family).observe(state.projected_cost)
            metrics.LLM_LATENCY.labels(**labels).observe(latency_ms)
        except Exception as e:
            log.debug('Metrics recording failed: %s', e)

    async def close(self) -> None:
        """Close the async executor and cleanup resources."""
        await self._connection_pool.close()

class AsyncRouteManager:
    """Manages async routing operations."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize async route manager.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._executor = AsyncExecutor(service)
        self._feature_flags = FeatureFlags()

    async def route_async(self, prompt: str, task_type: str='general', model: str | None=None, provider_opts: dict[str, Any] | None=None, **kwargs: Any) -> dict[str, Any]:
        """Route a prompt asynchronously.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            Response dictionary
        """
        if not self._feature_flags.ENABLE_OPENROUTER_ASYNC_ROUTING:
            result = self._service.route(prompt, task_type, model, provider_opts, **kwargs)
            return result.data if result.success else {'status': 'error', 'error': result.error}
        try:
            from .context import prepare_route_state
            state = prepare_route_state(self._service, prompt, task_type, model, provider_opts)
            if state.offline_mode:
                from .execution import execute_offline
                return execute_offline(self._service, state)
            return await self._executor.execute_online_async(state)
        except Exception as e:
            log.error('Async routing failed: %s', e)
            return {'status': 'error', 'error': str(e), 'model': model or 'unknown', 'tokens': 0, 'provider': provider_opts or {}}

    async def close(self) -> None:
        """Close the async route manager."""
        await self._executor.close()
_async_route_manager: AsyncRouteManager | None = None

def get_async_route_manager(service: OpenRouterService) -> AsyncRouteManager:
    """Get or create async route manager for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        AsyncRouteManager instance
    """
    global _async_route_manager
    if _async_route_manager is None:
        _async_route_manager = AsyncRouteManager(service)
    return _async_route_manager

async def close_async_route_manager() -> None:
    """Close the global async route manager."""
    global _async_route_manager
    if _async_route_manager:
        await _async_route_manager.close()
        _async_route_manager = None