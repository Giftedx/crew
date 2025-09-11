"""Data models for creator profiles and platform links."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CanonicalChannel:
    """Canonical representation of a video or livestream channel."""

    id: str
    handle: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalChannel:
        return cls(**data)


@dataclass
class CanonicalProfile:
    """Canonical representation of a social profile."""

    id: str | None = None
    handle: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalProfile:
        return cls(**data)


@dataclass
class CanonicalFeed:
    """Canonical representation of a podcast feed."""

    rss_url: str
    directory_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalFeed:
        return cls(**data)


@dataclass
class VerificationEvent:
    """Record of a verification attempt for a profile."""

    timestamp: datetime
    status: str
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationEvent:
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data["status"],
            details=data.get("details"),
        )


@dataclass
class Platforms:
    """Collection of platform links for a creator."""

    youtube: list[CanonicalChannel] = field(default_factory=list)
    twitch: list[CanonicalChannel] = field(default_factory=list)
    podcast: list[CanonicalFeed] = field(default_factory=list)
    instagram: list[CanonicalProfile] = field(default_factory=list)
    twitter: list[CanonicalProfile] = field(default_factory=list)
    tiktok: list[CanonicalProfile] = field(default_factory=list)
    other: list[CanonicalProfile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "youtube": [c.to_dict() for c in self.youtube],
            "twitch": [c.to_dict() for c in self.twitch],
            "podcast": [c.to_dict() for c in self.podcast],
            "instagram": [c.to_dict() for c in self.instagram],
            "twitter": [c.to_dict() for c in self.twitter],
            "tiktok": [c.to_dict() for c in self.tiktok],
            "other": [c.to_dict() for c in self.other],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Platforms:
        return cls(
            youtube=[CanonicalChannel.from_dict(d) for d in data.get("youtube", [])],
            twitch=[CanonicalChannel.from_dict(d) for d in data.get("twitch", [])],
            podcast=[CanonicalFeed.from_dict(d) for d in data.get("podcast", [])],
            instagram=[CanonicalProfile.from_dict(d) for d in data.get("instagram", [])],
            twitter=[CanonicalProfile.from_dict(d) for d in data.get("twitter", [])],
            tiktok=[CanonicalProfile.from_dict(d) for d in data.get("tiktok", [])],
            other=[CanonicalProfile.from_dict(d) for d in data.get("other", [])],
        )


@dataclass
class CreatorProfile:
    """Canonical profile for a creator, brand, or show."""

    name: str
    known_as: str | None = None
    type: str = "person"
    roles: list[str] = field(default_factory=list)
    shows: list[str] = field(default_factory=list)
    description: str | None = None
    content_tags: list[str] = field(default_factory=list)
    platforms: Platforms = field(default_factory=Platforms)
    frequent_collaborators: list[str] = field(default_factory=list)
    last_verified_at: datetime | None = None
    verification_log: list[VerificationEvent] = field(default_factory=list)
    last_checked: dict[str, datetime] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["platforms"] = self.platforms.to_dict()
        data["verification_log"] = [e.to_dict() for e in self.verification_log]
        if self.last_verified_at:
            data["last_verified_at"] = self.last_verified_at.isoformat()
        else:
            data["last_verified_at"] = None
        data["last_checked"] = {k: v.isoformat() for k, v in self.last_checked.items()}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CreatorProfile:
        last_verified_at = data.get("last_verified_at")
        return cls(
            name=data["name"],
            known_as=data.get("known_as"),
            type=data.get("type", "person"),
            roles=data.get("roles", []),
            shows=data.get("shows", []),
            description=data.get("description"),
            content_tags=data.get("content_tags", []),
            platforms=Platforms.from_dict(data.get("platforms", {})),
            frequent_collaborators=data.get("frequent_collaborators", []),
            last_verified_at=datetime.fromisoformat(last_verified_at) if last_verified_at else None,
            verification_log=[VerificationEvent.from_dict(ev) for ev in data.get("verification_log", [])],
            last_checked={k: datetime.fromisoformat(v) for k, v in data.get("last_checked", {}).items()},
        )


@dataclass
class CreatorSeed:
    """Seed data used to bootstrap a creator profile."""

    name: str
    type: str
    roles: list[str] = field(default_factory=list)
    shows: list[str] = field(default_factory=list)
    content_tags: list[str] = field(default_factory=list)
    seed_handles: dict[str, list[str]] = field(default_factory=dict)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CreatorSeed:
        return cls(
            name=data["name"],
            type=data.get("type", "person"),
            roles=data.get("roles", []),
            shows=data.get("shows", []),
            content_tags=data.get("content_tags", []),
            seed_handles=data.get("seed_handles", {}),
            notes=data.get("notes"),
        )


def load_seeds(path: str) -> list[CreatorSeed]:
    """Load creator seed profiles from a YAML file."""
    try:  # Local import guarded to keep optional dependency soft for type checking
        import yaml  # noqa: PLC0415
    except Exception:  # pragma: no cover - degrade gracefully if yaml missing
        raise ImportError(
            "PyYAML is required to load seed profiles. Install with 'pip install PyYAML' or add the 'dev' extras."
        ) from None

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    seeds = raw.get("profiles", [])
    return [CreatorSeed.from_dict(p) for p in seeds]
