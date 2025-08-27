from __future__ import annotations

"""Config-driven policy engine for privacy and usage rules."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

POLICY_PATH = Path("config/policy.yaml")
TENANT_DIR = Path("tenants")


@dataclass
class Decision:
    decision: str
    reasons: list[str]


@dataclass
class Policy:
    allowed_sources: Dict[str, list]
    forbidden_types: list
    pii_types: Dict[str, str]
    masks: Dict[str, str]
    storage: Dict[str, Any]
    consent: Dict[str, Any]
    per_command: Dict[str, Any]


def load_policy(tenant: Optional[str] = None) -> Policy:
    """Load base policy and optional per-tenant overrides."""
    with POLICY_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if tenant:
        override = TENANT_DIR / tenant / "policy_overrides.yaml"
        if override.exists():
            with override.open("r", encoding="utf-8") as f:
                ov = yaml.safe_load(f)
            for k, v in ov.items():
                if isinstance(v, dict) and k in data:
                    data[k].update(v)
                else:
                    data[k] = v
    return Policy(**data)


def check_source(source_meta: Dict[str, Any], policy: Policy) -> Decision:
    """Evaluate a content source against the policy."""
    src = source_meta.get("source_platform") or source_meta.get("type")
    allowed_ids = policy.allowed_sources.get(src)
    if allowed_ids is None:
        return Decision("block", ["source not allowed"])
    src_id = source_meta.get("id")
    if allowed_ids and src_id not in allowed_ids:
        return Decision("block", ["source not allowed"])
    return Decision("allow", [])


def check_payload(payload: str | bytes, context: Dict[str, Any], policy: Policy) -> Decision:
    """Check raw payload (text or bytes) prior to storage or display."""
    reasons: list[str] = []
    media_type = context.get("media_type")
    if media_type in policy.forbidden_types:
        reasons.append("forbidden media type")
    return Decision("allow" if not reasons else "block", reasons)


def check_use_case(use_case: str, context: Dict[str, Any], policy: Policy) -> Decision:
    """Check a command/use-case against policy limits."""
    rules = policy.per_command.get(use_case)
    if not rules:
        return Decision("block", ["unknown use case"])
    max_tokens = rules.get("max_tokens")
    if max_tokens is not None and context.get("tokens", 0) > max_tokens:
        return Decision("block", ["exceeds max_tokens"])
    return Decision("allow", [])


__all__ = [
    "Decision",
    "Policy",
    "load_policy",
    "check_source",
    "check_payload",
    "check_use_case",
]
