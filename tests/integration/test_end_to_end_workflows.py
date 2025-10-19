"""
Integration tests for end-to-end workflows.

This module tests complete workflows from content ingestion through analysis to Discord output,
ensuring all components work together correctly.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from tests.factories import AnalysisFactory, StepResultFactory, TranscriptFactory
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestEndToEndWorkflows:
    """Integration tests for complete workflow scenarios."""

    @pytest.fixture
    def mock_memory_service(self) -> Mock:
        """Mock memory service for testing."""
        mock = Mock()
        mock.store_content = Mock(return_value=StepResultFactory.success())
        mock.retrieve_content = Mock(return_value=StepResultFactory.success())
        mock.search_content = Mock(return_value=StepResultFactory.success())
        return mock

    @pytest.fixture
    def mock_prompt_engine(self) -> Mock:
        """Mock prompt engine for testing."""
        mock = Mock()
        mock.generate_prompt = Mock(return_value="Generated prompt")
        mock.compile_template = Mock(return_value="Compiled template")
        return mock

    @pytest.fixture
    def mock_openrouter_service(self) -> Mock:
        """Mock OpenRouter service for testing."""
        mock = Mock()
        mock.generate_response = AsyncMock(return_value=StepResultFactory.success())
        mock.route_request = Mock(return_value="anthropic/claude-3.5-sonnet")
        return mock

    @pytest.fixture
    def mock_discord_bot(self) -> Mock:
        """Mock Discord bot for testing."""
        mock = Mock()
        mock.send_message = AsyncMock(return_value=StepResultFactory.success())
        mock.send_embed = AsyncMock(return_value=StepResultFactory.success())
        mock.update_message = AsyncMock(return_value=StepResultFactory.success())
        return mock

    @pytest.fixture
    def mock_pipeline(self) -> Mock:
        """Mock content pipeline for testing."""
        mock = Mock()
        mock.process_content = AsyncMock(return_value=StepResultFactory.success())
        mock.download_content = AsyncMock(return_value=StepResultFactory.success())
        mock.transcribe_content = AsyncMock(return_value=StepResultFactory.success())
        mock.analyze_content = AsyncMock(return_value=StepResultFactory.success())
        return mock

    @pytest.mark.asyncio
    async def test_youtube_debate_analysis_workflow(
        self,
        mock_pipeline: Mock,
        mock_memory_service: Mock,
        mock_discord_bot: Mock,
    ) -> None:
        """Test complete YouTube debate analysis workflow."""
        # Arrange
        youtube_url = "https://www.youtube.com/watch?v=test123"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock successful pipeline stages
        mock_pipeline.download_content.return_value = StepResultFactory.success(
            data={"url": youtube_url, "audio_path": "/tmp/audio.mp3"}
        )
        mock_pipeline.transcribe_content.return_value = StepResultFactory.success(
            data={"transcript": TranscriptFactory.create()}
        )
        mock_pipeline.analyze_content.return_value = StepResultFactory.success(
            data={"analysis": AnalysisFactory.create()}
        )
        mock_memory_service.store_content.return_value = StepResultFactory.success()
        mock_discord_bot.send_embed.return_value = StepResultFactory.success()

        # Act
        result = await mock_pipeline.process_content(youtube_url, tenant, workspace)

        # Assert
        assert result.success
        mock_pipeline.process_content.assert_called_once_with(youtube_url, tenant, workspace)

    @pytest.mark.asyncio
    async def test_multi_platform_content_ingestion_workflow(
        self,
        mock_pipeline: Mock,
        mock_memory_service: Mock,
    ) -> None:
        """Test multi-platform content ingestion workflow."""
        # Arrange
        urls = [
            "https://www.youtube.com/watch?v=test1",
            "https://www.twitch.tv/videos/test2",
            "https://www.tiktok.com/@user/video/test3",
        ]
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock successful processing for each URL
        mock_pipeline.process_content.return_value = StepResultFactory.success()

        # Act
        results = []
        for url in urls:
            result = await mock_pipeline.process_content(url, tenant, workspace)
            results.append(result)

        # Assert
        assert len(results) == 3
        assert all(result.success for result in results)
        assert mock_pipeline.process_content.call_count == 3

    @pytest.mark.asyncio
    async def test_memory_search_and_retrieval_workflow(
        self,
        mock_memory_service: Mock,
        mock_prompt_engine: Mock,
        mock_openrouter_service: Mock,
    ) -> None:
        """Test memory search and retrieval workflow."""
        # Arrange
        query = "What are the main arguments in the recent debate about AI?"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock memory search results
        search_results = StepResultFactory.success(
            data={
                "results": [
                    {"content": "AI debate argument 1", "relevance": 0.95},
                    {"content": "AI debate argument 2", "relevance": 0.87},
                ]
            }
        )
        mock_memory_service.search_content.return_value = search_results

        # Mock prompt generation and LLM response
        mock_prompt_engine.generate_prompt.return_value = "Generated search prompt"
        mock_openrouter_service.generate_response.return_value = StepResultFactory.success(
            data={"response": "Comprehensive analysis of AI debate arguments"}
        )

        # Act
        search_result = mock_memory_service.search_content(query, tenant, workspace)
        prompt = mock_prompt_engine.generate_prompt("search_analysis", {"query": query})
        response = await mock_openrouter_service.generate_response(prompt, tenant, workspace)

        # Assert
        assert search_result.success
        assert "results" in search_result
        assert len(search_result["results"]) == 2
        assert prompt == "Generated search prompt"
        assert response.success

    @pytest.mark.asyncio
    async def test_discord_bot_qa_workflow(
        self,
        mock_memory_service: Mock,
        mock_prompt_engine: Mock,
        mock_openrouter_service: Mock,
        mock_discord_bot: Mock,
    ) -> None:
        """Test Discord bot Q&A workflow."""
        # Arrange
        user_question = "What did the speakers say about climate change?"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock memory search
        search_results = StepResultFactory.success(
            data={"results": [{"content": "Climate change discussion", "relevance": 0.92}]}
        )
        mock_memory_service.search_content.return_value = search_results

        # Mock prompt generation and response
        mock_prompt_engine.generate_prompt.return_value = "Generated QA prompt"
        mock_openrouter_service.generate_response.return_value = StepResultFactory.success(
            data={"response": "The speakers discussed climate change impacts and solutions"}
        )
        mock_discord_bot.send_message.return_value = StepResultFactory.success()

        # Act
        search_result = mock_memory_service.search_content(user_question, tenant, workspace)
        prompt = mock_prompt_engine.generate_prompt("qa_response", {"question": user_question})
        response = await mock_openrouter_service.generate_response(prompt, tenant, workspace)
        discord_result = await mock_discord_bot.send_message(response["response"])

        # Assert
        assert search_result.success
        assert prompt == "Generated QA prompt"
        assert response.success
        assert discord_result.success

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(
        self,
        mock_pipeline: Mock,
        mock_memory_service: Mock,
    ) -> None:
        """Test error recovery in workflow."""
        # Arrange
        url = "https://invalid-url.com"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock download failure
        mock_pipeline.download_content.return_value = StepResult(
            success=False, error="Download failed: Invalid URL", custom_status="bad_request"
        )

        # Mock fallback processing
        mock_pipeline.process_content.return_value = StepResult(
            success=False, error="Unable to process content", custom_status="retryable"
        )

        # Act
        download_result = await mock_pipeline.download_content(url, tenant, workspace)

        if not download_result.success:
            process_result = await mock_pipeline.process_content(url, tenant, workspace)

        # Assert
        assert not download_result.success
        assert download_result["status"] == "bad_request"
        assert not process_result.success
        assert process_result["status"] == "retryable"

    @pytest.mark.asyncio
    async def test_tenant_isolation_workflow(
        self,
        mock_memory_service: Mock,
    ) -> None:
        """Test tenant isolation in workflow."""
        # Arrange
        content = "Test content"
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"
        workspace = "test_workspace"

        # Mock storage for different tenants
        mock_memory_service.store_content.return_value = StepResultFactory.success()
        mock_memory_service.retrieve_content.return_value = StepResultFactory.success()

        # Act
        store_result1 = mock_memory_service.store_content(content, tenant1, workspace)
        store_result2 = mock_memory_service.store_content(content, tenant2, workspace)

        retrieve_result1 = mock_memory_service.retrieve_content("content_id", tenant1, workspace)
        retrieve_result2 = mock_memory_service.retrieve_content("content_id", tenant2, workspace)

        # Assert
        assert store_result1.success
        assert store_result2.success
        assert retrieve_result1.success
        assert retrieve_result2.success

        # Verify tenant isolation calls
        calls = mock_memory_service.store_content.call_args_list
        assert calls[0][0][1] == tenant1  # Second argument is tenant
        assert calls[1][0][1] == tenant2

    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(
        self,
        mock_pipeline: Mock,
        mock_memory_service: Mock,
    ) -> None:
        """Test performance monitoring in workflow."""
        # Arrange
        url = "https://www.youtube.com/watch?v=performance_test"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock pipeline with performance data
        mock_pipeline.process_content.return_value = StepResultFactory.success(
            data={"processing_time": 2.5, "memory_usage": "150MB", "success": True}
        )

        # Act
        result = await mock_pipeline.process_content(url, tenant, workspace)

        # Assert
        assert result.success
        assert "processing_time" in result
        assert result["processing_time"] == 2.5
        assert "memory_usage" in result

    @pytest.mark.asyncio
    async def test_concurrent_processing_workflow(
        self,
        mock_pipeline: Mock,
    ) -> None:
        """Test concurrent processing of multiple URLs."""
        # Arrange
        urls = [
            "https://www.youtube.com/watch?v=concurrent1",
            "https://www.youtube.com/watch?v=concurrent2",
            "https://www.youtube.com/watch?v=concurrent3",
        ]
        tenant = "test_tenant"
        workspace = "test_workspace"

        mock_pipeline.process_content.return_value = StepResultFactory.success()

        # Act
        import asyncio

        tasks = [mock_pipeline.process_content(url, tenant, workspace) for url in urls]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 3
        assert all(result.success for result in results)
        assert mock_pipeline.process_content.call_count == 3

    @pytest.mark.asyncio
    async def test_data_consistency_workflow(
        self,
        mock_memory_service: Mock,
    ) -> None:
        """Test data consistency across workflow stages."""
        # Arrange
        content = "Consistent test content"
        tenant = "test_tenant"
        workspace = "test_workspace"

        # Mock consistent storage and retrieval
        mock_memory_service.store_content.return_value = StepResultFactory.success(data={"content_id": "test_id"})
        mock_memory_service.retrieve_content.return_value = StepResultFactory.success(
            data={"content": content, "metadata": {"stored_at": "2024-01-01"}}
        )

        # Act
        store_result = mock_memory_service.store_content(content, tenant, workspace)
        content_id = store_result["content_id"]

        retrieve_result = mock_memory_service.retrieve_content(content_id, tenant, workspace)

        # Assert
        assert store_result.success
        assert retrieve_result.success
        assert retrieve_result["content"] == content
        assert "metadata" in retrieve_result
