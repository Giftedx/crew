# Advanced Contextual Bandit Algorithms

A sophisticated off-policy learning system implementing DoublyRobust and OffsetTree algorithms for enhanced decision making in multi-tenant environments.

## Overview

This system provides state-of-the-art contextual bandit algorithms that significantly improve upon traditional epsilon-greedy and Thompson sampling approaches through:

- **DoublyRobust Estimation**: Combines importance sampling with outcome modeling for robust off-policy evaluation
- **OffsetTree Algorithm**: Tree-based contextual understanding with adaptive splitting strategies
- **Shadow Evaluation**: Risk-free A/B testing framework for algorithm validation
- **Production-Ready Configuration**: Enterprise-grade feature flags and rollout controls

## Quick Start

### Basic Setup

Enable advanced bandits with minimal configuration:

```bash
# Enable advanced algorithms globally
export ENABLE_RL_ADVANCED=true

# Start with 10% traffic for safety
export RL_ROLLOUT_PERCENTAGE=0.10

# Enable shadow evaluation for comparison
export ENABLE_RL_SHADOW_EVAL=true
```

### Policy Selection

The system automatically selects algorithms based on configuration:

```python
from core.learning_engine import LearningEngine

# Initialize with automatic policy selection
engine = LearningEngine()

# Register domain with advanced algorithm
engine.register_domain("model_routing", policy="doubly_robust")

# Make recommendations with context
context = {"user_tier": "premium", "request_complexity": 0.8}
candidates = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
choice = engine.recommend("model_routing", context, candidates)

# Record reward for learning
engine.record("model_routing", context, choice, reward=1.0)
```

## Algorithm Details

### DoublyRobust Bandit

Combines reward modeling with importance sampling for enhanced off-policy learning:

**Key Features:**

- Learns reward models for each action using linear regression
- Uses importance weighting to correct for distribution shift
- Adaptive learning rate scheduling with decay
- Confidence-based exploration with uncertainty quantification

**Configuration Parameters:**

```bash
# Core algorithm parameters
export RL_DR_ALPHA=1.0              # Confidence parameter for exploration
export RL_DR_LEARNING_RATE=0.1      # Initial learning rate for reward models
export RL_DR_DIM=8                  # Context feature dimension

# Learning rate scheduling
export RL_DR_LR_DECAY=0.995         # Decay factor per update
export RL_DR_MIN_LR=0.001           # Minimum learning rate floor
export RL_DR_ADAPTIVE_LR=true       # Enable adaptive scheduling

# Importance sampling controls
export RL_DR_MAX_WEIGHT=10.0        # Maximum importance weight (clamping)
export RL_DR_MIN_WEIGHT=0.01        # Minimum importance weight threshold
```

**When to Use:**

- High-stakes decisions where off-policy evaluation is critical
- Environments with distribution shift between training and serving
- When you have historical data from different policies
- Need robust performance guarantees

### OffsetTree Bandit

Tree-based contextual bandit with adaptive context space partitioning:

**Key Features:**

- Automatically partitions context space using decision trees
- Uses variance reduction for intelligent splitting decisions
- Supports multiple base bandit algorithms per leaf
- Handles missing features gracefully

**Configuration Parameters:**

```bash
# Tree structure controls
export RL_OT_MAX_DEPTH=3            # Maximum tree depth
export RL_OT_MIN_SPLIT=10           # Minimum samples to consider split
export RL_OT_SPLIT_THRESHOLD=0.1    # Minimum variance reduction for split

# Tree optimization
export RL_OT_SPLIT_STRATEGY=variance        # variance, information_gain, mse
export RL_OT_FEATURE_SELECTION=all         # all, random, best
export RL_OT_MAX_FEATURES=5                 # Limit features per split

# Base bandit configuration
export RL_OT_BASE_BANDIT=thompson           # thompson, epsilon_greedy, ucb1
export RL_OT_HISTORY_SIZE=10000            # Context history size
```

**When to Use:**

- Complex context spaces with non-linear relationships
- When context features have hierarchical structure
- Need interpretable decision boundaries
- Heterogeneous user populations requiring segmentation

## Configuration Guide

### Environment Variables

The system supports 30+ environment variables for complete customization:

#### Global Controls

