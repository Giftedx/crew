# Router Consolidation Implementation Plan

## Overview

The current codebase has multiple router implementations with overlapping functionality, creating confusion and maintenance overhead. This plan outlines the consolidation of these routers into a unified, well-designed system.

## Current Router Implementations

### 1. Core Router (`src/core/router.py`)

- **Purpose**: Basic model selection with learning engine integration
- **Features**: Budget-aware selection, tenant filtering, fallback logic
- **Lines of Code**: ~82 lines
- **Dependencies**: Learning engine, token meter, tenancy

### 2. Advanced LLM Router (`src/core/llm_router.py`)

- **Purpose**: Cost-aware optimization with performance improvements
- **Features**: Complex cost-utility scoring, model profiling, caching
- **Lines of Code**: ~1100+ lines
- **Dependencies**: Heavy dependencies (Redis, sentence-transformers)

### 3. AI Routing Directory (`src/ai/routing/`)

- **Purpose**: Multiple bandit-based routing strategies
- **Features**: Thompson sampling, LinUCB, Vowpal Wabbit
- **Lines of Code**: ~500+ lines across multiple files
- **Dependencies**: Various ML libraries

### 4. Additional Routers (`src/ai/`)

- **Purpose**: Various specialized routing implementations
- **Features**: Adaptive routing, performance routing, enhanced routing
- **Lines of Code**: ~1000+ lines across multiple files
- **Dependencies**: Heavy ML dependencies

## Problems with Current Architecture

1. **Code Duplication**: Similar functionality implemented multiple times
2. **Inconsistent Behavior**: Different routers may behave differently for same inputs
3. **Maintenance Overhead**: Changes need to be made in multiple places
4. **Performance Issues**: Multiple routing layers add overhead
5. **Confusion**: Developers unsure which router to use
6. **Testing Complexity**: Need to test multiple implementations

## Unified Router Architecture

### Design Principles

1. **Single Responsibility**: Each router component has one clear purpose
2. **Strategy Pattern**: Different routing strategies as pluggable components
3. **Configuration-Driven**: Behavior controlled by configuration
4. **Performance-First**: Optimized for speed and efficiency
5. **Extensible**: Easy to add new routing strategies
6. **Testable**: Comprehensive test coverage

### Architecture Overview

```
src/core/routing/
├── __init__.py                 # Public API exports
├── base_router.py             # Abstract base router
├── router_factory.py          # Router creation and configuration
├── router_manager.py          # Router lifecycle management
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py       # Abstract strategy base
│   ├── bandit_strategy.py     # Consolidated bandit strategies
│   ├── cost_aware_strategy.py # Cost optimization strategies
│   ├── contextual_strategy.py # Context-aware routing
│   ├── fallback_strategy.py   # Fallback and reliability
│   └── performance_strategy.py # Performance-based routing
├── models/
│   ├── __init__.py
│   ├── router_request.py      # Router request model
│   ├── router_response.py     # Router response model
│   ├── routing_context.py     # Routing context model
│   └── model_profile.py       # Model performance profile
├── metrics/
│   ├── __init__.py
│   ├── router_metrics.py      # Routing performance metrics
│   ├── cost_metrics.py        # Cost tracking metrics
│   └── strategy_metrics.py    # Strategy-specific metrics
├── config/
│   ├── __init__.py
│   ├── router_config.py       # Router configuration
│   ├── model_config.py        # Model-specific configurations
│   └── strategy_config.py     # Strategy configurations
└── utils/
    ├── __init__.py
    ├── model_selector.py      # Model selection utilities
    ├── cost_calculator.py     # Cost calculation utilities
    └── performance_tracker.py # Performance tracking utilities
```

## Implementation Plan

### Phase 1: Foundation (Week 1)

#### 1.1 Create Base Architecture

```python
# src/core/routing/base_router.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class RouterRequest:
    """Request for router selection."""
    prompt: str
    context: Dict[str, Any]
    candidates: List[str]
    budget_usd: Optional[float] = None
    quality_threshold: Optional[float] = None
    latency_requirement: Optional[float] = None

@dataclass
class RouterResponse:
    """Response from router selection."""
    selected_model: str
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_latency: float
    fallback_models: List[str]

class BaseRouter(ABC):
    """Abstract base router interface."""

    @abstractmethod
    def route(self, request: RouterRequest) -> RouterResponse:
        """Route a request to the best model."""
        pass

    @abstractmethod
    def update(self, model: str, reward: float, context: Dict[str, Any]) -> None:
        """Update router with feedback."""
        pass
```

