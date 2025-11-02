"""OpenAI voice service for speech-to-speech capabilities."""
from __future__ import annotations
import io
from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from platform.core.step_result import StepResult

class OpenAIVoiceService(OpenAIService):
    """Service for OpenAI voice capabilities."""

    def __init__(self):
        super().__init__()
        self.voice_model = 'tts-1'
        self.voice_quality = 'hd'

    async def text_to_speech(self, text: str, voice: str='alloy', tenant: str='', workspace: str='') -> StepResult:
        """Convert text to speech using OpenAI TTS."""
        if not self._is_feature_enabled('ENABLE_OPENAI_VOICE'):
            return StepResult.fail('OpenAI voice features are disabled')
        try:
            response = await self.client.audio.speech.create(model='tts-1', voice=voice, input=text, response_format='mp3')
            audio_data = response.content
            return StepResult.ok(data={'audio_data': audio_data, 'format': 'mp3', 'voice': voice})
        except Exception as e:
            return StepResult.fail(f'Text-to-speech failed: {e!s}')

    async def speech_to_text(self, audio_data: bytes, tenant: str='', workspace: str='') -> StepResult:
        """Convert speech to text using OpenAI Whisper."""
        if not self._is_feature_enabled('ENABLE_OPENAI_VOICE'):
            return StepResult.fail('OpenAI voice features are disabled')
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = 'audio.wav'
            response = await self.client.audio.transcriptions.create(model='whisper-1', file=audio_file, response_format='text')
            return StepResult.ok(data={'text': response, 'confidence': 0.95})
        except Exception as e:
            return StepResult.fail(f'Speech-to-text failed: {e!s}')

    async def process_voice_command(self, audio_data: bytes, tenant: str, workspace: str) -> StepResult:
        """Process voice command with speech-to-text and response generation."""
        if not self._is_feature_enabled('ENABLE_OPENAI_VOICE'):
            return StepResult.fail('OpenAI voice features are disabled')
        try:
            stt_result = await self.speech_to_text(audio_data, tenant, workspace)
            if not stt_result.success:
                return stt_result
            text = stt_result.data['text']
            response = await self.client.chat.completions.create(model='gpt-4o-mini', messages=[{'role': 'system', 'content': f'You are a helpful Discord bot assistant. Respond to voice commands concisely. Tenant: {tenant}, Workspace: {workspace}'}, {'role': 'user', 'content': text}], max_tokens=500, temperature=0.7)
            response_text = response.choices[0].message.content
            tts_result = await self.text_to_speech(response_text, tenant=tenant, workspace=workspace)
            if not tts_result.success:
                return tts_result
            return StepResult.ok(data={'original_text': text, 'response_text': response_text, 'audio_response': tts_result.data['audio_data'], 'format': 'mp3'})
        except Exception as e:
            return StepResult.fail(f'Voice command processing failed: {e!s}')

    async def analyze_voice_content(self, audio_data: bytes, analysis_type: str, tenant: str, workspace: str) -> StepResult:
        """Analyze voice content for debate analysis."""
        if not self._is_feature_enabled('ENABLE_OPENAI_VOICE'):
            return StepResult.fail('OpenAI voice features are disabled')
        try:
            stt_result = await self.speech_to_text(audio_data, tenant, workspace)
            if not stt_result.success:
                return stt_result
            text = stt_result.data['text']
            from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
            structured_service = OpenAIStructuredOutputsService()
            analysis_result = await structured_service.analyze_content_structured(content=text, analysis_type=analysis_type, tenant=tenant, workspace=workspace)
            if not analysis_result.success:
                return analysis_result
            analysis_data = analysis_result.data
            analysis_data['voice_analysis'] = {'transcription_confidence': stt_result.data['confidence'], 'audio_processed': True}
            return StepResult.ok(data=analysis_data)
        except Exception as e:
            return StepResult.fail(f'Voice content analysis failed: {e!s}')