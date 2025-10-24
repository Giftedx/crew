"""Comprehensive tests for enhanced PII detection and redaction."""

from src.core.privacy.enhanced_pii_detector import (
    EnhancedPIIDetector,
    PIIDetectionResult,
    validate_pii_patterns,
)
from src.core.privacy.enhanced_redactor import (
    EnhancedRedactor,
    redact_enhanced_pii,
    redact_with_metadata,
)


class TestEnhancedPIIDetector:
    """Test enhanced PII detector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EnhancedPIIDetector()

    def test_email_detection(self):
        """Test email detection patterns."""
        test_cases = [
            ("test@example.com", "email"),
            ("user.name+tag@domain.co.uk", "email"),
            ("admin@company.org", "email"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"Email not detected in: {text}"

    def test_phone_detection(self):
        """Test phone number detection patterns."""
        test_cases = [
            ("555-123-4567", "phone"),
            ("(555) 123-4567", "phone"),
            ("+1-555-123-4567", "phone"),
            ("555.123.4567", "phone"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"Phone not detected in: {text}"

    def test_credit_card_detection(self):
        """Test credit card detection patterns."""
        test_cases = [
            ("4111-1111-1111-1111", "credit_card"),
            ("4111 1111 1111 1111", "credit_card"),
            ("4111111111111111", "credit_card"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"Credit card not detected in: {text}"

    def test_ssn_detection(self):
        """Test SSN detection patterns."""
        test_cases = [
            ("123-45-6789", "ssn"),
            ("123.45.6789", "ssn"),
            ("123456789", "ssn"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"SSN not detected in: {text}"

    def test_ip_detection(self):
        """Test IP address detection patterns."""
        test_cases = [
            ("192.168.1.1", "ip"),
            ("10.0.0.1", "ip"),
            ("172.16.0.1", "ip"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"IP not detected in: {text}"

    def test_address_detection(self):
        """Test address detection patterns."""
        test_cases = [
            ("123 Main Street", "address"),
            ("456 Oak Avenue", "address"),
            ("789 Pine Road", "address"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"Address not detected in: {text}"

    def test_coordinates_detection(self):
        """Test coordinates detection patterns."""
        test_cases = [
            ("40.7128, -74.0060", "coordinates"),
            ("37.7749, -122.4194", "coordinates"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"Coordinates not detected in: {text}"

    def test_api_key_detection(self):
        """Test API key detection patterns."""
        test_cases = [
            ("sk-1234567890abcdef", "api_key"),
            ("pk_test_1234567890abcdef", "api_key"),
            ("ak_1234567890abcdef", "api_key"),
        ]

        for text, expected_type in test_cases:
            result = self.detector.detect(text)
            found_types = [span.type for span in result.spans]
            assert expected_type in found_types, f"API key not detected in: {text}"

    def test_risk_level_assignment(self):
        """Test risk level assignment for different PII types."""
        test_cases = [
            ("123-45-6789", "critical"),  # SSN
            ("4111-1111-1111-1111", "critical"),  # Credit card
            ("test@example.com", "high"),  # Email
            ("555-123-4567", "high"),  # Phone
            ("123 Main Street", "medium"),  # Address
        ]

        for text, expected_risk in test_cases:
            result = self.detector.detect(text)
            if result.spans:
                assert result.spans[0].risk_level == expected_risk, f"Wrong risk level for: {text}"

    def test_confidence_scoring(self):
        """Test confidence scoring for different PII types."""
        result = self.detector.detect("test@example.com")

        if result.spans:
            assert result.spans[0].confidence > 0.8, "Email should have high confidence"

    def test_context_extraction(self):
        """Test context extraction around detected PII."""
        text = "Please contact me at test@example.com for more information."
        result = self.detector.detect(text)

        if result.spans:
            context = result.spans[0].context
            assert "test@example.com" in context, "Context should contain the detected PII"

    def test_overlapping_spans_removal(self):
        """Test removal of overlapping spans."""
        # Create overlapping spans manually
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 10, "test@test.com", 0.9, "low"),
            EnhancedSpan("email", 5, 15, "test.com", 0.7, "low"),  # Overlaps with first
        ]

        # Test removal
        non_overlapping = self.detector._remove_overlapping_spans(spans)
        assert len(non_overlapping) == 1, "Should remove overlapping spans"
        assert non_overlapping[0].confidence == 0.9, "Should keep highest confidence span"

    def test_detection_result_metadata(self):
        """Test detection result metadata."""
        text = "Contact me at test@example.com or call 555-123-4567"
        result = self.detector.detect(text)

        assert result.total_spans > 0, "Should detect PII"
        assert result.confidence_score > 0, "Should have confidence score"
        assert result.processing_time > 0, "Should have processing time"
        assert "high" in result.risk_summary, "Should have risk summary"

    def test_get_detection_stats(self):
        """Test detection statistics."""
        stats = self.detector.get_detection_stats()

        assert "pattern_count" in stats
        assert "pii_types" in stats
        assert "ml_enabled" in stats
        assert "confidence_scores" in stats

    def test_validate_pii_patterns(self):
        """Test PII pattern validation."""
        result = validate_pii_patterns()
        assert result.success, "Pattern validation should succeed"

    def test_empty_text_handling(self):
        """Test handling of empty text."""
        result = self.detector.detect("")
        assert result.total_spans == 0, "Empty text should have no spans"
        assert result.confidence_score == 0.0, "Empty text should have zero confidence"

    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text."""
        result = self.detector.detect("   \n\t   ")
        assert result.total_spans == 0, "Whitespace-only text should have no spans"


