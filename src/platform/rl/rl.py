"""Compatibility shim for platform.rl.rl module.

Re-exports RL components for backward compatibility.
"""

from platform.rl.langsmith_trajectory_evaluator import LangSmithTrajectoryEvaluator

__all__ = ["LangSmithTrajectoryEvaluator"]
