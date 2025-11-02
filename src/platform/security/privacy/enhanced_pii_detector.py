"""Enhanced PII detection with comprehensive patterns and ML-based detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.step_result import StepResult


# Enhanced regex patterns for better PII detection
ENHANCED_PATTERNS = {
    # Email patterns (more comprehensive)
    "email": [
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        re.compile(r"[A-Za-z0-9._%+-]+\+[A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # Gmail-style
    ],
    # Phone number patterns (international support)
    "phone": [
        re.compile(r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"),  # US format
        re.compile(
            r"\b(?:\+?[1-9]\d{0,3}[-.\s]?)?\(?([0-9]{2,4})\)?[-.\s]?([0-9]{2,4})[-.\s]?([0-9]{2,4})\b"
        ),  # International
        re.compile(r"\b(?:\+?44[-.\s]?)?\(?([0-9]{2,4})\)?[-.\s]?([0-9]{2,4})[-.\s]?([0-9]{2,4})\b"),  # UK format
    ],
    # IP address patterns
    "ip": [
        re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        re.compile(r"\b(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::1|::)\b"),  # IPv6
    ],
    # Credit card patterns (more comprehensive)
    "credit_card": [
        re.compile(r"\b(?:\d{4}[-.\s]?){3}\d{4}\b"),  # Standard format
        re.compile(r"\b(?:\d{4}[-.\s]?){3}\d{3}\b"),  # Amex format
        re.compile(r"\b\d{13,19}\b"),  # Raw digits
    ],
    # Social Security Number patterns
    "ssn": [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        re.compile(r"\b\d{3}\.\d{2}\.\d{4}\b"),
        re.compile(r"\b\d{9}\b"),  # Raw format
    ],
    # Driver's License patterns (US states)
    "drivers_license": [
        re.compile(r"\b[A-Z]{1,2}\d{6,8}\b"),  # General format
        re.compile(r"\b\d{8}\b"),  # Some states
        re.compile(r"\b[A-Z]\d{7}\b"),  # California format
    ],
    # Passport patterns
    "passport": [
        re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),  # General format
        re.compile(r"\b\d{9}\b"),  # US format
    ],
    # Address patterns (more comprehensive)
    "address": [
        re.compile(
            r"\b\d{1,5}\s+[A-Za-z0-9\.\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Circle|Cir)\b",
            re.I,
        ),
        re.compile(
            r"\b\d{1,5}\s+[A-Za-z0-9\.\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Circle|Cir)\s*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b",
            re.I,
        ),
    ],
    # Geographic coordinates
    "coordinates": [
        re.compile(r"\b-?\d{1,2}\.\d+,\s*-?\d{1,3}\.\d+\b"),  # Decimal degrees
        re.compile(r"\b\d{1,2}°\d{1,2}'\d{1,2}\.\d+\"[NS]\s+\d{1,3}°\d{1,2}'\d{1,2}\.\d+\"[EW]\b"),  # DMS format
    ],
    # Date of birth patterns
    "date_of_birth": [
        re.compile(r"\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/(?:19|20)\d{2}\b"),  # MM/DD/YYYY
        re.compile(r"\b(?:0[1-9]|[12][0-9]|3[01])/(?:0[1-9]|1[0-2])/(?:19|20)\d{2}\b"),  # DD/MM/YYYY
        re.compile(r"\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])\b"),  # YYYY-MM-DD
    ],
    # Bank account patterns
    "bank_account": [
        re.compile(r"\b\d{8,17}\b"),  # Account numbers
        re.compile(r"\b\d{9}\b"),  # Routing numbers
    ],
    # Medical record patterns
    "medical_record": [
        re.compile(r"\bMR\d{6,8}\b", re.I),  # Medical record numbers
        re.compile(r"\b\d{6,8}\b"),  # Patient IDs
    ],
    # License plate patterns
    "license_plate": [
        re.compile(r"\b[A-Z]{1,3}\d{1,4}[A-Z]{0,2}\b"),  # US format
        re.compile(r"\b\d{1,4}[A-Z]{1,3}\b"),  # Alternative format
    ],
    # Vehicle VIN patterns
    "vin": [
        re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"),  # Standard VIN format
    ],
    # MAC address patterns
    "mac_address": [
        re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b"),
    ],
    # URL patterns (may contain sensitive info)
    "sensitive_url": [
        re.compile(r"https?://[^\s]+(?:password|token|key|secret|auth)[^\s]*", re.I),
    ],
    # API key patterns
    "api_key": [
        re.compile(r"\b(?:sk|pk|ak|tk|key|token|secret)[-_]?[A-Za-z0-9]{20,}\b", re.I),
        re.compile(r"\b[A-Za-z0-9]{32,}\b"),  # Generic long alphanumeric
    ],
    # Bitcoin address patterns
    "bitcoin_address": [
        re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),  # Legacy format
        re.compile(r"\bbc1[a-z0-9]{39,59}\b"),  # Bech32 format
    ],
    # Ethereum address patterns
    "ethereum_address": [
        re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    ],
}

# Confidence scoring for different PII types
PII_CONFIDENCE_SCORES = {
    "email": 0.95,
    "phone": 0.90,
    "ip": 0.95,
    "credit_card": 0.98,
    "ssn": 0.99,
    "drivers_license": 0.85,
    "passport": 0.90,
    "address": 0.80,
    "coordinates": 0.85,
    "date_of_birth": 0.75,
    "bank_account": 0.70,
    "medical_record": 0.85,
    "license_plate": 0.80,
    "vin": 0.95,
    "mac_address": 0.90,
    "sensitive_url": 0.85,
    "api_key": 0.90,
    "bitcoin_address": 0.95,
    "ethereum_address": 0.95,
}


@dataclass
class EnhancedSpan:
    """Enhanced span with confidence and context information."""

    type: str
    start: int
    end: int
    value: str
    confidence: float
    context: str | None = None
    risk_level: str = "medium"  # low, medium, high, critical


@dataclass
class PIIDetectionResult:
    """Result of PII detection with metadata."""

    spans: list[EnhancedSpan]
    total_spans: int
    risk_summary: dict[str, int]
    confidence_score: float
    processing_time: float


class EnhancedPIIDetector:
    """Enhanced PII detector with comprehensive patterns and ML capabilities."""

    def __init__(self, enable_ml_detection: bool = True):
        """Initialize enhanced PII detector.

        Args:
            enable_ml_detection: Whether to enable ML-based detection
        """
        self.enable_ml_detection = enable_ml_detection
        self.patterns = ENHANCED_PATTERNS
        self.confidence_scores = PII_CONFIDENCE_SCORES

    def detect(self, text: str, lang: str = "en") -> PIIDetectionResult:
        """Detect PII in text with enhanced patterns.

        Args:
            text: Text to analyze
            lang: Language code (default: "en")

        Returns:
            PIIDetectionResult with detected spans and metadata
        """
        import time

        start_time = time.time()

        spans = []
        risk_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        # Pattern-based detection
        for pii_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    confidence = self.confidence_scores.get(pii_type, 0.5)
                    risk_level = self._determine_risk_level(pii_type, confidence)

                    span = EnhancedSpan(
                        type=pii_type,
                        start=match.start(),
                        end=match.end(),
                        value=match.group(),
                        confidence=confidence,
                        context=self._extract_context(text, match.start(), match.end()),
                        risk_level=risk_level,
                    )

                    spans.append(span)
                    risk_summary[risk_level] += 1

        # ML-based detection (if enabled)
        if self.enable_ml_detection:
            ml_spans = self._ml_detection(text, lang)
            spans.extend(ml_spans)
            for span in ml_spans:
                risk_summary[span.risk_level] += 1

        # Remove overlapping spans (keep highest confidence)
        spans = self._remove_overlapping_spans(spans)

        # Calculate overall confidence
        total_confidence = sum(span.confidence for span in spans)
        avg_confidence = total_confidence / len(spans) if spans else 0.0

        processing_time = time.time() - start_time

        return PIIDetectionResult(
            spans=spans,
            total_spans=len(spans),
            risk_summary=risk_summary,
            confidence_score=avg_confidence,
            processing_time=processing_time,
        )

    def _determine_risk_level(self, pii_type: str, confidence: float) -> str:
        """Determine risk level based on PII type and confidence."""
        if pii_type in ["ssn", "credit_card", "api_key"]:
            return "critical"
        elif pii_type in ["email", "phone", "drivers_license", "passport"]:
            return "high"
        elif pii_type in ["address", "coordinates", "date_of_birth"]:
            return "medium"
        else:
            return "low"

    def _extract_context(self, text: str, start: int, end: int, context_window: int = 50) -> str:
        """Extract context around detected PII."""
        context_start = max(0, start - context_window)
        context_end = min(len(text), end + context_window)
        return text[context_start:context_end]

    def _ml_detection(self, text: str, lang: str) -> list[EnhancedSpan]:
        """ML-based PII detection (placeholder for future implementation)."""
        # This would integrate with models like spaCy's NER or custom ML models
        # For now, return empty list
        return []

    def _remove_overlapping_spans(self, spans: list[EnhancedSpan]) -> list[EnhancedSpan]:
        """Remove overlapping spans, keeping highest confidence ones."""
        if not spans:
            return spans

        # Sort by confidence (descending)
        sorted_spans = sorted(spans, key=lambda s: s.confidence, reverse=True)

        non_overlapping = []
        for span in sorted_spans:
            # Check if this span overlaps with any already selected span
            overlaps = False
            for selected in non_overlapping:
                if span.start < selected.end and span.end > selected.start:
                    overlaps = True
                    break

            if not overlaps:
                non_overlapping.append(span)

        # Sort by start position for consistent ordering
        return sorted(non_overlapping, key=lambda s: s.start)

    def get_detection_stats(self) -> dict[str, any]:
        """Get detection statistics."""
        return {
            "pattern_count": sum(len(patterns) for patterns in self.patterns.values()),
            "pii_types": list(self.patterns.keys()),
            "ml_enabled": self.enable_ml_detection,
            "confidence_scores": self.confidence_scores,
        }


def detect_enhanced_pii(text: str, lang: str = "en") -> PIIDetectionResult:
    """Convenience function for enhanced PII detection."""
    detector = EnhancedPIIDetector()
    return detector.detect(text, lang)


def validate_pii_patterns() -> StepResult:
    """Validate PII detection patterns."""
    try:
        detector = EnhancedPIIDetector()

        # Test patterns with sample data
        test_cases = [
            ("test@example.com", "email"),
            ("555-123-4567", "phone"),
            ("192.168.1.1", "ip"),
            ("4111-1111-1111-1111", "credit_card"),
            ("123-45-6789", "ssn"),
        ]

        for text, expected_type in test_cases:
            result = detector.detect(text)
            found_types = [span.type for span in result.spans]
            if expected_type not in found_types:
                return StepResult.fail(f"Pattern validation failed for {expected_type}")

        return StepResult.ok(data={"status": "patterns_validated"})

    except Exception as e:
        return StepResult.fail(f"Pattern validation failed: {e}")


# Backward compatibility
def detect(text: str, lang: str = "en") -> list[EnhancedSpan]:
    """Backward compatible detection function."""
    result = detect_enhanced_pii(text, lang)
    return result.spans
