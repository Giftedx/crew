# Advanced Contextual Bandits API Reference

Complete API documentation for the advanced contextual bandit system.

## Core Classes

### DoublyRobustBandit

**Location:** `src/core/rl/policies/advanced_bandits.py`

```python
class DoublyRobustBandit:
    """Doubly Robust estimator for off-policy contextual bandits."""
```

#### Constructor

```python
def __init__(
    self,
    alpha: float = 1.0,
    dim: int = 8,
    learning_rate: float = 0.1
) -> None
```

**Parameters:**

- `alpha` (float): Confidence parameter for exploration. Higher values increase exploration.
- `dim` (int): Context feature dimension. Must match the number of features in context vectors.
- `learning_rate` (float): Initial learning rate for reward model updates.

#### Methods

##### recommend()

```python
def recommend(
    self,
    context: dict[str, Any],
    candidates: Sequence[Any]
) -> Any
```

Recommend action using doubly robust estimation with confidence intervals.

**Parameters:**

- `context` (dict): Context features as key-value pairs
- `candidates` (Sequence): Available actions to choose from

**Returns:**

- Action with highest upper confidence bound

**Raises:**

- `ValueError`: If candidates list is empty

**Example:**

```python
bandit = DoublyRobustBandit(alpha=2.0, dim=4)
context = {"user_tier": 1.0, "complexity": 0.8}
action = bandit.recommend(context, ["fast", "accurate", "balanced"])
```

##### update()

```python
def update(
    self,
    action: Any,
    reward: float,
    context: dict[str, Any]
) -> None
```

Update bandit with reward feedback using standard importance sampling.

**Parameters:**

- `action`: The action that was taken
- `reward` (float): Observed reward (any real number)
- `context` (dict): Context features when action was taken

**Example:**

```python
bandit.update("fast", 0.85, {"user_tier": 1.0, "complexity": 0.8})
```

##### update_with_importance_weight()

```python
def update_with_importance_weight(
    self,
    action: Any,
    reward: float,
    context: dict[str, Any],
    importance_weight: float
) -> None
```

Update with explicit importance weight for off-policy learning.

**Parameters:**

- `action`: The action that was taken
- `reward` (float): Observed reward
- `context` (dict): Context features
- `importance_weight` (float): Importance sampling weight (clamped to [0.01, 10.0])

**Example:**

```python
# Historical data from different policy
bandit.update_with_importance_weight(
    action="accurate",
    reward=1.0,
    context={"user_tier": 2.0},
    importance_weight=2.5  # Different policy was 2.5x more likely to choose this
)
```

##### state_dict()

```python
def state_dict(self) -> dict[str, Any]
```

Serialize bandit state for persistence.

**Returns:**

- Dictionary containing all bandit state including reward models and importance weights

##### load_state()

```python
def load_state(self, state: dict[str, Any]) -> None
```

Load bandit state from serialized format.

**Parameters:**

- `state` (dict): State dictionary from `state_dict()`

### OffsetTreeBandit

**Location:** `src/core/rl/policies/advanced_bandits.py`

```python
class OffsetTreeBandit:
    """OffsetTree algorithm for contextual bandits."""
```

#### Constructor

```python
def __init__(
    self,
    max_depth: int = 3,
    min_samples_split: int = 10,
    split_threshold: float = 0.1,
    base_bandit_factory: Callable[[], Any] = None
) -> None
```

**Parameters:**

- `max_depth` (int): Maximum tree depth
- `min_samples_split` (int): Minimum samples required to split a node
- `split_threshold` (float): Minimum variance reduction required for split
- `base_bandit_factory` (Callable): Factory function for leaf bandits

#### Methods

##### recommend()

```python
def recommend(
    self,
    context: dict[str, Any],
    candidates: Sequence[Any]
) -> Any
```

Recommend action using tree-based contextual understanding.

**Parameters:**

- `context` (dict): Context features
- `candidates` (Sequence): Available actions

**Returns:**

- Action recommended by appropriate leaf bandit

**Example:**

```python
tree_bandit = OffsetTreeBandit(max_depth=4, min_samples_split=15)
context = {"user_age": 25, "session_length": 300, "device": "mobile"}
action = tree_bandit.recommend(context, ["recommendation_a", "recommendation_b"])
```

##### update()

```python
def update(
    self,
    action: Any,
    reward: float,
    context: dict[str, Any]
) -> None
```

Update tree structure and leaf bandit.

**Parameters:**

- `action`: Action that was taken
- `reward` (float): Observed reward
- `context` (dict): Context features

**Side Effects:**

- May trigger tree splits if conditions are met
- Updates context history
- Updates leaf bandit at appropriate node

### AdvancedBanditConfigManager

**Location:** `src/core/rl/advanced_config.py`

