"""Aggregating fact check tool matching existing test expectations.

The test suite monkeypatches internal backend search methods such as
``_search_duckduckgo`` and ``_search_serply`` and expects ``run`` to
return a mapping (dict-like) containing:

    * status: "success" | "error" (StepResult supplies this automatically)
    * evidence: list of {title, url, snippet}

Behavior requirements inferred from tests:
        * If a backend raises ``RequestException`` it is skipped silently and
            the tool still returns success with remaining evidence.
        * If the claim is empty we treat it as a skipped invocation using
            ``StepResult.skip`` so the pipeline records a "skipped" outcome while
            preserving the contract for downstream callers.

Instrumentation (Copilot migration spec):
    * tool_runs_total{tool="fact_check", outcome=success|error|skipped}
"""

from __future__ import annotations

import logging
import os
from platform.http.http_utils import resilient_get, resilient_post
from typing import TYPE_CHECKING

from requests import RequestException

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable
_logger = logging.getLogger(__name__)


class FactCheckTool:
    """Aggregate lightweight search / evidence backends for fact-checking claims.

    Performs comprehensive fact-checking by aggregating evidence from multiple
    search backends including DuckDuckGo, Serply, Exa AI, Perplexity, and Wolfram Alpha.
    Handles API failures gracefully and returns evidence from available sources.
    """

    def __init__(self) -> None:
        """Initialize the FactCheckTool and set up metrics."""
        self._metrics = get_metrics()

    def run(self, claim: str, tenant: str = "global", workspace: str = "global") -> StepResult:
        """Aggregate evidence across all enabled backends with comprehensive error handling.

        Iterates through configured backends (DuckDuckGo, Serply, Exa, Perplexity, Wolfram)
        and collects evidence items. If a backend fails (e.g., due to network issues or
        missing keys), it logs the failure and continues to the next.

        Args:
            claim: The factual claim to verify.
            tenant: Tenant identifier for isolation.
            workspace: Workspace identifier.

        Returns:
            StepResult: A result object containing:
                - claim: The original claim.
                - evidence: A list of dicts with 'title', 'url', and 'snippet'.
                - backends_used: List of backends that successfully returned data.
                - backends_failed: List of backends that failed.
                - evidence_count: The total count of evidence items found.
                Returns a 'skipped' result if the claim is empty.
                Returns a 'network_error' result if a non-RequestException occurs.
        """
        from ultimate_discord_intelligence_bot.step_result import ErrorContext

        context = ErrorContext(operation="fact_checking", component="FactCheckTool", tenant=tenant, workspace=workspace)
        if not claim or not claim.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="No claim provided", evidence=[], claim=claim, context=context)
        _logger.info(f"FactCheckTool: Checking claim: {claim[:100]}...")
        evidence: list[dict] = []
        successful_backends: list[str] = []
        failed_backends: list[str] = []
        backends: list[tuple[str, Callable[[str], list[dict]]]] = [
            ("duckduckgo", self._search_duckduckgo),
            ("serply", self._search_serply),
            ("exa", self._search_exa),
            ("perplexity", self._search_perplexity),
            ("wolfram", self._search_wolfram),
        ]
        for name, fn in backends:
            try:
                _logger.debug(f"FactCheckTool: Calling backend '{name}'...")
                results = fn(claim) or []
                if results:
                    successful_backends.append(name)
                    evidence.extend(results)
                    _logger.info(f"FactCheckTool: Backend '{name}' returned {len(results)} evidence items")
                else:
                    _logger.debug(f"FactCheckTool: Backend '{name}' returned no results (likely no API key or no data)")
            except RequestException as e:
                failed_backends.append(name)
                _logger.warning(
                    f"FactCheckTool: Backend '{name}' failed (RequestException): {e} - possibly rate limited or unavailable"
                )
                continue
            except Exception as e:
                failed_backends.append(name)
                _logger.error(f"FactCheckTool: Backend '{name}' encountered unexpected error: {e}")
                self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "error"}).inc()
                return StepResult.network_error(
                    error=f"Backend '{name}' failed: {e!s}", context=context, claim=claim, failed_backend=name
                )
        _logger.info(
            f"FactCheckTool: Completed - {len(evidence)} total evidence items from {len(successful_backends)} backends. Successful: {successful_backends}, Failed: {failed_backends or 'None'}"
        )
        self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "success"}).inc()
        return StepResult.ok(
            claim=claim,
            evidence=evidence,
            backends_used=successful_backends,
            backends_failed=failed_backends,
            evidence_count=len(evidence),
        )

    def _search_duckduckgo(self, query: str) -> list[dict]:
        """Search DuckDuckGo for evidence (no API key required).

        Args:
            query: The search query string.

        Returns:
            list[dict]: A list of evidence items (title, url, snippet).
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
            response = resilient_get(url, params=params, timeout_seconds=10)
            if not response or response.status_code != 200:
                return []
            data = response.json()
            evidence = []
            if data.get("Abstract"):
                evidence.append(
                    {
                        "title": data.get("Heading", "DuckDuckGo Answer"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                    }
                )
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    evidence.append(
                        {
                            "title": topic.get("Text", "")[:100],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                        }
                    )
            return evidence
        except Exception:
            raise RequestException("DuckDuckGo search failed") from None

    def _search_serply(self, query: str) -> list[dict]:
        """Search via Serply API (requires API key).

        Args:
            query: The search query string.

        Returns:
            list[dict]: A list of evidence items from organic search results.
        """
        api_key = os.getenv("SERPLY_API_KEY")
        if not api_key:
            return []
        try:
            url = "https://api.serply.io/v1/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            params = {"q": query, "num": 5}
            response = resilient_get(url, headers=headers, params=params, timeout_seconds=15)
            if not response or response.status_code != 200:
                return []
            data = response.json()
            evidence = []
            for result in data.get("organic_results", [])[:5]:
                evidence.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                    }
                )
            return evidence
        except Exception:
            raise RequestException("Serply search failed") from None

    def _search_exa(self, query: str) -> list[dict]:
        """Search via Exa AI (requires API key).

        Args:
            query: The search query string.

        Returns:
            list[dict]: A list of evidence items with text snippets.
        """
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return []
        try:
            url = "https://api.exa.ai/search"
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            payload = {"query": query, "numResults": 5, "useAutoprompt": True}
            response = resilient_post(url, json_payload=payload, headers=headers, timeout_seconds=15)
            if not response or response.status_code != 200:
                return []
            data = response.json()
            evidence = []
            for result in data.get("results", [])[:5]:
                evidence.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("text", "")[:300],
                    }
                )
            return evidence
        except Exception:
            raise RequestException("Exa search failed") from None

    def _search_perplexity(self, query: str) -> list[dict]:
        """Search via Perplexity API (requires API key).

        Uses Perplexity's chat completion model to find evidence and citations.

        Args:
            query: The search query/claim.

        Returns:
            list[dict]: A list of evidence items, including citations.
        """
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return []
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": f"Find evidence for or against this claim: {query}"}],
                "max_tokens": 500,
                "temperature": 0.2,
                "return_citations": True,
            }
            response = resilient_post(url, json_payload=payload, headers=headers, timeout_seconds=20)
            if not response or response.status_code != 200:
                return []
            data = response.json()
            evidence = []
            if data.get("choices"):
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                citations = data.get("citations", [])
                if citations:
                    for citation in citations[:5]:
                        evidence.append({"title": citation, "url": citation, "snippet": content[:300]})
                else:
                    evidence.append({"title": "Perplexity AI Response", "url": "", "snippet": content[:300]})
            return evidence
        except Exception:
            raise RequestException("Perplexity search failed") from None

    def _search_wolfram(self, query: str) -> list[dict]:
        """Search via Wolfram Alpha API (requires App ID).

        Useful for fact-checking mathematical or scientific claims.

        Args:
            query: The search query.

        Returns:
            list[dict]: A list of evidence items extracted from Wolfram's pods.
        """
        app_id = os.getenv("WOLFRAM_ALPHA_APP_ID")
        if not app_id:
            return []
        try:
            url = "http://api.wolframalpha.com/v2/query"
            params = {"input": query, "format": "plaintext", "output": "json", "appid": app_id}
            response = resilient_get(url, params=params, timeout_seconds=15)
            if not response or response.status_code != 200:
                return []
            data = response.json()
            evidence = []
            pods = data.get("queryresult", {}).get("pods", [])
            for pod in pods[:3]:
                title = pod.get("title", "")
                subpods = pod.get("subpods", [])
                for subpod in subpods[:1]:
                    text = subpod.get("plaintext", "")
                    if text:
                        evidence.append(
                            {
                                "title": title,
                                "url": f"https://www.wolframalpha.com/input/?i={query.replace(' ', '+')}",
                                "snippet": text[:300],
                            }
                        )
            return evidence
        except Exception:
            raise RequestException("Wolfram Alpha search failed") from None
