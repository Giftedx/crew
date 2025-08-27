from __future__ import annotations

"""Lightweight models describing grounded answers."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    """Evidence backing part of an answer."""

    source_type: str
    locator: Dict[str, Any] = field(default_factory=dict)
    quote: Optional[str] = None
    confidence: float = 1.0


@dataclass
class AnswerContract:
    """Contract describing a grounded answer."""

    answer_text: str
    citations: List[Evidence]
    coverage_score: float = 1.0
    confidence_score: float = 1.0
    disclaimers: List[str] = field(default_factory=list)
    reasoning_brief: Optional[str] = None
    provenance_ids: List[str] = field(default_factory=list)
    policy_notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.citations:
            raise ValueError("at least one citation required")


__all__ = ["Evidence", "AnswerContract"]
