from __future__ import annotations

"""Lightweight policy loader and evaluator.

This module loads a YAML policy file and exposes helper functions to check
sources, payloads, and use cases. The policy is intentionally minimal but
provides a foundation that can be extended with richer rules as the project
grows.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


POLICY_PATH = Path(__file__).with_name("policy.yaml")


@dataclass
class Policy:
    allowed_sources: Dict[str, list]
    forbidden_data_types: list
    redaction_rules: Dict[str, str]
    storage: Dict[str, Any]
    consent_flags: Dict[str, Any]
    usage_rules: Dict[str, Any]


def load_policy(path: Path | None = None) -> Policy:
    """Load the policy YAML into a :class:`Policy` instance."""
    policy_path = path or POLICY_PATH
    with policy_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Policy(**data)


@dataclass
class PolicyDecision:
    decision: str
    reason: str | None = None


def check_source(source_meta: Dict[str, Any], policy: Policy) -> PolicyDecision:
    """Return whether ``source_meta`` is allowed under ``policy``.

    ``source_meta`` expects ``{"type": str, "id": str}``. If the source is not
    present in the policy's ``allowed_sources`` map the decision is ``block``.
    """
    src_type = source_meta.get("type")
    src_id = source_meta.get("id")
    allowed = set(policy.allowed_sources.get(f"{src_type}s", []))
    if src_id and src_id in allowed:
        return PolicyDecision("allow")
    return PolicyDecision("block", reason="source not allowed")


def check_payload(text: str, policy: Policy) -> PolicyDecision:
    """Naive payload check; blocks if obvious forbidden phrases appear."""
    lowered = text.lower()
    if any(ftype in lowered for ftype in policy.forbidden_data_types):
        return PolicyDecision("allow_with_redactions")
    return PolicyDecision("allow")


def check_use_case(use_case: str, policy: Policy) -> PolicyDecision:
    """Validate a command/use-case against ``policy`` usage rules."""
    if use_case not in policy.usage_rules:
        return PolicyDecision("block", reason="unknown use case")
    return PolicyDecision("allow")

