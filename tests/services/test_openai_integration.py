"""Tests for OpenAI integration services."""

from unittest.mock import AsyncMock, patch

import pytest

from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService
from ultimate_discord_intelligence_bot.services.openai_function_calling import OpenAIFunctionCallingService
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService
from ultimate_discord_intelligence_bot.services.openai_multimodal import MultimodalAnalysisService
from ultimate_discord_intelligence_bot.services.openai_streaming import OpenAIStreamingService
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService
from ultimate_discord_intelligence_bot.services.openai_voice import OpenAIVoiceService


class TestOpenAIIntegrationService:
    """Test OpenAI integration service."""

    @pytest.fixture
    def service(self):
        return OpenAIIntegrationService()

    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test successful health check."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(choices=[AsyncMock(message=AsyncMock(content="Hello"))])

            result = await service.health_check()

            assert result.success
            assert result.data["openai_available"] is True
            assert "services" in result.data

    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """Test health check with OpenAI unavailable."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            result = await service.health_check()

            assert result.success  # Health check should still succeed
            assert result.data["openai_available"] is False
            assert "openai_error" in result.data

    @pytest.mark.asyncio
    async def test_get_available_enhancements(self, service):
        """Test getting available enhancements."""
        enhancements = service.get_available_enhancements()

        assert isinstance(enhancements, list)
        # Should include at least structured_outputs and function_calling by default
        assert "structured_outputs" in enhancements
        assert "function_calling" in enhancements


class TestOpenAIStructuredOutputsService:
    """Test OpenAI structured outputs service."""

    @pytest.fixture
    def service(self):
        return OpenAIStructuredOutputsService()

    @pytest.mark.asyncio
    async def test_generate_structured_response_success(self, service):
        """Test successful structured response generation."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(
                choices=[AsyncMock(message=AsyncMock(content='{"score": 8.5, "confidence": 0.9}'))]
            )

            schema = {"type": "object", "properties": {"score": {"type": "number"}, "confidence": {"type": "number"}}}

            result = await service.generate_structured_response(
                prompt="Test prompt", schema=schema, tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert result.data["score"] == 8.5
            assert result.data["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_generate_structured_response_invalid_json(self, service):
        """Test structured response with invalid JSON."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(choices=[AsyncMock(message=AsyncMock(content='{"invalid": "json"'))])

            schema = {"type": "object", "properties": {"score": {"type": "number"}, "confidence": {"type": "number"}}}

            result = await service.generate_structured_response(
                prompt="Test prompt", schema=schema, tenant="test_tenant", workspace="test_workspace"
            )

            assert not result.success
            assert "Invalid JSON" in result.error


class TestOpenAIFunctionCallingService:
    """Test OpenAI function calling service."""

    @pytest.fixture
    def service(self):
        return OpenAIFunctionCallingService()

    def test_register_function(self, service):
        """Test function registration."""
        schema = {"name": "test_function", "description": "Test function", "parameters": {"type": "object"}}

        def handler():
            return "test result"

        service.register_function("test_function", schema, handler)

        assert "test_function" in service.functions
        assert "test_function" in service.function_handlers

    @pytest.mark.asyncio
    async def test_call_with_functions_text_response(self, service):
        """Test function calling with text response."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(
                choices=[AsyncMock(message=AsyncMock(content="Test response", function_call=None))]
            )

            result = await service.call_with_functions(
                prompt="Test prompt", tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert result.data["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_call_with_functions_function_call(self, service):
        """Test function calling with function call."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(
                choices=[
                    AsyncMock(
                        message=AsyncMock(
                            content=None,
                            function_call=AsyncMock(
                                name="analyze_debate_content",
                                arguments='{"content": "test", "analysis_type": "debate"}',
                            ),
                        )
                    )
                ]
            )

            result = await service.call_with_functions(
                prompt="Test prompt", tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert "score" in result.data


class TestOpenAIStreamingService:
    """Test OpenAI streaming service."""

    @pytest.fixture
    def service(self):
        return OpenAIStreamingService()

    @pytest.mark.asyncio
    async def test_stream_response_success(self, service):
        """Test successful streaming response."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            # Mock streaming response
            mock_chunk1 = AsyncMock()
            mock_chunk1.choices = [AsyncMock(delta=AsyncMock(content="Hello "))]

            mock_chunk2 = AsyncMock()
            mock_chunk2.choices = [AsyncMock(delta=AsyncMock(content="World"))]

            mock_create.return_value = [mock_chunk1, mock_chunk2]

            results = []
            async for result in service.stream_response(
                prompt="Test prompt", tenant="test_tenant", workspace="test_workspace"
            ):
                results.append(result)

            assert len(results) >= 2
            assert results[0].success
            assert results[0].data["content"] == "Hello "
            assert results[1].success
            assert results[1].data["content"] == "World"


class TestOpenAIVoiceService:
    """Test OpenAI voice service."""

    @pytest.fixture
    def service(self):
        return OpenAIVoiceService()

    @pytest.mark.asyncio
    async def test_text_to_speech_success(self, service):
        """Test successful text-to-speech."""
        with patch.object(service.client.audio.speech, "create") as mock_create:
            mock_create.return_value = AsyncMock(content=b"audio_data")

            result = await service.text_to_speech(
                text="Hello world", voice="alloy", tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert result.data["audio_data"] == b"audio_data"
            assert result.data["format"] == "mp3"
            assert result.data["voice"] == "alloy"

    @pytest.mark.asyncio
    async def test_speech_to_text_success(self, service):
        """Test successful speech-to-text."""
        with patch.object(service.client.audio.transcriptions, "create") as mock_create:
            mock_create.return_value = "Hello world"

            result = await service.speech_to_text(
                audio_data=b"audio_data", tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert result.data["text"] == "Hello world"
            assert result.data["confidence"] == 0.95


class TestOpenAIVisionService:
    """Test OpenAI vision service."""

    @pytest.fixture
    def service(self):
        return OpenAIVisionService()

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, service):
        """Test successful image analysis."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(
                choices=[AsyncMock(message=AsyncMock(content="Image analysis result"))]
            )

            result = await service.analyze_image(
                image_data=b"image_data", prompt="Analyze this image", tenant="test_tenant", workspace="test_workspace"
            )

            assert result.success
            assert result.data["analysis"] == "Image analysis result"
            assert result.data["model"] == "gpt-4o"


class TestMultimodalAnalysisService:
    """Test multimodal analysis service."""

    @pytest.fixture
    def service(self):
        return MultimodalAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_multimodal_content_success(self, service):
        """Test successful multimodal analysis."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_create.return_value = AsyncMock(
                choices=[AsyncMock(message=AsyncMock(content="Multimodal analysis result"))]
            )

            result = await service.analyze_multimodal_content(
                text="Test text",
                images=[b"image1", b"image2"],
                audio_data=None,
                tenant="test_tenant",
                workspace="test_workspace",
            )

            assert result.success
            assert result.data["multimodal_analysis"] == "Multimodal analysis result"
            assert result.data["modalities_analyzed"] == ["text", "images"]
            assert result.data["model"] == "gpt-4o"


class TestOpenAICostMonitoringService:
    """Test OpenAI cost monitoring service."""

    @pytest.fixture
    def service(self):
        return OpenAICostMonitoringService()

    def test_calculate_token_cost(self, service):
        """Test token cost calculation."""
        cost = service.calculate_token_cost("gpt-4o-mini", 1000, 500)
        assert cost > 0
        assert cost < 1.0  # Should be reasonable

    def test_calculate_tts_cost(self, service):
        """Test TTS cost calculation."""
        cost = service.calculate_tts_cost(1000)  # 1000 characters
        assert cost > 0
        assert cost < 1.0  # Should be reasonable

    @pytest.mark.asyncio
    async def test_record_request(self, service):
        """Test recording a request."""
        await service.record_request(
            model="gpt-4o-mini", input_tokens=100, output_tokens=50, response_time=1.5, success=True
        )

        metrics = service.get_current_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["total_tokens"] == 150
        assert metrics["total_cost"] > 0

    def test_get_cost_summary(self, service):
        """Test cost summary generation."""
        summary = service.get_cost_summary()

        assert "current_daily_cost" in summary
        assert "current_monthly_cost" in summary
        assert "average_daily_cost" in summary
        assert "projected_monthly_cost" in summary
        assert "cost_alerts" in summary