#### 1.2 Implement Strategy Pattern

```python
# src/core/routing/strategies/base_strategy.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ..models import RouterRequest, RouterResponse

class BaseStrategy(ABC):
    """Abstract base strategy for routing."""

    @abstractmethod
    def select_model(self, request: RouterRequest) -> RouterResponse:
        """Select model using this strategy."""
        pass

    @abstractmethod
    def update(self, model: str, reward: float, context: Dict[str, Any]) -> None:
        """Update strategy with feedback."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass
```

#### 1.3 Create Router Factory

```python
# src/core/routing/router_factory.py
from typing import Dict, Type
from .base_router import BaseRouter
from .strategies import BaseStrategy

class RouterFactory:
    """Factory for creating configured routers."""

    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """Register a routing strategy."""
        cls._strategies[name] = strategy_class

    @classmethod
    def create_router(cls, strategy_name: str, **kwargs) -> BaseRouter:
        """Create a router with specified strategy."""
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        strategy_class = cls._strategies[strategy_name]
        strategy = strategy_class(**kwargs)
        return UnifiedRouter(strategy)
```

### Phase 2: Strategy Implementation (Week 2)

#### 2.1 Consolidate Bandit Strategies

```python
# src/core/routing/strategies/bandit_strategy.py
from typing import Any, Dict, List
from ..models import RouterRequest, RouterResponse
from .base_strategy import BaseStrategy

class BanditStrategy(BaseStrategy):
    """Consolidated bandit-based routing strategy."""

    def __init__(self, bandit_type: str = "thompson"):
        self.bandit_type = bandit_type
        self.bandit = self._create_bandit(bandit_type)

    def select_model(self, request: RouterRequest) -> RouterResponse:
        """Select model using bandit algorithm."""
        # Implement consolidated bandit logic
        pass

    def _create_bandit(self, bandit_type: str):
        """Create appropriate bandit implementation."""
        if bandit_type == "thompson":
            return ThompsonBandit()
        elif bandit_type == "linucb":
            return LinUCBBandit()
        elif bandit_type == "vowpal":
            return VowpalBandit()
        else:
            raise ValueError(f"Unknown bandit type: {bandit_type}")
```

#### 2.2 Implement Cost-Aware Strategy

```python
# src/core/routing/strategies/cost_aware_strategy.py
from typing import Any, Dict, List
from ..models import RouterRequest, RouterResponse
from .base_strategy import BaseStrategy

class CostAwareStrategy(BaseStrategy):
    """Cost-aware routing strategy."""

    def __init__(self, cost_weight: float = 0.4, quality_weight: float = 0.5):
        self.cost_weight = cost_weight
        self.quality_weight = quality_weight
        self.model_profiles = {}

    def select_model(self, request: RouterRequest) -> RouterResponse:
        """Select model based on cost-utility optimization."""
        # Implement cost-aware selection logic
        pass
```

### Phase 3: Migration (Week 3)

#### 3.1 Create Migration Utilities

```python
# src/core/routing/migration.py
from typing import Dict, Any
from .router_factory import RouterFactory

class RouterMigrator:
    """Utilities for migrating from old routers to new unified router."""

    def __init__(self):
        self.router_factory = RouterFactory()

    def migrate_from_core_router(self, old_router) -> BaseRouter:
        """Migrate from core/router.py."""
        # Extract configuration from old router
        config = self._extract_core_router_config(old_router)

        # Create new router with equivalent strategy
        return self.router_factory.create_router("bandit", **config)

    def migrate_from_llm_router(self, old_router) -> BaseRouter:
        """Migrate from core/llm_router.py."""
        # Extract configuration from old router
        config = self._extract_llm_router_config(old_router)

        # Create new router with cost-aware strategy
        return self.router_factory.create_router("cost_aware", **config)
```

#### 3.2 Update Usage Points

