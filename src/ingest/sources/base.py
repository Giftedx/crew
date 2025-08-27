from __future__ import annotations

"""Source connector interface for the ingest scheduler."""

from dataclasses import dataclass
from typing import List, Protocol, Optional


@dataclass
class Watch:
    """Configuration for a watched source."""

    id: int
    source_type: str
    handle: str
    tenant: str
    workspace: str
    label: Optional[str] = None


@dataclass
class DiscoveryItem:
    """A new or updated piece of content discovered for a watch."""

    external_id: str
    url: str
    published_at: Optional[str] = None


class SourceConnector(Protocol):
    """Connector contract used by :mod:`scheduler`.

    Each connector must implement a ``discover`` method that returns new
    :class:`DiscoveryItem` objects for the given :class:`Watch` and a mutable
    ``state`` dictionary holding connector-specific cursor information.
    """

    def discover(self, watch: Watch, state: dict) -> List[DiscoveryItem]:
        ...

