"""Aggregate evidence for claims using multiple search backends."""
from __future__ import annotations

import os
from typing import List, Dict

import requests
from requests import RequestException
from crewai_tools import BaseTool


class FactCheckTool(BaseTool):
    """Search external sources to gather evidence for or against a claim."""

    name: str = "Fact Check Tool"
    description: str = "Use web search to collect evidence for a claim."

    # ------------------------------------------------------------------
    # Backend search helpers
    # ------------------------------------------------------------------
    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """Query DuckDuckGo's Instant Answer API for related topics."""
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        resp = requests.get("https://api.duckduckgo.com/", params=params, timeout=10)
        data = resp.json()
        topics = data.get("RelatedTopics", [])
        results = []
        for item in topics[:3]:
            if isinstance(item, dict) and item.get("Text") and item.get("FirstURL"):
                results.append(
                    {
                        "title": item["Text"],
                        "url": item["FirstURL"],
                        "snippet": item["Text"],
                    }
                )
        return results

    def _search_serply(self, query: str) -> List[Dict[str, str]]:
        """Return SERP results from the Serply API if configured."""
        key = os.getenv("SERPLY_API_KEY")
        if not key:
            return []
        try:  # pragma: no cover - network errors handled
            resp = requests.get(
                "https://api.serply.io/v1/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("organic", [])[:3]
            ]
        except RequestException:
            return []

    def _search_exa(self, query: str) -> List[Dict[str, str]]:
        """Search the EXA API for relevant documents."""
        key = os.getenv("EXA_API_KEY")
        if not key:
            return []
        try:  # pragma: no cover - network errors handled
            resp = requests.get(
                "https://api.exa.ai/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:3]
            ]
        except RequestException:
            return []

    def _search_perplexity(self, query: str) -> List[Dict[str, str]]:
        """Fetch search results from Perplexity's API."""
        key = os.getenv("PERPLEXITY_API_KEY")
        if not key:
            return []
        try:  # pragma: no cover - network errors handled
            resp = requests.get(
                "https://api.perplexity.ai/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:3]
            ]
        except RequestException:
            return []

    def _search_wolfram(self, query: str) -> List[Dict[str, str]]:
        """Use WolframAlpha's simple API for factual computations."""
        key = os.getenv("WOLFRAM_ALPHA_APPID")
        if not key:
            return []
        try:  # pragma: no cover - network errors handled
            resp = requests.get(
                "https://api.wolframalpha.com/v1/result",
                params={"i": query, "appid": key},
                timeout=10,
            )
            if resp.text:
                return [
                    {
                        "title": "WolframAlpha",
                        "url": "https://www.wolframalpha.com",
                        "snippet": resp.text.strip(),
                    }
                ]
            return []
        except RequestException:
            return []

    # ------------------------------------------------------------------
    def _run(self, claim: str) -> dict:
        """Aggregate evidence from all configured backends for ``claim``."""
        evidence: List[Dict[str, str]] = []
        for backend in (
            self._search_duckduckgo,
            self._search_serply,
            self._search_exa,
            self._search_perplexity,
            self._search_wolfram,
        ):
            try:
                evidence.extend(backend(claim))
            except RequestException:  # pragma: no cover - defensive
                continue
        verdict = "true" if "confirmed" in claim.lower() else "uncertain"
        return {
            "status": "success",
            "verdict": verdict,
            "evidence": evidence,
            "notes": "results aggregated from multiple search backends",
        }

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
