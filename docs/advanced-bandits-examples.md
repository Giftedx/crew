# Advanced Contextual Bandits: Examples and Tutorials

Practical examples demonstrating how to use the advanced contextual bandit algorithms in real-world scenarios.

## Tutorial 1: Basic Setup and First Recommendations

### Step 1: Enable Advanced Bandits

```bash
# Enable advanced algorithms
export ENABLE_RL_ADVANCED=true

# Start with conservative rollout
export RL_ROLLOUT_PERCENTAGE=0.05

# Enable shadow evaluation for safety
export ENABLE_RL_SHADOW_EVAL=true
```

### Step 2: Configure DoublyRobust for Model Routing

```python
from core.learning_engine import LearningEngine
from core.rl.advanced_config import get_config_manager, DoublyRobustConfig

# Initialize learning engine
engine = LearningEngine()

# Configure DoublyRobust for model routing domain
config_manager = get_config_manager()
model_routing_config = DoublyRobustConfig(
    alpha=1.5,          # Moderate exploration
    learning_rate=0.1,  # Standard learning rate
    dim=6               # 6 context features
)

config_manager.set_domain_config(
    "model_routing",
    doubly_robust_config=model_routing_config
)

# Register domain with DoublyRobust policy
engine.register_domain("model_routing", policy="doubly_robust")
```

### Step 3: Make Context-Aware Recommendations

```python
# Example context for model routing
context = {
    "user_tier": 1.0,           # Premium user (0=free, 1=premium, 2=enterprise)
    "request_complexity": 0.7,   # Complex request (0=simple, 1=very complex)
    "latency_tolerance": 0.3,    # Low latency tolerance (0=strict, 1=flexible)
    "cost_sensitivity": 0.8,     # Cost conscious (0=cost-insensitive, 1=very sensitive)
    "quality_requirement": 0.9,  # High quality needed (0=basic, 1=highest)
    "context_length": 0.4        # Medium context (0=short, 1=very long)
}

# Available model options
candidates = [
    "gpt-4-turbo",        # High quality, high cost, medium speed
    "gpt-3.5-turbo",      # Medium quality, low cost, high speed
    "claude-3-opus",      # High quality, high cost, low speed
    "claude-3-sonnet",    # Medium quality, medium cost, medium speed
]

# Get recommendation
recommended_model = engine.recommend("model_routing", context, candidates)
print(f"Recommended model: {recommended_model}")

# Simulate model usage and record reward
# In practice, this would be based on actual performance metrics
latency_ms = 1200
cost_cents = 15
quality_score = 0.92

# Calculate composite reward (customize based on your objectives)
latency_penalty = max(0, (latency_ms - 1000) / 1000)  # Penalty for > 1s
cost_penalty = cost_cents / 100                        # Normalize cost
reward = quality_score - 0.3 * latency_penalty - 0.2 * cost_penalty

engine.record("model_routing", context, recommended_model, reward)
print(f"Recorded reward: {reward:.3f}")
```

## Tutorial 2: OffsetTree for Content Analysis

### Scenario: Content Routing with Complex Context

You have a content analysis system that needs to route different types of content to specialized processors.

### Step 1: Configure OffsetTree

```python
from core.rl.advanced_config import OffsetTreeConfig

# Configure OffsetTree for content analysis
content_config = OffsetTreeConfig(
    max_depth=4,                    # Allow deeper trees for complex contexts
    min_samples_split=15,           # Conservative splitting
    split_threshold=0.2,            # Require significant variance reduction
    split_strategy="information_gain",  # Better feature selection
    base_bandit_type="thompson",    # Thompson sampling at leaves
)

config_manager.set_domain_config(
    "content_analysis",
    offset_tree_config=content_config
)

# Register domain
engine.register_domain("content_analysis", policy="offset_tree")
```

### Step 2: Multi-dimensional Content Context

