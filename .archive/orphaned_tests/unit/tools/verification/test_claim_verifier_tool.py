from unittest.mock import Mock, patch

from src.ultimate_discord_intelligence_bot.tools.claim_verifier_tool import (
    ClaimVerification,
    ClaimVerifierInput,
    ClaimVerifierTool,
    VerificationSource,
)


class TestClaimVerifierInput:
    """Test the ClaimVerifierInput schema."""

    def test_valid_input(self):
        """Test valid input creation."""
        input_data = ClaimVerifierInput(
            claim_text="The Triller lawsuit is progressing well",
            context="Ethan mentioned this in his latest podcast",
            max_sources=3,
            min_confidence=0.8,
            backends=["serply", "exa"],
        )

        assert input_data.claim_text == "The Triller lawsuit is progressing well"
        assert input_data.context == "Ethan mentioned this in his latest podcast"
        assert input_data.max_sources == 3
        assert input_data.min_confidence == 0.8
        assert input_data.backends == ["serply", "exa"]

    def test_default_values(self):
        """Test default values."""
        input_data = ClaimVerifierInput(claim_text="Test claim")

        assert input_data.claim_text == "Test claim"
        assert input_data.context == ""
        assert input_data.max_sources == 5
        assert input_data.min_confidence == 0.7
        assert input_data.backends == ["serply", "exa", "perplexity"]


class TestVerificationSource:
    """Test the VerificationSource dataclass."""

    def test_verification_source_creation(self):
        """Test creating a VerificationSource."""
        source = VerificationSource(
            source_id="test_001",
            title="Test Article",
            url="https://example.com/test",
            snippet="This is a test snippet",
            relevance_score=0.85,
            backend="serply",
            timestamp="2024-02-15T10:30:00Z",
            domain="example.com",
        )

        assert source.source_id == "test_001"
        assert source.title == "Test Article"
        assert source.url == "https://example.com/test"
        assert source.snippet == "This is a test snippet"
        assert source.relevance_score == 0.85
        assert source.backend == "serply"
        assert source.timestamp == "2024-02-15T10:30:00Z"
        assert source.domain == "example.com"


class TestClaimVerification:
    """Test the ClaimVerification dataclass."""

    def test_claim_verification_creation(self):
        """Test creating a ClaimVerification."""
        sources = [
            VerificationSource(
                source_id="test_001",
                title="Test Article",
                url="https://example.com/test",
                snippet="Test snippet",
                relevance_score=0.85,
                backend="serply",
                timestamp="2024-02-15T10:30:00Z",
                domain="example.com",
            )
        ]

        verification = ClaimVerification(
            claim_id="claim_1234",
            claim_text="Test claim",
            verification_status="verified",
            confidence_score=0.85,
            sources=sources,
            supporting_evidence=["Evidence 1", "Evidence 2"],
            contradicting_evidence=["Contradiction 1"],
            verification_summary="Claim verified with high confidence",
            backend_performance={"serply": {"sources_found": 1, "latency_seconds": 0.5, "success": True}},
        )

        assert verification.claim_id == "claim_1234"
        assert verification.claim_text == "Test claim"
        assert verification.verification_status == "verified"
        assert verification.confidence_score == 0.85
        assert len(verification.sources) == 1
        assert len(verification.supporting_evidence) == 2
        assert len(verification.contradicting_evidence) == 1
        assert verification.verification_summary == "Claim verified with high confidence"