```python
class AdvancedBanditConfigManager:
    """Centralized configuration manager for advanced bandit algorithms."""
```

#### Methods

##### get_config_manager()

```python
def get_config_manager() -> AdvancedBanditConfigManager
```

Get the global configuration manager singleton.

**Returns:**

- Global configuration manager instance

##### load_from_environment()

```python
def load_from_environment(self) -> None
```

Load all configuration from environment variables.

**Environment Variables:**

- Global: `ENABLE_RL_ADVANCED`, `RL_ROLLOUT_PERCENTAGE`, etc.
- DoublyRobust: `RL_DR_ALPHA`, `RL_DR_LEARNING_RATE`, etc.
- OffsetTree: `RL_OT_MAX_DEPTH`, `RL_OT_MIN_SPLIT`, etc.

##### get_doubly_robust_config()

```python
def get_doubly_robust_config(self, domain: str = "default") -> DoublyRobustConfig
```

Get DoublyRobust configuration for a specific domain.

**Parameters:**

- `domain` (str): Domain name, defaults to "default"

**Returns:**

- DoublyRobustConfig instance with domain-specific or default settings

##### get_offset_tree_config()

```python
def get_offset_tree_config(self, domain: str = "default") -> OffsetTreeConfig
```

Get OffsetTree configuration for a specific domain.

**Parameters:**

- `domain` (str): Domain name, defaults to "default"

**Returns:**

- OffsetTreeConfig instance with domain-specific or default settings

##### is_enabled_for_domain()

```python
def is_enabled_for_domain(self, domain: str) -> bool
```

Check if advanced bandits are enabled for a specific domain.

**Parameters:**

- `domain` (str): Domain name to check

**Returns:**

- True if advanced bandits should be used for this domain

**Logic:**

1. Check global `enable_advanced_bandits` flag
2. Check if domain is in `rollout_domains` list (if specified)
3. Apply hash-based percentage routing

##### set_domain_config()

```python
def set_domain_config(
    self,
    domain: str,
    doubly_robust_config: DoublyRobustConfig | None = None,
    offset_tree_config: OffsetTreeConfig | None = None,
) -> None
```

Set domain-specific configurations.

**Parameters:**

- `domain` (str): Domain name
- `doubly_robust_config` (optional): DoublyRobust config for this domain
- `offset_tree_config` (optional): OffsetTree config for this domain

## Configuration Classes

### DoublyRobustConfig

```python
@dataclass
class DoublyRobustConfig:
    # Core algorithm parameters
    alpha: float = 1.0
    learning_rate: float = 0.1
    dim: int = 8

    # Learning rate scheduling
    learning_rate_decay: float = 0.995
    min_learning_rate: float = 0.001
    adaptive_learning_rate: bool = True

    # Importance sampling controls
    max_importance_weight: float = 10.0
    min_importance_weight: float = 0.01
    importance_weight_smoothing: float = 0.9

    # Reward model regularization
    l2_regularization: float = 0.001
    variance_smoothing: float = 0.9
    confidence_scaling: float = 1.0

    # Memory management
    max_history_size: int = 1000
    cleanup_threshold: float = 0.8
```

**Validation:**

- `alpha` must be positive
- `learning_rate` must be in (0, 1]
- `dim` must be positive
- `max_importance_weight` must be > `min_importance_weight`

### OffsetTreeConfig

```python
@dataclass
class OffsetTreeConfig:
    # Tree structure parameters
    max_depth: int = 3
    min_samples_split: int = 10
    split_threshold: float = 0.1

    # Tree optimization
    split_strategy: str = "variance"  # variance, information_gain, mse
    feature_selection: str = "all"    # all, random, best
    max_features_per_split: int | None = None

    # Node management
    max_leaf_nodes: int | None = None
    min_samples_leaf: int = 5
    pruning_threshold: float = 0.05

    # Context handling
    context_history_size: int = 10000
    history_cleanup_size: int = 5000
    missing_feature_strategy: str = "default_left"

    # Base bandit configuration
    base_bandit_type: str = "thompson"
    base_bandit_params: dict[str, Any] = field(default_factory=dict)
```

**Validation:**

- `max_depth` must be positive
- `min_samples_split` must be > 1
- `split_strategy` must be one of: variance, information_gain, mse
- `feature_selection` must be one of: all, random, best

### AdvancedBanditGlobalConfig

```python
@dataclass
class AdvancedBanditGlobalConfig:
    # Feature flags
    enable_advanced_bandits: bool = False
    enable_shadow_evaluation: bool = False
    enable_auto_tuning: bool = False
    enable_performance_monitoring: bool = True

    # Rollout controls
    rollout_percentage: float = 0.0
    rollout_domains: list[str] = field(default_factory=list)
    rollout_tenants: list[str] = field(default_factory=list)

    # A/B testing configuration
    shadow_sample_threshold: int = 500
    performance_improvement_threshold: float = 0.05
    degradation_threshold: float = -0.10

    # Auto-tuning parameters
    tuning_interval_hours: int = 24
    tuning_sample_size: int = 1000
    learning_rate_search_space: tuple[float, float] = (0.001, 0.5)
    confidence_search_space: tuple[float, float] = (0.5, 3.0)
```

