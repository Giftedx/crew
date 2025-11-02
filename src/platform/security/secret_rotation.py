"""Secret rotation registry and helpers.

This module manages *logical* secret names and their versioned refs stored in
environment variables. It provides a lightweight in-memory registry recording
activation timestamps so that a grace period (dual-publish window) can be
enforced before retiring the previous version.

Config Integration (``config/security.yaml``)::

  secrets:
    rotation:
      enabled: true
      grace_hours: 24
      audit_events: true

Usage Pattern
-------------
1. Call :func:`register` when a service starts (or when a rotation is initiated)
   specifying ``logical_name`` and its ``current_ref`` (e.g. ``API_KEY:v2``) and
   optionally ``previous_ref``.
2. The registry tracks activation time of ``current_ref``.
3. When ready to *promote* a next version, call :func:`promote` with the new
   ref (which becomes current; previous is shifted).
4. After grace period passes, call :func:`retire_previous` to drop previous
   reference (enforced if grace not yet satisfied).

Security Events
---------------
Structured security events emitted on promote / retire when auditing enabled.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import yaml
from platform.time import default_utc_now
from .events import log_security_event
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / 'config' / 'security.yaml'

@dataclass
class SecretEntry:
    logical: str
    current_ref: str
    activated_at: datetime
    previous_ref: str | None = None
    previous_activated_at: datetime | None = None

    def grace_elapsed(self, grace: timedelta) -> bool:
        return default_utc_now() - self.activated_at >= grace
_registry: dict[str, SecretEntry] = {}

def _load_rotation_config(path: Path | None=None) -> dict[str, Any]:
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return data.get('secrets', {}).get('rotation', {})

def _audit(enabled: bool, actor: str | None, action: str, logical: str, **extra: Any) -> None:
    if not enabled:
        return
    log_security_event(actor=actor or 'system', action='secret_rotation', resource=logical, decision=action, reason=extra.pop('reason', None) or 'ok', **extra)

def register(logical: str, current_ref: str, *, previous_ref: str | None=None, activated_at: datetime | None=None, actor: str | None=None, config_path: Path | None=None) -> None:
    cfg = _load_rotation_config(config_path)
    auditing = bool(cfg.get('audit_events', True))
    entry = SecretEntry(logical=logical, current_ref=current_ref, previous_ref=previous_ref, activated_at=activated_at or default_utc_now())
    _registry[logical] = entry
    _audit(auditing, actor, 'register', logical, current_ref=current_ref, previous_ref=previous_ref)

def get_current(logical: str) -> str | None:
    entry = _registry.get(logical)
    return entry.current_ref if entry else None

def get_previous(logical: str) -> str | None:
    entry = _registry.get(logical)
    return entry.previous_ref if entry else None

def promote(logical: str, new_ref: str, *, actor: str | None=None, config_path: Path | None=None) -> None:
    cfg = _load_rotation_config(config_path)
    auditing = bool(cfg.get('audit_events', True))
    now = default_utc_now()
    if logical in _registry:
        entry = _registry[logical]
        entry.previous_ref = entry.current_ref
        entry.previous_activated_at = entry.activated_at
        entry.current_ref = new_ref
        entry.activated_at = now
    else:
        _registry[logical] = SecretEntry(logical=logical, current_ref=new_ref, previous_ref=None, activated_at=now)
    _audit(auditing, actor, 'promote', logical, current_ref=new_ref)

def retire_previous(logical: str, *, actor: str | None=None, config_path: Path | None=None, ignore_grace: bool=False) -> bool:
    cfg = _load_rotation_config(config_path)
    auditing = bool(cfg.get('audit_events', True))
    grace_hours = float(cfg.get('grace_hours', 24))
    grace = timedelta(hours=grace_hours)
    entry = _registry.get(logical)
    if not entry or not entry.previous_ref:
        return False
    if not ignore_grace and (not entry.grace_elapsed(grace)):
        _audit(auditing, actor, 'retire_blocked', logical, reason='grace_not_elapsed', previous_ref=entry.previous_ref)
        return False
    prev = entry.previous_ref
    entry.previous_ref = None
    _audit(auditing, actor, 'retire', logical, retired_ref=prev)
    return True

def list_entries() -> list[SecretEntry]:
    return list(_registry.values())
__all__ = ['get_current', 'get_previous', 'list_entries', 'promote', 'register', 'retire_previous']

def previous_available(logical: str, *, config_path: Path | None=None) -> bool:
    """Return True if a previous secret ref is still within grace window.

    This allows callers (e.g., dual-signature verification flows) to decide whether to
    accept both previous and current values.
    """
    cfg = _load_rotation_config(config_path)
    grace_hours = float(cfg.get('grace_hours', 24))
    grace = timedelta(hours=grace_hours)
    entry = _registry.get(logical)
    if not entry or not entry.previous_ref:
        return False
    return not entry.grace_elapsed(grace)

def validate_grace(logical: str, *, config_path: Path | None=None, actor: str | None=None) -> bool:
    """Emit an audit event if previous ref has exceeded grace but not retired.

    Returns True if a violation (stale previous) is detected.
    """
    cfg = _load_rotation_config(config_path)
    auditing = bool(cfg.get('audit_events', True))
    grace_hours = float(cfg.get('grace_hours', 24))
    grace = timedelta(hours=grace_hours)
    entry = _registry.get(logical)
    if not entry or not entry.previous_ref:
        return False
    previous_started = entry.previous_activated_at or entry.activated_at
    if default_utc_now() - previous_started >= grace:
        _audit(auditing, actor, 'grace_violation', logical, previous_ref=entry.previous_ref)
        return True
    return False
__all__.extend(['previous_available', 'validate_grace'])

def verify_ref(logical: str, ref: str, *, actor: str | None=None, config_path: Path | None=None) -> bool:
    """Return True if ``ref`` is an accepted secret reference for ``logical``.

    Acceptance criteria:
    - Matches current_ref
    - Matches previous_ref and still within grace window

    Emits an audit event (verify_accept / verify_reject) when auditing enabled.
    """
    cfg = _load_rotation_config(config_path)
    auditing = bool(cfg.get('audit_events', True))
    grace_hours = float(cfg.get('grace_hours', 24))
    grace = timedelta(hours=grace_hours)
    entry = _registry.get(logical)
    if not entry:
        _audit(auditing, actor, 'verify_reject', logical, reason='no_entry', attempted_ref=ref)
        return False
    if ref == entry.current_ref:
        _audit(auditing, actor, 'verify_accept', logical, attempted_ref=ref, match='current')
        return True
    if ref == entry.previous_ref and entry.previous_ref:
        if not entry.grace_elapsed(grace):
            _audit(auditing, actor, 'verify_accept', logical, attempted_ref=ref, match='previous')
            return True
        _audit(auditing, actor, 'verify_reject', logical, reason='previous_expired', attempted_ref=ref)
        return False
    _audit(auditing, actor, 'verify_reject', logical, reason='no_match', attempted_ref=ref)
    return False
__all__.append('verify_ref')