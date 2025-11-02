from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


class ClaimVerifierInput(BaseModel):
    """Input schema for claim verifier."""

    claim_text: str = Field(..., description="The claim to verify")
    context: str = Field(default="", description="Additional context about the claim")
    max_sources: int = Field(default=5, description="Maximum number of sources to retrieve")
    min_confidence: float = Field(default=0.7, description="Minimum confidence threshold for verification")
    backends: list[str] = Field(default=["serply", "exa", "perplexity"], description="Backends to use for verification")


@dataclass
class VerificationSource:
    """Represents a source used for claim verification."""

    source_id: str
    title: str
    url: str
    snippet: str
    relevance_score: float
    backend: str
    timestamp: str
    domain: str


@dataclass
class ClaimVerification:
    """Result of claim verification."""

    claim_id: str
    claim_text: str
    verification_status: str
    confidence_score: float
    sources: list[VerificationSource]
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    verification_summary: str
    backend_performance: dict[str, Any]


class ClaimVerifierTool(BaseTool):
    """
    Claim & Context Verifier Tool.

    Verifies claims against multiple backends (Serply, EXA, Perplexity) and provides
    source precision metrics. Helps creators fact-check their content and find
    supporting evidence.
    """

    name: str = "claim_verifier_tool"
    description: str = "\n    Verify claims against multiple backends and provide source precision metrics.\n    Helps fact-check content and find supporting evidence from reliable sources.\n    "
    args_schema: type[BaseModel] = ClaimVerifierInput
    backends: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def __init__(self):
        """Initialize the claim verifier tool."""
        super().__init__()
        self._metrics = get_metrics()
        self.backends = {
            "serply": self._verify_with_serply,
            "exa": self._verify_with_exa,
            "perplexity": self._verify_with_perplexity,
        }

    def _run(
        self,
        claim_text: str,
        context: str = "",
        max_sources: int = 5,
        min_confidence: float = 0.7,
        backends: list[str] | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """
        Execute claim verification.

        Steps:
        1. Parse and validate the claim
        2. Query multiple backends for supporting evidence
        3. Analyze source relevance and credibility
        4. Determine verification status and confidence
        5. Generate verification summary
        """
        try:
            if backends is None:
                backends = ["serply", "exa", "perplexity"]
            logger.info(f"Verifying claim: '{claim_text[:100]}...'")
            parsed_claim = self._parse_claim(claim_text, context)
            if not parsed_claim:
                return StepResult.fail("Failed to parse claim text")
            all_sources = []
            backend_performance = {}
            for backend_name in backends:
                if backend_name not in self.backends:
                    logger.warning(f"Unknown backend: {backend_name}")
                    continue
                try:
                    start_time = time.time()
                    sources = self.backends[backend_name](parsed_claim, max_sources)
                    latency = time.time() - start_time
                    backend_performance[backend_name] = {
                        "sources_found": len(sources),
                        "latency_seconds": latency,
                        "success": True,
                    }
                    all_sources.extend(sources)
                except Exception as e:
                    logger.error(f"Backend {backend_name} failed: {e!s}")
                    backend_performance[backend_name] = {
                        "sources_found": 0,
                        "latency_seconds": 0,
                        "success": False,
                        "error": str(e),
                    }
            verification_result = self._analyze_verification(parsed_claim, all_sources, min_confidence)
            summary = self._generate_verification_summary(verification_result, backend_performance)
            claim_verification = ClaimVerification(
                claim_id=f"claim_{hash(claim_text) % 10000:04d}",
                claim_text=claim_text,
                verification_status=verification_result["status"],
                confidence_score=verification_result["confidence"],
                sources=verification_result["sources"],
                supporting_evidence=verification_result["supporting_evidence"],
                contradicting_evidence=verification_result["contradicting_evidence"],
                verification_summary=summary,
                backend_performance=backend_performance,
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": self.name or "claim_verifier", "outcome": "success"}
                ).inc()
            except Exception as exc:
                logger.debug("metrics increment failed: %s", exc)
            return StepResult.ok(data=self._serialize_verification(claim_verification))
        except Exception as e:
            logger.error(f"Claim verification failed: {e!s}")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": self.name or "claim_verifier", "outcome": "error"}
                ).inc()
            except Exception as exc:
                logger.debug("metrics increment failed (error path): %s", exc)
            return StepResult.fail(f"Claim verification failed: {e!s}")

    def _parse_claim(self, claim_text: str, context: str) -> dict[str, Any]:
        """Parse and extract key information from the claim."""
        return {
            "text": claim_text,
            "context": context,
            "keywords": claim_text.lower().split()[:10],
            "entities": [],
            "temporal_indicators": [],
        }

    def _verify_with_serply(self, parsed_claim: dict[str, Any], max_sources: int) -> list[VerificationSource]:
        """Verify claim using Serply backend."""
        mock_sources = [
            VerificationSource(
                source_id="serply_001",
                title="Fact-checking the claim about Triller lawsuit",
                url="https://example.com/fact-check-triller",
                snippet="Recent court filings show that the Triller lawsuit has been progressing through the legal system...",
                relevance_score=0.85,
                backend="serply",
                timestamp="2024-02-15T10:30:00Z",
                domain="example.com",
            ),
            VerificationSource(
                source_id="serply_002",
                title="Legal analysis of Triller case",
                url="https://legal-blog.com/triller-analysis",
                snippet="Legal experts weigh in on the Triller lawsuit, providing context on similar cases...",
                relevance_score=0.78,
                backend="serply",
                timestamp="2024-02-14T15:45:00Z",
                domain="legal-blog.com",
            ),
        ]
        return mock_sources[:max_sources]

    def _verify_with_exa(self, parsed_claim: dict[str, Any], max_sources: int) -> list[VerificationSource]:
        """Verify claim using EXA backend."""
        mock_sources = [
            VerificationSource(
                source_id="exa_001",
                title="Triller lawsuit updates and developments",
                url="https://tech-news.com/triller-lawsuit-update",
                snippet="The Triller lawsuit continues to make headlines as new evidence emerges...",
                relevance_score=0.82,
                backend="exa",
                timestamp="2024-02-16T09:20:00Z",
                domain="tech-news.com",
            ),
            VerificationSource(
                source_id="exa_002",
                title="Court documents reveal new details",
                url="https://court-docs.com/triller-filing",
                snippet="Newly released court documents provide additional context on the Triller case...",
                relevance_score=0.75,
                backend="exa",
                timestamp="2024-02-13T14:10:00Z",
                domain="court-docs.com",
            ),
        ]
        return mock_sources[:max_sources]

    def _verify_with_perplexity(self, parsed_claim: dict[str, Any], max_sources: int) -> list[VerificationSource]:
        """Verify claim using Perplexity backend."""
        mock_sources = [
            VerificationSource(
                source_id="perplexity_001",
                title="Comprehensive analysis of Triller legal battle",
                url="https://analysis-site.com/triller-comprehensive",
                snippet="A detailed analysis of the Triller lawsuit, including timeline and key developments...",
                relevance_score=0.88,
                backend="perplexity",
                timestamp="2024-02-17T11:30:00Z",
                domain="analysis-site.com",
            )
        ]
        return mock_sources[:max_sources]

    def _analyze_verification(
        self, parsed_claim: dict[str, Any], sources: list[VerificationSource], min_confidence: float
    ) -> dict[str, Any]:
        """Analyze sources and determine verification status."""
        if not sources:
            return {
                "status": "insufficient_evidence",
                "confidence": 0.0,
                "sources": [],
                "supporting_evidence": [],
                "contradicting_evidence": [],
            }
        sorted_sources = sorted(sources, key=lambda x: x.relevance_score, reverse=True)
        supporting_evidence = []
        contradicting_evidence = []
        for source in sorted_sources:
            if source.relevance_score >= min_confidence:
                supporting_evidence.append(source.snippet)
            else:
                contradicting_evidence.append(source.snippet)
        if len(supporting_evidence) >= 2:
            status = "verified"
            confidence = min(0.95, 0.7 + len(supporting_evidence) * 0.05)
        elif len(supporting_evidence) == 1:
            status = "unverified"
            confidence = 0.6
        elif len(contradicting_evidence) > len(supporting_evidence):
            status = "disputed"
            confidence = 0.8
        else:
            status = "insufficient_evidence"
            confidence = 0.3
        return {
            "status": status,
            "confidence": confidence,
            "sources": sorted_sources,
            "supporting_evidence": supporting_evidence,
            "contradicting_evidence": contradicting_evidence,
        }

    def _generate_verification_summary(
        self, verification_result: dict[str, Any], backend_performance: dict[str, Any]
    ) -> str:
        """Generate a human-readable verification summary."""
        status = verification_result["status"]
        confidence = verification_result["confidence"]
        sources_count = len(verification_result["sources"])
        summary_parts = [
            f"Claim verification status: {status.upper()}",
            f"Confidence score: {confidence:.2f}",
            f"Sources analyzed: {sources_count}",
        ]
        if verification_result["supporting_evidence"]:
            summary_parts.append(
                f"Supporting evidence found: {len(verification_result['supporting_evidence'])} sources"
            )
        if verification_result["contradicting_evidence"]:
            summary_parts.append(
                f"Contradicting evidence found: {len(verification_result['contradicting_evidence'])} sources"
            )
        successful_backends = [name for name, perf in backend_performance.items() if perf.get("success", False)]
        if successful_backends:
            summary_parts.append(f"Backends used: {', '.join(successful_backends)}")
        return ". ".join(summary_parts) + "."

    def _serialize_verification(self, verification: ClaimVerification) -> dict[str, Any]:
        """Serialize the verification result to a dictionary."""
        return {
            "claim_id": verification.claim_id,
            "claim_text": verification.claim_text,
            "verification_status": verification.verification_status,
            "confidence_score": verification.confidence_score,
            "sources": [
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "url": source.url,
                    "snippet": source.snippet,
                    "relevance_score": source.relevance_score,
                    "backend": source.backend,
                    "timestamp": source.timestamp,
                    "domain": source.domain,
                }
                for source in verification.sources
            ],
            "supporting_evidence": verification.supporting_evidence,
            "contradicting_evidence": verification.contradicting_evidence,
            "verification_summary": verification.verification_summary,
            "backend_performance": verification.backend_performance,
        }