## Experiment Management Classes

### AdvancedBanditExperimentManager

**Location:** `src/core/rl/advanced_experiments.py`

```python
class AdvancedBanditExperimentManager(ExperimentManager):
    """Enhanced experiment manager for advanced bandit evaluation."""
```

#### Methods

##### register_advanced_bandit_experiment()

```python
def register_advanced_bandit_experiment(
    self,
    domain: str,
    baseline_policy: str = "epsilon_greedy",
    advanced_policies: dict[str, float] = None,
    shadow_samples: int = 1000,
    description: str = None,
) -> None
```

Register an A/B test comparing advanced bandits against baseline.

**Parameters:**

- `domain` (str): Domain name for the experiment
- `baseline_policy` (str): Baseline algorithm name
- `advanced_policies` (dict): Advanced algorithms with traffic allocation weights
- `shadow_samples` (int): Samples before considering activation
- `description` (str): Experiment description

**Example:**

```python
manager = AdvancedBanditExperimentManager()
manager.register_advanced_bandit_experiment(
    domain="content_analysis",
    baseline_policy="thompson",
    advanced_policies={"doubly_robust": 0.3, "offset_tree": 0.2},
    shadow_samples=500,
    description="Evaluate advanced algorithms for content routing"
)
```

##### record_advanced_metrics()

```python
def record_advanced_metrics(
    self,
    experiment_id: str,
    arm: str,
    reward: float,
    context: dict[str, Any] = None,
    bandit_instance: Any = None,
) -> None
```

Record reward and algorithm-specific metrics.

**Parameters:**

- `experiment_id` (str): Experiment identifier
- `arm` (str): Algorithm variant name
- `reward` (float): Observed reward
- `context` (dict): Context features (optional)
- `bandit_instance`: Bandit instance for extracting metrics (optional)

**Metrics Recorded:**

- Standard reward metrics
- Algorithm-specific metrics (MSE, tree depth, importance weights)
- Prometheus metrics for monitoring

##### get_advanced_experiment_summary()

```python
def get_advanced_experiment_summary(self, domain: str) -> dict[str, Any]
```

Get comprehensive experiment analysis.

**Parameters:**

- `domain` (str): Domain name

**Returns:**

- Dictionary with experiment snapshot and advanced analysis

**Example Response:**

```python
{
    "experiment_id": "advanced_bandits::content_analysis",
    "control": "epsilon_greedy",
    "phase": "active",
    "advanced_analysis": {
        "baseline_policy": "epsilon_greedy",
        "baseline_reward_mean": 0.72,
        "variant_comparisons": {
            "doubly_robust": {
                "reward_mean": 0.78,
                "reward_improvement_pct": 8.33,
                "reward_model_mse": 0.045,
                "importance_weight_avg": 1.2
            }
        },
        "recommendations": [
            "Consider activating doubly_robust: 8.3% improvement"
        ]
    }
}
```

### AdvancedBanditStats

```python
@dataclass
class AdvancedBanditStats(VariantStats):
    # Additional metrics specific to advanced bandits
    reward_model_mse: float = 0.0
    tree_depth_sum: int = 0
    importance_weight_sum: float = 0.0
    confidence_interval_width: float = 0.0
```

Enhanced statistics class that extends base experiment stats with algorithm-specific metrics.

## Integration Points

### LearningEngine Integration

The advanced bandits integrate seamlessly with the existing learning engine:

```python
from core.learning_engine import LearningEngine

# Automatic policy selection based on configuration
engine = LearningEngine()

# Register domain - policy selected from environment config
engine.register_domain("model_routing")

# Use normally - configuration determines algorithm
context = {"complexity": 0.8}
candidates = ["fast", "accurate"]
choice = engine.recommend("model_routing", context, candidates)
engine.record("model_routing", context, choice, 1.0)
```

**Environment Variable Integration:**

- `ENABLE_RL_ADVANCED=true` enables advanced algorithms
- `RL_ROLLOUT_PERCENTAGE=0.25` routes 25% of traffic
- Domain-specific configs loaded automatically

### Metrics Integration

All metrics are automatically exported to Prometheus:

