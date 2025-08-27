"""Shim package that exposes command helpers and discord.py classes."""

from importlib import import_module

_discord = import_module("discord")

from . import commands

Client = getattr(_discord, "Client", object)
Intents = getattr(_discord, "Intents", object)
File = getattr(_discord, "File", object)

__all__ = ["commands", "Client", "Intents", "File"]