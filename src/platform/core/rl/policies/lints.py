"""Compatibility shim for lints under `platform.core.rl.policies`.

Re-exports classes from `platform.rl.core.policies.lints`.
"""

from platform.rl.core.policies.lints import LinTSDiagBandit


__all__ = ["LinTSDiagBandit"]
