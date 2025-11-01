from __future__ import annotations

import contextlib
import importlib
import os
import site
import sys
import sysconfig
from importlib.machinery import PathFinder
from importlib.util import module_from_spec
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast


try:
    from scripts.helpers.ui_constants import (
        BUTTON_STYLE_LINK,
        BUTTON_STYLE_PRIMARY,
        BUTTON_STYLE_SECONDARY,
        LIGHTWEIGHT_IMPORT_FLAG,
    )
except ImportError:
    # Fallback constants when scripts.helpers not available
    BUTTON_STYLE_LINK = 5
    BUTTON_STYLE_PRIMARY = 1
    BUTTON_STYLE_SECONDARY = 2
    LIGHTWEIGHT_IMPORT_FLAG = "1"

# Public flags for availability
LIGHTWEIGHT_IMPORT = os.getenv("LIGHTWEIGHT_IMPORT") == LIGHTWEIGHT_IMPORT_FLAG
_DISCORD_AVAILABLE = False

# For static analysis, treat discord/commands as dynamic modules
discord: Any
commands: Any
app_commands: Any


def _import_real_discord_if_needed() -> tuple[Any | None, Any | None, Any | None]:
    """Import discord and its submodules, preferring the real site-packages package.

    If a local testing shim at src/discord shadows the real dependency and
    prevents importing discord.ext.commands, this function adjusts sys.path
    and sys.modules to resolve the genuine library.
    """

    # First attempt: normal import (may hit local shim)
    try:
        _discord = importlib.import_module("discord")
        _commands = importlib.import_module("discord.ext.commands")
        _app_commands = importlib.import_module("discord.app_commands")
        return _discord, _commands, _app_commands
    except Exception:
        pass

    # Fallback: remove local shim from sys.modules/path and try site-packages
    orig_path = list(sys.path)
    # Remove any already-imported discord modules to avoid cache effects
    for m in list(sys.modules):
        if m == "discord" or m.startswith("discord."):
            sys.modules.pop(m, None)
    try:
        # Exclude repository src path where a local shim may live
        try:
            # Path(__file__) -> .../src/ultimate_discord_intelligence_bot/discord_bot/discord_env.py
            # parents[2] resolves to the repository 'src' directory.
            repo_src = Path(__file__).resolve().parents[2]
            sys.path = [p for p in sys.path if Path(p).resolve() != repo_src]
        except Exception:
            pass
        # Candidate site-packages roots to search explicitly
        candidates: list[str] = []
        for key in ("purelib", "platlib"):
            try:
                p = sysconfig.get_path(key)
                if p and p not in candidates:
                    candidates.append(p)
            except Exception:
                pass
        try:
            for p in site.getsitepackages():  # type: ignore[attr-defined]
                if p not in candidates:
                    candidates.append(p)
        except Exception:
            pass

        def _load_from(paths: list[str], modname: str) -> Any:
            for root in paths:
                try:
                    spec = PathFinder.find_spec(modname, [root])
                    if spec and spec.loader:
                        mod = module_from_spec(spec)
                        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                        return mod
                except Exception:
                    continue
            return None

        _discord = _load_from(candidates, "discord")
        _commands = _load_from(candidates, "discord.ext.commands")
        _app_commands = _load_from(candidates, "discord.app_commands")
        if _discord and _commands and _app_commands:
            return _discord, _commands, _app_commands
        return None, None, None
    except Exception:
        return None, None, None
    finally:
        sys.path = orig_path


if not LIGHTWEIGHT_IMPORT:
    _d, _c, _a = _import_real_discord_if_needed()
    if _d is not None and _c is not None and _a is not None:
        with contextlib.suppress(Exception):  # pragma: no cover
            _ = importlib.import_module("discord.errors").LoginFailure
        discord = cast("Any", _d)
        commands = cast("Any", _c)
        app_commands = cast("Any", _a)
        _DISCORD_AVAILABLE = True
    else:  # pragma: no cover - dependency missing or shim-only environment
        _DISCORD_AVAILABLE = False
        LIGHTWEIGHT_IMPORT = True

if LIGHTWEIGHT_IMPORT or not _DISCORD_AVAILABLE:
    # Remove partially imported modules so tests can assert absence
    import sys as _sys

    for _m in list(_sys.modules):
        if _m == "discord" or _m.startswith("discord."):
            _sys.modules.pop(_m, None)

    class _ShimIntents:
        def __init__(self) -> None:
            self.message_content = True
            self.guilds = True

        @staticmethod
        def default() -> _ShimIntents:
            return _ShimIntents()

    class _ShimBot:
        def __init__(self, *_: Any, **__: Any) -> None:
            self.intents = _ShimIntents.default()
            self.tree = type("Tree", (), {"sync": staticmethod(list)})()

        def command(self, *_: Any, **__: Any) -> Any:
            def deco(fn: Any) -> Any:
                return fn

            return deco

        def event(self, fn: Any) -> Any:
            return fn

        async def process_commands(self, *_args: Any, **_kwargs: Any) -> None:  # minimal no-op
            return None

        async def start(self, *_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - shim gateway entrypoint
            raise AttributeError("_ShimBot does not support gateway start; use webhook/headless mode")

    class _ShimUI:
        class ButtonStyle:
            primary = BUTTON_STYLE_PRIMARY
            secondary = BUTTON_STYLE_SECONDARY
            link = BUTTON_STYLE_LINK

        class View:
            def __init__(self, *_: Any, **__: Any) -> None:
                pass

            def add_item(self, *_a: Any, **_k: Any) -> None:
                return None

        class Button:
            def __init__(self, *_: Any, **__: Any) -> None:
                pass

    discord = SimpleNamespace(Intents=_ShimIntents, Embed=object, Interaction=object, ui=_ShimUI)  # type: ignore[assignment]
    commands = SimpleNamespace(Bot=_ShimBot, CommandNotFound=Exception)  # type: ignore[assignment]
    app_commands = SimpleNamespace(
        describe=lambda **kwargs: lambda f: f,
        choices=lambda choices: lambda f: f,
        Choice=object,
    )  # type: ignore[assignment]
    discord = cast("Any", discord)
    commands = cast("Any", commands)
    app_commands = cast("Any", app_commands)


def build_intents() -> Any:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    return intents


__all__ = [
    "LIGHTWEIGHT_IMPORT",
    "_DISCORD_AVAILABLE",
    "app_commands",
    "build_intents",
    "commands",
    "discord",
]
