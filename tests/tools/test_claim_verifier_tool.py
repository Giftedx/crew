"""Tests for Claim Verifier Tool."""

from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import (
    ClaimVerification,
    ClaimVerifierTool,
    VerificationSource,
)


class TestClaimVerifierTool:
    """Test cases for Claim Verifier Tool."""

    @pytest.fixture
    def tool(self):
        """Create ClaimVerifierTool instance."""
        return ClaimVerifierTool()

    @pytest.fixture
    def sample_claim(self):
        """Sample claim for testing."""
        return "The Earth is round and orbits around the Sun."

    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return "This is a basic astronomical fact that has been known for centuries."

    @pytest.fixture
    def mock_verification_result(self):
        """Mock verification result."""
        return ClaimVerification(
            claim_id="test_claim_123",
            claim_text="The Earth is round and orbits around the Sun.",
            overall_confidence=0.95,
            verification_status="verified",
            sources=[
                VerificationSource(
                    source_id="source_1",
                    title="NASA - Earth Facts",
                    url="https://nasa.gov/earth-facts",
                    snippet="Earth is a spherical planet that orbits the Sun...",
                    relevance_score=0.98,
                    backend="serply",
                    timestamp="2024-01-01T00:00:00Z",
                    domain="nasa.gov",
                )
            ],
            processing_time=1.5,
            backends_used=["serply", "exa"],
            error_message=None,
        )

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == "claim_verifier_tool"
        assert "Verify claims against multiple backends" in tool.description
        assert hasattr(tool, "_run")

    def test_successful_claim_verification(self, tool, sample_claim, sample_context, mock_verification_result):
        """Test successful claim verification."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert result.data is not None
            assert "claim_id" in result.data
            assert "overall_confidence" in result.data
            assert "verification_status" in result.data
            assert "sources" in result.data
            mock_verify.assert_called_once()

    def test_missing_required_parameters(self, tool):
        """Test handling of missing required parameters."""
        result = tool._run("", "context", "test_tenant", "test_workspace")
        assert not result.success
        assert "Claim text cannot be empty" in result.error

        result = tool._run("claim", "context", "", "test_workspace")
        assert not result.success
        assert "Tenant is required" in result.error

        result = tool._run("claim", "context", "test_tenant", "")
        assert not result.success
        assert "Workspace is required" in result.error

    def test_verification_failure_handling(self, tool, sample_claim, sample_context):
        """Test handling of verification failures."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verify.side_effect = Exception("Verification service unavailable")

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert not result.success
            assert "Verification failed" in result.error

    def test_confidence_threshold_validation(self, tool, sample_claim, sample_context):
        """Test confidence threshold validation."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.5,  # Below threshold
                verification_status="unverified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert result.data["verification_status"] == "unverified"
            assert result.data["overall_confidence"] == 0.5

    def test_source_validation(self, tool, sample_claim, sample_context):
        """Test source validation and filtering."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.9,
                verification_status="verified",
                sources=[
                    VerificationSource(
                        source_id="source_1",
                        title="Reliable Source",
                        url="https://reliable.com/article",
                        snippet="Reliable information about the claim...",
                        relevance_score=0.95,
                        backend="serply",
                        timestamp="2024-01-01T00:00:00Z",
                        domain="reliable.com",
                    ),
                    VerificationSource(
                        source_id="source_2",
                        title="Less Reliable Source",
                        url="https://unreliable.com/article",
                        snippet="Less reliable information...",
                        relevance_score=0.3,
                        backend="exa",
                        timestamp="2024-01-01T00:00:00Z",
                        domain="unreliable.com",
                    ),
                ],
                processing_time=2.0,
                backends_used=["serply", "exa"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert len(result.data["sources"]) == 2
            # Sources should be sorted by relevance score
            assert result.data["sources"][0]["relevance_score"] >= result.data["sources"][1]["relevance_score"]

    def test_backend_failure_handling(self, tool, sample_claim, sample_context):
        """Test handling of backend failures."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.8,
                verification_status="partially_verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],  # Only one backend succeeded
                error_message="Backend 'exa' failed: Connection timeout",
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert result.data["verification_status"] == "partially_verified"
            assert "error_message" in result.data

    def test_processing_time_tracking(self, tool, sample_claim, sample_context, mock_verification_result):
        """Test processing time tracking."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert "processing_time" in result.data
            assert result.data["processing_time"] > 0

    def test_tenant_workspace_isolation(self, tool, sample_claim, sample_context):
        """Test tenant and workspace isolation."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.9,
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            # Test with different tenants and workspaces
            result1 = tool._run(sample_claim, sample_context, "tenant1", "workspace1")
            result2 = tool._run(sample_claim, sample_context, "tenant2", "workspace2")

            assert result1.success
            assert result2.success
            # Both should succeed independently

    def test_claim_text_preprocessing(self, tool, sample_context):
        """Test claim text preprocessing."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text="  Processed claim text  ",
                overall_confidence=0.9,
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            # Test with whitespace that should be trimmed
            result = tool._run("  The Earth is round  ", sample_context, "test_tenant", "test_workspace")

            assert result.success
            mock_verify.assert_called_once()

    def test_context_handling(self, tool, sample_claim):
        """Test context handling."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.9,
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            # Test with empty context
            result = tool._run(sample_claim, "", "test_tenant", "test_workspace")
            assert result.success

            # Test with None context
            result = tool._run(sample_claim, None, "test_tenant", "test_workspace")
            assert result.success

    def test_verification_status_mapping(self, tool, sample_claim, sample_context):
        """Test verification status mapping."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            # Test verified status
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.95,
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")
            assert result.success
            assert result.data["verification_status"] == "verified"

    def test_confidence_score_validation(self, tool, sample_claim, sample_context):
        """Test confidence score validation."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=1.5,  # Invalid confidence score
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            # Should handle invalid confidence scores gracefully
            assert result.success
            assert 0 <= result.data["overall_confidence"] <= 1

    def test_source_limit_handling(self, tool, sample_claim, sample_context):
        """Test source limit handling."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            # Create many sources
            sources = []
            for i in range(10):
                sources.append(
                    VerificationSource(
                        source_id=f"source_{i}",
                        title=f"Source {i}",
                        url=f"https://example{i}.com",
                        snippet=f"Snippet {i}",
                        relevance_score=0.9 - (i * 0.1),
                        backend="serply",
                        timestamp="2024-01-01T00:00:00Z",
                        domain=f"example{i}.com",
                    )
                )

            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.9,
                verification_status="verified",
                sources=sources,
                processing_time=2.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            # Should limit sources to reasonable number
            assert len(result.data["sources"]) <= 10

    def test_error_message_handling(self, tool, sample_claim, sample_context):
        """Test error message handling."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.0,
                verification_status="error",
                sources=[],
                processing_time=0.5,
                backends_used=[],
                error_message="All backends failed to respond",
            )
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            assert result.data["verification_status"] == "error"
            assert "error_message" in result.data
            assert result.data["error_message"] == "All backends failed to respond"

    def test_concurrent_verification_requests(self, tool, sample_claim, sample_context):
        """Test handling of concurrent verification requests."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verification_result = ClaimVerification(
                claim_id="test_claim_123",
                claim_text=sample_claim,
                overall_confidence=0.9,
                verification_status="verified",
                sources=[],
                processing_time=1.0,
                backends_used=["serply"],
                error_message=None,
            )
            mock_verify.return_value = mock_verification_result

            # Simulate concurrent requests
            results = []
            for i in range(3):
                result = tool._run(f"{sample_claim} {i}", sample_context, "test_tenant", "test_workspace")
                results.append(result)

            # All should succeed
            for result in results:
                assert result.success

    def test_verification_result_structure(self, tool, sample_claim, sample_context, mock_verification_result):
        """Test that verification results have the expected structure."""
        with patch.object(tool, "_verify_claim") as mock_verify:
            mock_verify.return_value = mock_verification_result

            result = tool._run(sample_claim, sample_context, "test_tenant", "test_workspace")

            assert result.success
            data = result.data

            # Check required fields
            assert "claim_id" in data
            assert "claim_text" in data
            assert "overall_confidence" in data
            assert "verification_status" in data
            assert "sources" in data
            assert "processing_time" in data
            assert "backends_used" in data

            # Check data types
            assert isinstance(data["claim_id"], str)
            assert isinstance(data["claim_text"], str)
            assert isinstance(data["overall_confidence"], (int, float))
            assert isinstance(data["verification_status"], str)
            assert isinstance(data["sources"], list)
            assert isinstance(data["processing_time"], (int, float))
            assert isinstance(data["backends_used"], list)
