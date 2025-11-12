"""Compatibility shim for advanced_bandits under `platform.core.rl.policies`.

Re-exports classes from `platform.rl.core.policies.advanced_bandits`.
"""

from platform.rl.core.policies.advanced_bandits import (
    DoublyRobustBandit,
    OffsetTreeBandit,
)


__all__ = [
    "DoublyRobustBandit",
    "OffsetTreeBandit",
]
