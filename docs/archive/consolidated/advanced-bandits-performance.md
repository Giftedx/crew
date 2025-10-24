# Advanced Contextual Bandits: Performance Optimization Guide

Comprehensive guide for optimizing the performance of advanced contextual bandit algorithms in production environments.

## Performance Optimization Overview

The advanced contextual bandit system is designed for high-throughput, low-latency operations while maintaining sophisticated decision-making capabilities. This guide covers optimization strategies across multiple dimensions.

## 1. Memory Optimization

### Algorithm Memory Management

```python
# Configure memory-efficient settings
export RL_DR_MAX_HISTORY=10000      # Limit DoublyRobust history
export RL_OT_MAX_NODES=5000         # Limit OffsetTree node count
export RL_MEMORY_CLEANUP_INTERVAL=3600  # Cleanup every hour

# Memory monitoring configuration
from core.rl.advanced_config import get_config_manager
import psutil
import gc

class MemoryOptimizedBanditManager:
    """Memory-efficient bandit management with automatic cleanup."""

    def __init__(self, memory_limit_mb=512):
        self.memory_limit_mb = memory_limit_mb
        self.config_manager = get_config_manager()
        self.last_cleanup = time.time()

    def check_memory_usage(self):
        """Monitor memory usage and trigger cleanup if needed."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb > self.memory_limit_mb:
            self.cleanup_memory()

        return memory_mb

    def cleanup_memory(self):
        """Clean up memory in bandit algorithms."""
        current_time = time.time()

        # Skip if cleaned up recently
        if current_time - self.last_cleanup < 300:  # 5 minutes
            return

        # Clean up DoublyRobust histories
        for domain in self.config_manager.get_active_domains():
            bandit = self._get_bandit_for_domain(domain)
            if hasattr(bandit, 'cleanup_old_data'):
                bandit.cleanup_old_data(max_age_hours=24)

        # Force garbage collection
        gc.collect()

        self.last_cleanup = current_time
        logger.info("Memory cleanup completed")
```

### Context Vector Optimization

```python
class OptimizedContextProcessor:
    """Efficient context processing with caching and compression."""

    def __init__(self, cache_size=10000):
        self.context_cache = {}
        self.cache_size = cache_size
        self.cache_hits = 0
        self.cache_misses = 0

    def process_context(self, raw_context):
        """Process context with caching for repeated patterns."""

        # Create cache key from context
        context_key = self._create_context_key(raw_context)

        if context_key in self.context_cache:
            self.cache_hits += 1
            return self.context_cache[context_key]

        self.cache_misses += 1

        # Process context
        processed = self._process_raw_context(raw_context)

        # Cache result (with size limit)
        if len(self.context_cache) < self.cache_size:
            self.context_cache[context_key] = processed
        elif len(self.context_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.context_cache))
            del self.context_cache[oldest_key]
            self.context_cache[context_key] = processed

        return processed

    def _create_context_key(self, context):
        """Create efficient cache key from context."""
        # Round float values to reduce cache misses from tiny differences
        rounded_context = {
            k: round(v, 3) if isinstance(v, float) else v
            for k, v in context.items()
        }
        return hash(tuple(sorted(rounded_context.items())))

    def _process_raw_context(self, raw_context):
        """Convert raw context to optimized vector format."""
        # Use numpy for efficient numerical operations
        import numpy as np

        # Extract and normalize features
        features = []
        for key in sorted(raw_context.keys()):  # Consistent ordering
            value = raw_context[key]
            if isinstance(value, (int, float)):
                features.append(float(value))
            elif isinstance(value, bool):
                features.append(1.0 if value else 0.0)
            else:
                # Hash non-numeric values
                features.append(hash(str(value)) % 1000 / 1000.0)

        return np.array(features, dtype=np.float32)  # Use float32 for memory efficiency

    def get_cache_stats(self):
        """Get cache performance statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.context_cache)
        }
```

## 2. Computational Optimization

### Algorithm-Specific Optimizations

#### DoublyRobust Optimization

