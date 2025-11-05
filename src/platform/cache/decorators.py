"""Caching decorators for easy integration with the advanced caching system.

This module provides decorators that make it simple to add caching to any function
with support for dependencies, TTL, and different cache types.
"""
from __future__ import annotations

import functools
import hashlib
import inspect
import logging
from collections.abc import Callable
from platform.cache.cache_service import get_cache_service
from typing import Any, TypeVar


logger = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])

def _make_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str='') -> str:
    """Generate a deterministic cache key from function call."""
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    key_parts = [prefix, func.__module__, func.__qualname__]
    for name, value in sorted(bound_args.arguments.items()):
        if name != 'self':
            key_parts.append(f'{name}={value!r}')
    key_string = '|'.join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
    return f'{prefix}{func.__name__}:{key_hash}'

def cached(ttl: int | None=None, cache_type: str='main', dependencies: list[str] | None=None, key_prefix: str='', condition: Callable[[], bool] | None=None) -> Callable[[F], F]:
    """Decorator for caching synchronous function results.

    Args:
        ttl: Time to live in seconds (uses cache default if None)
        cache_type: Type of cache to use ('main', 'llm', 'api')
        dependencies: List of cache keys this result depends on
        key_prefix: Prefix for cache keys
        condition: Function that returns True if caching should be used

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if condition and (not condition()):
                return func(*args, **kwargs)
            cache = get_cache_service()
            cache_key = _make_cache_key(func, args, kwargs, key_prefix)
            cached_result = cache.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f'Cache hit for {func.__name__}: {cache_key}')
                return cached_result
            result = func(*args, **kwargs)
            deps = set(dependencies) if dependencies else None
            success = cache.set(cache_key, result, ttl, deps, cache_type)
            if success:
                logger.debug(f'Cached result for {func.__name__}: {cache_key}')
            else:
                logger.warning(f'Failed to cache result for {func.__name__}: {cache_key}')
            return result
        return wrapper
    return decorator

def cached_async(ttl: int | None=None, cache_type: str='main', dependencies: list[str] | None=None, key_prefix: str='', condition: Callable[[], bool] | None=None) -> Callable[[F], F]:
    """Decorator for caching asynchronous function results.

    Args:
        ttl: Time to live in seconds (uses cache default if None)
        cache_type: Type of cache to use ('main', 'llm', 'api')
        dependencies: List of cache keys this result depends on
        key_prefix: Prefix for cache keys
        condition: Function that returns True if caching should be used

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if condition and (not condition()):
                return await func(*args, **kwargs)
            cache = get_cache_service()
            cache_key = _make_cache_key(func, args, kwargs, key_prefix)
            cached_result = await cache.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f'Cache hit for {func.__name__}: {cache_key}')
                return cached_result
            result = await func(*args, **kwargs)
            deps = set(dependencies) if dependencies else None
            success = await cache.set(cache_key, result, ttl, deps, cache_type)
            if success:
                logger.debug(f'Cached result for {func.__name__}: {cache_key}')
            else:
                logger.warning(f'Failed to cache result for {func.__name__}: {cache_key}')
            return result
        return wrapper
    return decorator

def cache_invalidate(keys: list[str] | Callable[..., list[str]], cache_type: str='main', cascade: bool=True) -> Callable[[F], F]:
    """Decorator that invalidates cache keys after function execution.

    Args:
        keys: List of cache keys to invalidate, or function that returns keys
        cache_type: Type of cache to use ('main', 'llm', 'api')
        cascade: Whether to cascade invalidation to dependents

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache = get_cache_service()
            invalidate_keys = keys(*args, **kwargs) if callable(keys) else keys
            for key in invalidate_keys:
                success = cache.delete(key, cascade, cache_type)
                if success:
                    logger.debug(f'Invalidated cache key: {key}')
                else:
                    logger.warning(f'Failed to invalidate cache key: {key}')
            return result
        return wrapper
    return decorator

def cache_invalidate_async(keys: list[str] | Callable[..., list[str]], cache_type: str='main', cascade: bool=True) -> Callable[[F], F]:
    """Decorator that invalidates cache keys after async function execution.

    Args:
        keys: List of cache keys to invalidate, or function that returns keys
        cache_type: Type of cache to use ('main', 'llm', 'api')
        cascade: Whether to cascade invalidation to dependents

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            cache = get_cache_service()
            invalidate_keys = keys(*args, **kwargs) if callable(keys) else keys
            for key in invalidate_keys:
                success = await cache.delete(key, cascade, cache_type)
                if success:
                    logger.debug(f'Invalidated cache key: {key}')
                else:
                    logger.warning(f'Failed to invalidate cache key: {key}')
            return result
        return wrapper
    return decorator

def llm_cached(model_param: str='model', prompt_param: str='prompt', ttl: int | None=None, dependencies: list[str] | None=None) -> Callable[[F], F]:
    """Specialized decorator for LLM function caching.

    Args:
        model_param: Parameter name for the model
        prompt_param: Parameter name for the prompt
        ttl: Time to live in seconds
        dependencies: List of cache keys this result depends on

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            model = bound_args.arguments.get(model_param, 'unknown')
            prompt = bound_args.arguments.get(prompt_param, '')
            key_content = f'{model}|{prompt}'
            key_hash = hashlib.sha256(key_content.encode()).hexdigest()[:16]
            cache_key = f'llm:{model}:{key_hash}'
            cached_result = await cache.get(cache_key, 'llm')
            if cached_result is not None:
                logger.debug(f'LLM cache hit for {func.__name__}: {cache_key}')
                return cached_result
            result = await func(*args, **kwargs)
            deps = set(dependencies) if dependencies else None
            success = await cache.set(cache_key, result, ttl, deps, 'llm')
            if success:
                logger.debug(f'Cached LLM result for {func.__name__}: {cache_key}')
            else:
                logger.warning(f'Failed to cache LLM result for {func.__name__}: {cache_key}')
            return result
        return wrapper
    return decorator

def api_cached(ttl: int=300, dependencies: list[str] | None=None) -> Callable[[F], F]:
    """Convenience decorator for API response caching."""
    return cached(ttl=ttl, cache_type='api', dependencies=dependencies, key_prefix='api:')

def api_cached_async(ttl: int=300, dependencies: list[str] | None=None) -> Callable[[F], F]:
    """Convenience decorator for async API response caching."""
    return cached_async(ttl=ttl, cache_type='api', dependencies=dependencies, key_prefix='api:')
__all__ = ['api_cached', 'api_cached_async', 'cache_invalidate', 'cache_invalidate_async', 'cached', 'cached_async', 'llm_cached']
