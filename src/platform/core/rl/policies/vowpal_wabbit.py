"""Compatibility shim for vowpal_wabbit under `platform.core.rl.policies`.

Re-exports classes from `platform.rl.core.policies.vowpal_wabbit`.
"""

from platform.rl.core.policies.vowpal_wabbit import VowpalWabbitBandit


__all__ = ["VowpalWabbitBandit"]