```python
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import SGDRegressor

class OptimizedDoublyRobustBandit:
    """Memory and compute optimized DoublyRobust implementation."""

    def __init__(self, alpha=1.0, learning_rate=0.1, use_sparse=True):
        self.alpha = alpha
        self.learning_rate = learning_rate
        self.use_sparse = use_sparse

        # Use incremental learning for efficiency
        self.reward_model = SGDRegressor(
            learning_rate='adaptive',
            eta0=learning_rate,
            random_state=42
        )

        # Sparse matrices for memory efficiency
        self.context_history = []
        self.reward_history = []
        self.action_history = []

        # Pre-allocate arrays for common operations
        self._prediction_buffer = np.zeros(10)  # Reuse for predictions

    def _predict_reward_optimized(self, context, action):
        """Optimized reward prediction with caching."""

        # Use pre-allocated buffer to avoid memory allocation
        if len(context) > len(self._prediction_buffer):
            self._prediction_buffer = np.zeros(len(context))

        # Create feature vector efficiently
        feature_vector = self._create_feature_vector(context, action)

        # Use incremental prediction if model is trained
        if hasattr(self.reward_model, 'coef_'):
            return self.reward_model.predict([feature_vector])[0]

        return 0.0  # Default for untrained model

    def _create_feature_vector(self, context, action):
        """Efficiently create feature vector from context and action."""
        # Convert context to numpy array if needed
        if not isinstance(context, np.ndarray):
            context = np.array(list(context.values()), dtype=np.float32)

        # Create one-hot encoding for action
        action_features = np.zeros(len(self.actions), dtype=np.float32)
        if action in self.actions:
            action_idx = self.actions.index(action)
            action_features[action_idx] = 1.0

        # Concatenate efficiently
        return np.concatenate([context, action_features])

    def update_optimized(self, action, reward, context):
        """Memory-efficient update with batch processing."""

        # Convert context for consistency
        if not isinstance(context, np.ndarray):
            context = np.array(list(context.values()), dtype=np.float32)

        # Add to history with memory limits
        self.context_history.append(context)
        self.reward_history.append(reward)
        self.action_history.append(action)

        # Limit history size to prevent memory growth
        max_history = 10000
        if len(self.context_history) > max_history:
            # Remove oldest 20% when limit exceeded
            remove_count = max_history // 5
            self.context_history = self.context_history[remove_count:]
            self.reward_history = self.reward_history[remove_count:]
            self.action_history = self.action_history[remove_count:]

        # Batch update every N samples for efficiency
        if len(self.reward_history) % 10 == 0:
            self._batch_update_model()

    def _batch_update_model(self):
        """Efficient batch update of reward model."""
        if len(self.reward_history) < 10:
            return

        # Create feature matrix for recent samples
        recent_samples = min(100, len(self.reward_history))  # Last 100 samples

        features = []
        rewards = []

        for i in range(-recent_samples, 0):
            feature_vector = self._create_feature_vector(
                self.context_history[i],
                self.action_history[i]
            )
            features.append(feature_vector)
            rewards.append(self.reward_history[i])

        # Partial fit for incremental learning
        if features:
            self.reward_model.partial_fit(features, rewards)
```

#### OffsetTree Optimization

