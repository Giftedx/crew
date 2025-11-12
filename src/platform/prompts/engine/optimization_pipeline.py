"""Compatibility shim for optimization_pipeline imports.

Re-exports from ultimate_discord_intelligence_bot.services.optimization_pipeline
for backward compatibility.
"""

from ultimate_discord_intelligence_bot.services.optimization_pipeline import (
    OptimizationConfig,
    OptimizationPipeline,
)


__all__ = ["OptimizationConfig", "OptimizationPipeline"]