```python
# Example migration in existing code
# OLD:
from core.router import Router
from core.learning_engine import LearningEngine

router = Router(engine=LearningEngine())

# NEW:
from core.routing import RouterFactory

router = RouterFactory.create_router("bandit")
```

### Phase 4: Testing and Validation (Week 4)

#### 4.1 Comprehensive Test Suite

```python
# tests/test_routing/
├── __init__.py
├── test_base_router.py
├── test_router_factory.py
├── test_strategies/
│   ├── __init__.py
│   ├── test_bandit_strategy.py
│   ├── test_cost_aware_strategy.py
│   └── test_contextual_strategy.py
├── test_migration.py
└── test_performance.py
```

#### 4.2 Performance Testing

```python
# tests/test_routing/test_performance.py
import time
import pytest
from core.routing import RouterFactory

class TestRouterPerformance:
    """Performance tests for unified router."""

    def test_router_selection_speed(self):
        """Test that router selection is fast."""
        router = RouterFactory.create_router("bandit")
        request = RouterRequest(
            prompt="Test prompt",
            context={},
            candidates=["gpt-4", "gpt-3.5-turbo"]
        )

        start_time = time.time()
        response = router.route(request)
        end_time = time.time()

        # Should complete in less than 10ms
        assert (end_time - start_time) < 0.01
        assert response.selected_model in request.candidates
```

### Phase 5: Documentation and Training (Week 5)

#### 5.1 API Documentation

```python
# src/core/routing/__init__.py
"""
Unified Router System

This module provides a unified, extensible router system for model selection.
The system uses the strategy pattern to allow different routing approaches
while maintaining a consistent interface.

Example:
    from core.routing import RouterFactory

    # Create a cost-aware router
    router = RouterFactory.create_router("cost_aware")

    # Route a request
    response = router.route(request)

    # Update with feedback
    router.update(response.selected_model, 0.8, context)
"""

from .router_factory import RouterFactory
from .base_router import BaseRouter, RouterRequest, RouterResponse
from .strategies import BaseStrategy

__all__ = [
    "RouterFactory",
    "BaseRouter",
    "RouterRequest",
    "RouterResponse",
    "BaseStrategy"
]
```

#### 5.2 Migration Guide

```markdown
# Router Migration Guide

## Overview
This guide helps migrate from the old router implementations to the new unified router system.

## Migration Steps

### 1. Update Imports
```python
# OLD
from core.router import Router

# NEW
from core.routing import RouterFactory
```

### 2. Update Router Creation

```python
# OLD
router = Router(engine=LearningEngine())

# NEW
router = RouterFactory.create_router("bandit")
```

### 3. Update Method Calls

```python
# OLD
model = router.route(task, candidates, context)

# NEW
request = RouterRequest(prompt=task, context=context, candidates=candidates)
response = router.route(request)
model = response.selected_model
```

```

## Benefits of Unified Router

### 1. Simplified Architecture
- Single router interface
- Consistent behavior across all routing
- Easier to understand and maintain

### 2. Better Performance
- Optimized routing algorithms
- Reduced overhead from multiple layers
- Efficient resource usage

### 3. Improved Extensibility
- Easy to add new routing strategies
- Pluggable architecture
- Configuration-driven behavior

### 4. Enhanced Testing
- Comprehensive test coverage
- Strategy-specific testing
- Performance validation

### 5. Better Documentation
- Clear API documentation
- Migration guides
- Usage examples

## Risk Mitigation

### 1. Backward Compatibility
- Maintain compatibility during transition
- Gradual migration approach
- Fallback mechanisms

### 2. Performance Monitoring
- Monitor routing performance
- Track selection accuracy
- Measure cost optimization

### 3. Testing Strategy
- Comprehensive test coverage
- Performance benchmarking
- Integration testing

### 4. Rollback Plan
- Maintain old router implementations
- Feature flags for switching
- Quick rollback procedures

## Success Metrics

### Code Quality
- Reduced lines of code (target: 50% reduction)
- Eliminated duplication
- Improved maintainability

### Performance
- Faster routing decisions (target: <10ms)
- Better model selection accuracy
- Improved cost optimization

### Developer Experience
- Simplified API
- Better documentation
- Easier testing

This consolidation will significantly improve the codebase quality while maintaining all existing functionality and improving performance.