```python
import numpy as np
from collections import defaultdict

class OptimizedOffsetTreeBandit:
    """Compute-optimized OffsetTree with efficient tree operations."""

    def __init__(self, max_depth=4, min_samples_split=20):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split

        # Use efficient data structures
        self.tree_nodes = {}  # dict for O(1) node access
        self.node_statistics = defaultdict(lambda: {
            'visits': 0,
            'reward_sum': 0.0,
            'reward_sq_sum': 0.0
        })

        # Pre-compute split candidates for efficiency
        self.split_candidates = self._generate_split_candidates()

    def _generate_split_candidates(self):
        """Pre-generate common split points for efficiency."""
        # Create quantile-based split points
        split_points = []
        for i in range(1, 10):  # 9 split points (10%, 20%, ..., 90%)
            split_points.append(i / 10.0)
        return split_points

    def _find_best_split_optimized(self, node_contexts, node_rewards):
        """Optimized split finding with vectorized operations."""
        if len(node_contexts) < self.min_samples_split:
            return None, None, 0.0

        contexts_array = np.array(node_contexts)
        rewards_array = np.array(node_rewards)

        best_gain = 0.0
        best_feature = None
        best_threshold = None

        # Vectorized operations for efficiency
        n_features = contexts_array.shape[1]

        for feature_idx in range(n_features):
            feature_values = contexts_array[:, feature_idx]

            # Use pre-computed split candidates
            feature_min, feature_max = feature_values.min(), feature_values.max()

            for split_quantile in self.split_candidates:
                threshold = feature_min + split_quantile * (feature_max - feature_min)

                # Vectorized split
                left_mask = feature_values <= threshold
                right_mask = ~left_mask

                if np.sum(left_mask) < 5 or np.sum(right_mask) < 5:
                    continue

                # Calculate information gain efficiently
                gain = self._calculate_information_gain_vectorized(
                    rewards_array, left_mask, right_mask
                )

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _calculate_information_gain_vectorized(self, rewards, left_mask, right_mask):
        """Vectorized information gain calculation."""

        # Parent variance
        parent_var = np.var(rewards)

        # Child variances
        left_rewards = rewards[left_mask]
        right_rewards = rewards[right_mask]

        if len(left_rewards) == 0 or len(right_rewards) == 0:
            return 0.0

        left_var = np.var(left_rewards)
        right_var = np.var(right_rewards)

        # Weighted variance reduction
        n_total = len(rewards)
        n_left = len(left_rewards)
        n_right = len(right_rewards)

        weighted_child_var = (n_left / n_total) * left_var + (n_right / n_total) * right_var

        return parent_var - weighted_child_var

    def recommend_optimized(self, context, candidates):
        """Optimized recommendation with path caching."""

        # Convert context to array for consistent operations
        if not isinstance(context, np.ndarray):
            context = np.array(list(context.values()), dtype=np.float32)

        # Find leaf node efficiently
        node_id = self._find_leaf_node_fast(context)

        # Get node statistics
        node_stats = self.node_statistics[node_id]

        if node_stats['visits'] == 0:
            # Random selection for unvisited nodes
            return np.random.choice(candidates)

        # Thompson sampling at leaf
        mean_reward = node_stats['reward_sum'] / node_stats['visits']

        # Efficient confidence calculation
        if node_stats['visits'] > 1:
            variance = (node_stats['reward_sq_sum'] / node_stats['visits']) - mean_reward**2
            std_dev = np.sqrt(max(variance, 0.01))  # Minimum variance for stability
        else:
            std_dev = 1.0

        confidence = np.sqrt(2 * np.log(node_stats['visits']) / node_stats['visits'])

        # Upper confidence bound
        ucb_value = mean_reward + confidence * std_dev

        # Select based on UCB (simplified for efficiency)
        return candidates[0] if ucb_value > 0.5 else np.random.choice(candidates)

    def _find_leaf_node_fast(self, context):
        """Fast leaf node finding with path caching."""

        # Start from root
        current_node = 'root'
        path = [current_node]

        # Traverse tree efficiently
        while current_node in self.tree_nodes:
            node_info = self.tree_nodes[current_node]

            if 'split_feature' not in node_info:
                break  # Leaf node

            feature_idx = node_info['split_feature']
            threshold = node_info['split_threshold']

            if context[feature_idx] <= threshold:
                current_node = f"{current_node}_left"
            else:
                current_node = f"{current_node}_right"

            path.append(current_node)

        return current_node
```

## 3. Network and I/O Optimization

### Async Processing

```python
import asyncio
import aiohttp
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class AsyncBanditProcessor:
    """Asynchronous bandit processing for high-throughput scenarios."""

    def __init__(self, max_workers=10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def process_batch_recommendations(self, requests: List[Dict[str, Any]]):
        """Process multiple recommendation requests concurrently."""

        # Create tasks for concurrent processing
        tasks = []
        for request in requests:
            task = asyncio.create_task(
                self._process_single_request(request)
            )
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Request {i} failed: {result}")
            else:
                successful_results.append(result)

        return successful_results

    async def _process_single_request(self, request):
        """Process a single recommendation request."""

        domain = request['domain']
        context = request['context']
        candidates = request['candidates']

        # Run CPU-intensive bandit computation in thread pool
        loop = asyncio.get_event_loop()

        recommendation = await loop.run_in_executor(
            self.executor,
            self._compute_recommendation,
            domain, context, candidates
        )

        return {
            'request_id': request.get('request_id'),
            'recommendation': recommendation,
            'domain': domain,
            'timestamp': time.time()
        }

    def _compute_recommendation(self, domain, context, candidates):
        """CPU-intensive bandit computation (runs in thread pool)."""

        # This would call your actual bandit engine
        from core.learning_engine import LearningEngine

        engine = LearningEngine()
        return engine.recommend(domain, context, candidates)

# Usage example
async def handle_batch_requests(request_batch):
    """Handle a batch of recommendation requests."""

    async with AsyncBanditProcessor(max_workers=20) as processor:
        results = await processor.process_batch_recommendations(request_batch)
        return results

# Example with FastAPI integration
from fastapi import FastAPI, BackgroundTasks
import uvloop  # High-performance event loop

# Use high-performance event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app = FastAPI()

@app.post("/recommendations/batch")
async def batch_recommendations(requests: List[Dict[str, Any]]):
    """Endpoint for batch recommendation processing."""

    # Process requests asynchronously
    results = await handle_batch_requests(requests)

    return {
        "processed": len(results),
        "results": results
    }
```

