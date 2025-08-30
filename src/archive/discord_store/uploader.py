"""Async Discord uploader using discord.py with webhook fallback.

Typing strategy:
 - ``discord`` is an optional dependency; when absent we provide minimal fallbacks so the
     module still type-checks and callers can feature-flag usage.
 - Avoid subclassing ``discord.Client`` directly (mypy complained about invalid base when
     stubs unavailable / treated as variable). Instead use composition: create a one-shot
     helper that owns a client instance when discord is present.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import aiohttp

try:  # optional dependency
    import discord
    _DISCORD_AVAILABLE = True
except Exception:  # pragma: no cover
    discord = None  # type: ignore
    _DISCORD_AVAILABLE = False


class UploadError(RuntimeError):
    """Raised when Discord returns an error during upload."""


@runtime_checkable
class _MessageLike(Protocol):  # minimal attrs we read
    id: Any
    channel: Any
    attachments: list[Any]


@runtime_checkable
class _FileFactory(Protocol):
    def __call__(self, path: Path) -> Any: ...


def _make_file(path: Path) -> Any:
    if _DISCORD_AVAILABLE and hasattr(discord, "File"):
        file_ctor = getattr(discord, "File", None)
        if callable(file_ctor):  # pragma: no branch - trivial
            return file_ctor(path)
    return path  # fallback sentinel

class _OneShotClient:
    """Composition wrapper around discord.Client (when available)."""

    def __init__(self, path: Path, channel_id: int) -> None:
        self._path = path
        self._channel_id = channel_id
        self._future: asyncio.Future[_MessageLike] = asyncio.get_event_loop().create_future()
        self._client: Any | None = None
        if _DISCORD_AVAILABLE and discord is not None:
            intents_cls = getattr(discord, "Intents", None)
            intents_val = intents_cls.none() if intents_cls and hasattr(intents_cls, "none") else None
            client_cls = getattr(discord, "Client", None)
            if client_cls is not None:
                self._client = client_cls(intents=intents_val)
                # register event handler dynamically
                async def on_ready():  # pragma: no cover - network dependent
                    channel = await self._client.fetch_channel(self._channel_id)
                    msg = await channel.send(file=_make_file(self._path))
                    self._future.set_result(cast(_MessageLike, msg))
                    await self._client.close()
                setattr(self._client, "on_ready", on_ready)

    async def start(self, token: str) -> None:  # pragma: no cover - network
        if not self._client:
            raise UploadError("discord client unavailable")
        await self._client.start(token)

    @property
    def future(self) -> asyncio.Future[_MessageLike]:
        return self._future


async def upload_file(
    path: str | Path,
    channel_id: str,
    *,
    token: str,
    use_webhook: bool = False,
) -> dict[str, Any]:
    """Upload ``path`` to Discord and return the message payload.

    ``channel_id`` is interpreted as a webhook URL when ``use_webhook`` is True.
    ``discord.py`` handles rate limits internally; network errors propagate as
    ``UploadError``.
    """
    p = Path(path)
    msg: _MessageLike | None = None
    if use_webhook:
        if not _DISCORD_AVAILABLE or discord is None:
            raise UploadError("discord not available for webhook upload")
        async with aiohttp.ClientSession() as session:  # pragma: no cover - network
            webhook_cls = getattr(discord, "Webhook", None)
            if webhook_cls is None:  # pragma: no cover - defensive
                raise UploadError("discord.Webhook unavailable")
            webhook = webhook_cls.from_url(channel_id, session=session)
            msg = cast(_MessageLike, await webhook.send(file=_make_file(p), wait=True))
    else:
        client = _OneShotClient(p, int(channel_id))
        try:
            await client.start(token)  # pragma: no cover - network
        except Exception as exc:  # pragma: no cover - network
            raise UploadError(str(exc)) from exc
        msg = await client.future
    if msg is None:
        raise UploadError("message upload failed")
    return {
        "id": str(msg.id),
        "channel_id": str(msg.channel.id),
        "attachments": [
            {
                "id": str(a.id),
                "url": getattr(a, "url", ""),
                "filename": getattr(a, "filename", ""),
                "size": getattr(a, "size", 0),
            }
            for a in msg.attachments
        ],
    }


def upload_file_sync(path: str | Path, channel_id: str, *, token: str) -> dict[str, Any]:
    """Synchronous wrapper around :func:`upload_file`."""
    return asyncio.run(upload_file(path, channel_id, token=token))


__all__ = ["upload_file", "upload_file_sync", "UploadError"]
