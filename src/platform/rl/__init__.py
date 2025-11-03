"""
Reinforcement learning (RL) utilities for the platform package.

This package intentionally avoids importing heavy, optional modules at import
 time to keep test environments lightweight. Submodules should be imported by
 fully-qualified name, e.g. ``from platform.rl.learning_engine import LearningEngine``.
"""

# Deliberately do not import optional submodules here to prevent ImportErrors
# in lightweight test environments. Consumers should import submodules
# explicitly. Keeping __all__ empty is acceptable.

__all__: list[str] = []