class TestClaimVerifierTool:
    """Test the ClaimVerifierTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ClaimVerifierTool()
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "claim_verifier_tool"
        assert "Verify claims against multiple backends" in self.tool.description
        assert self.tool.args_schema == ClaimVerifierInput
        assert "serply" in self.tool.backends
        assert "exa" in self.tool.backends
        assert "perplexity" in self.tool.backends

    def test_parse_claim(self):
        """Test claim parsing."""
        claim_text = "The Triller lawsuit is progressing well"
        context = "Ethan mentioned this in his latest podcast"

        parsed = self.tool._parse_claim(claim_text, context)

        assert parsed["text"] == claim_text
        assert parsed["context"] == context
        assert "triller" in parsed["keywords"]
        assert "lawsuit" in parsed["keywords"]
        assert isinstance(parsed["keywords"], list)
        assert isinstance(parsed["entities"], list)
        assert isinstance(parsed["temporal_indicators"], list)

    def test_verify_with_serply(self):
        """Test Serply backend verification."""
        parsed_claim = {
            "text": "Test claim",
            "context": "Test context",
            "keywords": ["test", "claim"],
            "entities": [],
            "temporal_indicators": [],
        }

        sources = self.tool._verify_with_serply(parsed_claim, max_sources=2)

        assert len(sources) <= 2
        assert all(isinstance(source, VerificationSource) for source in sources)
        assert all(source.backend == "serply" for source in sources)
        assert all(source.relevance_score > 0 for source in sources)

    def test_verify_with_exa(self):
        """Test EXA backend verification."""
        parsed_claim = {
            "text": "Test claim",
            "context": "Test context",
            "keywords": ["test", "claim"],
            "entities": [],
            "temporal_indicators": [],
        }

        sources = self.tool._verify_with_exa(parsed_claim, max_sources=2)

        assert len(sources) <= 2
        assert all(isinstance(source, VerificationSource) for source in sources)
        assert all(source.backend == "exa" for source in sources)
        assert all(source.relevance_score > 0 for source in sources)

    def test_verify_with_perplexity(self):
        """Test Perplexity backend verification."""
        parsed_claim = {
            "text": "Test claim",
            "context": "Test context",
            "keywords": ["test", "claim"],
            "entities": [],
            "temporal_indicators": [],
        }

        sources = self.tool._verify_with_perplexity(parsed_claim, max_sources=1)

        assert len(sources) <= 1
        assert all(isinstance(source, VerificationSource) for source in sources)
        assert all(source.backend == "perplexity" for source in sources)
        assert all(source.relevance_score > 0 for source in sources)

    def test_analyze_verification_verified(self):
        """Test verification analysis with verified status."""
        sources = [
            VerificationSource(
                source_id="test_001",
                title="Test Article 1",
                url="https://example.com/test1",
                snippet="Supporting evidence 1",
                relevance_score=0.85,
                backend="serply",
                timestamp="2024-02-15T10:30:00Z",
                domain="example.com",
            ),
            VerificationSource(
                source_id="test_002",
                title="Test Article 2",
                url="https://example.com/test2",
                snippet="Supporting evidence 2",
                relevance_score=0.80,
                backend="exa",
                timestamp="2024-02-15T11:30:00Z",
                domain="example.com",
            ),
        ]

        parsed_claim = {
            "text": "Test claim",
            "context": "",
            "keywords": [],
            "entities": [],
            "temporal_indicators": [],
        }
        result = self.tool._analyze_verification(parsed_claim, sources, min_confidence=0.7)

        assert result["status"] == "verified"
        assert result["confidence"] >= 0.7
        assert len(result["supporting_evidence"]) >= 2
        assert len(result["sources"]) == 2

    def test_analyze_verification_insufficient_evidence(self):
        """Test verification analysis with insufficient evidence."""
        sources = []

        parsed_claim = {
            "text": "Test claim",
            "context": "",
            "keywords": [],
            "entities": [],
            "temporal_indicators": [],
        }
        result = self.tool._analyze_verification(parsed_claim, sources, min_confidence=0.7)

        assert result["status"] == "insufficient_evidence"
        assert result["confidence"] == 0.0
        assert len(result["supporting_evidence"]) == 0
        assert len(result["sources"]) == 0

    def test_analyze_verification_unverified(self):
        """Test verification analysis with unverified status."""
        sources = [
            VerificationSource(
                source_id="test_001",
                title="Test Article",
                url="https://example.com/test",
                snippet="Weak evidence",
                relevance_score=0.65,  # Below min_confidence
                backend="serply",
                timestamp="2024-02-15T10:30:00Z",
                domain="example.com",
            )
        ]

        parsed_claim = {
            "text": "Test claim",
            "context": "",
            "keywords": [],
            "entities": [],
            "temporal_indicators": [],
        }
        result = self.tool._analyze_verification(parsed_claim, sources, min_confidence=0.7)

        # With one source below confidence threshold, it should be "disputed" not "insufficient_evidence"
        assert result["status"] == "disputed"
        assert result["confidence"] == 0.8
        assert len(result["supporting_evidence"]) == 0

    def test_generate_verification_summary(self):
        """Test verification summary generation."""
        verification_result = {
            "status": "verified",
            "confidence": 0.85,
            "sources": [Mock()],
            "supporting_evidence": ["Evidence 1", "Evidence 2"],
            "contradicting_evidence": [],
        }

        backend_performance = {
            "serply": {"sources_found": 2, "latency_seconds": 0.5, "success": True},
            "exa": {"sources_found": 1, "latency_seconds": 0.3, "success": True},
        }

        summary = self.tool._generate_verification_summary(verification_result, backend_performance)

        assert "VERIFIED" in summary
        assert "0.85" in summary
        assert "Sources analyzed: 1" in summary
        assert "Supporting evidence found: 2 sources" in summary
        assert "serply, exa" in summary

    def test_serialize_verification(self):
        """Test verification serialization."""
        sources = [
            VerificationSource(
                source_id="test_001",
                title="Test Article",
                url="https://example.com/test",
                snippet="Test snippet",
                relevance_score=0.85,
                backend="serply",
                timestamp="2024-02-15T10:30:00Z",
                domain="example.com",
            )
        ]

        verification = ClaimVerification(
            claim_id="claim_1234",
            claim_text="Test claim",
            verification_status="verified",
            confidence_score=0.85,
            sources=sources,
            supporting_evidence=["Evidence 1"],
            contradicting_evidence=[],
            verification_summary="Test summary",
            backend_performance={"serply": {"sources_found": 1, "latency_seconds": 0.5, "success": True}},
        )

        serialized = self.tool._serialize_verification(verification)

        assert serialized["claim_id"] == "claim_1234"
        assert serialized["claim_text"] == "Test claim"
        assert serialized["verification_status"] == "verified"
        assert serialized["confidence_score"] == 0.85
        assert len(serialized["sources"]) == 1
        assert serialized["sources"][0]["source_id"] == "test_001"
        assert serialized["sources"][0]["backend"] == "serply"
        assert len(serialized["supporting_evidence"]) == 1
        assert len(serialized["contradicting_evidence"]) == 0
        assert serialized["verification_summary"] == "Test summary"

    def test_run_success(self):
        """Test successful claim verification."""
        result = self.tool._run(
            claim_text="The Triller lawsuit is progressing well",
            context="Ethan mentioned this in his latest podcast",
            max_sources=3,
            min_confidence=0.7,
            backends=["serply", "exa"],
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        assert "data" in result.data
        data = result.data["data"]
        assert "claim_id" in data
        assert "claim_text" in data
        assert "verification_status" in data
        assert "confidence_score" in data
        assert "sources" in data
        assert "verification_summary" in data
        assert "backend_performance" in data

    def test_run_with_default_backends(self):
        """Test claim verification with default backends."""
        result = self.tool._run(
            claim_text="Test claim",
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert "backend_performance" in data
        # Should have tried all three default backends
        assert len(data["backend_performance"]) >= 1

    def test_run_with_invalid_backend(self):
        """Test claim verification with invalid backend."""
        result = self.tool._run(
            claim_text="Test claim",
            backends=["invalid_backend"],
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success  # Should still succeed but with warnings
        data = result.data["data"]
        assert "backend_performance" in data

    def test_run_claim_parsing_failure(self):
        """Test claim verification with parsing failure."""
        with patch.object(self.tool, "_parse_claim", return_value=None):
            result = self.tool._run(
                claim_text="Test claim",
                tenant=self.tenant,
                workspace=self.workspace,
            )

            assert not result.success
            assert "Failed to parse claim text" in result.error

    def test_run_backend_failure(self):
        """Test claim verification with backend failure."""
        # Patch the backend method directly in the backends dictionary
        original_method = self.tool.backends["serply"]
        self.tool.backends["serply"] = Mock(side_effect=Exception("API Error"))

        try:
            result = self.tool._run(
                claim_text="Test claim",
                backends=["serply"],
                tenant=self.tenant,
                workspace=self.workspace,
            )

            assert result.success  # Should still succeed even with backend failure
            data = result.data["data"]
            assert "backend_performance" in data
            assert data["backend_performance"]["serply"]["success"] is False
            assert "API Error" in data["backend_performance"]["serply"]["error"]
        finally:
            # Restore the original method
            self.tool.backends["serply"] = original_method

    def test_run_general_exception(self):
        """Test claim verification with general exception."""
        with patch.object(self.tool, "_parse_claim", side_effect=Exception("Unexpected error")):
            result = self.tool._run(
                claim_text="Test claim",
                tenant=self.tenant,
                workspace=self.workspace,
            )

            assert not result.success
            assert "Claim verification failed: Unexpected error" in result.error
