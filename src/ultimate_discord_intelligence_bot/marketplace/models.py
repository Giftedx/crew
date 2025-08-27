"""Database models for the plugin marketplace.

These lightweight dataclasses mirror the SQLite tables used to track
marketplace repositories, plugins, releases and installs.  The store in
:mod:`store` is responsible for persisting them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Repo:
    id: str
    name: str
    url: str
    type: str  # git|registry|archive
    status: str
    trust_tier: str
    signing_policy: str | None = None
    last_synced_at: Optional[datetime] = None


@dataclass(slots=True)
class Plugin:
    id: str
    repo_id: str
    name: str
    version: str
    manifest_hash: str
    signature: str
    signer_fingerprint: str
    trust_tier: str
    published_at: datetime


@dataclass(slots=True)
class Signer:
    fingerprint: str
    issuer: str
    subject: str
    trust_tier: str
    revoked: bool
    not_before: datetime
    not_after: datetime


@dataclass(slots=True)
class Release:
    plugin_id: str
    version: str
    artifact_url: str
    checksum_sha256: str
    signature: str
    min_core_version: str
    notes: str | None = None


@dataclass(slots=True)
class Advisory:
    id: str
    plugin_id: str | None
    cve_id: str | None
    severity: str
    description: str
    affected_versions: str
    fixed_in: str | None
    published_at: datetime


@dataclass(slots=True)
class Install:
    id: str
    tenant_id: str
    plugin_name: str
    version: str
    enabled: bool
    config: str
    trust_tier_assigned: str
    install_source: str
    installed_at: datetime
    updated_at: datetime | None = None


@dataclass(slots=True)
class Rollout:
    id: str
    plugin_name: str
    target_version: str
    staged_pct: int
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    rollback_of: str | None = None