### Database Optimization

```python
import sqlite3
import pickle
from contextlib import contextmanager
from typing import Optional

class OptimizedBanditStorage:
    """Optimized storage backend for bandit state and metrics."""

    def __init__(self, db_path: str = "bandits.db"):
        self.db_path = db_path
        self.connection_pool = []
        self.max_connections = 10

        # Initialize database
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database with optimized schema."""

        with self._get_connection() as conn:
            # Create tables with indexes for performance
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS bandit_state (
                    domain TEXT PRIMARY KEY,
                    algorithm TEXT NOT NULL,
                    state_data BLOB NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_bandit_domain ON bandit_state(domain);
                CREATE INDEX IF NOT EXISTS idx_bandit_updated ON bandit_state(last_updated);

                CREATE TABLE IF NOT EXISTS bandit_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context_hash TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_domain_time ON bandit_metrics(domain, timestamp);
                CREATE INDEX IF NOT EXISTS idx_metrics_algorithm ON bandit_metrics(algorithm);

                -- Enable WAL mode for better concurrency
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA cache_size=-64000;  -- 64MB cache
                PRAGMA temp_store=MEMORY;
            """)

    @contextmanager
    def _get_connection(self):
        """Get database connection with connection pooling."""

        if self.connection_pool:
            conn = self.connection_pool.pop()
        else:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            # Optimize connection settings
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-32000")  # 32MB per connection

        try:
            yield conn
        finally:
            if len(self.connection_pool) < self.max_connections:
                self.connection_pool.append(conn)
            else:
                conn.close()

    def save_bandit_state(self, domain: str, algorithm: str, state_data: Any):
        """Save bandit state with optimized serialization."""

        # Use pickle for efficient serialization
        serialized_data = pickle.dumps(state_data, protocol=pickle.HIGHEST_PROTOCOL)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO bandit_state
                (domain, algorithm, state_data, last_updated, version)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP,
                    COALESCE((SELECT version + 1 FROM bandit_state WHERE domain = ?), 1))
            """, (domain, algorithm, serialized_data, domain))
            conn.commit()

    def load_bandit_state(self, domain: str) -> Optional[Any]:
        """Load bandit state with efficient deserialization."""

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT state_data FROM bandit_state
                WHERE domain = ?
                ORDER BY version DESC
                LIMIT 1
            """, (domain,))

            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])

        return None

    def batch_save_metrics(self, metrics_batch: List[Dict[str, Any]]):
        """Efficiently save multiple metrics."""

        with self._get_connection() as conn:
            # Prepare batch insert
            insert_data = [
                (
                    metric['domain'],
                    metric['algorithm'],
                    metric['metric_name'],
                    metric['metric_value'],
                    metric.get('context_hash')
                )
                for metric in metrics_batch
            ]

            conn.executemany("""
                INSERT INTO bandit_metrics
                (domain, algorithm, metric_name, metric_value, context_hash)
                VALUES (?, ?, ?, ?, ?)
            """, insert_data)

            conn.commit()

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to maintain performance."""

        with self._get_connection() as conn:
            # Remove old metrics
            conn.execute("""
                DELETE FROM bandit_metrics
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            # Vacuum to reclaim space
            conn.execute("VACUUM")
            conn.commit()
```

## 4. Monitoring and Profiling

### Performance Monitoring

