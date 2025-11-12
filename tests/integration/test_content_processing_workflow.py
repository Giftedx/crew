"""Integration tests for content processing workflow."""

from unittest.mock import MagicMock, patch

import pytest

from domains.ingestion.providers.audio_transcription_tool import AudioTranscriptionTool
from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool
from domains.memory.vector.unified_memory_tool import UnifiedMemoryTool


class TestContentProcessingWorkflow:
    """Integration tests for the complete content processing workflow."""

    @pytest.fixture
    def workflow_tools(self):
        """Create all tools needed for the workflow."""
        return {
            "download_tool": MultiPlatformDownloadTool(),
            "transcription_tool": AudioTranscriptionTool(),
            "analysis_tool": EnhancedAnalysisTool(),
            "verification_tool": ClaimVerifierTool(),
            "memory_tool": UnifiedMemoryTool(),
        }

    @pytest.fixture
    def sample_video_url(self):
        """Sample video URL for testing."""
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "test_tenant", "workspace": "test_workspace"}

    def test_complete_content_processing_workflow(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test the complete content processing workflow from download to storage."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {
                "success": True,
                "platform": "youtube",
                "title": "Test Video",
                "file_path": "/tmp/test_video.mp4",
                "duration": 180,
                "quality": "720p",
                "metadata": {"uploader": "Test Channel", "view_count": 1000, "upload_date": "2024-01-01"},
            }
            download_result = workflow_tools["download_tool"]._run(
                sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert download_result.success
            assert download_result.data["platform"] == "youtube"
            assert download_result.data["file_path"] == "/tmp/test_video.mp4"
        with patch.object(workflow_tools["transcription_tool"], "_transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = {
                "success": True,
                "transcript": "This is a test transcript of the video content.",
                "language": "en",
                "confidence": 0.95,
                "segments": [
                    {"start": 0, "end": 10, "text": "This is a test transcript"},
                    {"start": 10, "end": 20, "text": "of the video content."},
                ],
            }
            transcription_result = workflow_tools["transcription_tool"]._run(
                "/tmp/test_video.mp4", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert transcription_result.success
            assert "transcript" in transcription_result.data
            assert transcription_result.data["language"] == "en"
        with patch.object(workflow_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["technology", "education"],
                "bias_indicators": ["subjective_language"],
                "sentiment": "positive",
                "sentiment_confidence": 0.85,
                "extracted_claims": ["Technology improves education"],
                "processing_time": 2.5,
            }
            analysis_result = workflow_tools["analysis_tool"]._run(
                transcription_result.data["transcript"],
                "comprehensive",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert analysis_result.success
            assert "political_topics" in analysis_result.data
            assert "sentiment" in analysis_result.data
        with patch.object(workflow_tools["verification_tool"], "_verify_claim") as mock_verify:
            mock_verify.return_value = {
                "claim_id": "claim_123",
                "claim_text": "Technology improves education",
                "overall_confidence": 0.9,
                "verification_status": "verified",
                "sources": [
                    {
                        "source_id": "source_1",
                        "title": "Educational Technology Study",
                        "url": "https://example.com/study",
                        "snippet": "Research shows technology improves learning outcomes...",
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
            verification_result = workflow_tools["verification_tool"]._run(
                analysis_result.data["extracted_claims"][0],
                "Educational context",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert verification_result.success
            assert verification_result.data["verification_status"] == "verified"
        with patch.object(workflow_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {
                "success": True,
                "content_id": "content_123",
                "namespace": "processed_content",
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {
                    "source": "youtube",
                    "analysis_results": analysis_result.data,
                    "verification_results": verification_result.data,
                },
            }
            content_data = {
                "original_url": sample_video_url,
                "download_info": download_result.data,
                "transcript": transcription_result.data["transcript"],
                "analysis": analysis_result.data,
                "verification": verification_result.data,
            }
            storage_result = workflow_tools["memory_tool"]._run(
                "store",
                str(content_data),
                {"workflow": "content_processing", "step": "complete"},
                "processed_content",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert storage_result.success
            assert storage_result.data["content_id"] == "content_123"

    def test_workflow_with_download_failure(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test workflow handling when download fails."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.side_effect = Exception("Download failed")
            download_result = workflow_tools["download_tool"]._run(
                sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert not download_result.success
            assert "Download failed" in download_result.error

    def test_workflow_with_transcription_failure(self, workflow_tools, sample_tenant_context):
        """Test workflow handling when transcription fails."""
        with patch.object(workflow_tools["transcription_tool"], "_transcribe_audio") as mock_transcribe:
            mock_transcribe.side_effect = Exception("Transcription failed")
            transcription_result = workflow_tools["transcription_tool"]._run(
                "/tmp/test_video.mp4", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert not transcription_result.success
            assert "Transcription failed" in transcription_result.error

    def test_workflow_with_analysis_failure(self, workflow_tools, sample_tenant_context):
        """Test workflow handling when analysis fails."""
        with patch.object(workflow_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            analysis_result = workflow_tools["analysis_tool"]._run(
                "Test transcript content",
                "comprehensive",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert not analysis_result.success
            assert "Analysis failed" in analysis_result.error

    def test_workflow_with_verification_failure(self, workflow_tools, sample_tenant_context):
        """Test workflow handling when verification fails."""
        with patch.object(workflow_tools["verification_tool"], "_verify_claim") as mock_verify:
            mock_verify.side_effect = Exception("Verification failed")
            verification_result = workflow_tools["verification_tool"]._run(
                "Test claim", "Test context", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert not verification_result.success
            assert "Verification failed" in verification_result.error

    def test_workflow_with_memory_failure(self, workflow_tools, sample_tenant_context):
        """Test workflow handling when memory storage fails."""
        with patch.object(workflow_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.side_effect = Exception("Storage failed")
            storage_result = workflow_tools["memory_tool"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            assert not storage_result.success
            assert "Storage failed" in storage_result.error

    def test_concurrent_workflow_processing(self, workflow_tools, sample_tenant_context):
        """Test concurrent processing of multiple workflows."""
        urls = ["https://youtube.com/watch?v=1", "https://youtube.com/watch?v=2", "https://youtube.com/watch?v=3"]
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {"success": True, "platform": "youtube", "file_path": "/tmp/test_video.mp4"}
            results = []
            for url in urls:
                result = workflow_tools["download_tool"]._run(
                    url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                results.append(result)
            for result in results:
                assert result.success

    def test_workflow_data_consistency(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test data consistency throughout the workflow."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            with patch.object(workflow_tools["transcription_tool"], "_transcribe_audio") as mock_transcribe:
                with patch.object(workflow_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                    with patch.object(workflow_tools["verification_tool"], "_verify_claim") as mock_verify:
                        with patch.object(workflow_tools["memory_tool"], "_store_content") as mock_store:
                            mock_download.return_value = {
                                "success": True,
                                "platform": "youtube",
                                "title": "Test Video",
                                "file_path": "/tmp/test_video.mp4",
                            }
                            mock_transcribe.return_value = {
                                "success": True,
                                "transcript": "Test transcript",
                                "language": "en",
                            }
                            mock_analyze.return_value = {
                                "political_topics": ["technology"],
                                "sentiment": "positive",
                                "extracted_claims": ["Technology is beneficial"],
                            }
                            mock_verify.return_value = {
                                "claim_id": "claim_123",
                                "verification_status": "verified",
                                "overall_confidence": 0.9,
                            }
                            mock_store.return_value = {"success": True, "content_id": "content_123"}
                            download_result = workflow_tools["download_tool"]._run(
                                sample_video_url,
                                "720p",
                                sample_tenant_context["tenant"],
                                sample_tenant_context["workspace"],
                            )
                            transcription_result = workflow_tools["transcription_tool"]._run(
                                download_result.data["file_path"],
                                sample_tenant_context["tenant"],
                                sample_tenant_context["workspace"],
                            )
                            analysis_result = workflow_tools["analysis_tool"]._run(
                                transcription_result.data["transcript"],
                                "comprehensive",
                                sample_tenant_context["tenant"],
                                sample_tenant_context["workspace"],
                            )
                            verification_result = workflow_tools["verification_tool"]._run(
                                analysis_result.data["extracted_claims"][0],
                                "Context",
                                sample_tenant_context["tenant"],
                                sample_tenant_context["workspace"],
                            )
                            storage_result = workflow_tools["memory_tool"]._run(
                                "store",
                                "Content data",
                                {"analysis": analysis_result.data},
                                "namespace",
                                sample_tenant_context["tenant"],
                                sample_tenant_context["workspace"],
                            )
                            assert download_result.success
                            assert transcription_result.success
                            assert analysis_result.success
                            assert verification_result.success
                            assert storage_result.success
                            assert download_result.data["file_path"] == "/tmp/test_video.mp4"
                            assert transcription_result.data["transcript"] == "Test transcript"
                            assert analysis_result.data["political_topics"] == ["technology"]
                            assert verification_result.data["verification_status"] == "verified"
                            assert storage_result.data["content_id"] == "content_123"

    def test_workflow_performance_metrics(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test workflow performance metrics collection."""
        with patch("ultimate_discord_intelligence_bot.obs.metrics.get_metrics") as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
                mock_download.return_value = {"success": True, "platform": "youtube"}
                workflow_tools["download_tool"]._run(
                    sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                mock_metrics_instance.increment.assert_called()
                mock_metrics_instance.timing.assert_called()

    def test_workflow_tenant_isolation(self, workflow_tools, sample_video_url):
        """Test tenant isolation in workflow processing."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {"success": True, "platform": "youtube"}
            result1 = workflow_tools["download_tool"]._run(sample_video_url, "720p", "tenant1", "workspace1")
            result2 = workflow_tools["download_tool"]._run(sample_video_url, "720p", "tenant2", "workspace2")
            assert result1.success
            assert result2.success

    def test_workflow_error_recovery(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test workflow error recovery mechanisms."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.side_effect = [Exception("Network error"), {"success": True, "platform": "youtube"}]
            result1 = workflow_tools["download_tool"]._run(
                sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert not result1.success
            result2 = workflow_tools["download_tool"]._run(
                sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert result2.success

    def test_workflow_data_validation(self, workflow_tools, sample_tenant_context):
        """Test data validation throughout the workflow."""
        result = workflow_tools["download_tool"]._run(
            "invalid-url", "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
        )
        assert not result.success
        with patch.object(workflow_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {"error": "Empty transcript"}
            result = workflow_tools["analysis_tool"]._run(
                "", "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert not result.success

    def test_workflow_memory_cleanup(self, workflow_tools, sample_video_url, sample_tenant_context):
        """Test memory cleanup after workflow completion."""
        with patch.object(workflow_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {"success": True, "platform": "youtube", "file_path": "/tmp/test_video.mp4"}
            result = workflow_tools["download_tool"]._run(
                sample_video_url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            assert result.success
            assert result.data["file_path"] == "/tmp/test_video.mp4"
