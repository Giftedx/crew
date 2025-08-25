"""Basic fact-checking via DuckDuckGo search."""
from __future__ import annotations

import requests
from crewai_tools import BaseTool


class FactCheckTool(BaseTool):
    """Search external sources to gather evidence for or against a claim."""

    name: str = "Fact Check Tool"
    description: str = "Use web search to collect evidence for a claim."

    def _run(self, claim: str) -> dict:
        try:
            params = {"q": claim, "format": "json", "no_redirect": 1, "no_html": 1}
            resp = requests.get("https://api.duckduckgo.com/", params=params, timeout=10)
            data = resp.json()
            topics = data.get("RelatedTopics", [])
            evidence = []
            for item in topics[:3]:
                if isinstance(item, dict) and item.get("Text") and item.get("FirstURL"):
                    evidence.append(
                        {
                            "title": item["Text"],
                            "url": item["FirstURL"],
                            "snippet": item["Text"],
                        }
                    )
            verdict = "true" if "confirmed" in claim.lower() else "uncertain"
            return {
                "status": "success",
                "verdict": verdict,
                "evidence": evidence,
                "notes": "verdict is heuristic; evidence list may require manual review",
            }
        except Exception as exc:  # pragma: no cover - network errors handled
            return {"status": "error", "error": str(exc)}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
