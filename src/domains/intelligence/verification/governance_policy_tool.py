"""Lightweight governance and content safety policy checker.

This tool performs a fast, dependency-free content safety triage on text
inputs (e.g., transcripts) to support governance enforcement in the pipeline.

It is intentionally heuristic and conservative: it flags obvious risk
categories for review and allows callers to gate downstream processing via
feature flags (e.g., red-line guards).

Returns StepResult with fields:
- categories: list[str] detected categories (e.g., violence, sexual, hate)
- confidence: float in [0,1]
- action: one of {pass, review, block}
- details: dict with matched_terms and counts
"""

from __future__ import annotations
from typing import Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.verification_base import VerificationBaseTool


class GovernancePolicyTool(VerificationBaseTool):
    name = "GovernancePolicyTool"
    description = "Heuristic content safety triage for transcripts and text bodies. Detects sensitive categories and recommends pass/review/block."

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._category_terms: dict[str, tuple[str, ...]] = {
            "violence": ("violence", "violent", "weapon", "attack", "threat"),
            "sexual": ("nsfw", "explicit", "adult"),
            "hate": ("hate speech", "racist", "discrimination"),
            "self_harm": ("suicide", "self-harm", "self harm"),
            "drugs": ("drugs", "narcotic", "illicit"),
            "politics": ("political", "election", "campaign", "policy"),
        }

    def run(self, input_data: Any) -> StepResult:
        text = input_data if isinstance(input_data, str) else (input_data or {}).get("transcript", "")
        return self._run(text, tenant="global", workspace="global")

    def _run(self, content: str, tenant: str, workspace: str, **_: Any) -> StepResult:
        if not isinstance(content, str) or not content.strip():
            return StepResult.validation_error("Empty content for governance check")
        lowered = content.lower()
        categories: list[str] = []
        matched_terms: dict[str, list[str]] = {}
        total_hits = 0
        for category, terms in self._category_terms.items():
            hits = [t for t in terms if t in lowered]
            if hits:
                categories.append(category)
                matched_terms[category] = hits
                total_hits += len(hits)
        distinct = len(categories)
        confidence = min(0.99, 0.5 + 0.2 * max(0, distinct)) if distinct else 0.5
        action = "pass"
        if categories:
            action = "review"
            if any((cat in {"violence", "hate", "self_harm"} for cat in categories)):
                action = "block"
        details = {"matched_terms": matched_terms, "total_hits": total_hits, "tenant": tenant, "workspace": workspace}
        return StepResult.ok(categories=categories, confidence=confidence, action=action, details=details)


__all__ = ["GovernancePolicyTool"]
