"""Comprehensive tests for OpenAI integration services."""

from unittest.mock import MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.services.openai_cost_monitoring import OpenAICostMonitoringService
from ultimate_discord_intelligence_bot.services.openai_function_calling import OpenAIFunctionCallingService
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService
from ultimate_discord_intelligence_bot.services.openai_multimodal import MultimodalAnalysisService
from ultimate_discord_intelligence_bot.services.openai_streaming import OpenAIStreamingService
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService
from ultimate_discord_intelligence_bot.services.openai_voice import OpenAIVoiceService
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestOpenAIIntegrationService:
    """Test OpenAI integration service."""

    @pytest.fixture
    def service(self):
        """Create OpenAI integration service instance."""
        return OpenAIIntegrationService()

    @pytest.mark.asyncio
    async def test_process_with_enhancements_success(self, service):
        """Test successful processing with enhancements."""
        with patch.object(service.structured_outputs, "analyze_content_structured") as mock_structured:
            mock_structured.return_value = StepResult.ok(data={"score": 8.5, "confidence": 0.9})
            result = await service.process_with_enhancements(
                content="Test content",
                enhancements=["structured_outputs"],
                tenant="test_tenant",
                workspace="test_workspace",
            )
            assert result.success
            assert "enhanced_analysis" in result.data
            assert "structured_analysis" in result.data["enhanced_analysis"]

    @pytest.mark.asyncio
    async def test_process_with_enhancements_vision(self, service):
        """Test processing with vision enhancement."""
        with patch.object(service.vision, "analyze_multiple_images") as mock_vision:
            mock_vision.return_value = StepResult.ok(data={"analysis": "Image analysis"})
            result = await service.process_with_enhancements(
                content="Test content",
                enhancements=["vision"],
                tenant="test_tenant",
                workspace="test_workspace",
                images=[b"fake_image_data"],
            )
            assert result.success
            assert "vision_analysis" in result.data["enhanced_analysis"]

    @pytest.mark.asyncio
    async def test_process_with_enhancements_multimodal(self, service):
        """Test processing with multimodal enhancement."""
        with patch.object(service.multimodal, "analyze_multimodal_content") as mock_multimodal:
            mock_multimodal.return_value = StepResult.ok(data={"multimodal_analysis": "Analysis"})
            result = await service.process_with_enhancements(
                content="Test content",
                enhancements=["multimodal"],
                tenant="test_tenant",
                workspace="test_workspace",
                images=[b"fake_image_data"],
            )
            assert result.success
            assert "multimodal_analysis" in result.data["enhanced_analysis"]

    def test_get_available_enhancements(self, service):
        """Test getting available enhancements."""
        enhancements = service.get_available_enhancements()
        assert isinstance(enhancements, list)
        assert "structured_outputs" in enhancements

    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test successful health check."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello"
            mock_create.return_value = mock_response
            result = await service.health_check()
            assert result.success
            assert result.data["openai_available"] is True

    def test_process_with_enhancements_sync(self, service):
        """Test synchronous processing for CrewAI compatibility."""
        result = service.process_with_enhancements_sync(
            content="Test content",
            enhancements=["structured_outputs"],
            tenant="test_tenant",
            workspace="test_workspace",
        )
        assert result.success
        assert "analysis" in result.data
        assert "enhanced" in result.data