```python
# Advanced bandit specific metrics
advanced_bandit_reward_model_mse{tenant="...", workspace="...", experiment_id="...", variant="..."}
advanced_bandit_tree_depth{tenant="...", workspace="...", experiment_id="...", variant="..."}
advanced_bandit_importance_weight{tenant="...", workspace="...", experiment_id="...", variant="..."}
advanced_bandit_confidence_interval{tenant="...", workspace="...", experiment_id="...", variant="..."}

# Standard experiment metrics
experiment_variant_allocations_total{tenant="...", workspace="...", experiment_id="...", variant="...", phase="..."}
experiment_rewards_total{tenant="...", workspace="...", experiment_id="...", variant="..."}
experiment_reward_value{tenant="...", workspace="...", experiment_id="...", variant="..."}
experiment_regret_total{tenant="...", workspace="...", experiment_id="...", variant="..."}
```

### Tenancy Integration

Full tenant isolation is maintained:

```python
from ultimate_discord_intelligence_bot.tenancy import with_tenant, TenantContext

# All operations are tenant-scoped
with with_tenant(TenantContext("tenant_123", "workspace_456")):
    # Bandit recommendations and updates
    choice = engine.recommend("domain", context, candidates)
    engine.record("domain", context, choice, reward)

    # Experiment management
    manager.record_advanced_metrics("exp_id", "variant", reward, context, bandit)

    # Configuration
    config_manager.is_enabled_for_tenant("tenant_123")
```

## Error Handling

### Common Exceptions

#### ValueError

Raised for invalid parameters:

```python
# Empty candidates list
bandit.recommend(context, [])  # ValueError: candidates must not be empty

# Invalid configuration
DoublyRobustConfig(alpha=-1.0)  # ValueError: alpha must be positive
```

#### ConfigurationError

Raised for invalid environment configuration:

```python
# Invalid rollout percentage
os.environ["RL_ROLLOUT_PERCENTAGE"] = "1.5"  # ValueError: rollout_percentage must be in [0, 1]
```

### Graceful Degradation

The system is designed for graceful degradation:

1. **Missing Configuration**: Falls back to defaults
2. **Algorithm Errors**: Falls back to epsilon-greedy
3. **Experiment Failures**: Continue with baseline algorithm
4. **Metrics Failures**: Log errors but continue operation

```python
# Example fallback in learning engine
try:
    bandit = DoublyRobustBandit(**config)
except Exception as e:
    logger.warning("Failed to create advanced bandit, falling back to epsilon-greedy: %s", e)
    bandit = EpsilonGreedyBandit()
```

## Performance Characteristics

### Time Complexity

**DoublyRobustBandit:**

- `recommend()`: O(K × D) where K=candidates, D=dimensions
- `update()`: O(D) for reward model update

**OffsetTreeBandit:**

- `recommend()`: O(log N × K) where N=samples, K=candidates
- `update()`: O(log N + F) where F=features (for potential splits)

### Memory Usage

**DoublyRobustBandit:**

- Reward models: O(A × D) where A=actions, D=dimensions
- Importance weights: O(A × H) where H=history size
- Total: ~10KB per action for default settings

**OffsetTreeBandit:**

- Tree nodes: O(N) where N=number of splits
- Context history: O(H × F) where H=history size, F=features
- Total: ~1MB for default settings with 10K history

### Scalability Limits

**Recommended Limits:**

- Context dimensions: ≤ 100 features for real-time performance
- Actions per domain: ≤ 1000 for memory efficiency
- Tree depth: ≤ 10 for interpretability
- History size: ≤ 100K samples for memory management

## Version Compatibility

**Python Version:** 3.9+ (requires modern type annotations)

**Dependencies:**

- No external ML libraries required (pure Python implementation)
- Compatible with existing CrewAI ecosystem
- Works with current Prometheus metrics system
- Integrates with existing tenant management

**Backward Compatibility:**

- All existing bandit policies continue to work unchanged
- Configuration is additive - no breaking changes
- Metrics are additional - existing dashboards unaffected
- Can be completely disabled via `ENABLE_RL_ADVANCED=false`

---

*API Reference Last Updated: September 2025*

## Environment Tuning (Routing)

For the baseline Thompson bandit router used by default routing paths, the following environment variables apply:

- `ENABLE_BANDIT_ROUTING`: Gate for enabling the bandit router.
- `BANDIT_MIN_EPSILON`: Forced exploration floor in [0.0, 1.0]; when > 0.0, an epsilon-greedy overlay can choose a non-argmax arm.
- `BANDIT_RESET_ENTROPY_THRESHOLD`: Entropy threshold below which the router counts a low-entropy step.
- `BANDIT_RESET_ENTROPY_WINDOW`: Number of consecutive low-entropy steps to trigger a state reset.

Semantics:

- Exploration and reset parameters are read dynamically at selection/reset time (not cached at import), so they can be adjusted mid-process in tests and controlled environments.
- Prior parameters (`BANDIT_PRIOR_ALPHA`, `BANDIT_PRIOR_BETA`) are read at import and act as stable defaults.
