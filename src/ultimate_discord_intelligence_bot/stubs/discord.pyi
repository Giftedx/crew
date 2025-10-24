"""Type stubs for discord module."""

from abc import ABC
from collections.abc import Awaitable, Callable
from typing import Any

# Basic types
class User:
    id: int
    name: str
    discriminator: str
    bot: bool
    system: bool
    created_at: Any
    avatar: str | None
    display_name: str
    mention: str

class Guild:
    id: int
    name: str
    owner_id: int
    created_at: Any
    member_count: int
    description: str | None

class Channel:
    id: int
    name: str
    guild: Guild | None
    created_at: Any

class TextChannel(Channel):
    topic: str | None
    slowmode_delay: int

class VoiceChannel(Channel):
    bitrate: int
    user_limit: int

class Message:
    id: int
    content: str
    author: User
    channel: Channel
    guild: Guild | None
    created_at: Any
    edited_at: Any | None
    attachments: list[Any]
    embeds: list[Any]
    reactions: list[Any]
    mention_everyone: bool
    pinned: bool
    tts: bool
    type: Any
    flags: Any

class Context:
    bot: Any
    guild: Guild | None
    channel: Channel
    author: User
    message: Message
    command: Any | None
    invoked_with: str | None
    prefix: str | None
    subcommand_passed: str | None
    command_failed: bool
    view: Any

# Bot classes
class Bot(ABC):
    def __init__(self, **kwargs: Any) -> None: ...
    async def start(self, token: str) -> None: ...
    async def close(self) -> None: ...
    def add_command(self, command: Any) -> None: ...
    def remove_command(self, name: str) -> Any | None: ...
    def get_command(self, name: str) -> Any | None: ...
    def add_cog(self, cog: Any) -> None: ...
    def remove_cog(self, name: str) -> Any | None: ...
    def get_cog(self, name: str) -> Any | None: ...
    def load_extension(self, name: str) -> None: ...
    def unload_extension(self, name: str) -> None: ...
    def reload_extension(self, name: str) -> None: ...

class AutoShardedBot(Bot):
    def __init__(self, **kwargs: Any) -> None: ...

# Command classes
class Command:
    name: str
    description: str
    brief: str | None
    usage: str | None
    aliases: list[str]
    checks: list[Callable[..., bool]]
    cooldown: Any
    cooldown_after_parsing: bool
    ignore_extra: bool
    rest_is_raw: bool
    case_insensitive: bool
    parent: Any | None
    full_parent_name: str
    qualified_name: str
    callback: Callable[..., Awaitable[Any]]
    params: dict[str, Any]

    def __init__(self, func: Callable[..., Awaitable[Any]], **kwargs: Any) -> None: ...
    async def invoke(self, ctx: Context) -> None: ...
    async def reinvoke(self, ctx: Context, *, call_hooks: bool = True) -> None: ...

class Group(Command):
    def __init__(self, func: Callable[..., Awaitable[Any]], **kwargs: Any) -> None: ...
    def command(self, name: str | None = None, **kwargs: Any) -> Callable[..., Command]: ...
    def group(self, name: str | None = None, **kwargs: Any) -> Callable[..., Group]: ...

# Decorators
def command(name: str | None = None, **kwargs: Any) -> Callable[..., Command]: ...
def group(name: str | None = None, **kwargs: Any) -> Callable[..., Group]: ...

# Events
def event(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]: ...

# File types
class File:
    def __init__(self, fp: Any, filename: str | None = None, **kwargs: Any) -> None: ...

# Embed types
class Embed:
    def __init__(self, **kwargs: Any) -> None: ...
    def add_field(self, name: str, value: str, inline: bool = True) -> None: ...
    def set_author(self, name: str, **kwargs: Any) -> None: ...
    def set_footer(self, text: str, **kwargs: Any) -> None: ...
    def set_thumbnail(self, url: str) -> None: ...
    def set_image(self, url: str) -> None: ...

# Color constants
class Color:
    def __init__(self, value: int) -> None: ...
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color: ...

# Permissions
class Permissions:
    def __init__(self, permissions: int = 0, **kwargs: Any) -> None: ...

# Activity types
class Activity:
    def __init__(self, **kwargs: Any) -> None: ...

class Game(Activity):
    def __init__(self, name: str, **kwargs: Any) -> None: ...

class Streaming(Activity):
    def __init__(self, name: str, url: str, **kwargs: Any) -> None: ...

# Status types
class Status:
    online: str
    idle: str
    dnd: str
    do_not_disturb: str
    invisible: str
    offline: str

# Error types
class DiscordException(Exception):
    def __init__(self, message: str, *args: Any) -> None: ...

class ClientException(DiscordException):
    pass

class NoMoreItems(DiscordException):
    pass

class InvalidArgument(ClientException):
    pass

class CommandNotFound(ClientException):
    pass

class MissingRequiredArgument(InvalidArgument):
    def __init__(self, param: Any) -> None: ...

class BadArgument(InvalidArgument):
    pass

class CommandError(Exception):
    def __init__(self, message: str, *args: Any) -> None: ...

class CheckFailure(CommandError):
    pass

class CommandOnCooldown(CommandError):
    def __init__(self, cooldown: Any, retry_after: float) -> None: ...

class MaxConcurrencyReached(CommandError):
    def __init__(self, number: int, per: Any) -> None: ...

class DisabledCommand(CommandError):
    pass

class CommandInvokeError(CommandError):
    def __init__(self, original: Exception) -> None: ...

class CommandRegistrationError(CommandError):
    pass

class ExtensionError(DiscordException):
    pass

class ExtensionNotFound(ExtensionError):
    def __init__(self, name: str) -> None: ...

class ExtensionAlreadyLoaded(ExtensionError):
    def __init__(self, name: str) -> None: ...

class ExtensionNotLoaded(ExtensionError):
    def __init__(self, name: str) -> None: ...

class ExtensionFailed(ExtensionError):
    def __init__(self, name: str, original: Exception) -> None: ...

class ExtensionCommandError(ExtensionError):
    def __init__(self, name: str, original: Exception) -> None: ...

# Intents
class Intents:
    def __init__(self, **kwargs: Any) -> None: ...
    @classmethod
    def default(cls) -> Intents: ...
    @classmethod
    def all(cls) -> Intents: ...
    @classmethod
    def none(cls) -> Intents: ...

# Gateway
class Gateway:
    def __init__(self, **kwargs: Any) -> None: ...

# HTTP
class HTTPClient:
    def __init__(self, **kwargs: Any) -> None: ...

# State
class ConnectionState:
    def __init__(self, **kwargs: Any) -> None: ...

# Shard
class ShardInfo:
    def __init__(self, shard_id: int, shard_count: int) -> None: ...

# Voice
class VoiceClient:
    def __init__(self, **kwargs: Any) -> None: ...

class VoiceProtocol:
    def __init__(self, **kwargs: Any) -> None: ...

# WebSocket
class WebSocketProtocol:
    def __init__(self, **kwargs: Any) -> None: ...

# Utils
def utils_find(predicate: Callable[..., bool], seq: list[Any]) -> Any | None: ...
def utils_get(iterable: list[Any], **attrs: Any) -> Any | None: ...

# Constants
__version__: str