```bash
# Master switches
export ENABLE_RL_ADVANCED=true              # Enable advanced algorithms
export ENABLE_RL_SHADOW_EVAL=true           # Enable A/B testing
export ENABLE_RL_AUTO_TUNING=false          # Enable auto-hyperparameter tuning
export ENABLE_RL_MONITORING=true            # Enable enhanced metrics

# Rollout controls
export RL_ROLLOUT_PERCENTAGE=0.25           # Percentage of traffic (0.0-1.0)
export RL_ROLLOUT_DOMAINS=model_routing,content_analysis  # Specific domains
export RL_ROLLOUT_TENANTS=premium_tenant,enterprise_corp  # Specific tenants
```

#### A/B Testing Configuration

```bash
# Shadow evaluation thresholds
export RL_SHADOW_THRESHOLD=500              # Samples before activation consideration
export RL_IMPROVEMENT_THRESHOLD=0.05        # 5% improvement required for promotion
export RL_DEGRADATION_THRESHOLD=-0.10       # 10% degradation triggers alarm

# Auto-activation controls
export RL_AUTO_ACTIVATE_AFTER=1000          # Samples before auto-activation
export RL_CONFIDENCE_LEVEL=0.95             # Statistical confidence required
```

### Domain-Specific Configuration

Configure different parameters per domain:

```python
from core.rl.advanced_config import get_config_manager

# Get configuration manager
config_manager = get_config_manager()

# Configure high-frequency domain with faster learning
fast_dr_config = DoublyRobustConfig(
    learning_rate=0.2,
    learning_rate_decay=0.99,
    alpha=0.5,  # Less exploration
)

# Configure complex domain with deeper trees
complex_ot_config = OffsetTreeConfig(
    max_depth=5,
    min_samples_split=20,
    split_strategy="information_gain",
)

# Apply domain-specific configs
config_manager.set_domain_config(
    "high_frequency_routing",
    doubly_robust_config=fast_dr_config
)

config_manager.set_domain_config(
    "complex_content_analysis",
    offset_tree_config=complex_ot_config
)
```

## Monitoring and Observability

### Key Metrics

The system exposes comprehensive metrics for monitoring:

#### Algorithm Performance

- `advanced_bandit_reward_model_mse`: DoublyRobust prediction accuracy
- `advanced_bandit_tree_depth`: OffsetTree complexity evolution
- `advanced_bandit_importance_weight`: Off-policy correction magnitude
- `advanced_bandit_confidence_interval`: Uncertainty quantification

#### Experiment Tracking

- `experiment_variant_allocations_total`: A/B test traffic distribution
- `experiment_rewards_total`: Reward collection by variant
- `experiment_regret_total`: Cumulative regret vs baseline
- `trajectory_evaluations_total`: LLM-as-judge evaluations

### Dashboard Queries

Example Prometheus queries for monitoring:

```promql
# Algorithm adoption rate
rate(experiment_variant_allocations_total{variant=~"doubly_robust|offset_tree"}[5m])

# Performance improvement over baseline
(
  rate(experiment_rewards_total{variant="doubly_robust"}[1h]) -
  rate(experiment_rewards_total{variant="epsilon_greedy"}[1h])
) / rate(experiment_rewards_total{variant="epsilon_greedy"}[1h]) * 100

# Tree complexity growth
increase(advanced_bandit_tree_depth[1d])

# Reward model accuracy degradation alert
advanced_bandit_reward_model_mse > 0.5
```

### Alerting Rules

Critical alerts for production deployment:

```yaml
groups:
- name: advanced_bandits
  rules:
  - alert: AdvancedBanditDegradation
    expr: experiment_regret_total > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Advanced bandit showing degradation"

  - alert: RewardModelAccuracyDrop
    expr: advanced_bandit_reward_model_mse > 1.0
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "DoublyRobust reward model accuracy degraded"
```

## Production Deployment

### Rollout Strategy

Recommended phased deployment approach:

#### Phase 1: Shadow Evaluation (Week 1-2)

```bash
export ENABLE_RL_ADVANCED=true
export ENABLE_RL_SHADOW_EVAL=true
export RL_ROLLOUT_PERCENTAGE=0.0    # Shadow only, no traffic
export RL_SHADOW_THRESHOLD=100      # Low threshold for quick results
```

