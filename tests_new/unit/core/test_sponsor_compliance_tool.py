from datetime import datetime
from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.tools.sponsor_compliance_tool import (
    ComplianceReport,
    ComplianceViolation,
    DisclosureRecommendation,
    SponsorComplianceInput,
    SponsorComplianceTool,
    SponsorMention,
)


class TestSponsorComplianceInput:
    """Test the SponsorComplianceInput schema."""

    def test_valid_input(self):
        """Test valid input creation."""
        input_data = SponsorComplianceInput(
            episode_id="episode_123",
            content_text="Test content",
            enable_sponsor_detection=True,
            enable_compliance_check=True,
            enable_disclosure_generation=True,
            jurisdiction="US",
            platform="youtube",
        )

        assert input_data.episode_id == "episode_123"
        assert input_data.content_text == "Test content"
        assert input_data.enable_sponsor_detection is True
        assert input_data.enable_compliance_check is True
        assert input_data.enable_disclosure_generation is True
        assert input_data.jurisdiction == "US"
        assert input_data.platform == "youtube"

    def test_default_values(self):
        """Test default values."""
        input_data = SponsorComplianceInput(episode_id="episode_123")

        assert input_data.episode_id == "episode_123"
        assert input_data.content_text == ""
        assert input_data.enable_sponsor_detection is True
        assert input_data.enable_compliance_check is True
        assert input_data.enable_disclosure_generation is True
        assert input_data.jurisdiction == "US"
        assert input_data.platform == "youtube"


class TestSponsorMention:
    """Test the SponsorMention dataclass."""

    def test_sponsor_mention_creation(self):
        """Test creating a SponsorMention."""
        mention = SponsorMention(
            sponsor_name="NordVPN",
            mention_text="Thanks to NordVPN for sponsoring this episode",
            timestamp=120.0,
            confidence=0.85,
            mention_type="explicit",
            context="Before we get started, I want to thank our sponsor...",
            is_disclosed=True,
            disclosure_location="beginning",
        )

        assert mention.sponsor_name == "NordVPN"
        assert mention.mention_text == "Thanks to NordVPN for sponsoring this episode"
        assert mention.timestamp == 120.0
        assert mention.confidence == 0.85
        assert mention.mention_type == "explicit"
        assert mention.context == "Before we get started, I want to thank our sponsor..."
        assert mention.is_disclosed is True
        assert mention.disclosure_location == "beginning"


class TestComplianceViolation:
    """Test the ComplianceViolation dataclass."""

    def test_compliance_violation_creation(self):
        """Test creating a ComplianceViolation."""
        violation = ComplianceViolation(
            violation_type="missing_disclosure",
            severity="high",
            description="Sponsor mention lacks clear disclosure",
            timestamp=120.0,
            suggested_fix="Add clear disclosure before sponsor mention",
            ftc_guideline_reference="Clear and conspicuous disclosure required",
            penalty_risk="fine",
        )

        assert violation.violation_type == "missing_disclosure"
        assert violation.severity == "high"
        assert violation.description == "Sponsor mention lacks clear disclosure"
        assert violation.timestamp == 120.0
        assert violation.suggested_fix == "Add clear disclosure before sponsor mention"
        assert violation.ftc_guideline_reference == "Clear and conspicuous disclosure required"
        assert violation.penalty_risk == "fine"


class TestDisclosureRecommendation:
    """Test the DisclosureRecommendation dataclass."""

    def test_disclosure_recommendation_creation(self):
        """Test creating a DisclosureRecommendation."""
        recommendation = DisclosureRecommendation(
            disclosure_text="This video is sponsored by NordVPN",
            placement_location="beginning",
            placement_timestamp=110.0,
            reasoning="FTC guidelines recommend disclosure before sponsor mention",
            compliance_score=0.9,
            template_type="platform_specific",
        )

        assert recommendation.disclosure_text == "This video is sponsored by NordVPN"
        assert recommendation.placement_location == "beginning"
        assert recommendation.placement_timestamp == 110.0
        assert recommendation.reasoning == "FTC guidelines recommend disclosure before sponsor mention"
        assert recommendation.compliance_score == 0.9
        assert recommendation.template_type == "platform_specific"


