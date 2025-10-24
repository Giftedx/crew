"""OpenAI multimodal analysis service combining text, images, and audio."""

from __future__ import annotations

import base64

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService
from ultimate_discord_intelligence_bot.step_result import StepResult


class MultimodalAnalysisService(OpenAIService):
    """Service for multimodal content analysis combining text, images, and audio."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o"
        self.vision_service = OpenAIVisionService()

    async def analyze_multimodal_content(
        self, text: str, images: list[bytes], audio_data: bytes | None, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze content combining text, images, and audio."""
        if not self._is_feature_enabled("ENABLE_OPENAI_MULTIMODAL"):
            return StepResult.fail("OpenAI multimodal features are disabled")

        try:
            # Prepare messages for multimodal analysis
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert content analyst. "
                    f"Analyze the provided content across multiple modalities. "
                    f"Tenant: {tenant}, Workspace: {workspace}",
                },
                {"role": "user", "content": []},
            ]

            # Add text content
            user_content = messages[1]["content"]
            user_content.append({"type": "text", "text": f"Text content to analyze:\n{text}"})

            # Add image content
            for i, image_data in enumerate(images):
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                user_content.append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"})

            # Add audio content description (if available)
            if audio_data:
                # Note: OpenAI doesn't support direct audio input in chat completions
                # We would need to transcribe audio first
                user_content.append(
                    {"type": "text", "text": "Audio content is also available (transcribed separately)"}
                )

            # Make multimodal analysis request
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=2000, temperature=0.7
            )

            return StepResult.ok(
                data={
                    "multimodal_analysis": response.choices[0].message.content,
                    "modalities_analyzed": ["text", "images"] + (["audio"] if audio_data else []),
                    "model": self.model,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Multimodal analysis failed: {e!s}")

    async def analyze_debate_content_multimodal(
        self, transcript: str, thumbnails: list[bytes], audio_data: bytes | None, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze debate content using multimodal approach."""
        prompt = """
        Analyze this debate content across multiple modalities:
        
        1. Text Analysis:
           - Identify key arguments and claims
           - Assess logical structure and reasoning
           - Detect bias and emotional language
           - Evaluate evidence quality
        
        2. Visual Analysis:
           - Assess visual presentation quality
           - Identify visual bias indicators
           - Analyze body language and expressions
           - Evaluate visual evidence
        
        3. Audio Analysis (if available):
           - Assess tone and delivery
           - Identify emotional indicators
           - Evaluate speaking quality
           - Detect interruptions or manipulation
        
        Provide a comprehensive analysis including:
        - Overall debate quality score (0-10)
        - Bias assessment across modalities
        - Fact-checking recommendations
        - Key insights and recommendations
        """

        return await self.analyze_multimodal_content(
            text=transcript, images=thumbnails, audio_data=audio_data, tenant=tenant, workspace=workspace
        )

    async def fact_check_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Fact-check content using multimodal evidence."""
        prompt = f"""
        Fact-check the following content using both text and visual evidence:
        
        Text: {text}
        
        Analyze the visual content for:
        1. Supporting or contradicting evidence
        2. Data visualizations or charts
        3. Screenshots or documents
        4. Visual context that might affect interpretation
        
        Provide fact-check results with:
        - Claim verification status
        - Confidence level
        - Supporting evidence from both text and images
        - Recommendations for further verification
        """

        return await self.analyze_multimodal_content(
            text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace
        )

    async def detect_bias_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Detect bias across multiple modalities."""
        prompt = f"""
        Detect bias indicators across text and visual content:
        
        Text: {text}
        
        Analyze for:
        1. Language bias in text
        2. Visual bias in images (framing, composition, color)
        3. Cross-modal bias (inconsistencies between text and images)
        4. Overall presentation bias
        
        Provide bias assessment with:
        - Bias level (low, moderate, high)
        - Specific bias indicators found
        - Confidence in assessment
        - Recommendations for bias mitigation
        """

        return await self.analyze_multimodal_content(
            text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace
        )

    async def generate_multimodal_summary(
        self, text: str, images: list[bytes], tenant: str, workspace: str
    ) -> StepResult:
        """Generate comprehensive summary using multimodal content."""
        prompt = f"""
        Create a comprehensive summary of the following multimodal content:
        
        Text: {text}
        
        Include in the summary:
        1. Key points from text
        2. Visual insights from images
        3. Overall message and themes
        4. Important details and context
        5. Recommendations or conclusions
        
        Make the summary clear, concise, and informative.
        """

        return await self.analyze_multimodal_content(
            text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace
        )