```python
import time
import psutil
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict, deque

@dataclass
class PerformanceMetrics:
    """Performance metrics for bandit operations."""
    operation: str
    duration_ms: float
    memory_usage_mb: float
    cpu_percent: float
    timestamp: float

class BanditPerformanceMonitor:
    """Comprehensive performance monitoring for bandit operations."""

    def __init__(self, max_metrics=10000):
        self.metrics_history = deque(maxlen=max_metrics)
        self.operation_stats = defaultdict(list)
        self.slow_operations = deque(maxlen=100)  # Track slow operations

        # Performance thresholds
        self.thresholds = {
            'recommendation_ms': 50,    # 50ms for recommendation
            'update_ms': 20,           # 20ms for update
            'memory_mb': 512,          # 512MB memory usage
            'cpu_percent': 80          # 80% CPU usage
        }

    def monitor_operation(self, operation_name: str):
        """Decorator to monitor bandit operations."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Start monitoring
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                start_cpu = psutil.cpu_percent()

                try:
                    # Execute operation
                    result = func(*args, **kwargs)

                    # Record success metrics
                    self._record_metrics(
                        operation_name, start_time, start_memory, start_cpu, success=True
                    )

                    return result

                except Exception as e:
                    # Record failure metrics
                    self._record_metrics(
                        operation_name, start_time, start_memory, start_cpu, success=False
                    )
                    raise

            return wrapper
        return decorator

    def _record_metrics(self, operation: str, start_time: float,
                       start_memory: float, start_cpu: float, success: bool):
        """Record performance metrics for an operation."""

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        end_cpu = psutil.cpu_percent()

        duration_ms = (end_time - start_time) * 1000
        memory_usage_mb = end_memory - start_memory
        cpu_percent = end_cpu - start_cpu

        # Create metrics record
        metrics = PerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_percent=cpu_percent,
            timestamp=end_time
        )

        # Store metrics
        self.metrics_history.append(metrics)
        self.operation_stats[operation].append(metrics)

        # Check for slow operations
        threshold_key = f"{operation}_ms"
        if threshold_key in self.thresholds:
            if duration_ms > self.thresholds[threshold_key]:
                self.slow_operations.append(metrics)
                logger.warning(f"Slow {operation}: {duration_ms:.1f}ms")

        # Log performance issues
        if memory_usage_mb > self.thresholds['memory_mb']:
            logger.warning(f"High memory usage in {operation}: {memory_usage_mb:.1f}MB")

        if cpu_percent > self.thresholds['cpu_percent']:
            logger.warning(f"High CPU usage in {operation}: {cpu_percent:.1f}%")

    def get_performance_summary(self, operation: str = None) -> Dict:
        """Get performance summary for operations."""

        if operation:
            metrics_list = self.operation_stats.get(operation, [])
        else:
            metrics_list = list(self.metrics_history)

        if not metrics_list:
            return {"error": "No metrics available"}

        # Calculate statistics
        durations = [m.duration_ms for m in metrics_list]
        memory_usage = [m.memory_usage_mb for m in metrics_list]

        return {
            "operation": operation or "all",
            "total_calls": len(metrics_list),
            "duration_stats": {
                "mean_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "p95_ms": self._percentile(durations, 95),
                "p99_ms": self._percentile(durations, 99)
            },
            "memory_stats": {
                "mean_mb": sum(memory_usage) / len(memory_usage),
                "max_mb": max(memory_usage),
                "total_mb": sum(memory_usage)
            },
            "slow_operations": len([d for d in durations if d > 100]),  # >100ms
            "recent_performance": durations[-10:] if len(durations) >= 10 else durations
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

# Global performance monitor instance
perf_monitor = BanditPerformanceMonitor()

# Example usage with bandit operations
class MonitoredLearningEngine:
    """Learning engine with performance monitoring."""

    @perf_monitor.monitor_operation("recommendation")
    def recommend(self, domain: str, context: Dict, candidates: List[str]) -> str:
        """Get recommendation with performance monitoring."""
        # Your actual recommendation logic here
        pass

    @perf_monitor.monitor_operation("update")
    def record(self, domain: str, context: Dict, action: str, reward: float):
        """Record reward with performance monitoring."""
        # Your actual recording logic here
        pass
```

### Memory Profiling

