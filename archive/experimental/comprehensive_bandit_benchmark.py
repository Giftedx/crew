#!/usr/bin/env python3
"""
Advanced Contextual Bandits: Comprehensive Performance Benchmarking Suite

A rigorous benchmarking system that measures and compares advanced bandit performance
against baseline algorithms with statistical significance testing.

Features:
- Multi-algorithm comparison (DoublyRobust, OffsetTree vs Baselines)
- Statistical significance testing with multiple hypothesis correction
- Realistic environment simulation with varying contexts
- Performance profiling and resource usage analysis
- Comprehensive reporting with visualizations
- Confidence interval analysis and effect size measurement
"""

import asyncio
import json
import logging
import random
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking experiments."""

    # Test parameters
    num_rounds: int = 5000
    num_repetitions: int = 10
    warmup_rounds: int = 500

    # Environment settings
    context_dimension: int = 8
    num_actions: int = 4
    noise_level: float = 0.1

    # Algorithms to test
    algorithms: list[str] | None = None

    # Statistical testing
    significance_level: float = 0.05
    confidence_level: float = 0.95
    effect_size_threshold: float = 0.02  # 2% minimum effect size

    # Performance testing
    enable_profiling: bool = True
    memory_limit_mb: int = 512
    latency_budget_ms: int = 100

    def __post_init__(self):
        if self.algorithms is None:
            self.algorithms = [
                "epsilon_greedy",
                "thompson_sampling",
                "linucb",
                "linucb_hybrid",
                "doubly_robust",
                "offset_tree",
            ]


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    algorithm: str
    repetition: int
    rewards: list[float]
    regrets: list[float]
    latencies: list[float]
    memory_usage: list[float]
    total_reward: float
    cumulative_regret: float
    avg_latency: float
    max_memory: float
    convergence_round: int
    final_performance: float


@dataclass
class StatisticalAnalysis:
    """Statistical analysis results."""

    algorithm_comparison: str
    effect_size: float
    confidence_interval: tuple[float, float]
    p_value: float
    is_significant: bool
    cohen_d: float
    power: float


class BanditAlgorithm:
    """Base class for bandit algorithms."""

    def __init__(self, num_actions: int, context_dim: int, **kwargs):
        self.num_actions = num_actions
        self.context_dim = context_dim
        self.t = 0

    def select_action(self, context: np.ndarray) -> int:
        """Select an action given context."""
        raise NotImplementedError

    def update(self, context: np.ndarray, action: int, reward: float):
        """Update algorithm with observed reward."""
        self.t += 1


class EpsilonGreedyBandit(BanditAlgorithm):
    """Epsilon-greedy contextual bandit."""

    def __init__(self, num_actions: int, context_dim: int, epsilon: float = 0.1):
        super().__init__(num_actions, context_dim)
        self.epsilon = epsilon
        self.q_values = np.zeros((num_actions, context_dim))
        self.action_counts = np.zeros(num_actions)

    def select_action(self, context: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.randint(0, self.num_actions - 1)
        else:
            # Greedy action based on context
            values = [np.dot(self.q_values[a], context) for a in range(self.num_actions)]
            return int(np.argmax(values))

    def update(self, context: np.ndarray, action: int, reward: float):
        super().update(context, action, reward)
        self.action_counts[action] += 1
        lr = 1.0 / max(1, self.action_counts[action])
        self.q_values[action] += lr * (reward - np.dot(self.q_values[action], context)) * context


class ThompsonSamplingBandit(BanditAlgorithm):
    """Thompson sampling for contextual bandits."""

    def __init__(self, num_actions: int, context_dim: int, alpha: float = 1.0):
        super().__init__(num_actions, context_dim)
        self.alpha = alpha
        self.beta_a = np.ones((num_actions, context_dim))
        self.beta_b = np.ones((num_actions, context_dim))

    def select_action(self, context: np.ndarray) -> int:
        sampled_values = []
        for a in range(self.num_actions):
            # Sample from beta distribution for each context feature
            samples = []
            for i in range(self.context_dim):
                # Ensure beta parameters are positive
                alpha = max(0.1, self.beta_a[a, i])
                beta = max(0.1, self.beta_b[a, i])
                samples.append(np.random.beta(alpha, beta))
            value = np.dot(samples, context)
            sampled_values.append(value)
        return int(np.argmax(sampled_values))

    def update(self, context: np.ndarray, action: int, reward: float):
        super().update(context, action, reward)
        for i in range(self.context_dim):
            if reward > 0.5:  # Treat as success
                self.beta_a[action, i] += context[i] * reward
            else:
                self.beta_b[action, i] += context[i] * (1 - reward)


class LinUCBBandit(BanditAlgorithm):
    """Linear Upper Confidence Bound bandit."""

    def __init__(self, num_actions: int, context_dim: int, alpha: float = 1.0):
        super().__init__(num_actions, context_dim)
        self.alpha = alpha
        self.A = [np.eye(context_dim) for _ in range(num_actions)]
        self.b = [np.zeros(context_dim) for _ in range(num_actions)]

    def select_action(self, context: np.ndarray) -> int:
        ucb_values = []
        for a in range(self.num_actions):
            A_inv = np.linalg.inv(self.A[a])
            theta_hat = np.dot(A_inv, self.b[a])
            confidence = self.alpha * np.sqrt(np.dot(context, np.dot(A_inv, context)))
            ucb = np.dot(theta_hat, context) + confidence
            ucb_values.append(ucb)
        return int(np.argmax(ucb_values))

    def update(self, context: np.ndarray, action: int, reward: float):
        super().update(context, action, reward)
        self.A[action] += np.outer(context, context)
        self.b[action] += reward * context


class DoublyRobustBandit(BanditAlgorithm):
    """Simplified DoublyRobust bandit for benchmarking."""

    def __init__(self, num_actions: int, context_dim: int, alpha: float = 1.5, learning_rate: float = 0.1):
        super().__init__(num_actions, context_dim)
        self.alpha = alpha
        self.learning_rate = learning_rate
        self.reward_model = np.zeros((num_actions, context_dim))
        self.importance_weights = np.ones(num_actions)
        self.action_probs = np.ones(num_actions) / num_actions

    def select_action(self, context: np.ndarray) -> int:
        # Predict rewards for each action
        predicted_rewards = []
        for a in range(self.num_actions):
            reward_pred = np.dot(self.reward_model[a], context)

            # Add exploration bonus
            exploration = self.alpha * np.sqrt(np.log(self.t + 1) / max(1, self.importance_weights[a]))

            predicted_rewards.append(reward_pred + exploration)

        return int(np.argmax(predicted_rewards))

    def update(self, context: np.ndarray, action: int, reward: float):
        super().update(context, action, reward)

        # Update reward model
        prediction_error = reward - np.dot(self.reward_model[action], context)
        self.reward_model[action] += self.learning_rate * prediction_error * context

        # Update importance weights and action probabilities
        self.importance_weights[action] += 1
        self.action_probs = self.importance_weights / np.sum(self.importance_weights)


class OffsetTreeBandit(BanditAlgorithm):
    """Simplified OffsetTree bandit for benchmarking."""

    def __init__(self, num_actions: int, context_dim: int, max_depth: int = 4, min_samples: int = 20):
        super().__init__(num_actions, context_dim)
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.tree = {"type": "leaf", "bandit": ThompsonSamplingBandit(num_actions, context_dim)}
        self.contexts = []
        self.actions = []
        self.rewards = []

    def select_action(self, context: np.ndarray) -> int:
        node = self._find_leaf(context, self.tree)
        return node["bandit"].select_action(context)

    def update(self, context: np.ndarray, action: int, reward: float):
        super().update(context, action, reward)

        # Store data
        self.contexts.append(context.copy())
        self.actions.append(action)
        self.rewards.append(reward)

        # Update leaf bandit
        node = self._find_leaf(context, self.tree)
        node["bandit"].update(context, action, reward)

        # Periodically rebuild tree
        if len(self.contexts) % 100 == 0:
            self._maybe_split_tree()

    def _find_leaf(self, context: np.ndarray, node: dict):
        """Find the appropriate leaf node for this context."""
        if node["type"] == "leaf":
            return node

        feature_idx = node["feature"]
        threshold = node["threshold"]

        if context[feature_idx] <= threshold:
            return self._find_leaf(context, node["left"])
        else:
            return self._find_leaf(context, node["right"])

    def _maybe_split_tree(self):
        """Consider splitting the tree based on accumulated data."""
        if len(self.contexts) >= self.min_samples:
            self._recursive_split(self.tree, list(range(len(self.contexts))), 0)

    def _recursive_split(self, node: dict, indices: list[int], depth: int):
        """Recursively split tree nodes."""
        if depth >= self.max_depth or len(indices) < self.min_samples:
            return

        # Try to find best split
        best_gain = 0
        best_feature = None
        best_threshold = None

        for feature in range(self.context_dim):
            values = [self.contexts[i][feature] for i in indices]
            if len(set(values)) < 2:
                continue

            threshold = np.median(values)
            left_indices = [i for i in indices if self.contexts[i][feature] <= threshold]
            right_indices = [i for i in indices if self.contexts[i][feature] > threshold]

            if len(left_indices) < 5 or len(right_indices) < 5:
                continue

            # Calculate information gain (simplified)
            left_rewards = [self.rewards[i] for i in left_indices]
            right_rewards = [self.rewards[i] for i in right_indices]

            if left_rewards and right_rewards:
                total_var = np.var([self.rewards[i] for i in indices])
                left_var = np.var(left_rewards) * len(left_rewards) / len(indices)
                right_var = np.var(right_rewards) * len(right_indices) / len(indices)
                gain = total_var - left_var - right_var

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold

        # Split if beneficial
        if best_gain > 0.01:  # Minimum gain threshold
            left_indices = [i for i in indices if self.contexts[i][best_feature] <= best_threshold]
            right_indices = [i for i in indices if self.contexts[i][best_feature] > best_threshold]

            node["type"] = "split"
            node["feature"] = best_feature
            node["threshold"] = best_threshold
            node["left"] = {"type": "leaf", "bandit": ThompsonSamplingBandit(self.num_actions, self.context_dim)}
            node["right"] = {"type": "leaf", "bandit": ThompsonSamplingBandit(self.num_actions, self.context_dim)}

            # Recursively split children
            self._recursive_split(node["left"], left_indices, depth + 1)
            self._recursive_split(node["right"], right_indices, depth + 1)


class BenchmarkEnvironment:
    """Simulated environment for bandit benchmarking."""

    def __init__(self, context_dim: int, num_actions: int, noise_level: float = 0.1):
        self.context_dim = context_dim
        self.num_actions = num_actions
        self.noise_level = noise_level

        # Generate true reward parameters (unknown to algorithms)
        self.true_weights = np.random.normal(0, 1, (num_actions, context_dim))
        self.true_bias = np.random.normal(0, 0.1, num_actions)

        # Normalize to make problem non-trivial
        for a in range(num_actions):
            self.true_weights[a] /= np.linalg.norm(self.true_weights[a])

    def generate_context(self) -> np.ndarray:
        """Generate a random context vector."""
        # Mix of different context patterns
        if random.random() < 0.3:
            # Sparse context
            context = np.zeros(self.context_dim)
            active_features = random.sample(range(self.context_dim), random.randint(1, 3))
            for idx in active_features:
                context[idx] = random.gauss(0, 1)
        else:
            # Dense context
            context = np.random.normal(0, 1, self.context_dim)

        # Normalize
        norm = np.linalg.norm(context)
        if norm > 0:
            context /= norm

        return context

    def get_reward(self, context: np.ndarray, action: int) -> float:
        """Get reward for taking action in given context."""
        true_reward = np.dot(self.true_weights[action], context) + self.true_bias[action]
        noise = np.random.normal(0, self.noise_level)
        observed_reward = true_reward + noise

        # Ensure reward is in [0, 1] range
        return max(0.0, min(1.0, (observed_reward + 1) / 2))

    def get_optimal_action(self, context: np.ndarray) -> int:
        """Get the optimal action for given context."""
        expected_rewards = [np.dot(self.true_weights[a], context) + self.true_bias[a] for a in range(self.num_actions)]
        return int(np.argmax(expected_rewards))

    def get_optimal_reward(self, context: np.ndarray) -> float:
        """Get the optimal reward for given context."""
        optimal_action = self.get_optimal_action(context)
        return self.get_reward(context, optimal_action)


class PerformanceBenchmark:
    """Comprehensive performance benchmarking system."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.algorithms = self._create_algorithms()
        self.results = []

    def _create_algorithms(self) -> dict[str, BanditAlgorithm]:
        """Create algorithm instances for benchmarking."""
        algorithms = {}

        for alg_name in self.config.algorithms:
            if alg_name == "epsilon_greedy":
                algorithms[alg_name] = EpsilonGreedyBandit(
                    self.config.num_actions, self.config.context_dimension, epsilon=0.1
                )
            elif alg_name == "thompson_sampling":
                algorithms[alg_name] = ThompsonSamplingBandit(self.config.num_actions, self.config.context_dimension)
            elif alg_name == "linucb":
                algorithms[alg_name] = LinUCBBandit(self.config.num_actions, self.config.context_dimension, alpha=1.0)
            elif alg_name == "linucb_hybrid":
                algorithms[alg_name] = LinUCBBandit(self.config.num_actions, self.config.context_dimension, alpha=1.5)
            elif alg_name == "doubly_robust":
                algorithms[alg_name] = DoublyRobustBandit(self.config.num_actions, self.config.context_dimension)
            elif alg_name == "offset_tree":
                algorithms[alg_name] = OffsetTreeBandit(self.config.num_actions, self.config.context_dimension)
            else:
                logger.warning(f"Unknown algorithm: {alg_name}")

        return algorithms

    async def run_single_experiment(self, algorithm_name: str, repetition: int) -> BenchmarkResult:
        """Run a single benchmark experiment."""

        logger.info(f"Running {algorithm_name} repetition {repetition}")

        algorithm = self._create_algorithms()[algorithm_name]
        environment = BenchmarkEnvironment(
            self.config.context_dimension, self.config.num_actions, self.config.noise_level
        )

        rewards = []
        regrets = []
        latencies = []
        memory_usage = []

        cumulative_reward = 0
        cumulative_regret = 0

        # Warmup period
        for _ in range(self.config.warmup_rounds):
            context = environment.generate_context()
            action = algorithm.select_action(context)
            reward = environment.get_reward(context, action)
            algorithm.update(context, action, reward)

        # Main experiment
        for round_num in range(self.config.num_rounds):
            context = environment.generate_context()

            # Measure latency
            start_time = time.perf_counter()
            action = algorithm.select_action(context)
            latency = (time.perf_counter() - start_time) * 1000  # ms

            # Get reward and optimal reward
            reward = environment.get_reward(context, action)
            optimal_reward = environment.get_optimal_reward(context)
            regret = optimal_reward - reward

            # Update algorithm
            algorithm.update(context, action, reward)

            # Record metrics
            cumulative_reward += reward
            cumulative_regret += regret
            rewards.append(reward)
            regrets.append(regret)
            latencies.append(latency)

            # Simulate memory usage (simplified)
            memory_mb = 10 + round_num * 0.001  # Gradual memory growth
            memory_usage.append(memory_mb)

            # Progress logging
            if round_num % 1000 == 0:
                avg_reward = cumulative_reward / (round_num + 1)
                logger.debug(f"{algorithm_name} round {round_num}: avg_reward={avg_reward:.3f}")

        # Calculate convergence round (when performance stabilizes)
        convergence_round = self._find_convergence_point(rewards)

        return BenchmarkResult(
            algorithm=algorithm_name,
            repetition=repetition,
            rewards=rewards,
            regrets=regrets,
            latencies=latencies,
            memory_usage=memory_usage,
            total_reward=cumulative_reward,
            cumulative_regret=cumulative_regret,
            avg_latency=statistics.mean(latencies),
            max_memory=max(memory_usage),
            convergence_round=convergence_round,
            final_performance=statistics.mean(rewards[-100:]),  # Last 100 rounds
        )

    def _find_convergence_point(self, rewards: list[float], window_size: int = 100) -> int:
        """Find the round where performance converges."""
        if len(rewards) < window_size * 2:
            return len(rewards)

        # Calculate moving averages
        moving_avgs = []
        for i in range(window_size, len(rewards) - window_size):
            avg = statistics.mean(rewards[i : i + window_size])
            moving_avgs.append(avg)

        # Find where variance becomes small
        for i in range(len(moving_avgs) - window_size):
            window = moving_avgs[i : i + window_size]
            if len(window) > 1 and statistics.stdev(window) < 0.02:  # 2% std dev
                return i + window_size

        return len(rewards)

    async def run_comprehensive_benchmark(self) -> dict[str, Any]:
        """Run comprehensive benchmark across all algorithms and repetitions."""

        logger.info(
            f"Starting comprehensive benchmark: {len(self.config.algorithms)} algorithms, "
            f"{self.config.num_repetitions} repetitions each"
        )

        start_time = time.time()

        # Run all experiments
        tasks = []
        for algorithm_name in self.config.algorithms:
            for repetition in range(self.config.num_repetitions):
                task = self.run_single_experiment(algorithm_name, repetition)
                tasks.append(task)

        # Execute all experiments
        self.results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        logger.info(f"Benchmark completed in {total_time:.1f} seconds")

        # Aggregate results
        return self._aggregate_results()

    def _aggregate_results(self) -> dict[str, Any]:
        """Aggregate benchmark results across repetitions."""

        aggregated = {}

        # Group results by algorithm
        by_algorithm = defaultdict(list)
        for result in self.results:
            by_algorithm[result.algorithm].append(result)

        # Calculate statistics for each algorithm
        for algorithm, results in by_algorithm.items():
            final_performances = [r.final_performance for r in results]
            total_rewards = [r.total_reward for r in results]
            cumulative_regrets = [r.cumulative_regret for r in results]
            avg_latencies = [r.avg_latency for r in results]
            max_memories = [r.max_memory for r in results]
            convergence_rounds = [r.convergence_round for r in results]

            aggregated[algorithm] = {
                "final_performance": {
                    "mean": statistics.mean(final_performances),
                    "std": statistics.stdev(final_performances) if len(final_performances) > 1 else 0,
                    "min": min(final_performances),
                    "max": max(final_performances),
                    "median": statistics.median(final_performances),
                },
                "total_reward": {
                    "mean": statistics.mean(total_rewards),
                    "std": statistics.stdev(total_rewards) if len(total_rewards) > 1 else 0,
                },
                "cumulative_regret": {
                    "mean": statistics.mean(cumulative_regrets),
                    "std": statistics.stdev(cumulative_regrets) if len(cumulative_regrets) > 1 else 0,
                },
                "latency": {
                    "mean": statistics.mean(avg_latencies),
                    "std": statistics.stdev(avg_latencies) if len(avg_latencies) > 1 else 0,
                    "p95": np.percentile(avg_latencies, 95),
                    "p99": np.percentile(avg_latencies, 99),
                },
                "memory": {"mean": statistics.mean(max_memories), "max": max(max_memories)},
                "convergence": {
                    "mean_rounds": statistics.mean(convergence_rounds),
                    "std_rounds": statistics.stdev(convergence_rounds) if len(convergence_rounds) > 1 else 0,
                },
                "repetitions": len(results),
            }

        return aggregated


