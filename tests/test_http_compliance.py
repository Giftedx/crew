"""Tests for HTTP compliance enforcement."""

import pytest

from src.ultimate_discord_intelligence_bot.core.http_compliance_audit import HTTPComplianceAuditor


class TestHTTPComplianceAuditor:
    """Test suite for HTTP compliance auditing."""

    @pytest.fixture
    def auditor(self, tmp_path):
        """Create an auditor instance with a temporary directory."""
        return HTTPComplianceAuditor(tmp_path)

    def test_detect_direct_import(self, auditor, tmp_path):
        """Test detection of direct requests import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import requests\nresponse = requests.get('http://example.com')")

        violations = auditor._check_file(test_file)

        assert len(violations) == 2
        assert "Direct import of requests" in violations[0][2]
        assert "Direct requests method call" in violations[1][2]

    def test_detect_from_import(self, auditor, tmp_path):
        """Test detection of from requests import."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from requests import Session\n")

        violations = auditor._check_file(test_file)

        assert len(violations) == 1
        assert "Direct import from requests" in violations[0][2]

    def test_no_violations_with_http_utils(self, auditor, tmp_path):
        """Test that http_utils usage is compliant."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
from src.ultimate_discord_intelligence_bot.core.http_utils import resilient_get

response = resilient_get('http://example.com')
""")

        violations = auditor._check_file(test_file)

        assert len(violations) == 0

    def test_skip_http_utils_file(self, auditor, tmp_path):
        """Test that http_utils.py itself is skipped."""
        test_file = tmp_path / "http_utils.py"
        test_file.write_text("import requests  # This is allowed in http_utils")

        result = auditor.audit_files()

        assert result.success

    def test_generate_fixes(self, auditor):
        """Test fix generation for violations."""
        auditor.violations = [
            ("test.py", 1, "Direct import of requests"),
            ("module.py", 10, "Direct requests method call"),
        ]

        fixes = auditor.generate_fixes()

        assert len(fixes) == 2
        assert "resilient_get" in fixes[0]
        assert "resilient_post" in fixes[0]
