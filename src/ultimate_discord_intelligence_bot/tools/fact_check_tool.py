"""Aggregate evidence for claims using multiple search backends."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar, cast

from requests import RequestException

from core.http_utils import (  # noqa: I001 - grouped explicitly: stdlib, third-party, internal
    REQUEST_TIMEOUT_SECONDS,
    is_retry_enabled,
    resilient_get,
    retrying_get,
)

from ._base import BaseTool


class _HTTPGetFn(Protocol):
    """Structural protocol for our minimal GET helpers.

    Using Mapping + optional kwargs for forward compatibility with http_utils
    which may accept additional keyword-only parameters (e.g. stream, max_attempts).
    """

    def __call__(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = ...,
        headers: Mapping[str, str] | None = ...,
        timeout_seconds: int = ...,
        **_: Any,
    ) -> Any: ...  # Response-like object

def _select_getter() -> _HTTPGetFn:
    """Return appropriate GET helper with a narrow structural cast.

    retrying_get / resilient_get have broader signatures; we only rely on a
    small subset. Casting keeps call sites typed without over-constraining
    http_utils implementation details.
    """
    return cast(_HTTPGetFn, retrying_get if is_retry_enabled() else resilient_get)

logger = logging.getLogger(__name__)


P = ParamSpec("P")
R = TypeVar("R")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for retrying failed operations with typing preserved."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(max_retries):  # noqa: PERF203 - deliberate retry loop with exception control flow
                try:  # noqa: PERF203 - controlled exception-based retry
                    return func(*args, **kwargs)
                except Exception as e:  # noqa: PERF203  # pragma: no cover - defensive; retry boundary
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
            return cast(R, [])  # Unreachable; cast for type checker

        return wrapper

    return decorator


EVIDENCE_WELL_SUPPORTED_THRESHOLD = 3
EVIDENCE_MODERATELY_SUPPORTED_THRESHOLD = 2
BACKEND_RESULT_SLICE = 3


class FactCheckTool(BaseTool[dict[str, Any]]):
    """Search external sources to gather evidence for or against a claim."""

    name: str = "Fact Check Tool"
    description: str = "Use web search to collect evidence for a claim."
    model_config = {"extra": "allow"}

    # ------------------------------------------------------------------
    # Backend search helpers with enhanced error handling
    # ------------------------------------------------------------------
    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_duckduckgo(self, query: str) -> list[dict[str, str]]:
        """Query DuckDuckGo's Instant Answer API for related topics."""
        if not query or not isinstance(query, str):
            return []

        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        url = "https://api.duckduckgo.com/"
        getter = _select_getter()
        resp = getter(url, params=params, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()

        data = resp.json()
        topics = data.get("RelatedTopics", [])
        results: list[dict[str, str]] = []

        results.extend(
            {
                "title": item["Text"],
                "url": item["FirstURL"],
                "snippet": item["Text"],
            }
            for item in topics[:BACKEND_RESULT_SLICE]
            if isinstance(item, dict) and item.get("Text") and item.get("FirstURL")
        )
        return results

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_serply(self, query: str) -> list[dict[str, str]]:
        """Return SERP results from the Serply API if configured."""
        key = os.getenv("SERPLY_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []

        try:
            url = "https://api.serply.io/v1/search"
            params = {"q": query}
            headers = {"Authorization": f"Bearer {key}"}
            getter = _select_getter()
            resp = getter(
                url,
                params=params,
                headers=headers,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()

            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("organic", [])[:BACKEND_RESULT_SLICE]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Serply API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_exa(self, query: str) -> list[dict[str, str]]:
        """Search the EXA API for relevant documents."""
        key = os.getenv("EXA_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []

        try:
            url = "https://api.exa.ai/search"
            params = {"q": query}
            headers = {"Authorization": f"Bearer {key}"}
            getter = _select_getter()
            resp = getter(
                url,
                params=params,
                headers=headers,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()

            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:BACKEND_RESULT_SLICE]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Exa API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_perplexity(self, query: str) -> list[dict[str, str]]:
        """Fetch search results from Perplexity's API."""
        key = os.getenv("PERPLEXITY_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []

        try:
            url = "https://api.perplexity.ai/search"
            params = {"q": query}
            headers = {"Authorization": f"Bearer {key}"}
            getter = _select_getter()
            resp = getter(
                url,
                params=params,
                headers=headers,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()

            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:BACKEND_RESULT_SLICE]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Perplexity API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_wolfram(self, query: str) -> list[dict[str, str]]:
        """Use WolframAlpha's simple API for factual computations."""
        key = os.getenv("WOLFRAM_ALPHA_APPID")
        if not key or not query or not isinstance(query, str):
            return []

        try:
            url = "https://api.wolframalpha.com/v1/result"
            params = {"i": query, "appid": key}
            getter = _select_getter()
            resp = getter(
                url,
                params=params,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()

            if resp.text and resp.text.strip():
                return [
                    {
                        "title": "WolframAlpha",
                        "url": "https://www.wolframalpha.com",
                        "snippet": resp.text.strip(),
                    }
                ]
            return []
        except RequestException as e:
            logger.warning(f"WolframAlpha API error: {e}")
            return []

    def _analyze_evidence(self, evidence: list[dict[str, str]]) -> str:
        """Analyze evidence quality and determine verdict."""
        if not evidence:
            return "insufficient_evidence"

        # Simple heuristic based on evidence count and sources
        if len(evidence) >= EVIDENCE_WELL_SUPPORTED_THRESHOLD:
            return "well_supported"
        elif len(evidence) >= EVIDENCE_MODERATELY_SUPPORTED_THRESHOLD:
            return "moderately_supported"
        else:
            return "limited_evidence"

    # ------------------------------------------------------------------
    def _run(self, claim: str) -> dict[str, Any]:  # noqa: PLR0911 - multiple early returns for validation errors keep control flow flat
        """Enhanced fact checking with comprehensive error handling."""
        start_time = time.time()

        # Input validation
        if not claim or not isinstance(claim, str):  # fast validation path
            return {  # early return simplifies downstream logic
                "status": "error",
                "error": "Claim is required and must be a non-empty string",
                "claim": claim,
                "timestamp": time.time(),
            }

        evidence: list[dict[str, str]] = []
        failed_backends = []

        backends = [
            ("duckduckgo", self._search_duckduckgo),
            ("serply", self._search_serply),
            ("exa", self._search_exa),
            ("perplexity", self._search_perplexity),
            ("wolfram", self._search_wolfram),
        ]

        logger.info(f"Starting fact check for claim: {claim[:100]}...")

        for name, backend_func in backends:  # noqa: PERF203 - network IO dominates; per-iteration try/except keeps failures isolated without measurable overhead
            try:  # noqa: PERF203 - intentional fine-grained error isolation per backend
                results = backend_func(claim)
                evidence.extend(results)
                logger.debug(f"Backend {name} returned {len(results)} results")
            except Exception as e:  # noqa: PERF203 - intentional isolation of failures
                error_msg = str(e)
                failed_backends.append({"backend": name, "error": error_msg})
                logger.error(f"Backend {name} failed: {error_msg}")

        # Determine verdict based on evidence quality
        verdict = self._analyze_evidence(evidence)
        processing_time = time.time() - start_time

        # Tests expect status "success" even when evidence list is empty but process completed
        result = {
            "status": "success",
            "verdict": verdict,
            "evidence": evidence,
            "evidence_count": len(evidence),
            "failed_backends": failed_backends,
            "claim": claim,
            "processing_time": processing_time,
            "timestamp": time.time(),
        }

        logger.info(
            f"Fact check completed in {processing_time:.2f}s with {len(evidence)} evidence items"
        )
        return result

    def run(self, *args, **kwargs) -> dict[str, Any]:
        """Public wrapper with type safety."""
        return self._run(*args, **kwargs)