```python
def extract_content_context(content_item):
    """Extract rich context features from content."""
    return {
        # Content characteristics
        "content_length": min(len(content_item.text) / 10000, 1.0),  # Normalized length
        "language_complexity": content_item.readability_score,        # 0-1 score
        "technical_density": content_item.technical_term_ratio,       # 0-1 ratio

        # User context
        "user_expertise": content_item.user.expertise_level,          # 0-1 level
        "user_engagement": content_item.user.avg_engagement,          # Historical engagement

        # Temporal context
        "time_of_day": content_item.timestamp.hour / 24,             # Normalized hour
        "day_of_week": content_item.timestamp.weekday() / 7,         # Normalized day

        # Business context
        "priority_level": content_item.priority / 5,                 # 1-5 scale normalized
        "topic_category": hash(content_item.category) % 100 / 100,   # Category hash
    }

# Available content processors
processors = [
    "fast_nlp",           # Quick processing, basic quality
    "advanced_nlp",       # Slower, high quality analysis
    "specialized_tech",   # For technical content
    "multimedia_processor", # For content with images/video
]

# Process content with context-aware routing
content_items = get_pending_content()  # Your content queue

for content in content_items:
    context = extract_content_context(content)
    processor = engine.recommend("content_analysis", context, processors)

    # Process content and measure performance
    start_time = time.time()
    result = process_content(content, processor)
    processing_time = time.time() - start_time

    # Calculate reward based on multiple objectives
    quality_score = evaluate_output_quality(result)
    speed_score = max(0, 1 - processing_time / 30)  # Prefer < 30s processing
    cost_score = 1 - get_processing_cost(processor) / 10  # Normalize cost

    # Weighted reward combining objectives
    reward = 0.5 * quality_score + 0.3 * speed_score + 0.2 * cost_score

    engine.record("content_analysis", context, processor, reward)
```

## Tutorial 3: A/B Testing with Shadow Evaluation

### Step 1: Set Up Experiment

```python
from core.rl.advanced_experiments import AdvancedBanditExperimentManager

# Initialize experiment manager
experiment_manager = AdvancedBanditExperimentManager()

# Register A/B test comparing algorithms
experiment_manager.register_advanced_bandit_experiment(
    domain="user_recommendation",
    baseline_policy="thompson",
    advanced_policies={
        "doubly_robust": 0.3,   # 30% traffic to DoublyRobust
        "offset_tree": 0.2,     # 20% traffic to OffsetTree
    },
    shadow_samples=1000,        # 1000 samples before considering activation
    description="Evaluate advanced algorithms for user recommendations"
)
```

### Step 2: Run Experiment with Metrics Collection

```python
import time
from core.rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit

# Create algorithm instances for metric collection
algorithms = {
    "thompson": ThompsonSamplingBandit(),
    "doubly_robust": DoublyRobustBandit(alpha=1.2, learning_rate=0.08),
    "offset_tree": OffsetTreeBandit(max_depth=3, min_samples_split=12),
}

# Simulate recommendation session
for session_id in range(5000):  # 5000 user sessions

    # Generate user context
    user_context = {
        "user_age_group": random.uniform(0, 1),
        "session_time": random.uniform(0, 1),
        "previous_engagement": random.uniform(0, 1),
        "device_type": random.choice([0.0, 0.5, 1.0]),  # mobile, tablet, desktop
        "location_cluster": random.uniform(0, 1),
    }

    # Get algorithm assignment from experiment
    experiment_id = "advanced_bandits::user_recommendation"

    # In practice, this would be determined by the experiment manager
    algorithm_name = experiment_manager.recommend(
        experiment_id, user_context, list(algorithms.keys())
    )

    algorithm = algorithms[algorithm_name]

    # Available recommendation types
    rec_types = ["trending", "personalized", "collaborative", "content_based"]

    # Get recommendation
    recommendation = algorithm.recommend(user_context, rec_types)

    # Simulate user interaction and measure reward
    user_clicked = simulate_user_interaction(recommendation, user_context)
    engagement_time = simulate_engagement_time(recommendation, user_context)

    # Calculate reward (customize based on your metrics)
    click_reward = 1.0 if user_clicked else 0.0
    engagement_reward = min(engagement_time / 300, 1.0)  # Normalize to 5 minutes
    reward = 0.7 * click_reward + 0.3 * engagement_reward

    # Record with experiment manager for advanced metrics
    experiment_manager.record_advanced_metrics(
        experiment_id=experiment_id,
        arm=algorithm_name,
        reward=reward,
        context=user_context,
        bandit_instance=algorithm
    )

    # Update algorithm
    algorithm.update(recommendation, reward, user_context)

    # Print progress every 1000 sessions
    if (session_id + 1) % 1000 == 0:
        print(f"Completed {session_id + 1} sessions")
```

