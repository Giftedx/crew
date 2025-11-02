from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentationScope:
    """Represents the library that produced telemetry."""

    name: str
    version: str | None = None
    schema_url: str | None = None

    def to_dict(self) -> dict[str, str | None]:  # pragma: no cover - helper
        return {
            "name": self.name,
            "version": self.version,
            "schema_url": self.schema_url,
        }


__all__ = ["InstrumentationScope"]
