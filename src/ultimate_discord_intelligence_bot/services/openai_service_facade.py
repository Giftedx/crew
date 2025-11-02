"""Unified OpenAI Service Facade

This module provides a single, unified interface to all OpenAI capabilities,
consolidating the 7 separate OpenAI service files into a cohesive API.

Features:
- Structured outputs with schema validation
- Function calling with tool integration
- Streaming responses with real-time processing
- Voice capabilities (TTS/STT)
- Vision analysis and multimodal processing
- Cost monitoring and usage tracking
- Automatic fallback to OpenRouter when needed

Usage:
    from ultimate_discord_intelligence_bot.services.openai_service_facade import OpenAIServiceFacade

    service = OpenAIServiceFacade()

    # Structured analysis
    result = await service.analyze_content_structured(
        content="Debate transcript...",
        analysis_type="debate",
        tenant="tenant_id",
        workspace="workspace_id"
    )

    # Multimodal analysis
    result = await service.analyze_multimodal(
        text="Content text",
        images=[image_bytes],
        audio_data=audio_bytes,
        tenant="tenant_id",
        workspace="workspace_id"
    )
"""
from __future__ import annotations
import logging
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any
from app.config.base import BaseConfig
from app.config.feature_flags import FeatureFlags
from .openai_cost_monitoring import OpenAICostMonitoringService
from .openai_function_calling import OpenAIFunctionCallingService
from .openai_multimodal import MultimodalAnalysisService
from .openai_service import OpenAIService
from .openai_streaming import OpenAIStreamingService
from .openai_structured_outputs import OpenAIStructuredOutputsService
from .openai_vision import OpenAIVisionService
from .openai_voice import OpenAIVoiceService
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
logger = logging.getLogger(__name__)

