"""Integration tests for memory and analysis workflow."""

from unittest.mock import MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.analysis.character_profile_tool import CharacterProfileTool
from ultimate_discord_intelligence_bot.tools.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.memory.graph_memory_tool import GraphMemoryTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import ClaimVerifierTool


class TestMemoryAnalysisWorkflow:
    """Integration tests for memory and analysis workflow."""

    @pytest.fixture
    def memory_tools(self):
        """Create all tools needed for the memory and analysis workflow."""
        return {
            "unified_memory": UnifiedMemoryTool(),
            "graph_memory": GraphMemoryTool(),
            "analysis": EnhancedAnalysisTool(),
            "character_profile": CharacterProfileTool(),
            "verification": ClaimVerifierTool(),
        }

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return "This is a political statement about healthcare policy that needs analysis and storage."

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "memory_tenant", "workspace": "memory_workspace"}

    def test_memory_analysis_workflow(self, memory_tools, sample_content, sample_tenant_context):
        """Test the complete memory and analysis workflow."""
        # Step 1: Analyze content
        with patch.object(memory_tools["analysis"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare", "policy"],
                "bias_indicators": ["subjective_language"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare policy needs improvement"],
                "processing_time": 2.0,
            }

            analysis_result = memory_tools["analysis"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )

            assert analysis_result.success
            assert "political_topics" in analysis_result.data
            assert "sentiment" in analysis_result.data

        # Step 2: Store analysis results in unified memory
        with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
            mock_store.return_value = {
                "success": True,
                "content_id": "analysis_123",
                "namespace": "analysis_results",
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {
                    "analysis_type": "comprehensive",
                    "political_topics": analysis_result.data["political_topics"],
                    "sentiment": analysis_result.data["sentiment"],
                },
            }

            store_result = memory_tools["unified_memory"]._run(
                "store",
                str(analysis_result.data),
                {"analysis_type": "comprehensive", "source": "content_analysis"},
                "analysis_results",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert store_result.success
            assert store_result.data["content_id"] == "analysis_123"

        # Step 3: Update character profile based on analysis
        with patch.object(memory_tools["character_profile"], "_update_profile") as mock_profile:
            mock_profile.return_value = {
                "success": True,
                "profile_id": "profile_123",
                "trust_score": 0.85,
                "bias_indicators": analysis_result.data["bias_indicators"],
                "political_topics": analysis_result.data["political_topics"],
                "sentiment_trend": "neutral",
                "total_events": 1,
            }

            profile_result = memory_tools["character_profile"]._run(
                "test_user",
                "content_analysis",
                analysis_result.data,
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert profile_result.success
            assert profile_result.data["trust_score"] == 0.85

        # Step 4: Store in graph memory for relationship tracking
        with patch.object(memory_tools["graph_memory"], "_store_relationship") as mock_graph:
            mock_graph.return_value = {
                "success": True,
                "relationship_id": "rel_123",
                "source_node": "test_user",
                "target_node": "healthcare_policy",
                "relationship_type": "discusses",
                "confidence": 0.9,
                "metadata": {
                    "sentiment": analysis_result.data["sentiment"],
                    "topics": analysis_result.data["political_topics"],
                },
            }

            graph_result = memory_tools["graph_memory"]._run(
                "store_relationship",
                "test_user",
                "healthcare_policy",
                "discusses",
                analysis_result.data,
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert graph_result.success
            assert graph_result.data["relationship_type"] == "discusses"

        # Step 5: Verify claims if any
        if analysis_result.data["extracted_claims"]:
            with patch.object(memory_tools["verification"], "_verify_claim") as mock_verify:
                mock_verify.return_value = {
                    "claim_id": "claim_123",
                    "claim_text": analysis_result.data["extracted_claims"][0],
                    "overall_confidence": 0.9,
                    "verification_status": "verified",
                    "sources": [
                        {
                            "source_id": "source_1",
                            "title": "Healthcare Policy Study",
                            "url": "https://example.com/study",
                            "snippet": "Research shows healthcare policy improvements...",
                            "relevance_score": 0.95,
                            "backend": "serply",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "domain": "example.com",
                        }
                    ],
                    "processing_time": 3.0,
                    "backends_used": ["serply", "exa"],
                    "error_message": None,
                }

                verification_result = memory_tools["verification"]._run(
                    analysis_result.data["extracted_claims"][0],
                    "Memory analysis context",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )

                assert verification_result.success
                assert verification_result.data["verification_status"] == "verified"

        # Step 6: Retrieve related content from memory
        with patch.object(memory_tools["unified_memory"], "_retrieve_content") as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "results": [
                    {
                        "content": "Previous analysis of healthcare policy",
                        "confidence": 0.9,
                        "metadata": {"analysis_type": "comprehensive"},
                        "content_id": "prev_analysis_123",
                    }
                ],
                "total_results": 1,
                "query": "healthcare policy analysis",
            }

            retrieve_result = memory_tools["unified_memory"]._run(
                "retrieve",
                "healthcare policy analysis",
                "general",
                {"analysis_type": "comprehensive"},
                10,
                0.7,
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert retrieve_result.success
            assert len(retrieve_result.data["results"]) == 1

    def test_memory_retrieval_workflow(self, memory_tools, sample_tenant_context):
        """Test memory retrieval workflow."""
        with patch.object(memory_tools["unified_memory"], "_retrieve_content") as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "results": [
                    {
                        "content": "Healthcare policy analysis",
                        "confidence": 0.9,
                        "metadata": {"topic": "healthcare"},
                        "content_id": "content_1",
                    },
                    {
                        "content": "Technology advancement analysis",
                        "confidence": 0.8,
                        "metadata": {"topic": "technology"},
                        "content_id": "content_2",
                    },
                ],
                "total_results": 2,
                "query": "policy analysis",
            }

            result = memory_tools["unified_memory"]._run(
                "retrieve",
                "policy analysis",
                "general",
                {},
                10,
                0.7,
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert result.success
            assert len(result.data["results"]) == 2

    def test_character_profile_workflow(self, memory_tools, sample_tenant_context):
        """Test character profile workflow."""
        with patch.object(memory_tools["character_profile"], "_get_profile") as mock_profile:
            mock_profile.return_value = {
                "success": True,
                "profile_id": "profile_123",
                "user_id": "test_user",
                "trust_score": 0.85,
                "bias_indicators": ["subjective_language"],
                "political_topics": ["healthcare", "technology"],
                "sentiment_trend": "neutral",
                "total_events": 5,
                "recent_activity": [
                    {
                        "event_type": "content_analysis",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "topics": ["healthcare"],
                        "sentiment": "neutral",
                    }
                ],
            }

            result = memory_tools["character_profile"]._run(
                "get_profile", "test_user", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )

            assert result.success
            assert result.data["trust_score"] == 0.85
            assert result.data["total_events"] == 5

    def test_graph_memory_workflow(self, memory_tools, sample_tenant_context):
        """Test graph memory workflow."""
        with patch.object(memory_tools["graph_memory"], "_query_relationships") as mock_query:
            mock_query.return_value = {
                "success": True,
                "relationships": [
                    {
                        "relationship_id": "rel_1",
                        "source_node": "user_1",
                        "target_node": "healthcare",
                        "relationship_type": "discusses",
                        "confidence": 0.9,
                        "metadata": {"sentiment": "positive"},
                    },
                    {
                        "relationship_id": "rel_2",
                        "source_node": "user_1",
                        "target_node": "technology",
                        "relationship_type": "discusses",
                        "confidence": 0.8,
                        "metadata": {"sentiment": "neutral"},
                    },
                ],
                "total_relationships": 2,
            }

            result = memory_tools["graph_memory"]._run(
                "query_relationships",
                "user_1",
                "discusses",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert result.success
            assert len(result.data["relationships"]) == 2

    def test_memory_analysis_error_handling(self, memory_tools, sample_tenant_context):
        """Test memory analysis error handling."""
        # Test analysis error
        with patch.object(memory_tools["analysis"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")

            result = memory_tools["analysis"]._run(
                "Test content", "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )

            assert not result.success
            assert "Analysis failed" in result.error

        # Test memory storage error
        with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
            mock_store.side_effect = Exception("Storage failed")

            result = memory_tools["unified_memory"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert not result.success
            assert "Storage failed" in result.error

        # Test character profile error
        with patch.object(memory_tools["character_profile"], "_update_profile") as mock_profile:
            mock_profile.side_effect = Exception("Profile update failed")

            result = memory_tools["character_profile"]._run(
                "test_user",
                "content_analysis",
                {"test": "data"},
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )

            assert not result.success
            assert "Profile update failed" in result.error

    def test_memory_concurrent_operations(self, memory_tools, sample_tenant_context):
        """Test concurrent memory operations."""
        with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

            # Simulate concurrent storage operations
            results = []
            for i in range(3):
                result = memory_tools["unified_memory"]._run(
                    "store",
                    f"Test content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                results.append(result)

            # All should succeed
            for result in results:
                assert result.success

    def test_memory_tenant_isolation(self, memory_tools):
        """Test tenant isolation in memory operations."""
        with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

            # Test with different tenants
            result1 = memory_tools["unified_memory"]._run(
                "store", "content1", "metadata1", "namespace1", "tenant1", "workspace1"
            )
            result2 = memory_tools["unified_memory"]._run(
                "store", "content2", "metadata2", "namespace2", "tenant2", "workspace2"
            )

            assert result1.success
            assert result2.success
            # Both should succeed independently

    def test_memory_data_consistency(self, memory_tools, sample_content, sample_tenant_context):
        """Test data consistency in memory operations."""
        with patch.object(memory_tools["analysis"], "_analyze_comprehensive") as mock_analyze:
            with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
                with patch.object(memory_tools["character_profile"], "_update_profile") as mock_profile:
                    # Set up mocks
                    mock_analyze.return_value = {
                        "political_topics": ["healthcare"],
                        "sentiment": "neutral",
                        "sentiment_confidence": 0.8,
                        "extracted_claims": ["Healthcare is important"],
                    }

                    mock_store.return_value = {
                        "success": True,
                        "content_id": "analysis_123",
                        "namespace": "analysis_results",
                    }

                    mock_profile.return_value = {"success": True, "profile_id": "profile_123", "trust_score": 0.85}

                    # Execute workflow
                    analysis_result = memory_tools["analysis"]._run(
                        sample_content,
                        "comprehensive",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )

                    store_result = memory_tools["unified_memory"]._run(
                        "store",
                        str(analysis_result.data),
                        {"analysis_type": "comprehensive"},
                        "analysis_results",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )

                    profile_result = memory_tools["character_profile"]._run(
                        "test_user",
                        "content_analysis",
                        analysis_result.data,
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )

                    # Verify data consistency
                    assert analysis_result.success
                    assert store_result.success
                    assert profile_result.success

                    # Verify data flow
                    assert analysis_result.data["political_topics"] == ["healthcare"]
                    assert store_result.data["content_id"] == "analysis_123"
                    assert profile_result.data["trust_score"] == 0.85

    def test_memory_performance_metrics(self, memory_tools, sample_tenant_context):
        """Test memory performance metrics collection."""
        with patch("ultimate_discord_intelligence_bot.obs.metrics.get_metrics") as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance

            with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
                mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

                # Execute memory operation
                memory_tools["unified_memory"]._run(
                    "store",
                    "Test content",
                    {"test": "metadata"},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )

                # Verify metrics were collected
                mock_metrics_instance.increment.assert_called()
                mock_metrics_instance.timing.assert_called()

    def test_memory_error_recovery(self, memory_tools, sample_tenant_context):
        """Test memory error recovery mechanisms."""
        with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
            # First attempt fails
            mock_store.side_effect = [
                Exception("Storage error"),
                {"success": True, "content_id": "test_123", "namespace": "test_namespace"},
            ]

            # First attempt should fail
            result1 = memory_tools["unified_memory"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert not result1.success

            # Second attempt should succeed
            result2 = memory_tools["unified_memory"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert result2.success

    def test_memory_validation(self, memory_tools, sample_tenant_context):
        """Test memory validation."""
        # Test with empty content
        result = memory_tools["unified_memory"]._run(
            "store",
            "",
            {"test": "metadata"},
            "test_namespace",
            sample_tenant_context["tenant"],
            sample_tenant_context["workspace"],
        )
        assert not result.success

        # Test with invalid namespace
        result = memory_tools["unified_memory"]._run(
            "store",
            "Test content",
            {"test": "metadata"},
            "",
            sample_tenant_context["tenant"],
            sample_tenant_context["workspace"],
        )
        assert not result.success

    def test_memory_workflow_integration(self, memory_tools, sample_content, sample_tenant_context):
        """Test complete memory workflow integration."""
        # This test would typically involve running the entire workflow
        # with real data and verifying end-to-end functionality

        with patch.object(memory_tools["analysis"], "_analyze_comprehensive") as mock_analyze:
            with patch.object(memory_tools["unified_memory"], "_store_content") as mock_store:
                with patch.object(memory_tools["character_profile"], "_update_profile") as mock_profile:
                    with patch.object(memory_tools["graph_memory"], "_store_relationship") as mock_graph:
                        # Set up all mocks
                        mock_analyze.return_value = {
                            "political_topics": ["healthcare"],
                            "sentiment": "neutral",
                            "sentiment_confidence": 0.8,
                            "extracted_claims": ["Healthcare is important"],
                        }

                        mock_store.return_value = {
                            "success": True,
                            "content_id": "analysis_123",
                            "namespace": "analysis_results",
                        }

                        mock_profile.return_value = {"success": True, "profile_id": "profile_123", "trust_score": 0.85}

                        mock_graph.return_value = {
                            "success": True,
                            "relationship_id": "rel_123",
                            "relationship_type": "discusses",
                        }

                        # Execute complete workflow
                        analysis_result = memory_tools["analysis"]._run(
                            sample_content,
                            "comprehensive",
                            sample_tenant_context["tenant"],
                            sample_tenant_context["workspace"],
                        )

                        store_result = memory_tools["unified_memory"]._run(
                            "store",
                            str(analysis_result.data),
                            {"analysis_type": "comprehensive"},
                            "analysis_results",
                            sample_tenant_context["tenant"],
                            sample_tenant_context["workspace"],
                        )

                        profile_result = memory_tools["character_profile"]._run(
                            "test_user",
                            "content_analysis",
                            analysis_result.data,
                            sample_tenant_context["tenant"],
                            sample_tenant_context["workspace"],
                        )

                        graph_result = memory_tools["graph_memory"]._run(
                            "store_relationship",
                            "test_user",
                            "healthcare",
                            "discusses",
                            analysis_result.data,
                            sample_tenant_context["tenant"],
                            sample_tenant_context["workspace"],
                        )

                        # Verify all operations succeeded
                        assert analysis_result.success
                        assert store_result.success
                        assert profile_result.success
                        assert graph_result.success

                        # Verify data consistency across all operations
                        assert analysis_result.data["political_topics"] == ["healthcare"]
                        assert store_result.data["content_id"] == "analysis_123"
                        assert profile_result.data["trust_score"] == 0.85
                        assert graph_result.data["relationship_type"] == "discusses"
