"""Simple content moderation utilities."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List
import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


@dataclass
class ModerationResult:
    action: str
    text: str


class Moderation:
    """Rule-based moderation checker using banned terms."""

    def __init__(
        self,
        banned_terms: List[str] | None = None,
        action: str | None = None,
        config_path: Path | None = None,
    ) -> None:
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        if banned_terms is None or action is None:
            data = self._load()
            banned_terms = banned_terms or data.get("banned_terms", [])
            action = action or data.get("action", "block")
        self.banned_terms = [t.lower() for t in banned_terms]
        self.action = action

    def _load(self) -> dict:
        if not self._config_path.exists():
            return {}
        data = yaml.safe_load(self._config_path.read_text()) or {}
        return data.get("moderation", {})

    def check(self, text: str) -> ModerationResult:
        lowered = text.lower()
        found = False
        cleaned = text
        for term in self.banned_terms:
            if term in lowered:
                found = True
                if self.action == "redact":
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    cleaned = pattern.sub("[redacted]", cleaned)
        if not found:
            return ModerationResult("allow", text)
        if self.action == "redact":
            return ModerationResult("redact", cleaned)
        return ModerationResult("block", text)
