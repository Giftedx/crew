"""Compatibility shim for linucb under `platform.core.rl.policies`.

Re-exports classes from `platform.rl.core.policies.linucb`.
"""

from platform.rl.core.policies.linucb import LinUCBDiagBandit


__all__ = ["LinUCBDiagBandit"]