class TestOpenAIStructuredOutputsService:
    """Test OpenAI structured outputs service."""

    @pytest.fixture
    def service(self):
        """Create structured outputs service instance."""
        return OpenAIStructuredOutputsService()

    @pytest.mark.asyncio
    async def test_generate_structured_response_success(self, service):
        """Test successful structured response generation."""
        schema = {"type": "object", "properties": {"score": {"type": "number"}, "confidence": {"type": "number"}}}
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"score": 8.5, "confidence": 0.9}'
            mock_create.return_value = mock_response
            result = await service.generate_structured_response(
                prompt="Analyze this content", schema=schema, tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "score" in result.data
            assert "confidence" in result.data

    @pytest.mark.asyncio
    async def test_analyze_content_structured_success(self, service):
        """Test successful structured content analysis."""
        with patch.object(service, "generate_structured_response") as mock_generate:
            mock_generate.return_value = StepResult.ok(data={"score": 8.5, "confidence": 0.9})
            result = await service.analyze_content_structured(
                content="Test content", analysis_type="debate", tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "score" in result.data
            assert "confidence" in result.data


class TestOpenAIFunctionCallingService:
    """Test OpenAI function calling service."""

    @pytest.fixture
    def service(self):
        """Create function calling service instance."""
        return OpenAIFunctionCallingService()

    def test_register_function(self, service):
        """Test function registration."""

        def test_handler(content: str):
            return {"result": "processed"}

        service.register_function(
            "test_function",
            {
                "name": "test_function",
                "description": "Test function",
                "parameters": {"type": "object", "properties": {"content": {"type": "string"}}},
            },
            test_handler,
        )
        assert "test_function" in service.functions
        assert service.functions["test_function"]["handler"] == test_handler

    @pytest.mark.asyncio
    async def test_call_with_functions_success(self, service):
        """Test successful function calling."""

        def test_handler(content: str):
            return {"result": "processed"}

        service.register_function(
            "test_function",
            {
                "name": "test_function",
                "description": "Test function",
                "parameters": {"type": "object", "properties": {"content": {"type": "string"}}},
            },
            test_handler,
        )
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].message.tool_calls = []
            mock_create.return_value = mock_response
            result = await service.call_with_functions(
                prompt="Use test_function to process this", tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "response" in result.data


class TestOpenAIStreamingService:
    """Test OpenAI streaming service."""

    @pytest.fixture
    def service(self):
        """Create streaming service instance."""
        return OpenAIStreamingService()

    @pytest.mark.asyncio
    async def test_stream_content_analysis_success(self, service):
        """Test successful content analysis streaming."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Streaming analysis content"
            mock_response.choices[0].finish_reason = "stop"
            mock_create.return_value = mock_response
            results = []
            async for result in service.stream_content_analysis(
                content="Test content", analysis_type="debate", tenant="test_tenant", workspace="test_workspace"
            ):
                results.append(result)
            assert len(results) > 0
            assert results[-1].success
            assert "content" in results[-1].data


class TestOpenAIVoiceService:
    """Test OpenAI voice service."""

    @pytest.fixture
    def service(self):
        """Create voice service instance."""
        return OpenAIVoiceService()

    @pytest.mark.asyncio
    async def test_text_to_speech_success(self, service):
        """Test successful text-to-speech conversion."""
        with patch.object(service.client.audio.speech, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.content = b"fake_audio_data"
            mock_create.return_value = mock_response
            result = await service.text_to_speech(
                text="Hello world", voice="alloy", tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "audio_data" in result.data
            assert result.data["format"] == "mp3"

    @pytest.mark.asyncio
    async def test_speech_to_text_success(self, service):
        """Test successful speech-to-text conversion."""
        with patch.object(service.client.audio.transcriptions, "create") as mock_create:
            mock_response = "Transcribed text"
            mock_create.return_value = mock_response
            result = await service.speech_to_text(
                audio_data=b"fake_audio_data", tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "text" in result.data
            assert result.data["confidence"] == 0.95


class TestOpenAIVisionService:
    """Test OpenAI vision service."""

    @pytest.fixture
    def service(self):
        """Create vision service instance."""
        return OpenAIVisionService()

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, service):
        """Test successful image analysis."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Image analysis result"
            mock_create.return_value = mock_response
            result = await service.analyze_image(
                image_data=b"fake_image_data",
                prompt="Analyze this image",
                tenant="test_tenant",
                workspace="test_workspace",
            )
            assert result.success
            assert "analysis" in result.data
            assert result.data["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_analyze_multiple_images_success(self, service):
        """Test successful multiple image analysis."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Multiple image analysis"
            mock_create.return_value = mock_response
            result = await service.analyze_multiple_images(
                images=[b"fake_image1", b"fake_image2"],
                prompt="Analyze these images",
                tenant="test_tenant",
                workspace="test_workspace",
            )
            assert result.success
            assert "analysis" in result.data
            assert result.data["image_count"] == 2


class TestMultimodalAnalysisService:
    """Test multimodal analysis service."""

    @pytest.fixture
    def service(self):
        """Create multimodal analysis service instance."""
        return MultimodalAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_multimodal_content_success(self, service):
        """Test successful multimodal content analysis."""
        with patch.object(service.client.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Multimodal analysis result"
            mock_create.return_value = mock_response
            result = await service.analyze_multimodal_content(
                text="Test text",
                images=[b"fake_image_data"],
                audio_data=None,
                tenant="test_tenant",
                workspace="test_workspace",
            )
            assert result.success
            assert "multimodal_analysis" in result.data
            assert "modalities_analyzed" in result.data


class TestOpenAICostMonitoringService:
    """Test OpenAI cost monitoring service."""

    @pytest.fixture
    def service(self):
        """Create cost monitoring service instance."""
        return OpenAICostMonitoringService()

    def test_record_request(self, service):
        """Test recording API request."""
        service.record_request(model="gpt-4o-mini", input_tokens=100, output_tokens=50, response_time=1.2, success=True)
        metrics = service.get_current_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["total_tokens"] == 150

    def test_get_cost_summary(self, service):
        """Test getting cost summary."""
        service.record_request("gpt-4o-mini", 100, 50, 1.0, True)
        service.record_request("gpt-4o", 200, 100, 2.0, True)
        summary = service.get_cost_summary()
        assert "total_cost" in summary
        assert "projected_monthly_cost" in summary
        assert summary["total_cost"] > 0

    def test_get_current_metrics(self, service):
        """Test getting current metrics."""
        service.record_request("gpt-4o-mini", 100, 50, 1.0, True)
        service.record_request("gpt-4o", 200, 100, 2.0, False)
        metrics = service.get_current_metrics()
        assert metrics["total_requests"] == 2
        assert metrics["total_tokens"] == 350
        assert metrics["success_rate"] == 0.5
        assert metrics["error_rate"] == 0.5


class TestOpenAIIntegrationEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline with OpenAI integration."""
        service = OpenAIIntegrationService()
        with patch.object(service.structured_outputs, "analyze_content_structured") as mock_structured:
            mock_structured.return_value = StepResult.ok(data={"score": 8.5, "confidence": 0.9})
            result = await service.process_with_enhancements(
                content="This is a test debate about climate change",
                enhancements=["structured_outputs", "function_calling"],
                tenant="test_tenant",
                workspace="test_workspace",
                analysis_type="debate",
            )
            assert result.success
            assert "enhanced_analysis" in result.data
            assert "openai_powered" in result.data
            assert result.data["openai_powered"] is True

    @pytest.mark.asyncio
    async def test_voice_command_processing(self):
        """Test voice command processing pipeline."""
        service = OpenAIIntegrationService()
        with patch.object(service.voice, "process_voice_command") as mock_voice:
            mock_voice.return_value = StepResult.ok(
                data={
                    "original_text": "Hello",
                    "response_text": "Hi there!",
                    "audio_response": b"fake_audio",
                    "format": "mp3",
                }
            )
            result = await service.process_voice_command(
                audio_data=b"fake_audio_data", tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "original_text" in result.data
            assert "response_text" in result.data

    @pytest.mark.asyncio
    async def test_multimodal_analysis_pipeline(self):
        """Test multimodal analysis pipeline."""
        service = OpenAIIntegrationService()
        with patch.object(service.multimodal, "analyze_multimodal_content") as mock_multimodal:
            mock_multimodal.return_value = StepResult.ok(
                data={
                    "multimodal_analysis": "Comprehensive analysis",
                    "modalities_analyzed": ["text", "images"],
                    "model": "gpt-4o",
                }
            )
            result = await service.fact_check_multimodal(
                text="This claim is true", images=[b"fake_image_data"], tenant="test_tenant", workspace="test_workspace"
            )
            assert result.success
            assert "multimodal_analysis" in result.data