### Step 3: Analyze Results

```python
# Get experiment summary
summary = experiment_manager.get_advanced_experiment_summary("user_recommendation")

print("Experiment Results:")
print(f"Baseline: {summary['advanced_analysis']['baseline_policy']}")
print(f"Baseline reward: {summary['advanced_analysis']['baseline_reward_mean']:.3f}")

print("\nVariant Performance:")
for variant, metrics in summary['advanced_analysis']['variant_comparisons'].items():
    if metrics.get('status') == 'insufficient_data':
        print(f"{variant}: Insufficient data ({metrics['pulls']} samples)")
        continue

    improvement = metrics['reward_improvement_pct']
    print(f"{variant}:")
    print(f"  Reward: {metrics['reward_mean']:.3f}")
    print(f"  Improvement: {improvement:+.1f}%")
    print(f"  Samples: {metrics['pulls']}")

    # Advanced metrics (if available)
    if 'reward_model_mse' in metrics:
        print(f"  Reward Model MSE: {metrics['reward_model_mse']:.4f}")
    if 'tree_depth_avg' in metrics:
        print(f"  Avg Tree Depth: {metrics['tree_depth_avg']:.1f}")

print("\nRecommendations:")
for rec in summary['advanced_analysis']['recommendations']:
    print(f"  • {rec}")
```

## Tutorial 4: Production Deployment with Monitoring

### Step 1: Production Configuration

```bash
# Production environment variables
export ENABLE_RL_ADVANCED=true
export ENABLE_RL_SHADOW_EVAL=true
export ENABLE_RL_MONITORING=true

# Conservative rollout
export RL_ROLLOUT_PERCENTAGE=0.15
export RL_ROLLOUT_DOMAINS=model_routing,content_analysis

# Performance thresholds
export RL_IMPROVEMENT_THRESHOLD=0.03  # 3% improvement required
export RL_DEGRADATION_THRESHOLD=-0.05 # 5% degradation triggers alert

# DoublyRobust production settings
export RL_DR_ALPHA=1.0
export RL_DR_LEARNING_RATE=0.08
export RL_DR_LR_DECAY=0.998
export RL_DR_MAX_WEIGHT=5.0

# OffsetTree production settings
export RL_OT_MAX_DEPTH=3
export RL_OT_MIN_SPLIT=20
export RL_OT_SPLIT_THRESHOLD=0.15
```

### Step 2: Monitoring Setup

