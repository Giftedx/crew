"""Local discord shim for ops/testing utilities.

This lightweight package only exists to satisfy unit tests that import
``from discord import commands`` and call helper functions like
``ops_incident_open`` or ``ops_ingest_queue_status``. It is not a
replacement for the real ``discord.py`` library used by the runtime.

At runtime, the bot imports the genuine library via
``ultimate_discord_intelligence_bot.discord_bot.discord_env`` which
explicitly avoids this shim. Tests, however, purposefully use this shim
to avoid bringing in the heavy gateway dependency.
"""

from typing import Any

from . import commands as commands  # re-export for ``from discord import commands``

__all__ = ["commands"]
"""Local 'discord' shim disabled.

This repository previously contained a test-only shim at ``src/discord`` that
shadowed the real ``discord.py`` package. To prevent accidental shadowing and
restore full gateway functionality, the shim now raises on access. Install the
official dependency instead: ``pip install discord.py``.
"""


def __getattr__(name: str) -> Any:  # pragma: no cover - shim should not be used
    raise ImportError("Local 'src/discord' shim is disabled. Install 'discord.py' and import the real package.")