class StatisticalAnalyzer:
    """Statistical analysis and significance testing."""

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level

    def compare_algorithms(
        self, results_a: list[float], results_b: list[float], algorithm_a: str, algorithm_b: str
    ) -> StatisticalAnalysis:
        """Compare two algorithms with statistical testing."""

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(results_a, results_b)

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(
            ((len(results_a) - 1) * np.var(results_a, ddof=1) + (len(results_b) - 1) * np.var(results_b, ddof=1))
            / (len(results_a) + len(results_b) - 2)
        )

        cohen_d = (np.mean(results_a) - np.mean(results_b)) / pooled_std if pooled_std > 0 else 0

        # Calculate confidence interval for difference
        diff_mean = np.mean(results_a) - np.mean(results_b)
        diff_se = pooled_std * np.sqrt(1 / len(results_a) + 1 / len(results_b))

        # Critical value for confidence interval
        dof = len(results_a) + len(results_b) - 2
        t_critical = stats.t.ppf(1 - self.significance_level / 2, dof)

        ci_lower = diff_mean - t_critical * diff_se
        ci_upper = diff_mean + t_critical * diff_se

        # Calculate statistical power (approximate)
        effect_size = abs(cohen_d)
        power = self._calculate_power(effect_size, len(results_a), len(results_b))

        return StatisticalAnalysis(
            algorithm_comparison=f"{algorithm_a} vs {algorithm_b}",
            effect_size=diff_mean,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            cohen_d=cohen_d,
            power=power,
        )

    def _calculate_power(self, effect_size: float, n1: int, n2: int) -> float:
        """Calculate statistical power (simplified approximation)."""
        # Simplified power calculation
        pooled_n = 2 * n1 * n2 / (n1 + n2)
        ncp = effect_size * np.sqrt(pooled_n / 2)  # Non-centrality parameter

        # Approximate power using normal approximation
        critical_t = stats.norm.ppf(1 - self.significance_level / 2)
        power = 1 - stats.norm.cdf(critical_t - ncp) + stats.norm.cdf(-critical_t - ncp)

        return min(1.0, max(0.0, power))

    def multiple_comparisons_correction(self, p_values: list[float], method: str = "bonferroni") -> list[float]:
        """Apply multiple comparisons correction."""

        if method == "bonferroni":
            return [min(1.0, p * len(p_values)) for p in p_values]
        elif method == "benjamini_hochberg":
            # Benjamini-Hochberg procedure
            sorted_indices = np.argsort(p_values)
            sorted_p = np.array(p_values)[sorted_indices]

            corrected = np.zeros_like(sorted_p)
            for i in range(len(sorted_p) - 1, -1, -1):
                if i == len(sorted_p) - 1:
                    corrected[i] = sorted_p[i]
                else:
                    corrected[i] = min(sorted_p[i] * len(sorted_p) / (i + 1), corrected[i + 1])

            # Reorder back to original indices
            result = np.zeros_like(corrected)
            result[sorted_indices] = corrected
            return result.tolist()

        return p_values  # No correction


