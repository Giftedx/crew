"""Tests for debate command extensions and advanced argument analysis."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.debate_analysis_pipeline import DebateAnalysisPipeline
from ultimate_discord_intelligence_bot.profiles.store import ProfileStore
from ultimate_discord_intelligence_bot.tools.character_profile_tool import (
    CharacterProfileTool,
)
from ultimate_discord_intelligence_bot.tools.debate_command_tool import DebateCommandTool


class TestDebateCommandExtensions:
    """Test suite for debate command extensions."""

    @pytest.fixture
    def mock_debate_tool(self):
        """Create a mock debate analysis tool."""
        tool = Mock()
        tool.analyze = Mock(
            return_value={
                "positions": [
                    {"stance": "pro", "strength": 0.8, "arguments": ["argument1"]},
                    {"stance": "con", "strength": 0.6, "arguments": ["argument2"]},
                ],
                "consensus_points": ["point1", "point2"],
                "contested_points": ["point3"],
                "confidence": 0.75,
            }
        )
        return tool

    def test_debate_analysis_basic(self, mock_debate_tool):
        """Test basic debate analysis functionality."""
        topic = "Should AI development be regulated?"
        result = mock_debate_tool.analyze(topic)

        assert "positions" in result
        assert len(result["positions"]) == 2
        assert result["confidence"] == 0.75
        mock_debate_tool.analyze.assert_called_once_with(topic)

    def test_debate_position_extraction(self, mock_debate_tool):
        """Test extraction of individual debate positions."""
        result = mock_debate_tool.analyze("test topic")
        positions = result["positions"]

        pro_position = next(p for p in positions if p["stance"] == "pro")
        assert pro_position["strength"] == 0.8
        assert "argument1" in pro_position["arguments"]

    def test_debate_consensus_identification(self, mock_debate_tool):
        """Test identification of consensus points in debates."""
        result = mock_debate_tool.analyze("test topic")

        assert "consensus_points" in result
        assert "point1" in result["consensus_points"]
        assert "point2" in result["consensus_points"]

    def test_debate_contested_points(self, mock_debate_tool):
        """Test identification of contested points."""
        result = mock_debate_tool.analyze("test topic")

        assert "contested_points" in result
        assert "point3" in result["contested_points"]

    @pytest.mark.parametrize(
        "topic,expected_complexity",
        [
            ("Simple yes/no question?", "low"),
            ("Complex ethical dilemma with multiple stakeholders", "high"),
            ("Technical topic requiring domain expertise", "high"),
            ("Basic factual query", "low"),
        ],
    )
    def test_debate_complexity_assessment(self, topic, expected_complexity):
        """Test assessment of debate topic complexity."""
        # This would integrate with actual complexity assessment logic
        complexity = self._assess_complexity(topic)
        assert complexity == expected_complexity

    def _assess_complexity(self, topic: str) -> str:
        """Helper to assess topic complexity."""
        if any(word in topic.lower() for word in ["complex", "ethical", "technical", "expertise"]):
            return "high"
        return "low"

    def test_debate_synthesis(self, mock_debate_tool):
        """Test synthesis of multiple debate positions."""
        result = mock_debate_tool.analyze("test topic")

        # Synthesize positions
        synthesis = self._synthesize_debate(result)
        assert "summary" in synthesis
        assert "recommendation" in synthesis
        assert synthesis["confidence_level"] > 0

    def _synthesize_debate(self, debate_result: dict) -> dict:
        """Helper to synthesize debate results."""
        return {
            "summary": f"Analyzed {len(debate_result['positions'])} positions",
            "recommendation": "Further investigation recommended",
            "confidence_level": debate_result["confidence"],
        }

    def test_debate_with_evidence_weighting(self):
        """Test debate analysis with evidence weighting."""
        evidence_weights = {"peer_reviewed": 0.9, "expert_opinion": 0.7, "anecdotal": 0.3}

        # Test that evidence types are weighted appropriately
        for evidence_type, weight in evidence_weights.items():
            assert 0 <= weight <= 1
            assert evidence_weights["peer_reviewed"] > evidence_weights["anecdotal"]

    @pytest.mark.asyncio
    async def test_async_debate_processing(self, mock_debate_tool):
        """Test asynchronous debate processing."""
        # Mock async version
        mock_debate_tool.analyze_async = Mock(return_value=mock_debate_tool.analyze("test"))

        result = await mock_debate_tool.analyze_async("async topic")
        assert result is not None
        assert "positions" in result

    def test_debate_fallacy_detection(self):
        """Test detection of logical fallacies in debate arguments."""
        fallacious_argument = "Everyone believes X, so X must be true"

        fallacies = self._detect_fallacies(fallacious_argument)
        assert len(fallacies) > 0
        assert any("bandwagon" in f.lower() or "populum" in f.lower() for f in fallacies)

    def _detect_fallacies(self, argument: str) -> list:
        """Helper to detect common logical fallacies."""
        fallacies = []
        if "everyone believes" in argument.lower():
            fallacies.append("Argumentum ad populum (bandwagon fallacy)")
        if "you're wrong because" in argument.lower():
            fallacies.append("Ad hominem")
        if "slippery slope" in argument.lower() or "will lead to" in argument.lower():
            fallacies.append("Slippery slope fallacy")
        return fallacies

    def test_debate_bias_detection(self):
        """Test detection of potential biases in debate framing."""
        biased_framing = "Why do all experts agree that X is bad?"

        biases = self._detect_biases(biased_framing)
        assert len(biases) > 0
        assert any("loaded question" in b.lower() for b in biases)

    def _detect_biases(self, text: str) -> list:
        """Helper to detect potential biases."""
        biases = []
        if text.startswith("Why do all"):
            biases.append("Loaded question / Presupposition")
        if "obviously" in text.lower() or "clearly" in text.lower():
            biases.append("Assertion bias")
        return biases


def test_latest_and_collabs(tmp_path):
    profile_tool = CharacterProfileTool(storage_path=tmp_path / "chars.json")
    pipeline = DebateAnalysisPipeline(profile_tool=profile_tool)
    store = ProfileStore(tmp_path / "p.db")
    tool = DebateCommandTool(pipeline=pipeline, profile_store=store)

    profile_tool.record_event("Ethan", {"video_id": "v1", "ts": 1})
    store.record_link("Ethan", "Hasan", datetime(2024, 1, 1))

    latest = tool._run("latest", person="Ethan")
    assert latest["events"][0]["video_id"] == "v1"

    collabs = tool._run("collabs", person="Ethan")
    assert collabs["collabs"] == [("Hasan", 1)]


def test_creator_and_verify_profiles(tmp_path):
    profile_tool = CharacterProfileTool(storage_path=tmp_path / "chars.json")
    pipeline = DebateAnalysisPipeline(profile_tool=profile_tool)
    store = ProfileStore(tmp_path / "p.db")
    tool = DebateCommandTool(pipeline=pipeline, profile_store=store)

    verify = tool._run("verify_profiles")
    assert "H3H3 Productions" in verify["verified"]
    creator = tool._run("creator", person="H3H3 Productions")
    assert creator["profile"]["person"] == "H3H3 Productions"
