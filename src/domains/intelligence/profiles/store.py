"""Profile storage for debate analysis."""

from __future__ import annotations

from .schema import CreatorProfile


class ProfileStore:
    """Store for creator profiles and collaborations."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize the profile store."""
        self.db_path = db_path
        self.profiles: dict[str, CreatorProfile] = {}
        self.collaborators: dict[str, list[str]] = {}

    def upsert_profile(self, profile: CreatorProfile) -> None:
        """Upsert a creator profile."""
        name = profile.get("name", "")
        if name:
            self.profiles[name] = profile

    def get_collaborators(self, person: str) -> list[str]:
        """Get collaborators for a person."""
        return self.collaborators.get(person, [])
