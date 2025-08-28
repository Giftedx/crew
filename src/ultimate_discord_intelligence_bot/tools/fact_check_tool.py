"""Aggregate evidence for claims using multiple search backends."""
from __future__ import annotations

import os
import time
import logging
from functools import wraps
from typing import List, Dict, Any

import requests
from requests import RequestException
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return []
        return wrapper
    return decorator

class FactCheckTool(BaseTool):
    """Search external sources to gather evidence for or against a claim."""

    name: str = "Fact Check Tool"
    description: str = "Use web search to collect evidence for a claim."

    # ------------------------------------------------------------------
    # Backend search helpers with enhanced error handling
    # ------------------------------------------------------------------
    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """Query DuckDuckGo's Instant Answer API for related topics."""
        if not query or not isinstance(query, str):
            return []
            
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        resp = requests.get("https://api.duckduckgo.com/", params=params, timeout=10)
        resp.raise_for_status()
        
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

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_serply(self, query: str) -> List[Dict[str, str]]:
        """Return SERP results from the Serply API if configured."""
        key = os.getenv("SERPLY_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []
            
        try:
            resp = requests.get(
                "https://api.serply.io/v1/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            resp.raise_for_status()
            
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("organic", [])[:3]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Serply API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_exa(self, query: str) -> List[Dict[str, str]]:
        """Search the EXA API for relevant documents."""
        key = os.getenv("EXA_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []
            
        try:
            resp = requests.get(
                "https://api.exa.ai/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            resp.raise_for_status()
            
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:3]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Exa API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_perplexity(self, query: str) -> List[Dict[str, str]]:
        """Fetch search results from Perplexity's API."""
        key = os.getenv("PERPLEXITY_API_KEY")
        if not key or not query or not isinstance(query, str):
            return []
            
        try:
            resp = requests.get(
                "https://api.perplexity.ai/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            resp.raise_for_status()
            
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("results", [])[:3]
                if item.get("title") and item.get("url")
            ]
        except RequestException as e:
            logger.warning(f"Perplexity API error: {e}")
            return []

    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_wolfram(self, query: str) -> List[Dict[str, str]]:
        """Use WolframAlpha's simple API for factual computations."""
        key = os.getenv("WOLFRAM_ALPHA_APPID")
        if not key or not query or not isinstance(query, str):
            return []
            
        try:
            resp = requests.get(
                "https://api.wolframalpha.com/v1/result",
                params={"i": query, "appid": key},
                timeout=10,
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

    def _analyze_evidence(self, evidence: List[Dict[str, str]]) -> str:
        """Analyze evidence quality and determine verdict."""
        if not evidence:
            return "insufficient_evidence"
            
        # Simple heuristic based on evidence count and sources
        if len(evidence) >= 3:
            return "well_supported"
        elif len(evidence) >= 2:
            return "moderately_supported"
        else:
            return "limited_evidence"

    # ------------------------------------------------------------------
    def _run(self, claim: str) -> Dict[str, Any]:
        """Enhanced fact checking with comprehensive error handling."""
        start_time = time.time()
        
        # Input validation
        if not claim or not isinstance(claim, str):
            return {
                "status": "error",
                "error": "Claim is required and must be a non-empty string",
                "claim": claim,
                "timestamp": time.time()
            }
        
        evidence: List[Dict[str, str]] = []
        failed_backends = []
        
        backends = [
            ("duckduckgo", self._search_duckduckgo),
            ("serply", self._search_serply), 
            ("exa", self._search_exa),
            ("perplexity", self._search_perplexity),
            ("wolfram", self._search_wolfram),
        ]
        
        logger.info(f"Starting fact check for claim: {claim[:100]}...")
        
        for name, backend_func in backends:
            try:
                results = backend_func(claim)
                evidence.extend(results)
                logger.debug(f"Backend {name} returned {len(results)} results")
            except Exception as e:
                error_msg = str(e)
                failed_backends.append({"backend": name, "error": error_msg})
                logger.error(f"Backend {name} failed: {error_msg}")
                
        # Determine verdict based on evidence quality
        verdict = self._analyze_evidence(evidence)
        processing_time = time.time() - start_time
        
        result = {
            "status": "success" if evidence else "partial",
            "verdict": verdict,
            "evidence": evidence,
            "evidence_count": len(evidence),
            "failed_backends": failed_backends,
            "claim": claim,
            "processing_time": processing_time,
            "timestamp": time.time()
        }
        
        logger.info(f"Fact check completed in {processing_time:.2f}s with {len(evidence)} evidence items")
        return result

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Public wrapper with type safety."""
        return self._run(*args, **kwargs)
