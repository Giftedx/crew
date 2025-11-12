"""Enhanced PII redactor with advanced masking strategies."""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from .enhanced_pii_detector import EnhancedSpan, PIIDetectionResult


class EnhancedRedactor:
    """Enhanced PII redactor with multiple masking strategies."""

    def __init__(self):
        """Initialize enhanced redactor."""
        self.masking_strategies = {
            "replace": self._replace_strategy,
            "hash": self._hash_strategy,
            "partial": self._partial_strategy,
            "contextual": self._contextual_strategy,
        }
        self.default_masks = {
            "email": "[EMAIL_REDACTED]",
            "phone": "[PHONE_REDACTED]",
            "ip": "[IP_REDACTED]",
            "credit_card": "[CARD_REDACTED]",
            "ssn": "[SSN_REDACTED]",
            "drivers_license": "[DL_REDACTED]",
            "passport": "[PASSPORT_REDACTED]",
            "address": "[ADDRESS_REDACTED]",
            "coordinates": "[COORDINATES_REDACTED]",
            "date_of_birth": "[DOB_REDACTED]",
            "bank_account": "[ACCOUNT_REDACTED]",
            "medical_record": "[MR_REDACTED]",
            "license_plate": "[PLATE_REDACTED]",
            "vin": "[VIN_REDACTED]",
            "mac_address": "[MAC_REDACTED]",
            "sensitive_url": "[URL_REDACTED]",
            "api_key": "[API_KEY_REDACTED]",
            "bitcoin_address": "[BTC_REDACTED]",
            "ethereum_address": "[ETH_REDACTED]",
        }

    def redact(
        self,
        text: str,
        spans: list[EnhancedSpan],
        strategy: str = "replace",
        custom_masks: dict[str, str] | None = None,
        preserve_format: bool = False,
    ) -> tuple[str, dict[str, int]]:
        """Redact PII from text using specified strategy.

        Args:
            text: Text to redact
            spans: List of detected PII spans
            strategy: Redaction strategy ("replace", "hash", "partial", "contextual")
            custom_masks: Custom masks for specific PII types
            preserve_format: Whether to preserve original format (e.g., phone number format)

        Returns:
            Tuple of (redacted_text, redaction_stats)
        """
        if not spans:
            return (text, {})
        sorted_spans = sorted(spans, key=lambda s: s.start, reverse=True)
        redacted_text = text
        redaction_stats = {}
        for span in sorted_spans:
            mask = self._get_mask(span.type, custom_masks, strategy, span.value, preserve_format)
            redacted_text = redacted_text[: span.start] + mask + redacted_text[span.end :]
            pii_type = span.type
            redaction_stats[pii_type] = redaction_stats.get(pii_type, 0) + 1
        return (redacted_text, redaction_stats)

    def _get_mask(
        self,
        pii_type: str,
        custom_masks: dict[str, str] | None,
        strategy: str,
        original_value: str,
        preserve_format: bool,
    ) -> str:
        """Get appropriate mask for PII type and strategy."""
        if custom_masks and pii_type in custom_masks:
            return custom_masks[pii_type]
        strategy_func = self.masking_strategies.get(strategy, self._replace_strategy)
        return strategy_func(pii_type, original_value, preserve_format)

    def _replace_strategy(self, pii_type: str, original_value: str, preserve_format: bool) -> str:
        """Simple replacement strategy."""
        return self.default_masks.get(pii_type, "[REDACTED]")

    def _hash_strategy(self, pii_type: str, original_value: str, preserve_format: bool) -> str:
        """Hash-based redaction strategy."""
        hash_obj = hashlib.sha256(original_value.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        if preserve_format:
            if pii_type == "phone":
                return f"***-***-{hash_hex[:4]}"
            elif pii_type == "email":
                return f"***@{hash_hex[:4]}.com"
            elif pii_type == "credit_card":
                return f"****-****-****-{hash_hex[:4]}"
            else:
                return f"[{pii_type.upper()}_{hash_hex}]"
        else:
            return f"[{pii_type.upper()}_{hash_hex}]"

    def _partial_strategy(self, pii_type: str, original_value: str, preserve_format: bool) -> str:
        """Partial redaction strategy (show some characters)."""
        if len(original_value) <= 4:
            return "*" * len(original_value)
        if pii_type == "email":
            local, domain = original_value.split("@", 1)
            if len(local) > 2:
                return f"{local[0]}***@{domain}"
            else:
                return "***@" + domain
        elif pii_type == "phone":
            return "***-***-" + original_value[-4:]
        elif pii_type == "credit_card":
            return "****-****-****-" + original_value[-4:]
        elif len(original_value) > 6:
            return original_value[:2] + "*" * (len(original_value) - 4) + original_value[-2:]
        else:
            return "*" * len(original_value)

    def _contextual_strategy(self, pii_type: str, original_value: str, preserve_format: bool) -> str:
        """Contextual redaction strategy based on PII type and risk level."""
        if pii_type in ["ssn", "credit_card", "api_key"]:
            return f"[{pii_type.upper()}_REDACTED]"
        elif pii_type in ["email", "phone", "drivers_license"]:
            return self._partial_strategy(pii_type, original_value, preserve_format)
        else:
            return self._hash_strategy(pii_type, original_value, preserve_format)

    def redact_with_metadata(
        self,
        text: str,
        detection_result: PIIDetectionResult,
        strategy: str = "replace",
        custom_masks: dict[str, str] | None = None,
        preserve_format: bool = False,
    ) -> tuple[str, dict[str, any]]:
        """Redact PII with comprehensive metadata.

        Args:
            text: Text to redact
            detection_result: Result from PII detection
            strategy: Redaction strategy
            custom_masks: Custom masks for specific PII types
            preserve_format: Whether to preserve original format

        Returns:
            Tuple of (redacted_text, redaction_metadata)
        """
        redacted_text, redaction_stats = self.redact(
            text, detection_result.spans, strategy, custom_masks, preserve_format
        )
        total_redactions = sum(redaction_stats.values())
        risk_redactions = {
            "critical": sum(1 for span in detection_result.spans if span.risk_level == "critical"),
            "high": sum(1 for span in detection_result.spans if span.risk_level == "high"),
            "medium": sum(1 for span in detection_result.spans if span.risk_level == "medium"),
            "low": sum(1 for span in detection_result.spans if span.risk_level == "low"),
        }
        metadata = {
            "original_length": len(text),
            "redacted_length": len(redacted_text),
            "total_redactions": total_redactions,
            "redaction_stats": redaction_stats,
            "risk_redactions": risk_redactions,
            "strategy_used": strategy,
            "preserve_format": preserve_format,
            "detection_confidence": detection_result.confidence_score,
            "processing_time": detection_result.processing_time,
        }
        return (redacted_text, metadata)

    def validate_redaction(self, original_text: str, redacted_text: str) -> StepResult:
        """Validate that redaction was successful.

        Args:
            original_text: Original text
            redacted_text: Redacted text

        Returns:
            StepResult with validation results
        """
        try:
            if original_text == redacted_text:
                return StepResult.fail("No redaction occurred")
            pii_patterns = [
                "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b",
                "\\b(?:\\+?1[-.\\s]?)?\\(?([0-9]{3})\\)?[-.\\s]?([0-9]{3})[-.\\s]?([0-9]{4})\\b",
                "\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b",
            ]
            for pattern in pii_patterns:
                if re.search(pattern, redacted_text):
                    return StepResult.fail(f"PII pattern still present: {pattern}")
            return StepResult.ok(data={"status": "redaction_validated"})
        except Exception as e:
            return StepResult.fail(f"Redaction validation failed: {e}")

    def get_redaction_stats(self) -> dict[str, any]:
        """Get redaction statistics."""
        return {
            "strategies_available": list(self.masking_strategies.keys()),
            "default_masks": self.default_masks,
            "supported_pii_types": list(self.default_masks.keys()),
        }


def redact_enhanced_pii(
    text: str,
    spans: list[EnhancedSpan],
    strategy: str = "replace",
    custom_masks: dict[str, str] | None = None,
    preserve_format: bool = False,
) -> tuple[str, dict[str, int]]:
    """Convenience function for enhanced PII redaction."""
    redactor = EnhancedRedactor()
    return redactor.redact(text, spans, strategy, custom_masks, preserve_format)


def redact_with_metadata(
    text: str,
    detection_result: PIIDetectionResult,
    strategy: str = "replace",
    custom_masks: dict[str, str] | None = None,
    preserve_format: bool = False,
) -> tuple[str, dict[str, any]]:
    """Convenience function for redaction with metadata."""
    redactor = EnhancedRedactor()
    return redactor.redact_with_metadata(text, detection_result, strategy, custom_masks, preserve_format)
