"""Shim package that exposes command helpers and discord.py classes.

The actual ``discord`` import is performed lazily via ``import_module`` so
tests that do not install the optional dependency still import this shim
without failing (tools using the real client will provide it in prod).
"""

from importlib import import_module

from . import commands  # re-export lightweight command helpers

_discord = import_module("discord")  # noqa: PLC0415 - dynamic optional dependency load

Client = getattr(_discord, "Client", object)
Intents = getattr(_discord, "Intents", object)
File = getattr(_discord, "File", object)

__all__ = ["commands", "Client", "Intents", "File"]