Monitor shadow metrics for 1-2 weeks to establish baseline performance.

#### Phase 2: Limited Rollout (Week 3-4)

```bash
export RL_ROLLOUT_PERCENTAGE=0.05   # 5% of traffic
export RL_ROLLOUT_DOMAINS=low_risk_domain  # Start with low-risk areas
export RL_IMPROVEMENT_THRESHOLD=0.03       # 3% improvement required
```

Gradually increase traffic based on performance metrics.

#### Phase 3: Expanded Deployment (Week 5-8)

```bash
export RL_ROLLOUT_PERCENTAGE=0.25   # 25% of traffic
export RL_ROLLOUT_DOMAINS=model_routing,content_analysis,memory_retrieval
```

Expand to critical domains with established performance gains.

#### Phase 4: Full Deployment (Week 9+)

```bash
export RL_ROLLOUT_PERCENTAGE=1.0    # Full traffic
# Remove domain restrictions for global deployment
```

### Troubleshooting

#### Common Issues

**1. No Algorithm Selection**

```bash
# Check if advanced bandits are enabled
echo $ENABLE_RL_ADVANCED

# Verify domain is in rollout list
echo $RL_ROLLOUT_DOMAINS

# Check rollout percentage
echo $RL_ROLLOUT_PERCENTAGE
```

**2. Poor Performance**

```bash
# Increase learning rate for faster adaptation
export RL_DR_LEARNING_RATE=0.2

# Reduce tree depth for simpler decisions
export RL_OT_MAX_DEPTH=2

# Check context feature quality
# Ensure features are normalized and informative
```

**3. High Memory Usage**

```bash
# Reduce history sizes
export RL_DR_MAX_HISTORY=500
export RL_OT_HISTORY_SIZE=5000

# Enable more aggressive cleanup
export RL_DR_CLEANUP_THRESHOLD=0.6
```

### Performance Tuning

#### DoublyRobust Optimization

For high-frequency domains:

```bash
export RL_DR_LEARNING_RATE=0.15     # Faster adaptation
export RL_DR_LR_DECAY=0.998         # Slower decay
export RL_DR_DIM=4                  # Fewer features for speed
export RL_DR_MAX_WEIGHT=5.0         # Lower weight variance
```

For high-accuracy domains:

```bash
export RL_DR_LEARNING_RATE=0.05     # More stable learning
export RL_DR_DIM=16                 # More feature capacity
export RL_DR_ALPHA=2.0              # More exploration
export RL_DR_L2_REGULARIZATION=0.01 # Prevent overfitting
```

#### OffsetTree Optimization

For complex contexts:

```bash
export RL_OT_MAX_DEPTH=5            # Deeper trees
export RL_OT_MIN_SPLIT=15           # More conservative splits
export RL_OT_SPLIT_STRATEGY=information_gain  # Better feature selection
export RL_OT_MAX_FEATURES=10        # More features per split
```

For simple contexts:

```bash
export RL_OT_MAX_DEPTH=2            # Shallow trees
export RL_OT_MIN_SPLIT=5            # Aggressive splitting
export RL_OT_SPLIT_STRATEGY=variance  # Fast splitting criterion
```

## Advanced Usage

### Custom Reward Functions

Implement domain-specific reward calculations:

```python
from core.learning_engine import LearningEngine

class CustomRewardEngine(LearningEngine):
    def record_with_custom_reward(self, domain: str, context: dict,
                                 action: str, outcome: dict) -> None:
        # Custom reward calculation
        if domain == "model_routing":
            # Combine latency, cost, and quality
            latency_penalty = max(0, (outcome['latency'] - 1000) / 1000)
            cost_penalty = outcome['cost'] / 100
            quality_bonus = outcome['quality_score']

            reward = quality_bonus - latency_penalty - cost_penalty
        else:
            reward = outcome.get('reward', 0.0)

        self.record(domain, context, action, reward)
```

### Multi-Objective Optimization

Configure algorithms for multiple objectives:

