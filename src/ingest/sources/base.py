from __future__ import annotations

"""Source connector interface for the ingest scheduler."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Watch:
    """Configuration for a watched source."""

    id: int
    source_type: str
    handle: str
    tenant: str
    workspace: str
    label: str | None = None


@dataclass
class DiscoveryItem:
    """A new or updated piece of content discovered for a watch."""

    external_id: str
    url: str
    published_at: str | None = None


class SourceConnector(Protocol):
    """Connector contract used by :mod:`scheduler`.

    Each connector must implement a ``discover`` method that returns new
    :class:`DiscoveryItem` objects for the given :class:`Watch` and a mutable
    ``state`` dictionary holding connector-specific cursor information.
    """

    def discover(self, watch: Watch, state: dict) -> list[DiscoveryItem]: ...
