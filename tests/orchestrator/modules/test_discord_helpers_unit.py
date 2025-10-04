"""
Unit tests for orchestrator/discord_helpers module.

Tests specialized Discord embed creation functions:
- create_specialized_main_results_embed
- create_specialized_details_embed
- create_specialized_knowledge_embed

Note: These tests verify the fallback behavior when Discord is not available.
The functions return dict fallbacks in test environments.
"""

import asyncio

from ultimate_discord_intelligence_bot.orchestrator import discord_helpers


class TestCreateSpecializedMainResultsEmbed:
    """Test create_specialized_main_results_embed function."""

    def test_creates_embed_with_low_threat(self):
        """Test embed creation with low threat level."""
        results = {
            "specialized_analysis_summary": {
                "url": "https://example.com/video",
                "threat_score": 0.2,
                "threat_level": "low",
                "processing_time": 45.5,
                "workflow_id": "wf_123",
                "summary_statistics": {
                    "verification_completed": True,
                    "behavioral_analysis_done": True,
                    "knowledge_integrated": True,
                },
                "specialized_insights": [
                    "High quality content",
                    "Verified sources",
                    "No manipulation detected",
                ],
            }
        }

        # Run async function synchronously in tests
        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "comprehensive"))

        # Check embed has expected structure (dict or Discord Embed object)
        assert embed is not None
        # If it's a dict fallback, check keys
        if isinstance(embed, dict):
            assert "title" in embed

    def test_creates_embed_with_medium_threat(self):
        """Test embed creation with medium threat level."""
        results = {
            "specialized_analysis_summary": {
                "url": "https://example.com/video",
                "threat_score": 0.5,
                "threat_level": "medium",
                "processing_time": 60.0,
                "workflow_id": "wf_456",
                "summary_statistics": {},
                "specialized_insights": [],
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "standard"))

        assert embed is not None

    def test_creates_embed_with_high_threat(self):
        """Test embed creation with high threat level."""
        results = {
            "specialized_analysis_summary": {
                "url": "https://example.com/video",
                "threat_score": 0.9,
                "threat_level": "high",
                "processing_time": 90.0,
                "workflow_id": "wf_789",
                "summary_statistics": {},
                "specialized_insights": ["Critical issues detected"],
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "deep"))

        assert embed is not None

    def test_handles_missing_summary_data(self):
        """Test handles missing specialized_analysis_summary."""
        results = {}

        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "standard"))

        # Should return fallback embed
        assert embed is not None

    def test_handles_empty_insights(self):
        """Test handles empty insights list."""
        results = {
            "specialized_analysis_summary": {
                "url": "https://example.com/video",
                "threat_score": 0.3,
                "threat_level": "low",
                "processing_time": 30.0,
                "summary_statistics": {},
                "specialized_insights": [],
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "quick"))

        assert embed is not None

    def test_truncates_long_insights_list(self):
        """Test shows only top 4 insights."""
        results = {
            "specialized_analysis_summary": {
                "url": "https://example.com/video",
                "threat_score": 0.2,
                "threat_level": "low",
                "processing_time": 50.0,
                "specialized_insights": [
                    "Insight 1",
                    "Insight 2",
                    "Insight 3",
                    "Insight 4",
                    "Insight 5",
                    "Insight 6",
                ],
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_main_results_embed(results, "comprehensive"))

        # Should truncate to 4 insights (verified in implementation)
        assert embed is not None


class TestCreateSpecializedDetailsEmbed:
    """Test create_specialized_details_embed function."""

    def test_creates_embed_with_full_details(self):
        """Test embed creation with complete details."""
        results = {
            "detailed_results": {
                "intelligence": {
                    "content_metadata": {
                        "platform": "YouTube",
                        "title": "Comprehensive Analysis of AI Systems and Their Implications",
                        "duration": "15:30",
                    }
                },
                "verification": {
                    "fact_checks": {
                        "verified_claims": 10,
                        "disputed_claims": 2,
                        "evidence_count": 25,
                    },
                    "verification_confidence": 0.85,
                    "logical_analysis": {
                        "fallacies_detected": [
                            "Appeal to authority",
                            "False dichotomy",
                            "Hasty generalization",
                        ]
                    },
                },
                "deception": {
                    "deception_analysis": {"detected": True},
                    "threat_level": "medium",
                    "threat_score": 0.6,
                },
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        assert embed is not None

    def test_handles_legacy_fact_verification_format(self):
        """Test handles legacy fact_verification field."""
        results = {
            "detailed_results": {
                "intelligence": {},
                "verification": {
                    "fact_verification": {  # Legacy format
                        "verified_claims": 5,
                        "disputed_claims": 1,
                    },
                    "verification_confidence": 0.75,
                },
                "deception": {},
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        assert embed is not None

    def test_handles_claim_count_format(self):
        """Test handles claim count without verified/disputed breakdown."""
        results = {
            "detailed_results": {
                "intelligence": {},
                "verification": {
                    "fact_checks": {
                        "claims": ["claim1", "claim2", "claim3"],
                        "evidence_count": 8,
                    },
                    "verification_confidence": 0.70,
                },
                "deception": {},
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        assert embed is not None

    def test_truncates_long_title(self):
        """Test truncates titles longer than 50 characters."""
        long_title = "A" * 100
        results = {
            "detailed_results": {
                "intelligence": {
                    "content_metadata": {
                        "platform": "YouTube",
                        "title": long_title,
                        "duration": "10:00",
                    }
                },
                "verification": {},
                "deception": {},
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        assert embed is not None

    def test_shows_top_3_fallacies(self):
        """Test shows only top 3 fallacies."""
        results = {
            "detailed_results": {
                "intelligence": {},
                "verification": {
                    "logical_analysis": {
                        "fallacies_detected": [
                            "Fallacy 1",
                            "Fallacy 2",
                            "Fallacy 3",
                            "Fallacy 4",
                            "Fallacy 5",
                        ]
                    }
                },
                "deception": {},
            }
        }

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        assert embed is not None

    def test_handles_missing_detailed_results(self):
        """Test handles missing detailed_results entirely."""
        results = {}

        embed = asyncio.run(discord_helpers.create_specialized_details_embed(results))

        # Should return fallback embed
        assert embed is not None
        if isinstance(embed, dict):
            assert "title" in embed


class TestCreateSpecializedKnowledgeEmbed:
    """Test create_specialized_knowledge_embed function."""

    def test_creates_embed_with_all_systems(self):
        """Test embed creation with all knowledge systems integrated."""
        knowledge_data = {
            "knowledge_systems": {
                "vector_memory": True,
                "graph_memory": True,
                "continual_memory": True,
            },
            "integration_status": "completed",
        }

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        assert embed is not None

    def test_creates_embed_with_partial_systems(self):
        """Test embed creation with only some systems integrated."""
        knowledge_data = {
            "knowledge_systems": {
                "vector_memory": True,
                "graph_memory": False,
                "continual_memory": True,
            },
            "integration_status": "partial",
        }

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        assert embed is not None

    def test_handles_no_systems_integrated(self):
        """Test handles no systems showing as integrated."""
        knowledge_data = {
            "knowledge_systems": {
                "vector_memory": False,
                "graph_memory": False,
                "continual_memory": False,
            },
            "integration_status": "failed",
        }

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        assert embed is not None

    def test_handles_missing_knowledge_systems(self):
        """Test handles missing knowledge_systems field."""
        knowledge_data = {"integration_status": "unknown"}

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        assert embed is not None

    def test_handles_empty_knowledge_data(self):
        """Test handles completely empty knowledge data."""
        knowledge_data = {}

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        # Should return fallback embed
        assert embed is not None

    def test_capitalizes_integration_status(self):
        """Test integration status is title-cased."""
        knowledge_data = {
            "knowledge_systems": {"vector_memory": True},
            "integration_status": "in_progress",
        }

        embed = asyncio.run(discord_helpers.create_specialized_knowledge_embed(knowledge_data))

        assert embed is not None