```python
import tracemalloc
from memory_profiler import profile
import cProfile
import pstats
from functools import wraps

class MemoryProfiler:
    """Advanced memory profiling for bandit operations."""

    def __init__(self):
        self.profiles = {}
        self.memory_snapshots = {}

    def start_memory_tracing(self):
        """Start memory tracing."""
        tracemalloc.start()

    def memory_snapshot(self, name: str):
        """Take a memory snapshot."""
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.memory_snapshots[name] = snapshot

            # Get current memory usage
            current, peak = tracemalloc.get_traced_memory()
            logger.info(f"Memory snapshot '{name}': Current={current/1024/1024:.1f}MB, Peak={peak/1024/1024:.1f}MB")

    def compare_snapshots(self, name1: str, name2: str):
        """Compare two memory snapshots."""
        if name1 in self.memory_snapshots and name2 in self.memory_snapshots:
            snapshot1 = self.memory_snapshots[name1]
            snapshot2 = self.memory_snapshots[name2]

            top_stats = snapshot2.compare_to(snapshot1, 'lineno')

            logger.info(f"Memory comparison {name1} -> {name2}:")
            for stat in top_stats[:10]:
                logger.info(f"  {stat}")

    def profile_memory(self, func):
        """Decorator for memory profiling."""

        @wraps(func)
        @profile  # memory_profiler decorator
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def profile_cpu(self, func):
        """Decorator for CPU profiling."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()

            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()

                # Save profile stats
                func_name = f"{func.__module__}.{func.__name__}"
                stats = pstats.Stats(profiler)
                stats.sort_stats('cumulative')

                # Store for later analysis
                self.profiles[func_name] = stats

                # Log top time consumers
                logger.info(f"CPU profile for {func_name}:")
                stats.print_stats(10)

            return result

        return wrapper

    def get_top_memory_consumers(self, snapshot_name: str) -> List[str]:
        """Get top memory consuming operations."""
        if snapshot_name not in self.memory_snapshots:
            return []

        snapshot = self.memory_snapshots[snapshot_name]
        top_stats = snapshot.statistics('lineno')

        return [str(stat) for stat in top_stats[:10]]

# Example usage
memory_profiler = MemoryProfiler()

class ProfiledBanditOperations:
    """Bandit operations with comprehensive profiling."""

    def __init__(self):
        memory_profiler.start_memory_tracing()

    @memory_profiler.profile_memory
    @memory_profiler.profile_cpu
    def intensive_bandit_operation(self, context_batch: List[Dict]):
        """Example of profiled intensive operation."""

        memory_profiler.memory_snapshot("operation_start")

        # Simulate intensive bandit operations
        results = []
        for context in context_batch:
            # Process each context
            result = self._process_single_context(context)
            results.append(result)

        memory_profiler.memory_snapshot("operation_end")
        memory_profiler.compare_snapshots("operation_start", "operation_end")

        return results

    def _process_single_context(self, context):
        """Process a single context (implement your logic)."""
        # Your bandit processing logic here
        pass
```

## 5. Configuration Optimization

### Production Configuration Templates

```bash
# High-throughput configuration
export ENABLE_RL_ADVANCED=true
export ENABLE_RL_MONITORING=true
export ENABLE_RL_SHADOW_EVAL=true

# Performance settings
export RL_BATCH_SIZE=100
export RL_UPDATE_INTERVAL=10
export RL_MEMORY_LIMIT_MB=1024

# DoublyRobust optimization
export RL_DR_ALPHA=1.2
export RL_DR_LEARNING_RATE=0.08
export RL_DR_LR_DECAY=0.999
export RL_DR_MAX_WEIGHT=3.0
export RL_DR_MAX_HISTORY=5000

# OffsetTree optimization
export RL_OT_MAX_DEPTH=3
export RL_OT_MIN_SPLIT=25
export RL_OT_SPLIT_THRESHOLD=0.2
export RL_OT_MAX_NODES=2000

# Rollout settings
export RL_ROLLOUT_PERCENTAGE=0.20
export RL_ROLLOUT_DOMAINS=model_routing,content_analysis

# Monitoring thresholds
export RL_LATENCY_THRESHOLD_MS=100
export RL_MEMORY_THRESHOLD_MB=512
export RL_ERROR_RATE_THRESHOLD=0.05
```

### Auto-tuning Configuration