```python
from core.rl.policies.advanced_bandits import DoublyRobustBandit

# Multi-objective DoublyRobust with weighted rewards
class MultiObjectiveBandit(DoublyRobustBandit):
    def __init__(self, objectives: dict[str, float], **kwargs):
        super().__init__(**kwargs)
        self.objectives = objectives  # {"latency": -0.3, "cost": -0.2, "quality": 0.5}

    def update(self, action, rewards: dict, context):
        # Combine multiple rewards with weights
        combined_reward = sum(
            self.objectives[obj] * rewards[obj]
            for obj in self.objectives
        )
        super().update(action, combined_reward, context)
```

### Integration with External Systems

#### MLflow Integration

Track experiments and model performance:

```python
import mlflow
from core.rl.advanced_experiments import AdvancedBanditExperimentManager

class MLflowExperimentManager(AdvancedBanditExperimentManager):
    def record_advanced_metrics(self, experiment_id, arm, reward, context=None, bandit_instance=None):
        super().record_advanced_metrics(experiment_id, arm, reward, context, bandit_instance)

        # Log to MLflow
        with mlflow.start_run(run_name=f"{experiment_id}_{arm}"):
            mlflow.log_metric("reward", reward)
            if context:
                mlflow.log_params(context)
            if isinstance(bandit_instance, DoublyRobustBandit):
                mlflow.log_metric("learning_rate", bandit_instance.learning_rate)
                mlflow.log_metric("alpha", bandit_instance.alpha)
```

#### Real-time Feature Stores

Integrate with feature stores for dynamic context:

```python
from feast import FeatureStore

class FeatureStoreEngine(LearningEngine):
    def __init__(self, feature_store_path: str):
        super().__init__()
        self.store = FeatureStore(repo_path=feature_store_path)

    def recommend_with_features(self, domain: str, entity_id: str, candidates):
        # Fetch real-time features
        features = self.store.get_online_features(
            features=["user_features:age", "user_features:tier", "session_features:complexity"],
            entity_rows=[{"user_id": entity_id}]
        ).to_dict()

        context = {k.split(":")[-1]: v[0] for k, v in features.items()}
        return self.recommend(domain, context, candidates)
```

## API Reference

### Core Classes

#### DoublyRobustBandit

```python
class DoublyRobustBandit:
    def __init__(self, alpha: float = 1.0, dim: int = 8, learning_rate: float = 0.1):
        """Initialize DoublyRobust bandit.

        Args:
            alpha: Confidence parameter for exploration
            dim: Context feature dimension
            learning_rate: Initial learning rate for reward models
        """

    def recommend(self, context: dict, candidates: list) -> Any:
        """Recommend action using doubly robust estimation."""

    def update(self, action: Any, reward: float, context: dict) -> None:
        """Update with reward feedback."""

    def update_with_importance_weight(self, action: Any, reward: float,
                                    context: dict, importance_weight: float) -> None:
        """Update with explicit importance weight for off-policy learning."""
```

#### OffsetTreeBandit

```python
class OffsetTreeBandit:
    def __init__(self, max_depth: int = 3, min_samples_split: int = 10,
                 split_threshold: float = 0.1):
        """Initialize OffsetTree bandit.

        Args:
            max_depth: Maximum tree depth
            min_samples_split: Minimum samples to split node
            split_threshold: Minimum variance reduction for split
        """

    def recommend(self, context: dict, candidates: list) -> Any:
        """Recommend using tree-based contextual understanding."""

    def update(self, action: Any, reward: float, context: dict) -> None:
        """Update tree and leaf bandit."""
```

#### AdvancedBanditConfigManager

```python
class AdvancedBanditConfigManager:
    def load_from_environment(self) -> None:
        """Load configuration from environment variables."""

    def get_doubly_robust_config(self, domain: str = "default") -> DoublyRobustConfig:
        """Get DoublyRobust configuration for domain."""

    def get_offset_tree_config(self, domain: str = "default") -> OffsetTreeConfig:
        """Get OffsetTree configuration for domain."""

    def is_enabled_for_domain(self, domain: str) -> bool:
        """Check if advanced bandits enabled for domain."""

    def set_domain_config(self, domain: str,
                         doubly_robust_config: DoublyRobustConfig = None,
                         offset_tree_config: OffsetTreeConfig = None) -> None:
        """Set domain-specific configurations."""
```