```python
from prometheus_client import start_http_server, generate_latest
import logging

# Set up logging for bandit performance
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced_bandits")

class ProductionBanditMonitor:
    def __init__(self, engine, experiment_manager):
        self.engine = engine
        self.experiment_manager = experiment_manager
        self.daily_stats = {}

    def log_recommendation(self, domain, context, candidates, recommendation, reward=None):
        """Log recommendation with context for analysis."""
        timestamp = time.time()

        log_entry = {
            "timestamp": timestamp,
            "domain": domain,
            "context_size": len(context),
            "num_candidates": len(candidates),
            "recommendation": recommendation,
            "reward": reward,
            "context_hash": hash(str(sorted(context.items())))
        }

        logger.info("Recommendation", extra=log_entry)

        # Track daily stats
        date = time.strftime("%Y-%m-%d", time.localtime(timestamp))
        if date not in self.daily_stats:
            self.daily_stats[date] = {"count": 0, "reward_sum": 0}

        self.daily_stats[date]["count"] += 1
        if reward is not None:
            self.daily_stats[date]["reward_sum"] += reward

    def get_daily_performance(self, date=None):
        """Get performance metrics for a specific date."""
        if date is None:
            date = time.strftime("%Y-%m-%d")

        stats = self.daily_stats.get(date, {"count": 0, "reward_sum": 0})
        if stats["count"] == 0:
            return {"date": date, "recommendations": 0, "avg_reward": 0}

        return {
            "date": date,
            "recommendations": stats["count"],
            "avg_reward": stats["reward_sum"] / stats["count"]
        }

    def check_algorithm_health(self):
        """Check if algorithms are performing within expected bounds."""
        alerts = []

        for domain in ["model_routing", "content_analysis"]:
            try:
                summary = self.experiment_manager.get_advanced_experiment_summary(domain)
                analysis = summary.get("advanced_analysis", {})

                baseline_reward = analysis.get("baseline_reward_mean", 0)

                for variant, metrics in analysis.get("variant_comparisons", {}).items():
                    if "reward_improvement_pct" in metrics:
                        improvement = metrics["reward_improvement_pct"] / 100

                        if improvement < -0.05:  # 5% degradation
                            alerts.append({
                                "severity": "critical",
                                "domain": domain,
                                "variant": variant,
                                "improvement": improvement,
                                "message": f"{variant} showing {improvement:.1%} degradation in {domain}"
                            })
                        elif improvement < -0.02:  # 2% degradation
                            alerts.append({
                                "severity": "warning",
                                "domain": domain,
                                "variant": variant,
                                "improvement": improvement,
                                "message": f"{variant} showing {improvement:.1%} degradation in {domain}"
                            })
            except Exception as e:
                alerts.append({
                    "severity": "error",
                    "domain": domain,
                    "message": f"Failed to check health for {domain}: {e}"
                })

        return alerts

# Initialize monitoring
monitor = ProductionBanditMonitor(engine, experiment_manager)

# Example production usage with monitoring
def production_recommendation_with_monitoring(domain, context, candidates):
    """Production recommendation with comprehensive monitoring."""

    # Get recommendation
    recommendation = engine.recommend(domain, context, candidates)

    # Log recommendation
    monitor.log_recommendation(domain, context, candidates, recommendation)

    return recommendation

def production_record_with_monitoring(domain, context, action, reward):
    """Production reward recording with monitoring."""

    # Record reward
    engine.record(domain, context, action, reward)

    # Update monitoring logs
    monitor.log_recommendation(domain, context, [], action, reward)

    # Check for alerts
    alerts = monitor.check_algorithm_health()
    for alert in alerts:
        if alert["severity"] == "critical":
            logger.error("Algorithm degradation alert", extra=alert)
        elif alert["severity"] == "warning":
            logger.warning("Algorithm performance warning", extra=alert)
```

### Step 3: Automated Performance Analysis

```python
import schedule
import json

def daily_performance_report():
    """Generate daily performance report."""
    date = time.strftime("%Y-%m-%d")

    # Get performance metrics
    performance = monitor.get_daily_performance(date)

    # Get experiment summaries
    experiment_summaries = {}
    for domain in ["model_routing", "content_analysis"]:
        try:
            summary = experiment_manager.get_advanced_experiment_summary(domain)
            experiment_summaries[domain] = summary
        except Exception as e:
            logger.error(f"Failed to get summary for {domain}: {e}")

    # Create report
    report = {
        "date": date,
        "overall_performance": performance,
        "experiment_summaries": experiment_summaries,
        "alerts": monitor.check_algorithm_health(),
        "configuration": {
            "rollout_percentage": os.getenv("RL_ROLLOUT_PERCENTAGE"),
            "enabled_domains": os.getenv("RL_ROLLOUT_DOMAINS", "").split(","),
            "shadow_evaluation": os.getenv("ENABLE_RL_SHADOW_EVAL"),
        }
    }

    # Save report
    report_path = f"/logs/bandit_reports/{date}_performance_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Daily performance report saved: {report_path}")

    # Send alerts if any critical issues
    critical_alerts = [a for a in report["alerts"] if a.get("severity") == "critical"]
    if critical_alerts:
        send_alert_notification(critical_alerts)

def send_alert_notification(alerts):
    """Send notification for critical alerts (implement based on your notification system)."""
    alert_summary = "\n".join([alert["message"] for alert in alerts])
    logger.critical(f"CRITICAL BANDIT ALERTS:\n{alert_summary}")

    # Implement your notification system here
    # Examples: Slack webhook, PagerDuty, email, etc.

# Schedule daily reports
schedule.every().day.at("06:00").do(daily_performance_report)

# Run scheduler in background thread
import threading

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
```

