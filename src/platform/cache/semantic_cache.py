"""
Semantic LLM caching system using GPTCache for intelligent response reuse.

This module implements advanced semantic caching that can recognize similar prompts
and reuse responses, providing significant cost savings and performance improvements.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from platform.config.configuration import get_config
from platform.observability import metrics
from typing import Any, cast


try:
    from gptcache import Cache
    from gptcache.embedding.openai import OpenAI as OpenAIEmbedding
    from gptcache.embedding.string import to_embeddings as string_to_embeddings
    from gptcache.manager import CacheBase, VectorBase, get_data_manager
    from gptcache.manager.scalar_data.sql_storage import SQLStorage
    from gptcache.processor.post import first
    from gptcache.processor.pre import get_prompt
    from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation
    GPTCACHE_AVAILABLE = True
except Exception:
    GPTCACHE_AVAILABLE = False

    class _CacheStub:

        def init(self, *args, **kwargs) -> None:
            return None

        def get(self, *args, **kwargs):
            return None

        def set(self, *args, **kwargs) -> None:
            return None

    def _noop(*args, **kwargs):
        return None

    class _OpenAIEmbeddingStub:

        def __init__(self, *args, **kwargs) -> None:
            pass
    Cache = _CacheStub

    def _cache_base_stub(*args, **kwargs):
        return object()

    def _vector_base_stub(*args, **kwargs):
        return object()

    def _get_data_manager_stub(*args, **kwargs):
        return object()
    CacheBase = _cache_base_stub
    VectorBase = _vector_base_stub
    get_data_manager = _get_data_manager_stub
    SQLStorage = object
    get_prompt = _noop
    first = _noop
    SearchDistanceEvaluation = _OpenAIEmbeddingStub
    OpenAIEmbedding = _OpenAIEmbeddingStub
    string_to_embeddings = _noop
logger = logging.getLogger(__name__)
try:
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

@dataclass
class CacheStats:
    """Statistics for semantic cache performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_stores: int = 0
    total_cost_saved: float = 0.0
    average_similarity: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.cache_hits / self.total_requests if self.total_requests > 0 else 0.0

