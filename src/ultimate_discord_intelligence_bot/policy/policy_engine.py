"""Policy engine module for content filtering and privacy controls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Use relative path to avoid circular imports
POLICY_PATH = Path(__file__).parent.parent.parent.parent / "config" / "policy.yaml"
TENANT_DIR = Path(__file__).parent.parent.parent.parent / "tenants"


@dataclass
class Decision:
    """Policy decision result."""

    decision: str
    reasons: list[str]


@dataclass
class Policy:
    """Policy configuration."""

    allowed_sources: dict[str, list[str] | None]
    forbidden_types: list[str]
    pii_types: dict[str, str]
    masks: dict[str, str]
    storage: dict[str, Any]
    consent: dict[str, Any]
    per_command: dict[str, Any]


def load_policy(tenant: str | None = None) -> Policy:
    """Load base policy and optional per-tenant overrides."""
    if POLICY_PATH.exists():
        with POLICY_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        # Default policy if file doesn't exist
        data = {
            "allowed_sources": {},
            "forbidden_types": [],
            "pii_types": {},
            "masks": {},
            "storage": {},
            "consent": {},
            "per_command": {},
        }

    if tenant:
        override = TENANT_DIR / tenant / "policy_overrides.yaml"
        if override.exists():
            with override.open("r", encoding="utf-8") as f:
                ov = yaml.safe_load(f) or {}
            for k, v in ov.items():
                if isinstance(v, dict) and k in data:
                    data[k].update(v)
                else:
                    data[k] = v

    return Policy(**data)


def check_source(source_meta: dict[str, Any], policy: Policy) -> Decision:
    """Evaluate a content source against the policy.

    Behavior:
        - If the source platform/type is absent -> block (unknown source).
        - If the source platform key not present in policy.allowed_sources -> block.
        - If the allowed list is ``None`` -> block (explicitly disabled source).
        - If the allowed list is non-empty and the provided id not in list -> block.
        - Otherwise allow.
    """
    raw_src = source_meta.get("source_platform") or source_meta.get("type")
    if raw_src is None:
        return Decision("block", ["unknown source"])
    src = str(raw_src)
    allowed_ids = policy.allowed_sources.get(src)
    if allowed_ids is None:
        return Decision("block", ["source not allowed"])
    src_id = source_meta.get("id")
    if allowed_ids and src_id not in allowed_ids:
        return Decision("block", ["source not allowed"])
    return Decision("allow", [])


def check_payload(payload: dict[str, Any] | str | bytes, policy: Policy) -> Decision:
    """Evaluate a payload against the policy.

    For now only inspects an optional ``media_type`` field when a mapping is
    provided; future enhancements may parse text for forbidden indicators.
    """
    media_type = None
    if isinstance(payload, dict):
        media_type = payload.get("media_type")
    # Simple forbidden media type enforcement
    if media_type and media_type in getattr(policy, "forbidden_types", []):
        return Decision("block", ["forbidden media type"])
    return Decision("allow", [])


def check_use_case(use_case: str, policy: Policy) -> Decision:
    """Evaluate a use case against the policy.

    If the use case is absent from ``per_command`` treat as blocked. Honor a
    ``max_tokens`` field when present (the caller must supply token count via
    a context layer – omitted here for lightweight parity with top-level engine).
    """
    rules = policy.per_command.get(use_case) if hasattr(policy, "per_command") else None
    if not rules:
        return Decision("block", ["unknown use case"])
    return Decision("allow", [])


__all__ = [
    "Decision",
    "Policy",
    "load_policy",
    "check_source",
    "check_payload",
    "check_use_case",
]