## Tutorial 5: Custom Reward Functions and Multi-Objective Optimization

### Step 1: Custom Reward Calculation

```python
class MultiObjectiveRewardCalculator:
    """Calculate rewards based on multiple business objectives."""

    def __init__(self, weights=None):
        self.weights = weights or {
            "quality": 0.4,
            "latency": 0.3,
            "cost": 0.2,
            "user_satisfaction": 0.1
        }

    def calculate_reward(self, outcome):
        """Calculate composite reward from multiple metrics."""

        # Quality score (0-1, higher is better)
        quality_score = outcome.get("quality_score", 0.5)

        # Latency penalty (convert ms to 0-1 score, lower latency is better)
        latency_ms = outcome.get("latency_ms", 1000)
        latency_score = max(0, 1 - (latency_ms - 100) / 2000)  # Prefer < 100ms

        # Cost efficiency (convert cost to 0-1 score, lower cost is better)
        cost_cents = outcome.get("cost_cents", 10)
        cost_score = max(0, 1 - cost_cents / 50)  # Normalize to $0.50

        # User satisfaction (direct 0-1 score)
        satisfaction_score = outcome.get("user_satisfaction", 0.5)

        # Calculate weighted composite reward
        reward = (
            self.weights["quality"] * quality_score +
            self.weights["latency"] * latency_score +
            self.weights["cost"] * cost_score +
            self.weights["user_satisfaction"] * satisfaction_score
        )

        return reward, {
            "quality_score": quality_score,
            "latency_score": latency_score,
            "cost_score": cost_score,
            "satisfaction_score": satisfaction_score,
            "composite_reward": reward
        }

# Initialize reward calculator
reward_calculator = MultiObjectiveRewardCalculator(
    weights={
        "quality": 0.5,      # Prioritize quality
        "latency": 0.3,      # Latency important
        "cost": 0.15,        # Cost less important
        "user_satisfaction": 0.05  # Satisfaction least important
    }
)

# Example usage in model routing
def route_model_with_multi_objective_reward(user_request):
    """Route model selection with multi-objective optimization."""

    # Extract context
    context = extract_request_context(user_request)

    # Get model recommendation
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]
    selected_model = engine.recommend("model_routing", context, models)

    # Execute request and measure outcomes
    start_time = time.time()
    response = execute_model_request(user_request, selected_model)
    latency_ms = (time.time() - start_time) * 1000

    # Measure all objectives
    outcome = {
        "quality_score": evaluate_response_quality(response, user_request),
        "latency_ms": latency_ms,
        "cost_cents": get_model_cost(selected_model, user_request),
        "user_satisfaction": get_user_feedback(response)  # Could be predicted
    }

    # Calculate multi-objective reward
    reward, reward_breakdown = reward_calculator.calculate_reward(outcome)

    # Record with detailed logging
    logger.info("Model routing decision", extra={
        "model": selected_model,
        "context": context,
        "outcome": outcome,
        "reward_breakdown": reward_breakdown,
        "final_reward": reward
    })

    # Update bandit
    engine.record("model_routing", context, selected_model, reward)

    return response, reward_breakdown
```

### Step 2: Adaptive Reward Weights