class TestEnhancedRedactor:
    """Test enhanced redactor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.redactor = EnhancedRedactor()

    def test_replace_strategy(self):
        """Test simple replacement strategy."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        redacted_text, stats = self.redactor.redact("test@example.com", spans, "replace")

        assert "[EMAIL_REDACTED]" in redacted_text, "Should replace with default mask"
        assert stats["email"] == 1, "Should count redaction"

    def test_hash_strategy(self):
        """Test hash-based redaction strategy."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        redacted_text, stats = self.redactor.redact("test@example.com", spans, "hash")

        assert "EMAIL_" in redacted_text, "Should use hash-based mask"
        assert stats["email"] == 1, "Should count redaction"

    def test_partial_strategy(self):
        """Test partial redaction strategy."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        redacted_text, stats = self.redactor.redact("test@example.com", spans, "partial")

        assert "t***@example.com" in redacted_text, "Should show partial email"
        assert stats["email"] == 1, "Should count redaction"

    def test_contextual_strategy(self):
        """Test contextual redaction strategy."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("ssn", 0, 11, "123-45-6789", 0.99, "critical"),
        ]

        redacted_text, stats = self.redactor.redact("123-45-6789", spans, "contextual")

        assert "SSN_REDACTED" in redacted_text, "Should fully redact critical PII"
        assert stats["ssn"] == 1, "Should count redaction"

    def test_custom_masks(self):
        """Test custom masking."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        custom_masks = {"email": "[CUSTOM_EMAIL_MASK]"}
        redacted_text, stats = self.redactor.redact("test@example.com", spans, "replace", custom_masks)

        assert "[CUSTOM_EMAIL_MASK]" in redacted_text, "Should use custom mask"
        assert stats["email"] == 1, "Should count redaction"

    def test_preserve_format(self):
        """Test format preservation."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("phone", 0, 12, "555-123-4567", 0.9, "high"),
        ]

        redacted_text, stats = self.redactor.redact("555-123-4567", spans, "partial", preserve_format=True)

        assert "***-***-4567" in redacted_text, "Should preserve phone format"
        assert stats["phone"] == 1, "Should count redaction"

    def test_redact_with_metadata(self):
        """Test redaction with comprehensive metadata."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        detection_result = PIIDetectionResult(
            spans=spans,
            total_spans=1,
            risk_summary={"high": 1, "medium": 0, "low": 0, "critical": 0},
            confidence_score=0.9,
            processing_time=0.001,
        )

        redacted_text, metadata = self.redactor.redact_with_metadata("test@example.com", detection_result, "replace")

        assert "[EMAIL_REDACTED]" in redacted_text, "Should redact email"
        assert metadata["total_redactions"] == 1, "Should count redactions"
        assert metadata["risk_redactions"]["high"] == 1, "Should count risk redactions"
        assert metadata["strategy_used"] == "replace", "Should record strategy"

    def test_validate_redaction(self):
        """Test redaction validation."""
        original = "Contact me at test@example.com"
        redacted = "Contact me at [EMAIL_REDACTED]"

        result = self.redactor.validate_redaction(original, redacted)
        assert result.success, "Should validate successful redaction"

    def test_validate_redaction_failure(self):
        """Test redaction validation failure."""
        original = "Contact me at test@example.com"
        redacted = "Contact me at test@example.com"  # No redaction

        result = self.redactor.validate_redaction(original, redacted)
        assert not result.success, "Should fail validation for no redaction"

    def test_get_redaction_stats(self):
        """Test redaction statistics."""
        stats = self.redactor.get_redaction_stats()

        assert "strategies_available" in stats
        assert "default_masks" in stats
        assert "supported_pii_types" in stats

    def test_multiple_spans_redaction(self):
        """Test redaction of multiple PII spans."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
            EnhancedSpan("phone", 20, 32, "555-123-4567", 0.9, "high"),
        ]

        text = "test@example.com and 555-123-4567"
        redacted_text, stats = self.redactor.redact(text, spans, "replace")

        assert "[EMAIL_REDACTED]" in redacted_text, "Should redact email"
        assert "[PHONE_REDACTED]" in redacted_text, "Should redact phone"
        assert stats["email"] == 1, "Should count email redaction"
        assert stats["phone"] == 1, "Should count phone redaction"

    def test_convenience_functions(self):
        """Test convenience functions."""
        from src.core.privacy.enhanced_pii_detector import EnhancedSpan

        spans = [
            EnhancedSpan("email", 0, 16, "test@example.com", 0.9, "high"),
        ]

        # Test redact_enhanced_pii
        redacted_text, _stats = redact_enhanced_pii("test@example.com", spans, "replace")
        assert "[EMAIL_REDACTED]" in redacted_text, "Convenience function should work"

        # Test redact_with_metadata

        detection_result = PIIDetectionResult(
            spans=spans,
            total_spans=1,
            risk_summary={"high": 1, "medium": 0, "low": 0, "critical": 0},
            confidence_score=0.9,
            processing_time=0.001,
        )

        redacted_text, metadata = redact_with_metadata("test@example.com", detection_result, "replace")
        assert "[EMAIL_REDACTED]" in redacted_text, "Metadata function should work"
        assert metadata["total_redactions"] == 1, "Should have metadata"