```python
import optuna
from typing import Dict, Any

class BanditAutoTuner:
    """Automated hyperparameter tuning for bandit algorithms."""

    def __init__(self, evaluation_metric='reward_mean'):
        self.evaluation_metric = evaluation_metric
        self.study = None

    def optimize_doubly_robust(self, n_trials=100):
        """Optimize DoublyRobust hyperparameters."""

        def objective(trial):
            # Suggest hyperparameters
            alpha = trial.suggest_float('alpha', 0.5, 3.0)
            learning_rate = trial.suggest_float('learning_rate', 0.01, 0.3)
            lr_decay = trial.suggest_float('lr_decay', 0.99, 0.9999)
            max_weight = trial.suggest_float('max_weight', 2.0, 10.0)

            # Test configuration
            config = {
                'alpha': alpha,
                'learning_rate': learning_rate,
                'lr_decay': lr_decay,
                'max_weight': max_weight
            }

            # Evaluate performance (implement your evaluation logic)
            performance = self._evaluate_configuration('doubly_robust', config)

            return performance[self.evaluation_metric]

        self.study = optuna.create_study(direction='maximize')
        self.study.optimize(objective, n_trials=n_trials)

        return self.study.best_params

    def optimize_offset_tree(self, n_trials=50):
        """Optimize OffsetTree hyperparameters."""

        def objective(trial):
            # Suggest hyperparameters
            max_depth = trial.suggest_int('max_depth', 2, 6)
            min_samples_split = trial.suggest_int('min_samples_split', 10, 50)
            split_threshold = trial.suggest_float('split_threshold', 0.05, 0.5)

            config = {
                'max_depth': max_depth,
                'min_samples_split': min_samples_split,
                'split_threshold': split_threshold
            }

            performance = self._evaluate_configuration('offset_tree', config)
            return performance[self.evaluation_metric]

        self.study = optuna.create_study(direction='maximize')
        self.study.optimize(objective, n_trials=n_trials)

        return self.study.best_params

    def _evaluate_configuration(self, algorithm: str, config: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate a configuration (implement based on your evaluation framework)."""

        # This would run your bandit with the configuration and measure performance
        # Return metrics like reward_mean, latency_p95, memory_usage, etc.

        # Placeholder implementation
        return {
            'reward_mean': 0.75,
            'latency_p95': 45.0,
            'memory_usage': 256.0,
            'error_rate': 0.02
        }
```

## Performance Benchmarking

### Benchmark Suite