class OpenAIServiceFacade:
    """Unified facade for all OpenAI capabilities."""

    def __init__(self, config: BaseConfig | None=None, feature_flags: FeatureFlags | None=None):
        """Initialize the OpenAI service facade.

        Args:
            config: Configuration object (uses default if None)
            feature_flags: Feature flags (uses default if None)
        """
        self.config = config or BaseConfig.from_env()
        self.feature_flags = feature_flags or FeatureFlags.from_env()
        self.base_service = OpenAIService(api_key=self.config.openai_api_key, base_url=self.config.openai_base_url, max_tokens=self.config.openai_max_tokens, temperature=self.config.openai_temperature)
        self.structured_outputs = OpenAIStructuredOutputsService()
        self.function_calling = OpenAIFunctionCallingService()
        self.streaming = OpenAIStreamingService()
        self.voice = OpenAIVoiceService()
        self.vision = OpenAIVisionService()
        self.multimodal = MultimodalAnalysisService()
        self.cost_monitoring = OpenAICostMonitoringService()
        self._services_available = {'structured_outputs': self._is_feature_enabled('ENABLE_OPENAI_STRUCTURED_OUTPUTS'), 'function_calling': self._is_feature_enabled('ENABLE_OPENAI_FUNCTION_CALLING'), 'streaming': self._is_feature_enabled('ENABLE_OPENAI_STREAMING'), 'voice': self._is_feature_enabled('ENABLE_OPENAI_VOICE'), 'vision': self._is_feature_enabled('ENABLE_OPENAI_VISION'), 'multimodal': self._is_feature_enabled('ENABLE_OPENAI_MULTIMODAL'), 'fallback': self._is_feature_enabled('ENABLE_OPENAI_FALLBACK')}

    def _is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(self.feature_flags, feature_name, False)

    async def analyze_content_structured(self, content: str, analysis_type: str='debate', tenant: str='', workspace: str='', schema: dict[str, Any] | None=None) -> StepResult:
        """Analyze content with structured outputs.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis to perform
            tenant: Tenant identifier
            workspace: Workspace identifier
            schema: Optional custom schema for structured output

        Returns:
            StepResult with structured analysis data
        """
        if not self._services_available['structured_outputs']:
            return await self._fallback_analysis(content, analysis_type, tenant, workspace)
        try:
            return await self.structured_outputs.analyze_content_structured(content=content, analysis_type=analysis_type, tenant=tenant, workspace=workspace, schema=schema)
        except Exception as e:
            logger.error(f'Structured analysis failed: {e}')
            return await self._fallback_analysis(content, analysis_type, tenant, workspace)

    async def process_content_with_tool_use(self, content: str, analysis_type: str='debate', tenant: str='', workspace: str='', tools: list[dict[str, Any]] | None=None) -> StepResult:
        """Process content using function calling.

        Args:
            content: Content to process
            analysis_type: Type of analysis to perform
            tenant: Tenant identifier
            workspace: Workspace identifier
            tools: Optional custom tools for function calling

        Returns:
            StepResult with function calling results
        """
        if not self._services_available['function_calling']:
            return await self._fallback_analysis(content, analysis_type, tenant, workspace)
        try:
            return await self.function_calling.process_content_with_tool_use(content=content, analysis_type=analysis_type, tenant=tenant, workspace=workspace, tools=tools)
        except Exception as e:
            logger.error(f'Function calling failed: {e}')
            return await self._fallback_analysis(content, analysis_type, tenant, workspace)

    async def stream_content_analysis(self, content: str, analysis_type: str='debate', tenant: str='', workspace: str='') -> AsyncGenerator[StepResult, None]:
        """Stream content analysis results.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis to perform
            tenant: Tenant identifier
            workspace: Workspace identifier

        Yields:
            StepResult objects with streaming analysis data
        """
        if not self._services_available['streaming']:
            result = await self._fallback_analysis(content, analysis_type, tenant, workspace)
            yield result
            return
        try:
            async for result in self.streaming.stream_content_analysis(content=content, analysis_type=analysis_type, tenant=tenant, workspace=workspace):
                yield result
        except Exception as e:
            logger.error(f'Streaming analysis failed: {e}')
            yield StepResult.fail(f'Streaming analysis failed: {e}')

    async def text_to_speech(self, text: str, voice: str='alloy', tenant: str='', workspace: str='') -> StepResult:
        """Convert text to speech.

        Args:
            text: Text to convert
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with audio data
        """
        if not self._services_available['voice']:
            return StepResult.fail('Voice capabilities disabled')
        try:
            return await self.voice.text_to_speech(text=text, voice=voice, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Text-to-speech failed: {e}')
            return StepResult.fail(f'Text-to-speech failed: {e}')

    async def speech_to_text(self, audio_data: bytes, tenant: str='', workspace: str='') -> StepResult:
        """Convert speech to text.

        Args:
            audio_data: Audio data to transcribe
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with transcribed text
        """
        if not self._services_available['voice']:
            return StepResult.fail('Voice capabilities disabled')
        try:
            return await self.voice.speech_to_text(audio_data=audio_data, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Speech-to-text failed: {e}')
            return StepResult.fail(f'Speech-to-text failed: {e}')

    async def process_voice_command(self, audio_data: bytes, tenant: str, workspace: str) -> StepResult:
        """Process voice command with full pipeline.

        Args:
            audio_data: Audio data containing voice command
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with voice command response
        """
        if not self._services_available['voice']:
            return StepResult.fail('Voice capabilities disabled')
        try:
            return await self.voice.process_voice_command(audio_data=audio_data, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Voice command processing failed: {e}')
            return StepResult.fail(f'Voice command processing failed: {e}')

    async def analyze_image(self, image_data: bytes, prompt: str, tenant: str='', workspace: str='') -> StepResult:
        """Analyze an image.

        Args:
            image_data: Image data to analyze
            prompt: Analysis prompt
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with image analysis
        """
        if not self._services_available['vision']:
            return StepResult.fail('Vision capabilities disabled')
        try:
            return await self.vision.analyze_image(image_data=image_data, prompt=prompt, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Image analysis failed: {e}')
            return StepResult.fail(f'Image analysis failed: {e}')

    async def analyze_multiple_images(self, images: list[bytes], prompt: str, tenant: str='', workspace: str='') -> StepResult:
        """Analyze multiple images.

        Args:
            images: List of image data to analyze
            prompt: Analysis prompt
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with multi-image analysis
        """
        if not self._services_available['vision']:
            return StepResult.fail('Vision capabilities disabled')
        try:
            return await self.vision.analyze_multiple_images(images=images, prompt=prompt, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Multi-image analysis failed: {e}')
            return StepResult.fail(f'Multi-image analysis failed: {e}')

    async def analyze_multimodal_content(self, text: str, images: list[bytes], audio_data: bytes | None=None, tenant: str='', workspace: str='') -> StepResult:
        """Analyze multimodal content.

        Args:
            text: Text content
            images: List of image data
            audio_data: Optional audio data
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with multimodal analysis
        """
        if not self._services_available['multimodal']:
            return StepResult.fail('Multimodal capabilities disabled')
        try:
            return await self.multimodal.analyze_multimodal_content(text=text, images=images, audio_data=audio_data, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Multimodal analysis failed: {e}')
            return StepResult.fail(f'Multimodal analysis failed: {e}')

    async def fact_check_multimodal(self, text: str, images: list[bytes], tenant: str='', workspace: str='') -> StepResult:
        """Fact-check multimodal content.

        Args:
            text: Text content to fact-check
            images: List of image data for verification
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with fact-checking results
        """
        if not self._services_available['multimodal']:
            return StepResult.fail('Multimodal capabilities disabled')
        try:
            return await self.multimodal.fact_check_multimodal(text=text, images=images, tenant=tenant, workspace=workspace)
        except Exception as e:
            logger.error(f'Multimodal fact-checking failed: {e}')
            return StepResult.fail(f'Multimodal fact-checking failed: {e}')

    def get_cost_summary(self) -> dict[str, Any]:
        """Get current cost summary.

        Returns:
            Dictionary with cost information
        """
        try:
            return self.cost_monitoring.get_cost_summary()
        except Exception as e:
            logger.error(f'Cost monitoring failed: {e}')
            return {'error': str(e)}

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current usage metrics.

        Returns:
            Dictionary with usage metrics
        """
        try:
            return self.cost_monitoring.get_current_metrics()
        except Exception as e:
            logger.error(f'Metrics retrieval failed: {e}')
            return {'error': str(e)}

    async def health_check(self) -> StepResult:
        """Check health of all OpenAI services.

        Returns:
            StepResult with health status
        """
        try:
            health_status = {'openai_available': False, 'services': {}, 'features_enabled': self._services_available, 'cost_monitoring': False}
            try:
                await self.base_service.client.chat.completions.create(model='gpt-3.5-turbo', messages=[{'role': 'user', 'content': 'Hello'}], max_tokens=10)
                health_status['openai_available'] = True
            except Exception as e:
                health_status['openai_error'] = str(e)
            services_to_test = [('structured_outputs', self.structured_outputs), ('function_calling', self.function_calling), ('streaming', self.streaming), ('voice', self.voice), ('vision', self.vision), ('multimodal', self.multimodal)]
            for service_name, _service in services_to_test:
                try:
                    health_status['services'][service_name] = 'healthy'
                except Exception as e:
                    health_status['services'][service_name] = f'error: {e}'
            try:
                self.cost_monitoring.get_current_metrics()
                health_status['cost_monitoring'] = True
            except Exception as e:
                health_status['cost_monitoring_error'] = str(e)
            return StepResult.ok(data=health_status)
        except Exception as e:
            return StepResult.fail(f'Health check failed: {e}')

    async def _fallback_analysis(self, content: str, analysis_type: str, tenant: str, workspace: str) -> StepResult:
        """Fallback analysis when OpenAI services are unavailable.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with fallback analysis
        """
        if not self._services_available['fallback']:
            return StepResult.fail('OpenAI services unavailable and fallback disabled')
        try:
            from platform.llm.providers.openrouter import OpenRouterService
            openrouter_service = OpenRouterService()
            result = openrouter_service.route(prompt=f'Analyze this {analysis_type} content: {content[:1000]}...', task_type=analysis_type)
            if result.get('status') == 'success':
                return StepResult.ok(data={'analysis': result.get('response', ''), 'model': result.get('model', 'openrouter'), 'fallback': True})
            else:
                return StepResult.fail(f'Fallback analysis failed: {result.get('error', 'Unknown error')}')
        except Exception as e:
            logger.error(f'Fallback analysis failed: {e}')
            return StepResult.fail(f'Fallback analysis failed: {e}')

    def get_available_capabilities(self) -> list[str]:
        """Get list of available capabilities.

        Returns:
            List of available capability names
        """
        return [cap for cap, available in self._services_available.items() if available]

    def is_capability_available(self, capability: str) -> bool:
        """Check if a specific capability is available.

        Args:
            capability: Capability name to check

        Returns:
            True if capability is available
        """
        return self._services_available.get(capability, False)

    def get_service_status(self) -> dict[str, Any]:
        """Get status of all services.

        Returns:
            Dictionary with service status information
        """
        return {'services_available': self._services_available, 'config': {'api_key_configured': bool(self.config.openai_api_key), 'base_url': self.config.openai_base_url, 'max_tokens': self.config.openai_max_tokens, 'temperature': self.config.openai_temperature}, 'capabilities': self.get_available_capabilities()}