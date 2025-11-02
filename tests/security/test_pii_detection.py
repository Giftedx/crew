"""Security tests for PII detection and redaction."""
from __future__ import annotations
from platform.core.privacy.privacy_filter import filter_text

class TestPIIDetection:
    """Test PII detection and redaction functionality."""

    def test_email_detection_and_redaction(self):
        """Test detection and redaction of email addresses."""
        text_with_email = 'Contact us at john.doe@example.com for more information.'
        redacted_text, report = filter_text(text_with_email)
        assert 'john.doe@example.com' not in redacted_text
        assert '[EMAIL]' in redacted_text or '[REDACTED]' in redacted_text
        assert len(report.found) > 0
        assert any((span.type == 'email' for span in report.found))

    def test_phone_number_detection_and_redaction(self):
        """Test detection and redaction of phone numbers."""
        text_with_phone = 'Call us at (555) 123-4567 or 555-123-4567 for support.'
        redacted_text, report = filter_text(text_with_phone)
        assert '(555) 123-4567' not in redacted_text
        assert '555-123-4567' not in redacted_text
        assert '[PHONE]' in redacted_text or '[REDACTED]' in redacted_text
        assert len(report.found) > 0
        assert any((span.type == 'phone' for span in report.found))

    def test_ssn_detection_and_redaction(self):
        """Test detection and redaction of Social Security Numbers."""
        text_with_ssn = 'SSN: 123-45-6789 is required for verification.'
        redacted_text, report = filter_text(text_with_ssn)
        assert '123-45-6789' not in redacted_text
        assert '[SSN]' in redacted_text or '[REDACTED]' in redacted_text
        assert len(report.found) > 0
        assert any((span.type == 'ssn' for span in report.found))

    def test_credit_card_detection_and_redaction(self):
        """Test detection and redaction of credit card numbers."""
        text_with_cc = 'Payment: 4111-1111-1111-1111 or 4111111111111111'
        redacted_text, report = filter_text(text_with_cc)
        assert '4111-1111-1111-1111' not in redacted_text
        assert '4111111111111111' not in redacted_text
        assert '[CREDIT_CARD]' in redacted_text or '[REDACTED]' in redacted_text
        assert len(report.found) > 0
        assert any((span.type == 'credit_card' for span in report.found))

    def test_ip_address_detection_and_redaction(self):
        """Test detection and redaction of IP addresses."""
        text_with_ip = 'Server at 192.168.1.1 and 10.0.0.1 is responding.'
        redacted_text, report = filter_text(text_with_ip)
        assert '192.168.1.1' not in redacted_text
        assert '10.0.0.1' not in redacted_text
        assert '[IP]' in redacted_text or '[REDACTED]' in redacted_text
        assert len(report.found) > 0
        assert any((span.type == 'ip_address' for span in report.found))

    def test_no_pii_detection(self):
        """Test that text without PII is not modified."""
        clean_text = 'This is a normal text without any personal information.'
        redacted_text, report = filter_text(clean_text)
        assert redacted_text == clean_text
        assert len(report.found) == 0

    def test_multiple_pii_types(self):
        """Test detection of multiple PII types in one text."""
        text_with_multiple_pii = 'Contact john@example.com at (555) 123-4567. SSN: 123-45-6789. Payment: 4111-1111-1111-1111'
        redacted_text, report = filter_text(text_with_multiple_pii)
        assert 'john@example.com' not in redacted_text
        assert '(555) 123-4567' not in redacted_text
        assert '123-45-6789' not in redacted_text
        assert '4111-1111-1111-1111' not in redacted_text
        assert len(report.found) >= 4

    def test_edge_cases(self):
        """Test edge cases in PII detection."""
        redacted_text, report = filter_text('')
        assert redacted_text == ''
        assert len(report.found) == 0
        redacted_text, report = filter_text('   \n\t   ')
        assert redacted_text.strip() == ''
        assert len(report.found) == 0
        text_with_false_positives = 'The number 123 is not a SSN.'
        redacted_text, report = filter_text(text_with_false_positives)
        assert '123' in redacted_text

    def test_redaction_quality(self):
        """Test that redaction maintains text readability."""
        text_with_pii = 'Email john@example.com and call (555) 123-4567.'
        redacted_text, _report = filter_text(text_with_pii)
        assert 'Email' in redacted_text
        assert 'and call' in redacted_text
        assert '[EMAIL]' in redacted_text or '[REDACTED]' in redacted_text
        assert '[PHONE]' in redacted_text or '[REDACTED]' in redacted_text

    def test_tenant_specific_policy(self):
        """Test tenant-specific PII policy overrides."""
        text_with_pii = 'Contact john@example.com for support.'
        tenant_context = {'tenant': 'test_tenant'}
        redacted_text, report = filter_text(text_with_pii, context=tenant_context)
        assert 'john@example.com' not in redacted_text
        assert len(report.found) > 0