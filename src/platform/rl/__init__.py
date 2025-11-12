"""
Reinforcement learning (RL) utilities for the platform package.

This package intentionally avoids importing heavy, optional modules at import
 time to keep test environments lightweight. Submodules should be imported by
 fully-qualified name, e.g. ``from platform.rl.learning_engine import LearningEngine``.
"""

# Deliberately do not import optional submodules here to prevent ImportErrors
# in lightweight test environments. Consumers should import submodules
# explicitly.


# Placeholder for backward compatibility
class _LearnModule:
    """Placeholder for learn module."""


learn = _LearnModule()


__all__: list[str] = ["learn"]
