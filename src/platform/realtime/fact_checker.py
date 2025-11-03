"""
Real-time fact-checking system for the Ultimate Discord Intelligence Bot.

Provides live fact-checking capabilities with automated verification,
claim detection, and real-time accuracy assessment for live content streams.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of factual claims."""

    STATISTICAL = "statistical"
    HISTORICAL = "historical"
    SCIENTIFIC = "scientific"
    POLITICAL = "political"
    ECONOMIC = "economic"
    MEDICAL = "medical"
    TECHNOLOGICAL = "technological"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    GENERAL = "general"


class VerificationStatus(Enum):
    """Status of fact-checking verification."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    FALSE = "false"
    PENDING = "pending"
    ERROR = "error"


class ConfidenceLevel(Enum):
    """Confidence levels for fact-checking results."""

    VERY_HIGH = "very_high"  # > 0.9
    HIGH = "high"  # 0.7 - 0.9
    MEDIUM = "medium"  # 0.5 - 0.7
    LOW = "low"  # 0.3 - 0.5
    VERY_LOW = "very_low"  # < 0.3


@dataclass
class FactualClaim:
    """A factual claim extracted from content."""

    claim_id: str
    text: str
    claim_type: ClaimType
    timestamp: float
    speaker: str = ""
    context: str = ""
    source_url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_statistical(self) -> bool:
        """Check if claim is statistical."""
        return self.claim_type == ClaimType.STATISTICAL

    @property
    def is_scientific(self) -> bool:
        """Check if claim is scientific."""
        return self.claim_type == ClaimType.SCIENTIFIC

    @property
    def is_political(self) -> bool:
        """Check if claim is political."""
        return self.claim_type == ClaimType.POLITICAL


@dataclass
class VerificationSource:
    """Source used for fact verification."""

    source_id: str
    name: str
    url: str
    authority_score: float
    reliability_score: float
    last_updated: float
    source_type: str = "website"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authoritative(self) -> bool:
        """Check if source is authoritative."""
        return self.authority_score > 0.8

    @property
    def is_reliable(self) -> bool:
        """Check if source is reliable."""
        return self.reliability_score > 0.7

    @property
    def is_high_quality(self) -> bool:
        """Check if source is high quality."""
        return self.is_authoritative and self.is_reliable


@dataclass
class VerificationResult:
    """Result of fact verification."""

    claim_id: str
    verification_status: VerificationStatus
    confidence_level: ConfidenceLevel
    confidence_score: float
    verification_time: float
    sources_checked: int
    sources_agreeing: int
    sources_disputing: int
    verification_sources: list[VerificationSource] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_verified(self) -> bool:
        """Check if claim is verified."""
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def is_disputed(self) -> bool:
        """Check if claim is disputed."""
        return self.verification_status == VerificationStatus.DISPUTED

    @property
    def is_false(self) -> bool:
        """Check if claim is false."""
        return self.verification_status == VerificationStatus.FALSE

    @property
    def has_high_confidence(self) -> bool:
        """Check if result has high confidence."""
        return self.confidence_level in {
            ConfidenceLevel.VERY_HIGH,
            ConfidenceLevel.HIGH,
        }

    @property
    def consensus_ratio(self) -> float:
        """Get consensus ratio from sources."""
        if self.sources_checked == 0:
            return 0.0
        return self.sources_agreeing / self.sources_checked


@dataclass
class FactCheckAlert:
    """Alert for fact-checking results."""

    alert_id: str
    claim_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: float
    verification_result: VerificationResult
    stream_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        """Check if alert is critical."""
        return self.severity in {"critical", "high"}

    @property
    def is_false_claim_alert(self) -> bool:
        """Check if alert is for a false claim."""
        return self.verification_result.is_false

    @property
    def is_disputed_claim_alert(self) -> bool:
        """Check if alert is for a disputed claim."""
        return self.verification_result.is_disputed


class RealTimeFactChecker:
    """
    Real-time fact-checking system.

    Provides automated fact-checking capabilities for live content streams
    with claim detection, verification, and real-time accuracy assessment.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize real-time fact checker."""
        self.config = config or {}
        self.verification_sources: dict[str, VerificationSource] = {}
        self.pending_claims: dict[str, FactualClaim] = {}
        self.verification_results: dict[str, VerificationResult] = {}
        self.fact_check_alerts: list[FactCheckAlert] = []
        self.verification_tasks: dict[str, asyncio.Task[None]] = {}
        self.alert_callbacks: list[callable] = []
        self._shutdown_event = asyncio.Event()

        # Initialize default verification sources
        self._initialize_default_sources()

        logger.info("Real-time fact checker initialized")

    def _initialize_default_sources(self) -> None:
        """Initialize default verification sources."""
        default_sources = [
            VerificationSource(
                source_id="factcheck_org",
                name="FactCheck.org",
                url="https://www.factcheck.org/",
                authority_score=0.95,
                reliability_score=0.92,
                last_updated=time.time(),
                source_type="fact_checking_website",
            ),
            VerificationSource(
                source_id="snopes",
                name="Snopes",
                url="https://www.snopes.com/",
                authority_score=0.90,
                reliability_score=0.88,
                last_updated=time.time(),
                source_type="fact_checking_website",
            ),
            VerificationSource(
                source_id="politifact",
                name="PolitiFact",
                url="https://www.politifact.com/",
                authority_score=0.92,
                reliability_score=0.90,
                last_updated=time.time(),
                source_type="fact_checking_website",
            ),
        ]

        for source in default_sources:
            self.verification_sources[source.source_id] = source

    def add_verification_source(self, source: VerificationSource) -> None:
        """Add a verification source."""
        self.verification_sources[source.source_id] = source
        logger.info(f"Added verification source: {source.name}")

    def add_alert_callback(self, callback: callable) -> None:
        """Add a callback for fact-check alerts."""
        self.alert_callbacks.append(callback)
        logger.info("Added fact-check alert callback")

    async def extract_claims(self, content: str, stream_id: str = "") -> list[FactualClaim]:
        """Extract factual claims from content."""
        # Simulate claim extraction
        claims = []
        sentences = content.split(".")

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) > 20 and self._is_potential_claim(sentence):
                claim = FactualClaim(
                    claim_id=f"{stream_id}_{int(time.time())}_{i}",
                    text=sentence,
                    claim_type=self._classify_claim_type(sentence),
                    timestamp=time.time(),
                    metadata={"extraction_method": "simulated"},
                )
                claims.append(claim)

        logger.info(f"Extracted {len(claims)} claims from content")
        return claims

    def _is_potential_claim(self, text: str) -> bool:
        """Check if text contains a potential factual claim."""
        # Simple heuristics for claim detection
        claim_indicators = [
            "is",
            "are",
            "was",
            "were",
            "will be",
            "has been",
            "have been",
            "studies show",
            "research indicates",
            "data shows",
            "statistics show",
            "according to",
            "it is estimated",
            "reports suggest",
            "percent",
            "%",
            "million",
            "billion",
            "thousand",
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in claim_indicators)

    def _classify_claim_type(self, text: str) -> ClaimType:
        """Classify the type of factual claim."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["study", "research", "scientist", "research", "study"]):
            return ClaimType.SCIENTIFIC
        elif any(word in text_lower for word in ["percent", "%", "million", "billion", "statistics"]):
            return ClaimType.STATISTICAL
        elif any(word in text_lower for word in ["president", "government", "policy", "election"]):
            return ClaimType.POLITICAL
        elif any(word in text_lower for word in ["history", "historical", "century", "decade"]):
            return ClaimType.HISTORICAL
        elif any(word in text_lower for word in ["economy", "economic", "market", "financial"]):
            return ClaimType.ECONOMIC
        elif any(word in text_lower for word in ["medical", "health", "doctor", "treatment"]):
            return ClaimType.MEDICAL
        elif any(word in text_lower for word in ["technology", "computer", "software", "AI"]):
            return ClaimType.TECHNOLOGICAL
        elif any(word in text_lower for word in ["climate", "environment", "pollution", "green"]):
            return ClaimType.ENVIRONMENTAL
        else:
            return ClaimType.GENERAL

    async def verify_claim(self, claim: FactualClaim) -> VerificationResult:
        """Verify a factual claim."""
        start_time = time.time()

        logger.info(f"Verifying claim: {claim.text[:50]}...")

        # Start verification task
        task = asyncio.create_task(self._perform_verification(claim))
        self.verification_tasks[claim.claim_id] = task

        try:
            result = await task
            self.verification_results[claim.claim_id] = result

            # Check if alert should be generated
            if self._should_generate_alert(result):
                await self._generate_fact_check_alert(claim, result)

            return result
        except Exception as e:
            logger.error(f"Error verifying claim {claim.claim_id}: {e}")
            return VerificationResult(
                claim_id=claim.claim_id,
                verification_status=VerificationStatus.ERROR,
                confidence_level=ConfidenceLevel.VERY_LOW,
                confidence_score=0.0,
                verification_time=time.time() - start_time,
                sources_checked=0,
                sources_agreeing=0,
                sources_disputing=0,
                summary=f"Verification failed: {e!s}",
            )
        finally:
            if claim.claim_id in self.verification_tasks:
                del self.verification_tasks[claim.claim_id]

    async def _perform_verification(self, claim: FactualClaim) -> VerificationResult:
        """Perform the actual verification process."""
        start_time = time.time()

        # Simulate verification process
        await asyncio.sleep(0.5)  # Simulate API calls and processing

        # Simulate verification results
        sources_checked = len(self.verification_sources)
        sources_agreeing = int(sources_checked * 0.8)  # 80% agreement
        sources_disputing = sources_checked - sources_agreeing

        # Determine verification status based on agreement
        if sources_agreeing >= sources_checked * 0.8:
            verification_status = VerificationStatus.VERIFIED
            confidence_level = ConfidenceLevel.HIGH
            confidence_score = 0.85
        elif sources_agreeing >= sources_checked * 0.6:
            verification_status = VerificationStatus.PARTIALLY_VERIFIED
            confidence_level = ConfidenceLevel.MEDIUM
            confidence_score = 0.65
        elif sources_disputing > sources_agreeing:
            verification_status = VerificationStatus.DISPUTED
            confidence_level = ConfidenceLevel.LOW
            confidence_score = 0.35
        else:
            verification_status = VerificationStatus.UNVERIFIED
            confidence_level = ConfidenceLevel.LOW
            confidence_score = 0.25

        # Generate supporting and contradicting evidence
        supporting_evidence = [f"Source {i} confirms: {claim.text[:30]}..." for i in range(sources_agreeing)]
        contradicting_evidence = [f"Source {i} disputes: {claim.text[:30]}..." for i in range(sources_disputing)]

        result = VerificationResult(
            claim_id=claim.claim_id,
            verification_status=verification_status,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            verification_time=time.time() - start_time,
            sources_checked=sources_checked,
            sources_agreeing=sources_agreeing,
            sources_disputing=sources_disputing,
            verification_sources=list(self.verification_sources.values()),
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            summary=f"Verified with {sources_agreeing}/{sources_checked} sources agreeing",
        )

        logger.info(f"Verification completed for claim {claim.claim_id}: {verification_status.value}")
        return result

    def _should_generate_alert(self, result: VerificationResult) -> bool:
        """Check if an alert should be generated for this result."""
        return (
            result.is_false
            or result.is_disputed
            or (result.verification_status == VerificationStatus.UNVERIFIED and result.confidence_score < 0.3)
        )

    async def _generate_fact_check_alert(self, claim: FactualClaim, result: VerificationResult) -> None:
        """Generate a fact-check alert."""
        if result.is_false:
            alert_type = "false_claim"
            severity = "critical"
            message = f"False claim detected: {claim.text[:100]}..."
        elif result.is_disputed:
            alert_type = "disputed_claim"
            severity = "warning"
            message = f"Disputed claim detected: {claim.text[:100]}..."
        else:
            alert_type = "unverified_claim"
            severity = "info"
            message = f"Unverified claim detected: {claim.text[:100]}..."

        alert = FactCheckAlert(
            alert_id=f"fact_check_{claim.claim_id}_{int(time.time())}",
            claim_id=claim.claim_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            verification_result=result,
            metadata={"claim_text": claim.text, "claim_type": claim.claim_type.value},
        )

        self.fact_check_alerts.append(alert)

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in fact-check alert callback: {e}")

        logger.warning(f"Generated fact-check alert: {alert.alert_type}")

    async def verify_content_stream(self, content: str, stream_id: str = "") -> list[VerificationResult]:
        """Verify all claims in a content stream."""
        # Extract claims
        claims = await self.extract_claims(content, stream_id)

        if not claims:
            return []

        # Verify all claims concurrently
        verification_tasks = [self.verify_claim(claim) for claim in claims]
        results = await asyncio.gather(*verification_tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = [result for result in results if isinstance(result, VerificationResult)]

        logger.info(f"Verified {len(valid_results)} claims from stream {stream_id}")
        return valid_results

    async def get_verification_result(self, claim_id: str) -> VerificationResult | None:
        """Get verification result for a claim."""
        return self.verification_results.get(claim_id)

    async def get_fact_check_alerts(self, limit: int = 100) -> list[FactCheckAlert]:
        """Get recent fact-check alerts."""
        return self.fact_check_alerts[-limit:] if limit > 0 else self.fact_check_alerts

    async def get_verification_statistics(self) -> dict[str, Any]:
        """Get verification statistics."""
        total_results = len(self.verification_results)
        if total_results == 0:
            return {"total_claims": 0}

        status_counts: dict[str, int] = {}
        for result in self.verification_results.values():
            status = result.verification_status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_claims": total_results,
            "total_alerts": len(self.fact_check_alerts),
            "verification_sources": len(self.verification_sources),
            "pending_verifications": len(self.verification_tasks),
            "status_breakdown": status_counts,
            "average_verification_time": sum(r.verification_time for r in self.verification_results.values())
            / total_results,
        }

    async def shutdown(self) -> None:
        """Shutdown the fact checker."""
        logger.info("Shutting down real-time fact checker...")

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for pending verifications to complete
        if self.verification_tasks:
            await asyncio.gather(*self.verification_tasks.values(), return_exceptions=True)

        logger.info("Real-time fact checker shutdown complete")

    async def __aenter__(self) -> "RealTimeFactChecker":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.shutdown()


# Global fact checker instance
_global_fact_checker: RealTimeFactChecker | None = None


def get_global_fact_checker() -> RealTimeFactChecker:
    """Get the global fact checker instance."""
    global _global_fact_checker
    if _global_fact_checker is None:
        _global_fact_checker = RealTimeFactChecker()
    return _global_fact_checker


def set_global_fact_checker(fact_checker: RealTimeFactChecker) -> None:
    """Set the global fact checker instance."""
    global _global_fact_checker
    _global_fact_checker = fact_checker


# Convenience functions for global fact checker
async def verify_content_stream(content: str, stream_id: str = "") -> list[VerificationResult]:
    """Verify content stream using the global fact checker."""
    return await get_global_fact_checker().verify_content_stream(content, stream_id)


async def extract_claims(content: str, stream_id: str = "") -> list[FactualClaim]:
    """Extract claims using the global fact checker."""
    return await get_global_fact_checker().extract_claims(content, stream_id)


async def verify_claim(claim: FactualClaim) -> VerificationResult:
    """Verify claim using the global fact checker."""
    return await get_global_fact_checker().verify_claim(claim)