class TestComplianceReport:
    """Test the ComplianceReport dataclass."""

    def test_compliance_report_creation(self):
        """Test creating a ComplianceReport."""
        report = ComplianceReport(
            episode_id="episode_123",
            analysis_timestamp=datetime.now(),
            sponsor_mentions=[],
            violations=[],
            recommendations=[],
            overall_compliance_score=0.85,
            risk_level="low",
            summary="Content appears compliant",
            next_steps=["No action needed"],
        )

        assert report.episode_id == "episode_123"
        assert isinstance(report.analysis_timestamp, datetime)
        assert report.sponsor_mentions == []
        assert report.violations == []
        assert report.recommendations == []
        assert report.overall_compliance_score == 0.85
        assert report.risk_level == "low"
        assert report.summary == "Content appears compliant"
        assert report.next_steps == ["No action needed"]


class TestSponsorComplianceTool:
    """Test the SponsorComplianceTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SponsorComplianceTool()
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"
        self.episode_id = "episode_123"

    def test_tool_initialization(self):
        """Test tool initialization."""
        assert self.tool.name == "sponsor_compliance_tool"
        assert "Analyze content for sponsor mentions" in self.tool.description
        assert self.tool.args_schema == SponsorComplianceInput

    def test_retrieve_episode_content(self):
        """Test episode content retrieval."""
        content = self.tool._retrieve_episode_content(self.episode_id, self.tenant, self.workspace)

        assert content is not None
        assert len(content) > 0
        assert "NordVPN" in content
        assert "sponsor" in content.lower()

    def test_split_content_into_segments(self):
        """Test content segmentation."""
        content = "Hello world. This is a test. Another sentence here."
        segments = self.tool._split_content_into_segments(content)

        assert len(segments) > 0
        assert all("text" in segment for segment in segments)
        assert all("timestamp" in segment for segment in segments)

    def test_extract_sponsor_name(self):
        """Test sponsor name extraction."""
        text = "Thanks to NordVPN for sponsoring this episode"
        sponsor_name = self.tool._extract_sponsor_name(text, "thanks to")

        assert sponsor_name == "NordVPN"

    def test_check_disclosure_presence(self):
        """Test disclosure presence checking."""
        text_with_disclosure = "This video is sponsored by NordVPN"
        text_without_disclosure = "Check out NordVPN"

        assert self.tool._check_disclosure_presence(text_with_disclosure) is True
        assert self.tool._check_disclosure_presence(text_without_disclosure) is False

    def test_determine_disclosure_location(self):
        """Test disclosure location determination."""
        text_with_beginning_disclosure = "Sponsored by NordVPN. Thanks to them for making this possible."
        text_with_middle_disclosure = "Thanks to NordVPN for sponsoring this episode"

        location1 = self.tool._determine_disclosure_location(text_with_beginning_disclosure, "thanks to")
        location2 = self.tool._determine_disclosure_location(text_with_middle_disclosure, "thanks to")

        assert location1 == "beginning"
        assert location2 == "none"  # No disclosure keywords before "thanks to"

    def test_check_deceptive_practices(self):
        """Test deceptive practices detection."""
        deceptive_content = "This miracle cure will guarantee results"
        normal_content = "This product works well for most people"

        assert self.tool._check_deceptive_practices(deceptive_content) is True
        assert self.tool._check_deceptive_practices(normal_content) is False

    def test_generate_disclosure_text(self):
        """Test disclosure text generation."""
        youtube_disclosure = self.tool._generate_disclosure_text("NordVPN", "youtube", "US")
        twitch_disclosure = self.tool._generate_disclosure_text("NordVPN", "twitch", "US")
        tiktok_disclosure = self.tool._generate_disclosure_text("NordVPN", "tiktok", "US")

        assert "This video is sponsored by NordVPN" in youtube_disclosure
        assert "Thanks to NordVPN" in twitch_disclosure
        assert "#ad #sponsored by NordVPN" in tiktok_disclosure

    def test_calculate_compliance_score(self):
        """Test compliance score calculation."""
        # Test with no sponsors
        score_no_sponsors = self.tool._calculate_compliance_score([], [])
        assert score_no_sponsors == 1.0

        # Test with disclosed sponsors
        disclosed_mention = SponsorMention(
            sponsor_name="NordVPN",
            mention_text="Sponsored by NordVPN",
            timestamp=120.0,
            confidence=0.85,
            mention_type="explicit",
            context="",
            is_disclosed=True,
            disclosure_location="beginning",
        )
        score_disclosed = self.tool._calculate_compliance_score([disclosed_mention], [])
        assert score_disclosed > 0.8

        # Test with violations
        violation = ComplianceViolation(
            violation_type="missing_disclosure",
            severity="high",
            description="Test violation",
            timestamp=120.0,
            suggested_fix="Add disclosure",
            ftc_guideline_reference="Test guideline",
            penalty_risk="fine",
        )
        score_with_violations = self.tool._calculate_compliance_score([disclosed_mention], [violation])
        assert score_with_violations <= score_disclosed  # Should be equal or less

    def test_determine_risk_level(self):
        """Test risk level determination."""
        # Test critical risk
        critical_violation = ComplianceViolation(
            violation_type="deceptive_practices",
            severity="critical",
            description="Test",
            timestamp=120.0,
            suggested_fix="Fix",
            ftc_guideline_reference="Test",
            penalty_risk="legal_action",
        )
        risk_critical = self.tool._determine_risk_level(0.9, [critical_violation])
        assert risk_critical == "critical"

        # Test low risk
        risk_low = self.tool._determine_risk_level(0.9, [])
        assert risk_low == "low"

    def test_generate_summary(self):
        """Test summary generation."""
        mention = SponsorMention(
            sponsor_name="NordVPN",
            mention_text="Sponsored by NordVPN",
            timestamp=120.0,
            confidence=0.85,
            mention_type="explicit",
            context="",
            is_disclosed=True,
            disclosure_location="beginning",
        )

        summary = self.tool._generate_summary([mention], [], 0.85)
        assert "1 sponsor mentions" in summary
        assert "1 properly disclosed" in summary
        assert "0 compliance violations" in summary
        assert "0.85" in summary

    def test_generate_next_steps(self):
        """Test next steps generation."""
        # Test with violations
        violation = ComplianceViolation(
            violation_type="missing_disclosure",
            severity="high",
            description="Test",
            timestamp=120.0,
            suggested_fix="Fix",
            ftc_guideline_reference="Test",
            penalty_risk="fine",
        )
        next_steps_with_violations = self.tool._generate_next_steps([violation], [])
        assert "Review and address compliance violations" in next_steps_with_violations

        # Test with recommendations
        recommendation = DisclosureRecommendation(
            disclosure_text="Test disclosure",
            placement_location="beginning",
            placement_timestamp=110.0,
            reasoning="Test reasoning",
            compliance_score=0.9,
            template_type="standard",
        )
        next_steps_with_recommendations = self.tool._generate_next_steps([], [recommendation])
        assert "Add disclosure text at recommended timestamps" in next_steps_with_recommendations

        # Test with no issues
        next_steps_no_issues = self.tool._generate_next_steps([], [])
        assert "Content appears compliant" in next_steps_no_issues[0]

    def test_run_success(self):
        """Test successful compliance analysis."""
        result = self.tool._run(
            episode_id=self.episode_id,
            enable_sponsor_detection=True,
            enable_compliance_check=True,
            enable_disclosure_generation=True,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["episode_id"] == self.episode_id
        assert "sponsor_mentions" in data
        assert "violations" in data
        assert "recommendations" in data
        assert "overall_compliance_score" in data
        assert "risk_level" in data
        assert "summary" in data
        assert "next_steps" in data

    def test_run_with_content_text(self):
        """Test analysis with provided content text."""
        content_text = "This video is sponsored by NordVPN. Use code H3PODCAST for 70% off."

        result = self.tool._run(
            content_text=content_text,
            enable_sponsor_detection=True,
            enable_compliance_check=True,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert data["episode_id"] == "text_analysis"
        assert len(data["sponsor_mentions"]) > 0

    def test_run_episode_not_found(self):
        """Test handling of non-existent episode."""
        # Mock the retrieve method to return empty content
        original_method = self.tool._retrieve_episode_content
        self.tool._retrieve_episode_content = Mock(return_value="")

        try:
            result = self.tool._run(
                episode_id="nonexistent_episode",
                tenant=self.tenant,
                workspace=self.workspace,
            )

            assert not result.success
            assert "No content available" in result.error
        finally:
            # Restore original method
            self.tool._retrieve_episode_content = original_method

    def test_run_disabled_features(self):
        """Test running with disabled features."""
        result = self.tool._run(
            episode_id=self.episode_id,
            enable_sponsor_detection=False,
            enable_compliance_check=False,
            enable_disclosure_generation=False,
            tenant=self.tenant,
            workspace=self.workspace,
        )

        assert result.success
        data = result.data["data"]
        assert len(data["sponsor_mentions"]) == 0
        assert len(data["violations"]) == 0
        assert len(data["recommendations"]) == 0

    def test_serialize_compliance_report(self):
        """Test compliance report serialization."""
        report = ComplianceReport(
            episode_id="episode_123",
            analysis_timestamp=datetime.now(),
            sponsor_mentions=[],
            violations=[],
            recommendations=[],
            overall_compliance_score=0.85,
            risk_level="low",
            summary="Test summary",
            next_steps=["Test step"],
        )

        serialized = self.tool._serialize_compliance_report(report)

        assert serialized["episode_id"] == "episode_123"
        assert "analysis_timestamp" in serialized
        assert serialized["sponsor_mentions"] == []
        assert serialized["violations"] == []
        assert serialized["recommendations"] == []
        assert serialized["overall_compliance_score"] == 0.85
        assert serialized["risk_level"] == "low"
        assert serialized["summary"] == "Test summary"
        assert serialized["next_steps"] == ["Test step"]

    def test_detect_sponsor_mentions(self):
        """Test sponsor mention detection."""
        content = "Thanks to NordVPN for sponsoring this episode. Use code H3PODCAST for 70% off."

        mentions = self.tool._detect_sponsor_mentions(content, "youtube")

        assert len(mentions) > 0
        mention = mentions[0]
        assert mention.sponsor_name == "NordVPN"
        assert "NordVPN" in mention.mention_text
        assert mention.confidence > 0.0
        assert mention.mention_type == "explicit"

    def test_check_compliance_violations(self):
        """Test compliance violation checking."""
        # Create a mention without disclosure
        mention = SponsorMention(
            sponsor_name="NordVPN",
            mention_text="Check out NordVPN",
            timestamp=120.0,
            confidence=0.85,
            mention_type="explicit",
            context="",
            is_disclosed=False,
            disclosure_location="none",
        )

        violations = self.tool._check_compliance_violations([mention], "Test content", "US", "youtube")

        assert len(violations) > 0
        violation = violations[0]
        assert violation.violation_type == "missing_disclosure"
        assert violation.severity == "high"

    def test_generate_disclosure_recommendations(self):
        """Test disclosure recommendation generation."""
        mention = SponsorMention(
            sponsor_name="NordVPN",
            mention_text="Check out NordVPN",
            timestamp=120.0,
            confidence=0.85,
            mention_type="explicit",
            context="",
            is_disclosed=False,
            disclosure_location="none",
        )

        recommendations = self.tool._generate_disclosure_recommendations([mention], [], "US", "youtube")

        assert len(recommendations) > 0
        recommendation = recommendations[0]
        assert "NordVPN" in recommendation.disclosure_text
        assert recommendation.placement_location == "beginning"
        assert recommendation.compliance_score > 0.8
