"""Compatibility shim for core package.

Re-exports from platform and services for backward compatibility.
"""

from platform.config import flags
from platform.llm import router, token_meter
from platform.rl import learn, learning_engine

from ultimate_discord_intelligence_bot.services import prompt_engine

# Already have these from previous work
from . import alerts, degradation_reporter, eval_harness, http_utils, log_schema


# Placeholder modules
class _ReliabilityModule:
    """Placeholder for reliability module."""


class _RewardPipeModule:
    """Placeholder for reward pipe module."""


reliability = _ReliabilityModule()
reward_pipe = _RewardPipeModule()


__all__ = [
    "alerts",
    "degradation_reporter",
    "eval_harness",
    "flags",
    "http_utils",
    "learn",
    "learning_engine",
    "log_schema",
    "prompt_engine",
    "reliability",
    "reward_pipe",
    "router",
    "token_meter",
]
