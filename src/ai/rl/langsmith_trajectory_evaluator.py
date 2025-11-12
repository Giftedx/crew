"""Compatibility shim for ai.rl.langsmith_trajectory_evaluator.

Re-exports from platform.rl for backward compatibility.
"""

from platform.rl.langsmith_trajectory_evaluator import LangSmithTrajectoryEvaluator


__all__ = ["LangSmithTrajectoryEvaluator"]
