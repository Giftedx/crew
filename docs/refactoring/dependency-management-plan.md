# Dependency Management Refactoring Plan

## Overview

The current codebase has issues with heavy dependencies that cause import failures and deployment problems. This plan outlines the refactoring of dependency management to make dependencies optional and provide graceful fallbacks.

## Current Dependency Issues

### 1. Heavy Dependencies Causing Import Failures

**Problem**: Import failures due to missing dependencies:

```python
# Current problematic imports
from redis import Redis  # Fails if Redis not installed
from sentence_transformers import SentenceTransformer  # Heavy ML dependency
from transformers import AutoTokenizer  # Large model dependencies
```

**Impact**:

- Import failures in production environments
- Difficult deployment in resource-constrained environments
- Testing complexity with optional dependencies
- Docker image bloat from unnecessary dependencies

### 2. Dependency Categories Analysis

#### Core Dependencies (Always Required)

- `typing`, `dataclasses`, `pathlib` - Python standard library
- `pydantic` - Data validation (used extensively)
- `requests` - HTTP client (core functionality)

#### Standard Dependencies (Commonly Available)

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-dotenv` - Environment configuration

#### Optional Dependencies (Feature-Specific)

- `redis` - Caching and rate limiting
- `sentence-transformers` - Embeddings and semantic search
- `transformers` - NLP model loading
- `torch` - PyTorch for ML models
- `qdrant-client` - Vector database client
- `psycopg2` - PostgreSQL adapter

#### Development Dependencies

- `pytest` - Testing framework
- `black`, `ruff` - Code formatting and linting
- `mypy` - Type checking

## Unified Dependency Management Architecture

### Design Principles

1. **Lazy Loading**: Load dependencies only when needed
2. **Graceful Degradation**: Provide fallback implementations
3. **Feature Flags**: Control feature availability based on dependencies
4. **Clear Error Messages**: Inform users about missing dependencies
5. **Dependency Groups**: Organize dependencies by feature

### Architecture Overview

```
src/core/dependencies/
├── __init__.py                 # Public API exports
├── dependency_manager.py       # Main dependency management
├── optional_deps.py           # Optional dependency handling
├── fallback_handlers.py       # Fallback implementations
├── dependency_checker.py      # Runtime dependency validation
├── feature_flags.py           # Feature flag management
└── groups/
    ├── __init__.py
    ├── caching.py             # Caching dependencies
    ├── ml.py                  # Machine learning dependencies
    ├── database.py            # Database dependencies
    └── monitoring.py          # Monitoring dependencies
```

## Implementation Plan

### Phase 1: Dependency Manager Foundation (Week 1)

#### 1.1 Create Dependency Manager

```python
# src/core/dependencies/dependency_manager.py
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class DependencyStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    OPTIONAL = "optional"

@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    status: DependencyStatus
    import_path: str
    fallback_handler: Optional[Callable] = None
    feature_flag: Optional[str] = None

class DependencyManager:
    """Manages optional dependencies and fallbacks."""
    
    def __init__(self):
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._cache: Dict[str, Any] = {}
    
    def register_dependency(
        self,
        name: str,
        import_path: str,
        fallback_handler: Optional[Callable] = None,
        feature_flag: Optional[str] = None
    ) -> None:
        """Register a dependency."""
        status = self._check_dependency(import_path)
        self._dependencies[name] = DependencyInfo(
            name=name,
            status=status,
            import_path=import_path,
            fallback_handler=fallback_handler,
            feature_flag=feature_flag
        )
    
    def get_dependency(self, name: str) -> Any:
        """Get a dependency with fallback if needed."""
        if name in self._cache:
            return self._cache[name]
        
        dep_info = self._dependencies.get(name)
        if not dep_info:
            raise ValueError(f"Dependency '{name}' not registered")
        
        if dep_info.status == DependencyStatus.AVAILABLE:
            try:
                module = self._import_dependency(dep_info.import_path)
                self._cache[name] = module
                return module
            except ImportError:
                # Fallback if import fails at runtime
                if dep_info.fallback_handler:
                    fallback = dep_info.fallback_handler()
                    self._cache[name] = fallback
                    return fallback
                raise
        
        elif dep_info.fallback_handler:
            fallback = dep_info.fallback_handler()
            self._cache[name] = fallback
            return fallback
        
        else:
            raise ImportError(f"Dependency '{name}' not available and no fallback provided")
    
    def _check_dependency(self, import_path: str) -> DependencyStatus:
        """Check if a dependency is available."""
        try:
            self._import_dependency(import_path)
            return DependencyStatus.AVAILABLE
        except ImportError:
            return DependencyStatus.UNAVAILABLE
    
    def _import_dependency(self, import_path: str) -> Any:
        """Import a dependency."""
        module_path, class_name = import_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