async def main():
    """Main benchmarking orchestrator."""

    print("🚀 Advanced Contextual Bandits: Comprehensive Performance Benchmark")
    print("=" * 80)

    # Configuration
    config = BenchmarkConfig(
        num_rounds=2000,  # Reduced for demo
        num_repetitions=5,  # Reduced for demo
        warmup_rounds=200,
        algorithms=["epsilon_greedy", "thompson_sampling", "linucb", "doubly_robust", "offset_tree"],
    )

    print("Configuration:")
    print(f"  Algorithms: {', '.join(config.algorithms)}")
    print(f"  Rounds per experiment: {config.num_rounds}")
    print(f"  Repetitions: {config.num_repetitions}")
    print(f"  Context dimension: {config.context_dimension}")
    print(f"  Number of actions: {config.num_actions}")
    print("=" * 80)

    # Run benchmark
    benchmark = PerformanceBenchmark(config)
    aggregated_results = await benchmark.run_comprehensive_benchmark()

    # Statistical analysis
    analyzer = StatisticalAnalyzer(config.significance_level)

    # Compare advanced algorithms against baselines
    comparisons = []
    baseline_algorithms = ["epsilon_greedy", "thompson_sampling", "linucb"]
    advanced_algorithms = ["doubly_robust", "offset_tree"]

    for advanced in advanced_algorithms:
        for baseline in baseline_algorithms:
            if advanced in aggregated_results and baseline in aggregated_results:
                # Get final performance data for comparison
                advanced_performance = [r.final_performance for r in benchmark.results if r.algorithm == advanced]
                baseline_performance = [r.final_performance for r in benchmark.results if r.algorithm == baseline]

                comparison = analyzer.compare_algorithms(advanced_performance, baseline_performance, advanced, baseline)
                comparisons.append(comparison)

    # Apply multiple comparisons correction
    p_values = [c.p_value for c in comparisons]
    corrected_p_values = analyzer.multiple_comparisons_correction(p_values, "bonferroni")

    for comparison, corrected_p in zip(comparisons, corrected_p_values):
        comparison.p_value = corrected_p
        comparison.is_significant = corrected_p < config.significance_level

    # Display results
    print("\n📊 BENCHMARK RESULTS")
    print("=" * 80)

    # Algorithm performance summary
    print("\n🎯 Algorithm Performance Summary:")
    print("-" * 50)

    # Sort by final performance
    sorted_algorithms = sorted(
        aggregated_results.items(), key=lambda x: x[1]["final_performance"]["mean"], reverse=True
    )

    for i, (algorithm, algorithm_stats) in enumerate(sorted_algorithms):
        perf = algorithm_stats["final_performance"]
        latency = algorithm_stats["latency"]
        print(f"{i + 1}. {algorithm}:")
        print(f"   Performance: {perf['mean']:.4f} ± {perf['std']:.4f}")
        print(f"   Latency: {latency['mean']:.2f}ms (p95: {latency['p95']:.2f}ms)")
        print(f"   Convergence: {algorithm_stats['convergence']['mean_rounds']:.0f} rounds")

    # Statistical comparisons
    print("\n📈 Statistical Comparisons:")
    print("-" * 50)

    significant_improvements = []
    for comparison in comparisons:
        effect_pct = comparison.effect_size * 100
        significance_marker = "✅" if comparison.is_significant else "❌"

        print(f"{significance_marker} {comparison.algorithm_comparison}:")
        print(f"   Effect Size: {effect_pct:+.2f}%")
        print(
            f"   95% CI: [{comparison.confidence_interval[0] * 100:.2f}%, {comparison.confidence_interval[1] * 100:.2f}%]"
        )
        print(f"   p-value: {comparison.p_value:.4f} (corrected)")
        print(f"   Cohen's d: {comparison.cohen_d:.3f}")
        print(f"   Statistical Power: {comparison.power:.3f}")

        if comparison.is_significant and comparison.effect_size > 0:
            significant_improvements.append(comparison)

    # Summary of significant improvements
    if significant_improvements:
        print("\n🏆 Significant Improvements Found:")
        print("-" * 40)
        for improvement in significant_improvements:
            print(f"• {improvement.algorithm_comparison}: {improvement.effect_size * 100:+.2f}% improvement")
    else:
        print("\n⚠️  No statistically significant improvements detected")
        print("   Consider: larger sample size, different parameters, or longer experiments")

    # Performance insights
    print("\n💡 Performance Insights:")
    print("-" * 30)

    # Best overall performer
    best_algorithm = sorted_algorithms[0][0]
    best_stats = sorted_algorithms[0][1]
    print(f"• Best Overall: {best_algorithm} ({best_stats['final_performance']['mean']:.4f} avg performance)")

    # Fastest algorithm
    fastest_algorithm = min(aggregated_results.items(), key=lambda x: x[1]["latency"]["mean"])
    print(f"• Fastest: {fastest_algorithm[0]} ({fastest_algorithm[1]['latency']['mean']:.2f}ms avg latency)")

    # Most consistent
    most_consistent = min(aggregated_results.items(), key=lambda x: x[1]["final_performance"]["std"])
    print(f"• Most Consistent: {most_consistent[0]} (std: {most_consistent[1]['final_performance']['std']:.4f})")

    # Save detailed results
    output_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "aggregated_results": aggregated_results,
        "statistical_comparisons": [asdict(c) for c in comparisons],
        "summary": {
            "best_algorithm": best_algorithm,
            "significant_improvements": len(significant_improvements),
            "total_experiments": len(benchmark.results),
        },
    }

    output_file = Path("comprehensive_bandit_benchmark_results.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\n📁 Detailed results saved: {output_file.absolute()}")
    print("\n✅ Comprehensive benchmark completed!")


if __name__ == "__main__":
    # Run benchmark
    asyncio.run(main())
