"""Aggregating fact check tool matching existing test expectations.

The test suite monkeypatches internal backend search methods such as
``_search_duckduckgo`` and ``_search_serply`` and expects ``run`` to
return a mapping (dict‑like) containing:

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

import logging
import os
from collections.abc import Callable

from requests import RequestException  # http-compliance: allow-direct-requests (exception type import only)

from core.http_utils import resilient_get, resilient_post
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

_logger = logging.getLogger(__name__)


class FactCheckTool:
    """Aggregate lightweight search / evidence backends.

    The concrete backend methods intentionally return lists of evidence
    dictionaries and default to empty lists so that tests can monkeypatch
    them without needing network access.
    """

    def __init__(self) -> None:
        self._metrics = get_metrics()

    # --- Public API -----------------------------------------------------
    def run(self, claim: str) -> StepResult:
        """Aggregate evidence across all enabled backends.

        Returns a ``StepResult`` whose mapping interface satisfies legacy
        test expectations (``result["status"]`` & ``result["evidence"]``).
        """
        if not claim:
            self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="No claim provided", evidence=[], claim=claim)

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
                # Backend unavailable – skip silently per tests expecting overall success
                failed_backends.append(name)
                _logger.warning(
                    f"FactCheckTool: Backend '{name}' failed (RequestException): {e} - possibly rate limited or unavailable"
                )
                continue
            except Exception as e:  # pragma: no cover - defensive guard
                # Unexpected error – treat whole tool as failed for visibility
                failed_backends.append(name)
                _logger.error(f"FactCheckTool: Backend '{name}' encountered unexpected error: {e}")
                self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "error"}).inc()
                return StepResult.fail(error=str(e), claim=claim)

        # Always success even if evidence list empty (tests assert success with empty list)
        _logger.info(
            f"FactCheckTool: Completed - {len(evidence)} total evidence items from {len(successful_backends)} backends. "
            f"Successful: {successful_backends}, Failed: {failed_backends or 'None'}"
        )
        self._metrics.counter("tool_runs_total", labels={"tool": "fact_check", "outcome": "success"}).inc()
        return StepResult.ok(
            claim=claim,
            evidence=evidence,
            backends_used=successful_backends,
            backends_failed=failed_backends,
            evidence_count=len(evidence),
        )

    # --- Backend implementations (production-ready) --------------------
    def _search_duckduckgo(self, query: str) -> list[dict]:
        """Search DuckDuckGo for evidence (no API key required)."""
        try:
            # DuckDuckGo Instant Answer API - free, no auth required
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}

            response = resilient_get(url, params=params, timeout_seconds=10)
            if not response or response.status_code != 200:
                return []

            data = response.json()
            evidence = []

            # Extract abstract (primary answer)
            if data.get("Abstract"):
                evidence.append(
                    {
                        "title": data.get("Heading", "DuckDuckGo Answer"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                    }
                )

            # Extract related topics
            for topic in data.get("RelatedTopics", [])[:3]:  # Limit to 3
                if isinstance(topic, dict) and topic.get("Text"):
                    evidence.append(
                        {
                            "title": topic.get("Text", "")[:100],  # Use first 100 chars as title
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                        }
                    )

            return evidence
        except Exception:  # pragma: no cover - network errors should be caught as RequestException
            raise RequestException("DuckDuckGo search failed")

    def _search_serply(self, query: str) -> list[dict]:
        """Search via Serply API (requires API key)."""
        api_key = os.getenv("SERPLY_API_KEY")
        if not api_key:
            return []  # Skip if no API key configured

        try:
            url = "https://api.serply.io/v1/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            params = {"q": query, "num": 5}  # Limit to 5 results

            response = resilient_get(url, headers=headers, params=params, timeout_seconds=15)
            if not response or response.status_code != 200:
                return []

            data = response.json()
            evidence = []

            # Extract organic results
            for result in data.get("organic_results", [])[:5]:
                evidence.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                    }
                )

            return evidence
        except Exception:  # pragma: no cover - network errors
            raise RequestException("Serply search failed")

    def _search_exa(self, query: str) -> list[dict]:
        """Search via Exa AI (requires API key)."""
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

            # Extract results
            for result in data.get("results", [])[:5]:
                evidence.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("text", "")[:300],  # Limit snippet length
                    }
                )

            return evidence
        except Exception:  # pragma: no cover - network errors
            raise RequestException("Exa search failed")

    def _search_perplexity(self, query: str) -> list[dict]:
        """Search via Perplexity API (requires API key)."""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return []

        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",  # Fast, affordable online model
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

            # Extract response and citations
            if data.get("choices"):
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")

                # Extract citations if available
                citations = data.get("citations", [])
                if citations:
                    for citation in citations[:5]:  # Limit to 5
                        evidence.append({"title": citation, "url": citation, "snippet": content[:300]})
                else:
                    # Fallback: use the response itself
                    evidence.append({"title": "Perplexity AI Response", "url": "", "snippet": content[:300]})

            return evidence
        except Exception:  # pragma: no cover - network errors
            raise RequestException("Perplexity search failed")

    def _search_wolfram(self, query: str) -> list[dict]:
        """Search via Wolfram Alpha API (requires App ID)."""
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

            # Extract pods (answer units)
            pods = data.get("queryresult", {}).get("pods", [])
            for pod in pods[:3]:  # Limit to 3 pods
                title = pod.get("title", "")
                subpods = pod.get("subpods", [])
                for subpod in subpods[:1]:  # Take first subpod only
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
        except Exception:  # pragma: no cover - network errors
            raise RequestException("Wolfram Alpha search failed")