```

#### 1.2 Create Fallback Handlers

```python
# src/core/dependencies/fallback_handlers.py
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FallbackHandlers:
    """Collection of fallback implementations for optional dependencies."""
    
    @staticmethod
    def redis_fallback():
        """Fallback Redis implementation using in-memory storage."""
        class FallbackRedis:
            def __init__(self):
                self._storage: Dict[str, Any] = {}
                logger.warning("Using fallback Redis implementation (in-memory)")
            
            def get(self, key: str) -> Optional[str]:
                return self._storage.get(key)
            
            def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
                self._storage[key] = value
                return True
            
            def delete(self, key: str) -> bool:
                return self._storage.pop(key, None) is not None
            
            def exists(self, key: str) -> bool:
                return key in self._storage
        
        return FallbackRedis()
    
    @staticmethod
    def sentence_transformers_fallback():
        """Fallback sentence transformer using simple embeddings."""
        class FallbackSentenceTransformer:
            def __init__(self):
                logger.warning("Using fallback sentence transformer (simple embeddings)")
            
            def encode(self, texts: List[str]) -> List[List[float]]:
                # Simple hash-based embeddings as fallback
                import hashlib
                embeddings = []
                for text in texts:
                    # Create a simple hash-based embedding
                    hash_obj = hashlib.md5(text.encode())
                    hash_bytes = hash_obj.digest()
                    # Convert to float vector
                    embedding = [float(b) / 255.0 for b in hash_bytes]
                    embeddings.append(embedding)
                return embeddings
        
        return FallbackSentenceTransformer()
    
    @staticmethod
    def qdrant_fallback():
        """Fallback Qdrant client using in-memory storage."""
        class FallbackQdrantClient:
            def __init__(self):
                self._collections: Dict[str, Dict] = {}
                logger.warning("Using fallback Qdrant client (in-memory)")
            
            def create_collection(self, collection_name: str, **kwargs) -> bool:
                self._collections[collection_name] = {
                    'vectors': [],
                    'payloads': [],
                    'config': kwargs
                }
                return True
            
            def upsert(self, collection_name: str, points: List[Dict]) -> bool:
                if collection_name not in self._collections:
                    self.create_collection(collection_name)
                
                for point in points:
                    self._collections[collection_name]['vectors'].append(point.get('vector', []))
                    self._collections[collection_name]['payloads'].append(point.get('payload', {}))
                return True
            
            def search(self, collection_name: str, query_vector: List[float], limit: int = 10):
                if collection_name not in self._collections:
                    return []
                
                # Simple similarity search using cosine similarity
                vectors = self._collections[collection_name]['vectors']
                payloads = self._collections[collection_name]['payloads']
                
                # Calculate similarities (simplified)
                results = []
                for i, vector in enumerate(vectors):
                    if len(vector) == len(query_vector):
                        # Simple dot product as similarity measure
                        similarity = sum(a * b for a, b in zip(vector, query_vector))
                        results.append({
                            'id': i,
                            'score': similarity,
                            'payload': payloads[i]
                        })
                
                # Sort by similarity and return top results
                results.sort(key=lambda x: x['score'], reverse=True)
                return results[:limit]
        
        return FallbackQdrantClient()
```

### Phase 2: Dependency Groups (Week 2)

#### 2.1 Caching Dependencies

```python
# src/core/dependencies/groups/caching.py
from ..dependency_manager import DependencyManager
from ..fallback_handlers import FallbackHandlers

def register_caching_dependencies(manager: DependencyManager) -> None:
    """Register caching-related dependencies."""
    
    # Redis for caching and rate limiting
    manager.register_dependency(
        name="redis",
        import_path="redis.Redis",
        fallback_handler=FallbackHandlers.redis_fallback,
        feature_flag="ENABLE_REDIS_CACHE"
    )
    
    # Optional: Memcached fallback
    manager.register_dependency(
        name="memcached",
        import_path="pymemcache.Client",
        feature_flag="ENABLE_MEMCACHED"
    )
```

#### 2.2 Machine Learning Dependencies

```python
# src/core/dependencies/groups/ml.py
from ..dependency_manager import DependencyManager
from ..fallback_handlers import FallbackHandlers

def register_ml_dependencies(manager: DependencyManager) -> None:
    """Register machine learning dependencies."""
    
    # Sentence transformers for embeddings
    manager.register_dependency(
        name="sentence_transformer",
        import_path="sentence_transformers.SentenceTransformer",
        fallback_handler=FallbackHandlers.sentence_transformers_fallback,
        feature_flag="ENABLE_SEMANTIC_SEARCH"
    )
    
    # Transformers for model loading
    manager.register_dependency(
        name="transformers",
        import_path="transformers.AutoTokenizer",
        feature_flag="ENABLE_TRANSFORMERS"
    )
    
    # PyTorch for ML models
    manager.register_dependency(
        name="torch",
        import_path="torch.nn.Module",
        feature_flag="ENABLE_PYTORCH"
    )