class SemanticCacheInterface(ABC):
    """Abstract interface for semantic caching implementations."""

    @abstractmethod
    def get(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """Retrieve cached response for semantically similar prompt."""

    @abstractmethod
    def set(self, prompt: str, model: str, response: dict[str, Any], **kwargs) -> None:
        """Store response in semantic cache."""

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""

class GPTCacheSemanticCache(SemanticCacheInterface):
    """GPTCache-based semantic caching with configurable similarity thresholds."""

    def __init__(self, similarity_threshold: float=0.8, embedding_model: str='text-embedding-ada-002', cache_dir: str='./cache', max_cache_size: int=10000, enable_vector_cache: bool=True):
        """Initialize semantic cache with GPTCache.

        Args:
            similarity_threshold: Minimum similarity for cache hits (0.0-1.0)
            embedding_model: Model for generating semantic embeddings
            cache_dir: Directory for persistent cache storage
            max_cache_size: Maximum number of cached items
            enable_vector_cache: Whether to use vector-based similarity search
        """
        if not GPTCACHE_AVAILABLE:
            raise ImportError('GPTCache not available - install with: pip install gptcache')
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.enable_vector_cache = enable_vector_cache
        self.stats = CacheStats()
        self.cache: Any = Cache()
        self._cache_get_fn: Any | None = None
        self._cache_set_fn: Any | None = None
        self._initialize_cache()
        logger.info(f'Semantic cache initialized with threshold {similarity_threshold}')

    def _initialize_cache(self):
        """Initialize GPTCache with appropriate managers and configurations."""
        try:
            config = get_config()
            embedding_func = None
            if hasattr(config, 'openai_api_key') and config.openai_api_key:
                use_openai_embedding = False
                try:
                    import openai as _openai
                    if hasattr(_openai, 'api_base'):
                        use_openai_embedding = True
                    else:
                        logger.info('OpenAI v1 client detected; skipping GPTCache OpenAI embeddings and using string embeddings')
                except Exception:
                    use_openai_embedding = False
                if use_openai_embedding:
                    try:
                        embedding_func = OpenAIEmbedding(model=self.embedding_model)
                        logger.info('Using OpenAI embeddings for semantic cache')
                    except Exception as e:
                        logger.warning(f'OpenAI embedding failed: {e}, falling back to string embeddings')
            if embedding_func is None:
                embedding_func = string_to_embeddings
                logger.info('Using string embeddings for semantic cache')
            cache_path = Path(self.cache_dir).expanduser().resolve()
            cache_path.mkdir(parents=True, exist_ok=True)
            sql_db_path = cache_path / ('gptcache.db' if self.enable_vector_cache else 'gptcache_simple.db')
            faiss_index_path = cache_path / 'faiss.index'
            use_vector_cache = bool(self.enable_vector_cache and FAISS_AVAILABLE)
            if self.enable_vector_cache and (not FAISS_AVAILABLE):
                logger.info('FAISS not available; disabling vector cache and using scalar-only cache')
            if use_vector_cache:
                data_manager = get_data_manager(CacheBase('sqlite', sql_url=f'sqlite:///{sql_db_path}'), VectorBase('faiss', dimension=384, index_path=str(faiss_index_path)), max_size=self.max_cache_size, clean_size=int(self.max_cache_size * 0.2))
                similarity_evaluation = SearchDistanceEvaluation()
            else:
                data_manager = get_data_manager(CacheBase('sqlite', sql_url=f'sqlite:///{sql_db_path}'), max_size=self.max_cache_size)
                similarity_evaluation = None
            self.cache.init(pre_embedding_func=get_prompt, embedding_func=embedding_func, data_manager=data_manager, similarity_evaluation=similarity_evaluation, post_process_messages_func=first)
            api_pairs = [('get', 'set'), ('query', 'put'), ('search', 'insert')]
            for gm, sm in api_pairs:
                get_fn = getattr(self.cache, gm, None)
                set_fn = getattr(self.cache, sm, None)
                if callable(get_fn) and callable(set_fn):
                    self._cache_get_fn = get_fn
                    self._cache_set_fn = set_fn
                    logger.info(f'Semantic cache using GPTCache API: {gm}/{sm}')
                    break
            if self._cache_get_fn is None or self._cache_set_fn is None:
                logger.info('GPTCache API not recognized; using fallback simple cache')
                self._initialize_simple_cache()
                return
        except Exception as e:
            logger.error(f'Failed to initialize GPTCache: {e}')
            self._initialize_simple_cache()

    def _initialize_simple_cache(self):
        """Fallback to simple in-memory cache if GPTCache initialization fails."""
        logger.info('Initializing simple fallback cache')
        self.simple_cache = {}
        self.cache = None

    def _build_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Build a stable cache key from prompt and parameters."""
        key_data = {'prompt': prompt.strip(), 'model': model, **{k: v for k, v in kwargs.items() if k in ['temperature', 'max_tokens', 'top_p']}}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """Retrieve cached response for semantically similar prompt."""
        self.stats.total_requests += 1
        try:
            if self.cache is not None and self._cache_get_fn is not None:
                ns = kwargs.get('namespace')
                ns_prefix = f'[ns:{ns}]\n' if ns else ''
                prompt_ns = f'{ns_prefix}{prompt}'
                model_scoped = f'{model}@@ns={ns}' if ns else model
                try:
                    result_obj = self._cache_get_fn(prompt_ns, model=model_scoped)
                except TypeError:
                    result_obj = self._cache_get_fn(prompt_ns)
                if result_obj is not None:
                    self.stats.cache_hits += 1
                    metrics.LLM_CACHE_HITS.labels(**metrics.label_ctx(), model=model, provider='semantic').inc()
                    estimated_cost_saved = 0.001
                    self.stats.total_cost_saved += estimated_cost_saved
                    logger.debug(f'Semantic cache hit for model {model}')
                    return cast('dict[str, Any]', result_obj) if isinstance(result_obj, dict) else None
                else:
                    self.stats.cache_misses += 1
                    try:
                        metrics.LLM_CACHE_MISSES.labels(**metrics.label_ctx(), model=model, provider='semantic').inc()
                    except Exception:
                        pass
                    return None
            else:
                ns = kwargs.get('namespace')
                model_scoped = f'{model}@@ns={ns}' if ns else model
                cache_key = self._build_cache_key(prompt, model_scoped, **kwargs)
                result = self.simple_cache.get(cache_key)
                if result is not None:
                    if result.get('expires_at', 0) > time.time():
                        self.stats.cache_hits += 1
                        return result.get('data')
                    else:
                        del self.simple_cache[cache_key]
                self.stats.cache_misses += 1
                try:
                    metrics.LLM_CACHE_MISSES.labels(**metrics.label_ctx(), model=model, provider='semantic').inc()
                except Exception:
                    pass
                return None
        except Exception as e:
            logger.error(f'Cache get error: {e}')
            self.stats.cache_misses += 1
            try:
                metrics.LLM_CACHE_MISSES.labels(**metrics.label_ctx(), model=model, provider='semantic').inc()
            except Exception:
                pass
            return None

    def set(self, prompt: str, model: str, response: dict[str, Any], **kwargs) -> None:
        """Store response in semantic cache."""
        try:
            if self.cache is not None and self._cache_set_fn is not None:
                ns = kwargs.get('namespace')
                ns_prefix = f'[ns:{ns}]\n' if ns else ''
                prompt_ns = f'{ns_prefix}{prompt}'
                model_scoped = f'{model}@@ns={ns}' if ns else model
                try:
                    self._cache_set_fn(prompt_ns, response, model=model_scoped)
                except TypeError:
                    self._cache_set_fn(prompt_ns, response)
                self.stats.cache_stores += 1
                logger.debug(f'Stored response in semantic cache for model {model}')
            else:
                ns = kwargs.get('namespace')
                model_scoped = f'{model}@@ns={ns}' if ns else model
                cache_key = self._build_cache_key(prompt, model_scoped, **kwargs)
                self.simple_cache[cache_key] = {'data': response, 'expires_at': time.time() + 3600, 'stored_at': time.time()}
                self.stats.cache_stores += 1
                if len(self.simple_cache) > self.max_cache_size:
                    sorted_keys = sorted(self.simple_cache.keys(), key=lambda k: self.simple_cache[k].get('stored_at', 0))
                    for key in sorted_keys[:len(sorted_keys) - self.max_cache_size + 100]:
                        del self.simple_cache[key]
        except Exception as e:
            logger.error(f'Cache set error: {e}')

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self.stats

    def clear_cache(self):
        """Clear all cached data."""
        try:
            if self.cache is not None:
                self._initialize_cache()
            else:
                self.simple_cache.clear()
            self.stats = CacheStats()
            logger.info('Semantic cache cleared')
        except Exception as e:
            logger.error(f'Failed to clear cache: {e}')

class FallbackSemanticCache(SemanticCacheInterface):
    """Fallback semantic cache that uses simple string matching when GPTCache unavailable."""

    def __init__(self, ttl: int=3600):
        self.ttl = ttl
        self.cache: dict[str, dict[str, Any]] = {}
        self.stats = CacheStats()

    def _fuzzy_match(self, prompt1: str, prompt2: str) -> float:
        """Simple fuzzy matching based on word overlap."""
        words1 = set(prompt1.lower().split())
        words2 = set(prompt2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0

    def get(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """Retrieve cached response using simple fuzzy matching."""
        self.stats.total_requests += 1
        current_time = time.time()
        expired_keys = [key for key, value in self.cache.items() if value.get('expires_at', 0) < current_time]
        for key in expired_keys:
            del self.cache[key]
        ns = kwargs.get('namespace')
        ns_prefix = f'[ns:{ns}]\n' if ns else ''
        prompt_ns = f'{ns_prefix}{prompt}'
        best_match = None
        best_similarity = 0.0
        ns = kwargs.get('namespace')
        model_scoped = f'{model}@@ns={ns}' if ns else model
        for cached_prompt, cached_data in self.cache.items():
            if cached_data.get('model') == model_scoped:
                similarity = self._fuzzy_match(prompt_ns, cached_prompt)
                if similarity > best_similarity and similarity > 0.8:
                    best_match = cached_data
                    best_similarity = similarity
        if best_match:
            self.stats.cache_hits += 1
            self.stats.average_similarity = (self.stats.average_similarity * (self.stats.cache_hits - 1) + best_similarity) / self.stats.cache_hits
            return best_match.get('response')
        self.stats.cache_misses += 1
        try:
            metrics.LLM_CACHE_MISSES.labels(**metrics.label_ctx(), model=model, provider='semantic').inc()
        except Exception:
            pass
        return None

    def set(self, prompt: str, model: str, response: dict[str, Any], **kwargs) -> None:
        """Store response in fallback cache."""
        ns = kwargs.get('namespace')
        ns_prefix = f'[ns:{ns}]\n' if ns else ''
        prompt_ns = f'{ns_prefix}{prompt}'
        model_scoped = f'{model}@@ns={ns}' if ns else model
        self.cache[prompt_ns] = {'model': model_scoped, 'response': response, 'expires_at': time.time() + self.ttl, 'stored_at': time.time()}
        self.stats.cache_stores += 1

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self.stats

def create_semantic_cache(similarity_threshold: float=0.8, embedding_model: str='text-embedding-ada-002', cache_dir: str='./cache', fallback_enabled: bool=True, fallback_ttl_seconds: int=3600) -> SemanticCacheInterface:
    """Factory function to create appropriate semantic cache implementation.

    Args:
        similarity_threshold: Minimum similarity for cache hits
        embedding_model: Model for generating embeddings
        cache_dir: Directory for cache storage
        fallback_enabled: Whether to use fallback cache if GPTCache unavailable

    Returns:
        Configured semantic cache implementation
    """
    try:
        if GPTCACHE_AVAILABLE:
            return GPTCacheSemanticCache(similarity_threshold=similarity_threshold, embedding_model=embedding_model, cache_dir=cache_dir)
        elif fallback_enabled:
            import os as _os
            _explicit = (_os.getenv('ENABLE_SEMANTIC_CACHE') or '').lower() in {'1', 'true', 'yes'}
            if _explicit:
                logger.warning('GPTCache not available, using fallback semantic cache')
            else:
                logger.info('Semantic cache fallback active (GPTCache unavailable and feature not explicitly enabled)')
            return FallbackSemanticCache(ttl=fallback_ttl_seconds)
        else:
            raise ImportError('GPTCache required but not available')
    except Exception as e:
        if fallback_enabled:
            logger.warning(f'Failed to initialize semantic cache: {e}, using fallback')
            return FallbackSemanticCache(ttl=fallback_ttl_seconds)
        else:
            raise
_semantic_cache: SemanticCacheInterface | None = None

def get_semantic_cache() -> SemanticCacheInterface:
    """Get or create global semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        config = get_config()
        cache_dir = getattr(config, 'cache_dir', './cache')
        similarity_threshold = getattr(config, 'semantic_cache_threshold', 0.8)
        _semantic_cache = create_semantic_cache(similarity_threshold=similarity_threshold, cache_dir=cache_dir, fallback_ttl_seconds=int(getattr(config, 'semantic_cache_ttl_seconds', 3600)))
    return _semantic_cache
__all__ = ['CacheStats', 'FallbackSemanticCache', 'GPTCacheSemanticCache', 'SemanticCacheInterface', 'create_semantic_cache', 'get_semantic_cache']
