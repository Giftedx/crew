"""Async Discord uploader using discord.py with webhook fallback."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict

import aiohttp
import discord


class UploadError(RuntimeError):
    """Raised when Discord returns an error during upload."""


class _OneShotClient(discord.Client):
    """Client that uploads a single file then closes."""

    def __init__(self, path: Path, channel_id: int) -> None:
        intents = discord.Intents.none()
        super().__init__(intents=intents)
        self._path = path
        self._channel_id = channel_id
        self._future: asyncio.Future[discord.Message] = asyncio.get_event_loop().create_future()

    async def on_ready(self) -> None:  # pragma: no cover - requires network
        channel = await self.fetch_channel(self._channel_id)
        msg = await channel.send(file=discord.File(self._path))
        self._future.set_result(msg)
        await self.close()


async def upload_file(
    path: str | Path,
    channel_id: str,
    *,
    token: str,
    use_webhook: bool = False,
) -> Dict:
    """Upload ``path`` to Discord and return the message payload.

    ``channel_id`` is interpreted as a webhook URL when ``use_webhook`` is True.
    ``discord.py`` handles rate limits internally; network errors propagate as
    ``UploadError``.
    """
    p = Path(path)
    if use_webhook:
        async with aiohttp.ClientSession() as session:  # pragma: no cover - network
            webhook = discord.Webhook.from_url(channel_id, session=session)
            msg = await webhook.send(file=discord.File(p), wait=True)
    else:
        client = _OneShotClient(p, int(channel_id))
        try:
            await client.start(token)  # pragma: no cover - network
        except Exception as exc:  # pragma: no cover - network
            raise UploadError(str(exc)) from exc
        msg = await client._future
    return {
        "id": str(msg.id),
        "channel_id": str(msg.channel.id),
        "attachments": [
            {
                "id": str(a.id),
                "url": a.url,
                "filename": a.filename,
                "size": a.size,
            }
            for a in msg.attachments
        ],
    }


def upload_file_sync(path: str | Path, channel_id: str, *, token: str) -> Dict:
    """Synchronous wrapper around :func:`upload_file`."""
    return asyncio.run(upload_file(path, channel_id, token=token))


__all__ = ["upload_file", "upload_file_sync", "UploadError"]