```

#### 2.3 Database Dependencies

```python
# src/core/dependencies/groups/database.py
from ..dependency_manager import DependencyManager
from ..fallback_handlers import FallbackHandlers

def register_database_dependencies(manager: DependencyManager) -> None:
    """Register database dependencies."""
    
    # Qdrant vector database
    manager.register_dependency(
        name="qdrant",
        import_path="qdrant_client.QdrantClient",
        fallback_handler=FallbackHandlers.qdrant_fallback,
        feature_flag="ENABLE_QDRANT"
    )
    
    # PostgreSQL adapter
    manager.register_dependency(
        name="psycopg2",
        import_path="psycopg2.connect",
        feature_flag="ENABLE_POSTGRES"
    )
    
    # SQLite (usually available)
    manager.register_dependency(
        name="sqlite3",
        import_path="sqlite3.connect"
    )
```

### Phase 3: Feature Flag Integration (Week 3)

#### 3.1 Feature Flag Manager

```python
# src/core/dependencies/feature_flags.py
import os
from typing import Dict, Any
from enum import Enum

class FeatureFlagStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    OPTIONAL = "optional"

class FeatureFlagManager:
    """Manages feature flags for optional dependencies."""
    
    def __init__(self):
        self._flags: Dict[str, FeatureFlagStatus] = {}
        self._load_flags()
    
    def _load_flags(self) -> None:
        """Load feature flags from environment variables."""
        flag_mappings = {
            "ENABLE_REDIS_CACHE": "redis_cache",
            "ENABLE_SEMANTIC_SEARCH": "semantic_search",
            "ENABLE_QDRANT": "qdrant",
            "ENABLE_TRANSFORMERS": "transformers",
            "ENABLE_PYTORCH": "pytorch",
            "ENABLE_POSTGRES": "postgres",
        }
        
        for env_var, flag_name in flag_mappings.items():
            value = os.getenv(env_var, "false").lower()
            if value in ("true", "1", "yes", "on"):
                self._flags[flag_name] = FeatureFlagStatus.ENABLED
            elif value in ("false", "0", "no", "off"):
                self._flags[flag_name] = FeatureFlagStatus.DISABLED
            else:
                self._flags[flag_name] = FeatureFlagStatus.OPTIONAL
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag_name, FeatureFlagStatus.OPTIONAL) == FeatureFlagStatus.ENABLED
    
    def is_required(self, flag_name: str) -> bool:
        """Check if a feature is required (enabled and not optional)."""
        return self._flags.get(flag_name, FeatureFlagStatus.OPTIONAL) == FeatureFlagStatus.ENABLED
```

#### 3.2 Integration with Dependency Manager

```python
# src/core/dependencies/optional_deps.py
from .dependency_manager import DependencyManager
from .feature_flags import FeatureFlagManager
from typing import Any, Optional

class OptionalDependencies:
    """Convenience class for accessing optional dependencies."""
    
    def __init__(self):
        self.dependency_manager = DependencyManager()
        self.feature_flags = FeatureFlagManager()
        self._register_all_dependencies()
    
    def _register_all_dependencies(self) -> None:
        """Register all optional dependencies."""
        from .groups import caching, ml, database
        
        caching.register_caching_dependencies(self.dependency_manager)
        ml.register_ml_dependencies(self.dependency_manager)
        database.register_database_dependencies(self.dependency_manager)
    
    def get_redis(self) -> Any:
        """Get Redis client with fallback."""
        if not self.feature_flags.is_enabled("redis_cache"):
            return self.dependency_manager.get_dependency("redis").fallback_handler()
        return self.dependency_manager.get_dependency("redis")
    
    def get_sentence_transformer(self) -> Any:
        """Get sentence transformer with fallback."""
        if not self.feature_flags.is_enabled("semantic_search"):
            return self.dependency_manager.get_dependency("sentence_transformer").fallback_handler()
        return self.dependency_manager.get_dependency("sentence_transformer")
    
    def get_qdrant(self) -> Any:
        """Get Qdrant client with fallback."""
        if not self.feature_flags.is_enabled("qdrant"):
            return self.dependency_manager.get_dependency("qdrant").fallback_handler()
        return self.dependency_manager.get_dependency("qdrant")

# Global instance
optional_deps = OptionalDependencies()
```

### Phase 4: Migration of Existing Code (Week 4)

#### 4.1 Update Cache Implementation

```python
# src/core/llm_cache.py (Updated)
from typing import Optional, Any
from .dependencies.optional_deps import optional_deps
import logging

