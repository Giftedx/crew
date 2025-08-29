from __future__ import annotations

"""Builders and validators for :class:`AnswerContract`."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from .schema import AnswerContract, Evidence

CONFIG_PATH = Path("config/grounding.yaml")
TENANT_DIR = Path("tenants")


class GroundingError(RuntimeError):
    """Raised when an answer fails grounding requirements."""


@dataclass
class GroundingConfig:
    defaults: dict
    commands: dict


def load_config(tenant: str | None = None) -> GroundingConfig:
    """Load base config and optional per-tenant overrides."""

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if tenant:
        override = TENANT_DIR / tenant / "grounding_overrides.yaml"
        if override.exists():
            with override.open("r", encoding="utf-8") as f:
                ov = yaml.safe_load(f) or {}
            for k, v in ov.get("commands", {}).items():
                data.setdefault("commands", {}).setdefault(k, {}).update(v)
    return GroundingConfig(defaults=data.get("defaults", {}), commands=data.get("commands", {}))


def build_contract(
    answer: str, evidence: list[Evidence], *, use_case: str, tenant: str | None = None
) -> AnswerContract:
    """Create and validate an :class:`AnswerContract` for ``answer``."""

    cfg = load_config(tenant)
    rules = cfg.commands.get(use_case, cfg.defaults)
    min_cit = int(rules.get("min_citations", 1))
    if len(evidence) < min_cit:
        raise GroundingError(f"requires >= {min_cit} citations")
    if rules.get("require_timestamped"):
        for ev in evidence:
            loc = ev.locator or {}
            if not any(k in loc for k in ("t_start", "start")):
                raise GroundingError("timestamp required")
    return AnswerContract(answer_text=answer, citations=evidence)


__all__ = ["load_config", "GroundingError", "build_contract", "GroundingConfig"]