```python
class AdaptiveRewardCalculator(MultiObjectiveRewardCalculator):
    """Reward calculator that adapts weights based on context."""

    def __init__(self):
        # Different weights for different scenarios
        self.weight_profiles = {
            "high_priority": {
                "quality": 0.6, "latency": 0.3, "cost": 0.05, "user_satisfaction": 0.05
            },
            "cost_sensitive": {
                "quality": 0.3, "latency": 0.2, "cost": 0.4, "user_satisfaction": 0.1
            },
            "latency_critical": {
                "quality": 0.25, "latency": 0.6, "cost": 0.1, "user_satisfaction": 0.05
            },
            "default": {
                "quality": 0.4, "latency": 0.3, "cost": 0.2, "user_satisfaction": 0.1
            }
        }

    def get_weights_for_context(self, context):
        """Select weight profile based on context."""

        # Priority-based selection
        if context.get("priority_level", 0) > 0.8:
            return self.weight_profiles["high_priority"]

        # Cost sensitivity
        if context.get("cost_sensitivity", 0) > 0.7:
            return self.weight_profiles["cost_sensitive"]

        # Latency requirements
        if context.get("latency_tolerance", 1) < 0.3:
            return self.weight_profiles["latency_critical"]

        # Default
        return self.weight_profiles["default"]

    def calculate_contextual_reward(self, outcome, context):
        """Calculate reward with context-adaptive weights."""

        # Get appropriate weights for this context
        weights = self.get_weights_for_context(context)

        # Temporarily update weights
        original_weights = self.weights
        self.weights = weights

        # Calculate reward
        reward, breakdown = self.calculate_reward(outcome)

        # Restore original weights
        self.weights = original_weights

        # Add weight profile to breakdown
        breakdown["weight_profile"] = weights

        return reward, breakdown

# Use adaptive rewards
adaptive_calculator = AdaptiveRewardCalculator()

def smart_model_routing(user_request):
    """Model routing with context-adaptive rewards."""

    context = extract_request_context(user_request)

    # Route and execute
    selected_model = engine.recommend("model_routing", context, models)
    response, outcome = execute_and_measure(user_request, selected_model)

    # Calculate adaptive reward
    reward, breakdown = adaptive_calculator.calculate_contextual_reward(outcome, context)

    # Record with context-aware reward
    engine.record("model_routing", context, selected_model, reward)

    return response
```

## Best Practices Summary

### 1. Start Small and Scale Gradually

```python
# Phase 1: Shadow evaluation only
export RL_ROLLOUT_PERCENTAGE=0.0
export ENABLE_RL_SHADOW_EVAL=true

# Phase 2: Small rollout
export RL_ROLLOUT_PERCENTAGE=0.05

# Phase 3: Expand gradually
export RL_ROLLOUT_PERCENTAGE=0.25
```

### 2. Monitor Everything

```python
# Essential monitoring points
- Reward trends over time
- Algorithm-specific metrics (MSE, tree depth, importance weights)
- Performance degradation alerts
- Context distribution changes
- Recommendation diversity
```

### 3. Configuration Tuning Guidelines

```python
# DoublyRobust tuning
- Higher alpha (2.0-3.0) for more exploration in uncertain environments
- Lower learning_rate (0.05) for noisy reward signals
- Higher learning_rate (0.15) for stable environments
- Larger dim (16-32) for rich context spaces

# OffsetTree tuning
- Deeper trees (5-7) for complex, non-linear contexts
- Shallower trees (2-3) for simple contexts
- Higher min_samples_split (20-50) for stable, conservative splits
- Lower split_threshold (0.05) for more aggressive partitioning
```

### 4. Reward Function Design

```python
# Good practices
- Normalize all metrics to 0-1 scale
- Use weighted combinations of multiple objectives
- Make rewards context-dependent when appropriate
- Include leading indicators, not just final outcomes
- Log reward breakdown for debugging

# Avoid
- Sparse rewards (all 0 or 1)
- Heavily delayed feedback
- Rewards that don't align with business objectives
- Complex non-linear reward functions initially
```

### 5. A/B Testing Best Practices

```python
# Statistical validity
- Run for sufficient sample size (typically 1000+ per variant)
- Set appropriate significance thresholds (3-5% improvement)
- Monitor statistical power throughout experiment
- Account for multiple hypothesis testing

# Business validity
- Align metrics with business objectives
- Monitor for unintended consequences
- Have rollback plan for degraded performance
- Consider long-term vs short-term effects
```

These tutorials provide comprehensive examples for implementing advanced contextual bandits in production environments. Each tutorial builds on the previous ones, from basic setup to sophisticated multi-objective optimization and production monitoring.

---

## Last Updated

Examples Last Updated: September 2025