logger = logging.getLogger(__name__)

class LLMCache:
    """LLM cache with optional Redis backend."""
    
    def __init__(self):
        self.redis_client = optional_deps.get_redis()
        self.is_redis = hasattr(self.redis_client, 'get') and not hasattr(self.redis_client, '_storage')
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            if self.is_redis:
                return self.redis_client.get(key)
            else:
                return self.redis_client.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in cache."""
        try:
            if self.is_redis:
                return self.redis_client.set(key, value, ex=ttl)
            else:
                return self.redis_client.set(key, value)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False
```

#### 4.2 Update Vector Store Implementation

```python
# src/memory/vector_store.py (Updated)
from typing import List, Dict, Any
from core.dependencies.optional_deps import optional_deps
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store with optional Qdrant backend."""
    
    def __init__(self):
        self.qdrant_client = optional_deps.get_qdrant()
        self.is_qdrant = hasattr(self.qdrant_client, 'search') and not hasattr(self.qdrant_client, '_collections')
    
    def create_collection(self, collection_name: str, **kwargs) -> bool:
        """Create a vector collection."""
        try:
            return self.qdrant_client.create_collection(collection_name, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to create collection: {e}")
            return False
    
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Upsert points to collection."""
        try:
            return self.qdrant_client.upsert(collection_name, points)
        except Exception as e:
            logger.warning(f"Failed to upsert points: {e}")
            return False
    
    def search(self, collection_name: str, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            return self.qdrant_client.search(collection_name, query_vector, limit)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
```

### Phase 5: Testing and Validation (Week 5)

#### 5.1 Dependency Testing

```python
# tests/test_dependencies/
├── __init__.py
├── test_dependency_manager.py
├── test_fallback_handlers.py
├── test_feature_flags.py
└── test_optional_deps.py
```

#### 5.2 Integration Testing

```python
# tests/test_dependencies/test_optional_deps.py
import pytest
from unittest.mock import patch
from core.dependencies.optional_deps import optional_deps

class TestOptionalDependencies:
    """Test optional dependency handling."""
    
    def test_redis_fallback(self):
        """Test Redis fallback when not available."""
        with patch.dict('os.environ', {'ENABLE_REDIS_CACHE': 'false'}):
            redis = optional_deps.get_redis()
            assert hasattr(redis, '_storage')  # Fallback has _storage attribute
    
    def test_qdrant_fallback(self):
        """Test Qdrant fallback when not available."""
        with patch.dict('os.environ', {'ENABLE_QDRANT': 'false'}):
            qdrant = optional_deps.get_qdrant()
            assert hasattr(qdrant, '_collections')  # Fallback has _collections attribute
    
    def test_feature_flag_integration(self):
        """Test feature flag integration."""
        with patch.dict('os.environ', {'ENABLE_SEMANTIC_SEARCH': 'true'}):
            transformer = optional_deps.get_sentence_transformer()
            # Should try to load real transformer first
            assert transformer is not None
```

## Benefits of Refactored Dependency Management

### 1. Improved Deployment

- Smaller Docker images (no unnecessary dependencies)
- Faster deployment times
- Better compatibility with different environments

### 2. Enhanced Testing

- Easier testing without heavy dependencies
- Faster test execution
- Better test isolation

### 3. Better User Experience

- Clear error messages about missing dependencies
- Graceful degradation when features unavailable
- Easy feature toggling

### 4. Reduced Maintenance

- Centralized dependency management
- Consistent fallback patterns
- Easier dependency updates

### 5. Performance Benefits

- Lazy loading of heavy dependencies
- Reduced memory usage
- Faster application startup

## Migration Strategy

### 1. Gradual Migration

- Migrate one module at a time
- Maintain backward compatibility
- Test thoroughly at each step

### 2. Feature Flag Control

- Use feature flags to control migration
- Allow rollback if issues arise
- Monitor performance impact

### 3. Documentation Updates

- Update installation instructions
- Document optional dependencies
- Provide migration guides

### 4. Testing Strategy

- Test with and without optional dependencies
- Validate fallback behavior
- Performance testing

## Success Metrics

### Deployment

- Reduced Docker image size (target: 50% reduction)
- Faster deployment times (target: 30% improvement)
- Fewer deployment failures

### Performance

- Faster application startup (target: 40% improvement)
- Reduced memory usage (target: 25% reduction)
- Better resource utilization

### Developer Experience

- Clearer error messages
- Easier local development setup
- Better testing experience

### Reliability

- Fewer import failures
- Better error handling
- Improved system stability

This refactoring will significantly improve the dependency management of the codebase while maintaining all existing functionality and providing better fallback mechanisms.