```python
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt

class BanditBenchmark:
    """Comprehensive benchmarking suite for bandit algorithms."""

    def __init__(self):
        self.results = {}

    def benchmark_throughput(self, algorithm_name: str, bandit_instance,
                           n_requests=10000, n_threads=10):
        """Benchmark recommendation throughput."""

        # Generate test data
        contexts = self._generate_test_contexts(n_requests)
        candidates = ['option1', 'option2', 'option3', 'option4']

        # Single-threaded benchmark
        start_time = time.time()
        for context in contexts[:1000]:  # Sample for single-threaded
            bandit_instance.recommend(context, candidates)
        single_thread_time = time.time() - start_time

        # Multi-threaded benchmark
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = []
            for context in contexts:
                future = executor.submit(bandit_instance.recommend, context, candidates)
                futures.append(future)

            # Wait for completion
            for future in as_completed(futures):
                future.result()

        multi_thread_time = time.time() - start_time

        # Calculate metrics
        single_thread_rps = 1000 / single_thread_time
        multi_thread_rps = n_requests / multi_thread_time

        self.results[f"{algorithm_name}_throughput"] = {
            'single_thread_rps': single_thread_rps,
            'multi_thread_rps': multi_thread_rps,
            'scaling_factor': multi_thread_rps / single_thread_rps,
            'avg_latency_ms': (multi_thread_time / n_requests) * 1000
        }

        return self.results[f"{algorithm_name}_throughput"]

    def benchmark_memory_usage(self, algorithm_name: str, bandit_instance,
                              n_updates=10000):
        """Benchmark memory usage over time."""

        import psutil
        process = psutil.Process()

        memory_usage = []
        contexts = self._generate_test_contexts(n_updates)

        # Initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024

        for i, context in enumerate(contexts):
            # Make recommendation and update
            candidates = ['option1', 'option2', 'option3']
            action = bandit_instance.recommend(context, candidates)
            reward = np.random.random()  # Simulated reward
            bandit_instance.update(action, reward, context)

            # Track memory every 100 updates
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_usage.append(current_memory - initial_memory)

        self.results[f"{algorithm_name}_memory"] = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': memory_usage[-1] + initial_memory,
            'memory_growth_mb': memory_usage[-1],
            'memory_growth_rate': memory_usage[-1] / len(memory_usage),
            'memory_timeline': memory_usage
        }

        return self.results[f"{algorithm_name}_memory"]

    def benchmark_convergence(self, algorithm_name: str, bandit_instance,
                             n_rounds=5000):
        """Benchmark convergence speed and quality."""

        # Simulate environment with known optimal action
        optimal_action = 'option2'
        action_rewards = {
            'option1': 0.3,
            'option2': 0.8,  # Optimal
            'option3': 0.5,
            'option4': 0.4
        }

        regret_history = []
        cumulative_regret = 0
        optimal_selections = 0

        for round_num in range(n_rounds):
            # Generate context
            context = self._generate_test_contexts(1)[0]

            # Get recommendation
            candidates = list(action_rewards.keys())
            selected_action = bandit_instance.recommend(context, candidates)

            # Calculate reward and regret
            reward = action_rewards[selected_action] + np.random.normal(0, 0.1)
            optimal_reward = action_rewards[optimal_action]
            regret = optimal_reward - action_rewards[selected_action]

            cumulative_regret += regret
            regret_history.append(cumulative_regret)

            if selected_action == optimal_action:
                optimal_selections += 1

            # Update bandit
            bandit_instance.update(selected_action, reward, context)

        self.results[f"{algorithm_name}_convergence"] = {
            'final_regret': cumulative_regret,
            'regret_history': regret_history,
            'optimal_selection_rate': optimal_selections / n_rounds,
            'convergence_round': self._find_convergence_point(regret_history)
        }

        return self.results[f"{algorithm_name}_convergence"]

    def _generate_test_contexts(self, n_contexts: int) -> List[Dict[str, float]]:
        """Generate test contexts for benchmarking."""

        contexts = []
        for _ in range(n_contexts):
            context = {
                'feature1': np.random.random(),
                'feature2': np.random.random(),
                'feature3': np.random.random(),
                'feature4': np.random.random(),
                'feature5': np.random.random()
            }
            contexts.append(context)

        return contexts

    def _find_convergence_point(self, regret_history: List[float]) -> int:
        """Find the point where regret slope becomes minimal."""

        if len(regret_history) < 100:
            return len(regret_history)

        # Calculate moving slopes
        window_size = 50
        slopes = []

        for i in range(window_size, len(regret_history)):
            recent_regrets = regret_history[i-window_size:i]
            slope = (recent_regrets[-1] - recent_regrets[0]) / window_size
            slopes.append(slope)

        # Find where slope becomes small and stable
        convergence_threshold = 0.01
        for i, slope in enumerate(slopes):
            if abs(slope) < convergence_threshold:
                return i + window_size

        return len(regret_history)

    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""

        report = "# Bandit Algorithm Performance Report\n\n"

        for algorithm, metrics in self.results.items():
            report += f"## {algorithm}\n\n"

            if 'throughput' in algorithm:
                report += f"- Single-threaded RPS: {metrics['single_thread_rps']:.1f}\n"
                report += f"- Multi-threaded RPS: {metrics['multi_thread_rps']:.1f}\n"
                report += f"- Scaling factor: {metrics['scaling_factor']:.2f}x\n"
                report += f"- Average latency: {metrics['avg_latency_ms']:.2f}ms\n\n"

            elif 'memory' in algorithm:
                report += f"- Initial memory: {metrics['initial_memory_mb']:.1f}MB\n"
                report += f"- Final memory: {metrics['final_memory_mb']:.1f}MB\n"
                report += f"- Memory growth: {metrics['memory_growth_mb']:.1f}MB\n"
                report += f"- Growth rate: {metrics['memory_growth_rate']:.3f}MB/update\n\n"

            elif 'convergence' in algorithm:
                report += f"- Final regret: {metrics['final_regret']:.3f}\n"
                report += f"- Optimal selection rate: {metrics['optimal_selection_rate']:.3f}\n"
                report += f"- Convergence round: {metrics['convergence_round']}\n\n"

        return report

# Example usage
benchmark = BanditBenchmark()

# Benchmark different algorithms
from core.rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit

# DoublyRobust benchmark
dr_bandit = DoublyRobustBandit(alpha=1.2, learning_rate=0.08)
dr_throughput = benchmark.benchmark_throughput('DoublyRobust', dr_bandit)
dr_memory = benchmark.benchmark_memory_usage('DoublyRobust', dr_bandit)
dr_convergence = benchmark.benchmark_convergence('DoublyRobust', dr_bandit)

# OffsetTree benchmark
ot_bandit = OffsetTreeBandit(max_depth=3, min_samples_split=20)
ot_throughput = benchmark.benchmark_throughput('OffsetTree', ot_bandit)
ot_memory = benchmark.benchmark_memory_usage('OffsetTree', ot_bandit)
ot_convergence = benchmark.benchmark_convergence('OffsetTree', ot_bandit)

# Generate report
report = benchmark.generate_report()
print(report)

# Save detailed results
with open('/logs/bandit_benchmark_results.json', 'w') as f:
    json.dump(benchmark.results, f, indent=2)
```

This performance optimization guide provides comprehensive strategies for maximizing the efficiency and scalability of the advanced contextual bandit system across memory usage, computational performance, network I/O, monitoring, and configuration tuning.

## Last Updated

Performance Optimization Guide Last Updated: September 2025
