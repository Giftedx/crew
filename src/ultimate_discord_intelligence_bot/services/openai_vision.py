"""OpenAI vision service for image and video analysis."""

from __future__ import annotations

import base64

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.step_result import StepResult


class OpenAIVisionService(OpenAIService):
    """Service for OpenAI vision capabilities."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o"  # Vision model

    async def analyze_image(self, image_data: bytes, prompt: str, tenant: str, workspace: str) -> StepResult:
        """Analyze image using OpenAI vision."""
        if not self._is_feature_enabled("ENABLE_OPENAI_VISION"):
            return StepResult.fail("OpenAI vision features are disabled")

        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{prompt}\nTenant: {tenant}, Workspace: {workspace}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        ],
                    }
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return StepResult.ok(data={"analysis": response.choices[0].message.content, "model": self.model})

        except Exception as e:
            return StepResult.fail(f"Image analysis failed: {e!s}")

    async def analyze_video_frame(self, frame_data: bytes, prompt: str, tenant: str, workspace: str) -> StepResult:
        """Analyze video frame using OpenAI vision."""
        return await self.analyze_image(frame_data, prompt, tenant, workspace)

    async def analyze_thumbnail(self, thumbnail_data: bytes, video_url: str, tenant: str, workspace: str) -> StepResult:
        """Analyze video thumbnail for content understanding."""
        prompt = f"""
        Analyze this video thumbnail and provide insights about:
        1. Content type (debate, news, entertainment, etc.)
        2. Visual elements that might indicate bias
        3. Key themes or topics visible
        4. Overall quality and professionalism
        5. Any text or captions visible
        
        Video URL: {video_url}
        """

        return await self.analyze_image(thumbnail_data, prompt, tenant, workspace)

    async def analyze_multiple_images(
        self, images: list[bytes], prompt: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze multiple images for comprehensive understanding."""
        if not self._is_feature_enabled("ENABLE_OPENAI_VISION"):
            return StepResult.fail("OpenAI vision features are disabled")

        try:
            # Prepare content with multiple images
            content = [{"type": "text", "text": f"{prompt}\nTenant: {tenant}, Workspace: {workspace}"}]

            for i, image_data in enumerate(images):
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                content.append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"})

            response = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": content}], max_tokens=1500, temperature=0.7
            )

            return StepResult.ok(
                data={"analysis": response.choices[0].message.content, "model": self.model, "image_count": len(images)}
            )

        except Exception as e:
            return StepResult.fail(f"Multiple image analysis failed: {e!s}")

    async def extract_text_from_image(self, image_data: bytes, tenant: str, workspace: str) -> StepResult:
        """Extract text from image using OpenAI vision."""
        prompt = """
        Extract all text visible in this image. Return the text exactly as it appears,
        maintaining line breaks and formatting where possible.
        """

        return await self.analyze_image(image_data, prompt, tenant, workspace)

    async def detect_bias_in_visual_content(self, image_data: bytes, tenant: str, workspace: str) -> StepResult:
        """Detect bias indicators in visual content."""
        prompt = """
        Analyze this image for potential bias indicators:
        1. Visual composition and framing
        2. Color choices and symbolism
        3. Text or captions that might be biased
        4. Overall presentation style
        5. Any elements that might influence perception
        
        Provide a bias assessment with confidence level.
        """

        return await self.analyze_image(image_data, prompt, tenant, workspace)
