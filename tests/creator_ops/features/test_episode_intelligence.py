"""
Tests for Episode Intelligence Pack feature.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.episode_intelligence import (
    EpisodeIntelligencePack,
)
from ultimate_discord_intelligence_bot.creator_ops.features.intelligence_agent import (
    EpisodeIntelligenceAgent,
)
from ultimate_discord_intelligence_bot.creator_ops.features.intelligence_models import (
    AgendaItem,
    BrandSafetyAnalysis,
    DefamationRisk,
    EpisodeIntelligence,
    FactCheckableClaim,
    GuestInfo,
    IntelligenceConfig,
    IntelligenceResult,
    OutboundLink,
    RiskLevel,
)
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import (
    AlignedSegment,
    AlignedTranscript,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestEpisodeIntelligencePack:
    """Test suite for EpisodeIntelligencePack."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=CreatorOpsConfig)
        self.knowledge_api = Mock()
        self.intelligence_pack = EpisodeIntelligencePack(self.config, self.knowledge_api)

        # Create mock transcript
        self.transcript = AlignedTranscript(
            segments=[
                AlignedSegment(
                    start_time=0.0,
                    end_time=30.0,
                    speakers=["Host"],
                    text="Welcome to the show! Today we're discussing technology trends.",
                    topics=["technology", "trends"],
                    sentiment_score=0.2,
                ),
                AlignedSegment(
                    start_time=30.0,
                    end_time=60.0,
                    speakers=["Guest"],
                    text="According to recent studies, AI is transforming industries.",
                    topics=["AI", "industries"],
                    sentiment_score=0.1,
                ),
                AlignedSegment(
                    start_time=60.0,
                    end_time=90.0,
                    speakers=["Host"],
                    text="That's fascinating! Can you share more details?",
                    topics=["AI", "details"],
                    sentiment_score=0.3,
                ),
            ],
            duration=90.0,
            metadata={"title": "Tech Trends Discussion"},
        )

    def test_init(self):
        """Test EpisodeIntelligencePack initialization."""
        assert self.intelligence_pack.config == self.config
        assert self.intelligence_pack.knowledge_api == self.knowledge_api
        assert self.intelligence_pack.output_dir == Path("outputs/intelligence_packs")

    @pytest.mark.asyncio
    async def test_generate_intelligence_pack_success(self):
        """Test successful intelligence pack generation."""
        # Mock the individual generation methods
        with (
            patch.object(self.intelligence_pack, "_generate_agenda") as mock_agenda,
            patch.object(self.intelligence_pack, "_generate_guest_info") as mock_guests,
            patch.object(self.intelligence_pack, "_generate_claims") as mock_claims,
            patch.object(self.intelligence_pack, "_generate_quotations") as mock_quotations,
            patch.object(self.intelligence_pack, "_generate_links") as mock_links,
            patch.object(self.intelligence_pack, "_generate_thumbnail_suggestions") as mock_thumbnails,
            patch.object(self.intelligence_pack, "_generate_brand_safety_analysis") as mock_brand_safety,
            patch.object(self.intelligence_pack, "_generate_defamation_risk") as mock_defamation,
            patch.object(self.intelligence_pack, "_generate_key_insights") as mock_insights,
            patch.object(self.intelligence_pack, "_export_intelligence_pack") as mock_export,
        ):
            # Configure mocks
            mock_agenda.return_value = StepResult.ok(data={"agenda": []})
            mock_guests.return_value = StepResult.ok(data={"guests": []})
            mock_claims.return_value = StepResult.ok(data={"claims": []})
            mock_quotations.return_value = StepResult.ok(data={"quotations": []})
            mock_links.return_value = StepResult.ok(data={"links": []})
            mock_thumbnails.return_value = StepResult.ok(data={"thumbnails": []})
            mock_brand_safety.return_value = StepResult.ok(data={"brand_safety": None})
            mock_defamation.return_value = StepResult.ok(data={"defamation_risk": None})
            mock_insights.return_value = StepResult.ok(data={"insights": []})
            mock_export.return_value = StepResult.ok(data={"formats": [], "file_paths": {}})

            # Test
            result = await self.intelligence_pack.generate_intelligence_pack(
                episode_id="test_episode", transcript=self.transcript
            )

            # Verify
            assert result.success
            assert "result" in result.data
            intelligence_result = result.data["result"]
            assert isinstance(intelligence_result, IntelligenceResult)
            assert intelligence_result.episode_id == "test_episode"
            assert intelligence_result.success

    @pytest.mark.asyncio
    async def test_generate_agenda(self):
        """Test agenda generation."""
        result = await self.intelligence_pack._generate_agenda(self.transcript, IntelligenceConfig())

        assert result.success
        assert "agenda" in result.data
        agenda = result.data["agenda"]
        assert isinstance(agenda, list)

        # Should have agenda items based on topic changes
        if agenda:
            agenda_item = agenda[0]
            assert isinstance(agenda_item, AgendaItem)
            assert agenda_item.title
            assert agenda_item.start_time >= 0
            assert agenda_item.end_time > agenda_item.start_time

    @pytest.mark.asyncio
    async def test_generate_guest_info(self):
        """Test guest information generation."""
        result = await self.intelligence_pack._generate_guest_info(self.transcript)

        assert result.success
        assert "guests" in result.data
        guests = result.data["guests"]
        assert isinstance(guests, list)

        # Should have guest info for each speaker
        if guests:
            guest = guests[0]
            assert isinstance(guest, GuestInfo)
            assert guest.name
            assert guest.role
            assert guest.total_speaking_time > 0

    @pytest.mark.asyncio
    async def test_generate_claims(self):
        """Test claims generation."""
        result = await self.intelligence_pack._generate_claims(self.transcript, None, IntelligenceConfig())

        assert result.success
        assert "claims" in result.data
        claims = result.data["claims"]
        assert isinstance(claims, list)

        # Should detect claims with "according to" indicators
        if claims:
            claim = claims[0]
            assert isinstance(claim, FactCheckableClaim)
            assert claim.claim_id
            assert claim.text
            assert claim.speaker
            assert claim.timestamp >= 0

    @pytest.mark.asyncio
    async def test_generate_quotations(self):
        """Test quotations generation."""
        result = await self.intelligence_pack._generate_quotations(self.transcript, IntelligenceConfig())

        assert result.success
        assert "quotations" in result.data
        quotations = result.data["quotations"]
        assert isinstance(quotations, list)

    @pytest.mark.asyncio
    async def test_generate_links(self):
        """Test links generation."""
        # Add a URL to transcript
        transcript_with_url = AlignedTranscript(
            segments=[
                AlignedSegment(
                    start_time=0.0,
                    end_time=30.0,
                    speakers=["Host"],
                    text="Check out this link: https://example.com for more info",
                    topics=["technology"],
                    sentiment_score=0.2,
                )
            ],
            duration=30.0,
            metadata={"title": "Test Episode"},
        )

        result = await self.intelligence_pack._generate_links(transcript_with_url)

        assert result.success
        assert "links" in result.data
        links = result.data["links"]
        assert isinstance(links, list)

        # Should detect the URL
        if links:
            link = links[0]
            assert isinstance(link, OutboundLink)
            assert link.url == "https://example.com"
            assert link.domain == "example.com"

    @pytest.mark.asyncio
    async def test_generate_brand_safety_analysis(self):
        """Test brand safety analysis generation."""
        result = await self.intelligence_pack._generate_brand_safety_analysis(self.transcript, None)

        assert result.success
        assert "brand_safety" in result.data
        brand_safety = result.data["brand_safety"]
        assert isinstance(brand_safety, BrandSafetyAnalysis)
        assert 1.0 <= brand_safety.overall_score <= 5.0

    @pytest.mark.asyncio
    async def test_generate_defamation_risk(self):
        """Test defamation risk assessment generation."""
        result = await self.intelligence_pack._generate_defamation_risk(self.transcript, [], IntelligenceConfig())

        assert result.success
        assert "defamation_risk" in result.data
        defamation_risk = result.data["defamation_risk"]
        assert isinstance(defamation_risk, DefamationRisk)
        assert defamation_risk.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
        ]

    @pytest.mark.asyncio
    async def test_generate_key_insights(self):
        """Test key insights generation."""
        intelligence = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=3600,  # 1 hour
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=10,
            guests=[Mock(), Mock()],  # 2 guests
            claims=[Mock() for _ in range(6)],  # 6 claims
        )

        result = await self.intelligence_pack._generate_key_insights(intelligence)

        assert result.success
        assert "insights" in result.data
        insights = result.data["insights"]
        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_calculate_average_sentiment(self):
        """Test average sentiment calculation."""
        sentiment = self.intelligence_pack._calculate_average_sentiment(self.transcript)
        assert isinstance(sentiment, float)
        assert -1.0 <= sentiment <= 1.0

    def test_extract_top_topics(self):
        """Test top topics extraction."""
        topics = self.intelligence_pack._extract_top_topics(self.transcript)
        assert isinstance(topics, list)
        assert len(topics) <= 5

    @pytest.mark.asyncio
    async def test_export_intelligence_pack(self):
        """Test intelligence pack export."""
        intelligence = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
        )

        config = IntelligenceConfig(export_markdown=True, export_json=True)

        result = await self.intelligence_pack._export_intelligence_pack(intelligence, config)

        assert result.success
        assert "formats" in result.data
        assert "file_paths" in result.data
        formats = result.data["formats"]
        assert isinstance(formats, list)

    def test_generate_markdown_content(self):
        """Test Markdown content generation."""
        intelligence = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
            agenda=[
                AgendaItem(
                    title="Introduction",
                    start_time=0.0,
                    end_time=30.0,
                    duration=30.0,
                    description="Welcome segment",
                    speakers=["Host"],
                    topics=["introduction"],
                )
            ],
        )

        content = self.intelligence_pack._generate_markdown_content(intelligence)
        assert isinstance(content, str)
        assert "Test Episode" in content
        assert "Introduction" in content

    def test_generate_html_content(self):
        """Test HTML content generation."""
        intelligence = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
        )

        content = self.intelligence_pack._generate_html_content(intelligence)
        assert isinstance(content, str)
        assert "<html>" in content
        assert "Test Episode" in content

    def test_intelligence_to_dict(self):
        """Test intelligence pack to dictionary conversion."""
        intelligence = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
        )

        intelligence_dict = self.intelligence_pack._intelligence_to_dict(intelligence)
        assert isinstance(intelligence_dict, dict)
        assert intelligence_dict["episode_id"] == "test"
        assert intelligence_dict["episode_title"] == "Test Episode"

    def test_helper_methods(self):
        """Test helper methods."""
        # Test claim type determination
        claim_type = self.intelligence_pack._determine_claim_type("According to studies, this is true")
        assert claim_type in [
            "statistical",
            "historical",
            "scientific",
            "personal",
            "general",
        ]

        # Test claim confidence calculation
        confidence = self.intelligence_pack._calculate_claim_confidence("According to studies", "statistical")
        assert 0.0 <= confidence <= 1.0

        # Test quotation significance
        significance = self.intelligence_pack._calculate_quotation_significance("This is important insight")
        assert 0.0 <= significance <= 1.0

        # Test viral potential
        potential = self.intelligence_pack._calculate_viral_potential("This is amazing and shocking!")
        assert 0.0 <= potential <= 1.0

        # Test domain extraction
        domain = self.intelligence_pack._extract_domain("https://example.com/path")
        assert domain == "example.com"

        # Test link type determination
        link_type = self.intelligence_pack._determine_link_type("https://twitter.com/user")
        assert link_type == "social"

        # Test engagement score
        segment = AlignedSegment(
            start_time=0.0,
            end_time=30.0,
            speakers=["Host"],
            text="This is exciting!",
            topics=["excitement"],
            sentiment_score=0.8,
        )
        score = self.intelligence_pack._calculate_engagement_score(segment)
        assert 0.0 <= score <= 1.0


