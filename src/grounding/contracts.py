from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .citation_utils import append_numeric_citations
from .schema import AnswerContract, Evidence


"""Builders and validators for :class:`AnswerContract`."""

CONFIG_PATH = Path("config/grounding.yaml")
TENANT_DIR = Path("tenants")


class GroundingError(RuntimeError):
    """Raised when an answer fails grounding requirements."""


@dataclass
class GroundingConfig:
    defaults: dict[str, object]
    commands: dict[str, dict[str, object]]


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
    raw_min = rules.get("min_citations", 1)
    if isinstance(raw_min, int | str):
        try:
            min_cit = int(raw_min)
        except Exception:
            min_cit = 1
    else:
        min_cit = 1
    if len(evidence) < min_cit:
        raise GroundingError(f"requires >= {min_cit} citations")
    if rules.get("require_timestamped"):
        for ev in evidence:
            loc = ev.locator or {}
            if not any(k in loc for k in ("t_start", "start")):
                raise GroundingError("timestamp required")
    # Ensure standardized numeric citation tail formatting
    formatted_answer = append_numeric_citations(answer, evidence)
    return AnswerContract(answer_text=formatted_answer, citations=evidence)


__all__ = ["GroundingConfig", "GroundingError", "build_contract", "load_config"]
