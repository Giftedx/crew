from __future__ import annotations

from pathlib import Path
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any

import dspy

from .dspy_components.signature import DebateAnalysisSignature


if TYPE_CHECKING:
    from collections.abc import Callable

class AgentOptimizer:
    """A service to optimize agent prompts using DSPy."""

    def __init__(self, model: str='gpt-4o-mini', storage_dir: str='crew_data/dspy_optimized'):
        """
        Initializes the AgentOptimizer.

        Args:
            model: The LLM model to use for optimization.
            storage_dir: Directory to store optimized prompts.
        """
        self.lm = dspy.OpenAI(model=model)
        dspy.configure(lm=self.lm)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def optimize_agent_prompt(self, agent_signature: dspy.Signature, training_examples: list[dspy.Example], metric: Callable[[Any, Any], float], optimization_level: str='medium') -> StepResult:
        """
        Optimizes an agent's prompt using the specified metric and training data.

        Args:
            agent_signature: The DSPy signature defining the agent's task.
            training_examples: A list of dspy.Example objects for training.
            metric: A callable function to evaluate the performance of the agent.
            optimization_level: The level of optimization to perform ("light", "medium", "heavy").

        Returns:
            A StepResult containing the optimized DSPy module.
        """
        try:

            class AgentModule(dspy.Module):

                def __init__(self, signature):
                    super().__init__()
                    self.predict = dspy.ChainOfThought(signature)

                def forward(self, **kwargs):
                    return self.predict(**kwargs)
            optimizer = dspy.MIPROv2(metric=metric, auto=optimization_level)
            optimized_module = optimizer.compile(AgentModule(agent_signature), trainset=training_examples)
            return StepResult.ok(data=optimized_module)
        except Exception as e:
            return StepResult.fail(f'DSPy optimization failed: {e}')

    def save_optimized_module(self, optimized_module: dspy.Module, agent_name: str, version: str='v1') -> StepResult:
        """
        Saves an optimized DSPy module to disk.

        Args:
            optimized_module: The optimized module to save.
            agent_name: The name of the agent (e.g., "mission_orchestrator").
            version: The version identifier for this optimization.

        Returns:
            StepResult indicating success or failure.
        """
        try:
            filename = f'{agent_name}_{version}_optimized.json'
            filepath = self.storage_dir / filename
            optimized_module.save(str(filepath))
            return StepResult.ok(data={'saved_to': str(filepath), 'agent': agent_name, 'version': version})
        except Exception as e:
            return StepResult.fail(f'Failed to save optimized module: {e}')

    def load_optimized_module(self, agent_name: str, version: str='v1', signature: dspy.Signature | None=None) -> StepResult:
        """
        Loads a previously optimized DSPy module from disk.

        Args:
            agent_name: The name of the agent.
            version: The version identifier to load.
            signature: The DSPy signature to use when loading the module.

        Returns:
            StepResult containing the loaded module.
        """
        try:
            filename = f'{agent_name}_{version}_optimized.json'
            filepath = self.storage_dir / filename
            if not filepath.exists():
                return StepResult.fail(f'Optimized module not found: {filepath}')
            if signature:

                class AgentModule(dspy.Module):

                    def __init__(self, sig):
                        super().__init__()
                        self.predict = dspy.ChainOfThought(sig)

                    def forward(self, **kwargs):
                        return self.predict(**kwargs)
                module = AgentModule(signature)
                module.load(str(filepath))
            else:
                module = dspy.Module()
                module.load(str(filepath))
            return StepResult.ok(data=module)
        except Exception as e:
            return StepResult.fail(f'Failed to load optimized module: {e}')

    def compare_optimized_vs_baseline(self, optimized_module: dspy.Module, baseline_module: dspy.Module, test_examples: list[dspy.Example], metric: Callable[[Any, Any], float]) -> StepResult:
        """
        Compares optimized module performance against baseline.

        Args:
            optimized_module: The optimized DSPy module.
            baseline_module: The baseline (unoptimized) module.
            test_examples: Test examples for evaluation.
            metric: Metric function for scoring.

        Returns:
            StepResult with comparison results.
        """
        try:
            optimized_scores = []
            baseline_scores = []
            for example in test_examples:
                try:
                    optimized_pred = optimized_module(**example.inputs())
                    optimized_score = metric(example, optimized_pred)
                    optimized_scores.append(optimized_score)
                except Exception:
                    optimized_scores.append(0.0)
                try:
                    baseline_pred = baseline_module(**example.inputs())
                    baseline_score = metric(example, baseline_pred)
                    baseline_scores.append(baseline_score)
                except Exception:
                    baseline_scores.append(0.0)
            avg_optimized = sum(optimized_scores) / len(optimized_scores) if optimized_scores else 0
            avg_baseline = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
            improvement = (avg_optimized - avg_baseline) / avg_baseline * 100 if avg_baseline > 0 else 0
            comparison = {'optimized_avg_score': avg_optimized, 'baseline_avg_score': avg_baseline, 'improvement_percent': improvement, 'test_examples_count': len(test_examples), 'optimized_scores': optimized_scores, 'baseline_scores': baseline_scores, 'recommendation': 'deploy_optimized' if improvement > 10 else 'keep_baseline' if improvement < -5 else 'monitor'}
            return StepResult.ok(data=comparison)
        except Exception as e:
            return StepResult.fail(f'A/B comparison failed: {e}')

    def calculate_metric(self, module: dspy.Module, examples: list[dspy.Example], metric: Callable[[Any, Any], float]) -> StepResult:
        """
        Calculate performance metric for a module on a set of examples.

        Args:
            module: The DSPy module to evaluate.
            examples: Examples to evaluate on.
            metric: Metric function for scoring.

        Returns:
            StepResult with metric calculation results.
        """
        try:
            scores = []
            for example in examples:
                try:
                    prediction = module(**example.inputs())
                    score = metric(example, prediction)
                    scores.append(score)
                except Exception:
                    scores.append(0.0)
            avg_score = sum(scores) / len(scores) if scores else 0.0
            result = {'average_score': avg_score, 'total_examples': len(examples), 'scores': scores, 'min_score': min(scores) if scores else 0.0, 'max_score': max(scores) if scores else 0.0}
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f'Metric calculation failed: {e}')

def example_metric(example, prediction, _trace=None):
    return example.answer == prediction.answer
if __name__ == '__main__':
    train_set = [dspy.Example(transcript='The debate was about climate change. One side argued for policy, the other for markets.', answer='Claims: Pro-policy vs. Pro-market').with_inputs('transcript'), dspy.Example(transcript='They discussed universal healthcare. Arguments included cost and accessibility.', answer='Claims: Cost vs. Accessibility').with_inputs('transcript')]
    optimizer_service = AgentOptimizer()
    signature = DebateAnalysisSignature
    result = optimizer_service.optimize_agent_prompt(agent_signature=signature, training_examples=train_set, metric=example_metric, optimization_level='light')
    if result.success:
        optimized_program = result.data
        print('✅ DSPy optimization successful!')
    else:
        print(f'❌ DSPy optimization failed: {result.error}')