class TestEpisodeIntelligenceAgent:
    """Test suite for EpisodeIntelligenceAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=CreatorOpsConfig)
        self.config.openrouter_api_key = "test_key"
        self.agent = EpisodeIntelligenceAgent(self.config)

    def test_init(self):
        """Test EpisodeIntelligenceAgent initialization."""
        assert self.agent.config == self.config
        assert self.agent.agents is not None
        assert self.agent.tasks is not None
        assert self.agent.crew is not None

    def test_create_agents(self):
        """Test agent creation."""
        agents = self.agent._create_agents()

        expected_roles = [
            "content_analyst",
            "risk_assessor",
            "monetization_expert",
            "audience_specialist",
        ]
        for role in expected_roles:
            assert role in agents
            assert agents[role].role == role.replace("_", " ").title()

    def test_create_tasks(self):
        """Test task creation."""
        tasks = self.agent._create_tasks()

        expected_tasks = [
            "content_analysis",
            "risk_assessment",
            "monetization_analysis",
            "audience_engagement",
        ]
        for task in expected_tasks:
            assert task in tasks
            assert tasks[task].description is not None

    @pytest.mark.asyncio
    async def test_analyze_episode_intelligence(self):
        """Test episode intelligence analysis."""
        intelligence_pack = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
        )

        transcript = AlignedTranscript(segments=[], duration=90.0, metadata={"title": "Test Episode"})

        # Mock crew execution
        with patch.object(self.agent.crew, "kickoff") as mock_kickoff:
            mock_kickoff.return_value = {
                "content_analysis": "Content is engaging and well-structured",
                "risk_assessment": "Low risk content with no major concerns",
                "monetization_analysis": "Good opportunities for sponsorships",
                "audience_engagement": {"retention": 0.8, "engagement": 0.7},
            }

            result = await self.agent.analyze_episode_intelligence(intelligence_pack, transcript)

            assert result.success
            assert "analysis" in result.data

    def test_parse_crew_results(self):
        """Test crew results parsing."""
        mock_result = {
            "content_analysis": "Content is engaging and well-structured",
            "risk_assessment": "Low risk content with no major concerns",
            "monetization_analysis": "Good opportunities for sponsorships",
            "audience_engagement": {"retention": 0.8, "engagement": 0.7},
        }

        analysis = self.agent._parse_crew_results(mock_result)

        assert "episode_summary" in analysis
        assert "key_insights" in analysis
        assert "content_analysis" in analysis
        assert "risk_assessment" in analysis
        assert "monetization_analysis" in analysis
        assert "audience_engagement" in analysis

    def test_extract_insights(self):
        """Test insight extraction."""
        text = "This is an important insight. This is a recommendation. This is a suggestion."
        insights = self.agent._extract_insights(text)

        assert isinstance(insights, list)
        assert len(insights) <= 5

    def test_generate_episode_summary(self):
        """Test episode summary generation."""
        analysis = {
            "content_analysis": "Content is engaging and well-structured",
            "risk_assessment": "Low risk content with no major concerns",
            "monetization_analysis": "Good opportunities for sponsorships",
        }

        summary = self.agent._generate_episode_summary(analysis)

        assert isinstance(summary, str)
        assert "Content Analysis" in summary
        assert "Risk Assessment" in summary
        assert "Monetization" in summary

    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """Test recommendations generation."""
        intelligence_pack = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=1,  # Single speaker
            total_segments=3,
            claims=[Mock()],  # Has claims
            quotations=[Mock()],  # Has quotations
            links=[Mock()],  # Has links
            guests=[Mock()],  # Has guests
            average_sentiment=-0.5,  # Negative sentiment
        )

        analysis = {"key_insights": []}

        recommendations = await self.agent._generate_recommendations(intelligence_pack, analysis)

        assert "content" in recommendations
        assert "monetization" in recommendations
        assert "risks" in recommendations
        assert "improvements" in recommendations

        # Should have recommendations based on intelligence pack content
        assert len(recommendations["content"]) > 0
        assert len(recommendations["monetization"]) > 0
        assert len(recommendations["improvements"]) > 0

    @pytest.mark.asyncio
    async def test_generate_intelligence_report(self):
        """Test intelligence report generation."""
        intelligence_pack = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
        )

        analysis = Mock()
        analysis.episode_summary = "Test summary"
        analysis.key_insights = ["Insight 1", "Insight 2"]
        analysis.content_recommendations = ["Rec 1", "Rec 2"]
        analysis.monetization_opportunities = ["Opp 1", "Opp 2"]
        analysis.risk_assessments = ["Risk 1", "Risk 2"]
        analysis.improvement_suggestions = ["Suggestion 1", "Suggestion 2"]
        analysis.audience_engagement_predictions = {"retention": 0.8}

        result = await self.agent.generate_intelligence_report(intelligence_pack, analysis)

        assert result.success
        assert "report" in result.data
        report = result.data["report"]
        assert report["episode_id"] == "test"
        assert report["summary"] == "Test summary"

    @pytest.mark.asyncio
    async def test_get_intelligence_dashboard_data(self):
        """Test dashboard data generation."""
        intelligence_pack = EpisodeIntelligence(
            episode_id="test",
            episode_title="Test Episode",
            episode_duration=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            total_speakers=2,
            total_segments=3,
            agenda=[Mock()],
            guests=[Mock()],
            claims=[Mock()],
            quotations=[Mock()],
            links=[Mock()],
            brand_safety=Mock(overall_score=4.0, flagged_segments=[]),
            defamation_risk=Mock(risk_level=RiskLevel.LOW),
            top_topics=["technology", "AI"],
        )

        analysis = Mock()
        analysis.key_insights = ["Insight 1", "Insight 2"]
        analysis.content_recommendations = ["Rec 1", "Rec 2"]
        analysis.monetization_opportunities = ["Opp 1", "Opp 2"]
        analysis.risk_assessments = ["Risk 1", "Risk 2"]
        analysis.improvement_suggestions = ["Suggestion 1", "Suggestion 2"]
        analysis.audience_engagement_predictions = {"retention": 0.8}

        result = await self.agent.get_intelligence_dashboard_data(intelligence_pack, analysis)

        assert result.success
        assert "dashboard" in result.data
        dashboard = result.data["dashboard"]

        assert "episode_overview" in dashboard
        assert "content_metrics" in dashboard
        assert "safety_metrics" in dashboard
        assert "engagement_predictions" in dashboard
        assert "top_topics" in dashboard
        assert "key_insights" in dashboard
        assert "recommendations" in dashboard
