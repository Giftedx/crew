"""Internal Discord package for test helpers and observability modules.

This shim exposes lightweight, internal modules under ``src/discord`` used by
our tests (e.g., ``src.discord.observability``). It deliberately avoids importing
or shadowing the external ``discord.py`` package and does not re-export bot
command utilities.

If you need the real gateway client, install and import ``discord.py``.
"""

# Do not import submodules at package import time. Tests will import the
# desired subpackages directly, e.g. ``src.discord.observability``.

__all__: list[str] = []