### Configuration Classes

#### DoublyRobustConfig

```python
@dataclass
class DoublyRobustConfig:
    # Core parameters
    alpha: float = 1.0
    learning_rate: float = 0.1
    dim: int = 8

    # Learning rate scheduling
    learning_rate_decay: float = 0.995
    min_learning_rate: float = 0.001
    adaptive_learning_rate: bool = True

    # Importance sampling
    max_importance_weight: float = 10.0
    min_importance_weight: float = 0.01
    importance_weight_smoothing: float = 0.9

    # Regularization
    l2_regularization: float = 0.001
    variance_smoothing: float = 0.9
    confidence_scaling: float = 1.0
```

#### OffsetTreeConfig

```python
@dataclass
class OffsetTreeConfig:
    # Tree structure
    max_depth: int = 3
    min_samples_split: int = 10
    split_threshold: float = 0.1

    # Optimization
    split_strategy: str = "variance"  # variance, information_gain, mse
    feature_selection: str = "all"    # all, random, best
    max_features_per_split: int | None = None

    # Node management
    max_leaf_nodes: int | None = None
    min_samples_leaf: int = 5
    pruning_threshold: float = 0.05

    # Base bandit
    base_bandit_type: str = "thompson"
    base_bandit_params: dict[str, Any] = field(default_factory=dict)
```

## Contributing

### Development Setup

1. **Install Dependencies**

```bash
pip install -e '.[dev]'
make setup
```

2. **Run Tests**

```bash
make test-fast          # Quick tests
make test               # Full test suite
make test-advanced      # Advanced bandit tests only
```

3. **Code Quality**

```bash
make format lint type   # Auto-fix and check
make compliance         # Audit patterns
```

### Adding New Algorithms

To add a new bandit algorithm:

1. **Implement Algorithm**

```python
# In src/core/rl/policies/my_algorithm.py
from .bandit_base import _BanditLike

class MyBandit(_BanditLike):
    def recommend(self, context: dict, candidates: list) -> Any:
        # Algorithm implementation
        pass

    def update(self, action: Any, reward: float, context: dict) -> None:
        # Learning implementation
        pass
```

2. **Add Configuration**

```python
# In src/core/rl/advanced_config.py
@dataclass
class MyBanditConfig:
    param1: float = 1.0
    param2: int = 10
```

3. **Register in Learning Engine**

```python
# In src/core/learning_engine.py
elif p in {"my_algorithm", "my_bandit"}:
    config = config_manager.get_my_bandit_config()
    bandit = MyBandit(param1=config.param1, param2=config.param2)
```

4. **Add Tests**

```python
# In tests/core/rl/policies/test_my_algorithm.py
class TestMyBandit:
    def test_recommendation(self):
        bandit = MyBandit()
        result = bandit.recommend({"feature": 0.5}, ["a", "b"])
        assert result in ["a", "b"]
```

### Performance Benchmarks

Run performance benchmarks to validate improvements:

```bash
# Benchmark against baselines
python benchmarks/bandit_comparison.py --algorithms doubly_robust,offset_tree,epsilon_greedy

# Load testing
python benchmarks/load_test.py --concurrent-users 100 --duration 300

# Memory profiling
python benchmarks/memory_profile.py --algorithm doubly_robust --contexts 10000
```

Expected performance improvements:

- **10-30%** reward improvement over epsilon-greedy in contextual scenarios
- **5-15%** improvement over Thompson sampling with proper tuning
- **Sub-millisecond** recommendation latency for contexts with <50 features
- **Linear memory usage** in context history size

## License and Support

This advanced bandit system is part of the Ultimate Discord Intelligence Bot project.

**Support Channels:**

- Internal documentation: `/docs/rl/advanced-bandits/`
- Metrics dashboard: `https://monitoring.internal/dashboards/advanced-bandits`
- Incident response: Follow standard on-call procedures for algorithm degradation

**Version Compatibility:**

- Python 3.9+ required for type annotations
- Compatible with existing CrewAI orchestration
- Backward compatible with all existing bandit policies
- Progressive enhancement - can be disabled without affecting existing functionality

---

*Last updated: September 2025*
*Next review: October 2025 (monthly cadence for rapidly evolving algorithms)*
