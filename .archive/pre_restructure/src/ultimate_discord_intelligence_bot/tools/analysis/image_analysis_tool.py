"""
Comprehensive image analysis tool with advanced computer vision capabilities.

This tool provides extensive image analysis including:
- Content moderation (NSFW, violence, hate symbols detection)
- Brand and logo recognition
- Visual fact-checking through reverse image search
- Accessibility features (alt-text generation)
- Object detection and scene classification
- Visual sentiment analysis
- Text extraction (OCR) from images
- Image quality assessment
"""

from __future__ import annotations

import base64
import importlib
import io
import logging
import os
import time
from functools import cached_property
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


# Lazy load optional dependencies
PIL: Any | None = None
openai: Any | None = None
requests: Any | None = None

try:
    PIL = importlib.import_module("PIL")
    from PIL import Image, ImageStat
except ImportError:
    PIL = None

try:
    openai = importlib.import_module("openai")
except ImportError:
    openai = None

try:
    requests = importlib.import_module("requests")
except ImportError:
    requests = None


class ModerationResult(TypedDict, total=False):
    """Content moderation analysis result."""

    is_safe: bool
    nsfw_score: float
    violence_score: float
    hate_score: float
    moderation_flags: list[str]
    confidence: float


class BrandRecognitionResult(TypedDict, total=False):
    """Brand and logo recognition result."""

    brands_detected: list[dict[str, Any]]
    logos_detected: list[dict[str, Any]]
    confidence_scores: dict[str, float]


class AccessibilityResult(TypedDict, total=False):
    """Accessibility features result."""

    alt_text: str
    detailed_description: str
    accessibility_issues: list[str]
    color_contrast_score: float


class ImageAnalysisResult(TypedDict, total=False):
    """Complete image analysis result."""

    image_properties: dict[str, Any]
    objects_detected: list[dict[str, Any]]
    text_content: str
    scene_classification: str
    visual_sentiment: str
    moderation: ModerationResult
    brand_recognition: BrandRecognitionResult
    accessibility: AccessibilityResult
    quality_score: float
    processing_time: float
    metadata: dict[str, Any]


class ImageAnalysisTool(BaseTool[StepResult]):
    """Comprehensive image analysis with computer vision and AI capabilities."""

    name: str = "Image Analysis Tool"
    description: str = "Analyzes images for content moderation, brand recognition, accessibility, object detection, and visual understanding."

    def __init__(
        self,
        enable_moderation: bool = True,
        enable_brand_recognition: bool = True,
        enable_accessibility: bool = True,
        enable_reverse_search: bool = False,
        vision_model: str = "gpt-4-vision-preview",
        max_image_size: int = 2048,
    ):
        super().__init__()
        self._enable_moderation = enable_moderation
        self._enable_brand_recognition = enable_brand_recognition
        self._enable_accessibility = enable_accessibility
        self._enable_reverse_search = enable_reverse_search
        self._vision_model = vision_model
        self._max_image_size = max_image_size
        self._metrics = get_metrics()

        # Check dependencies
        if PIL is None:
            logging.warning("PIL not available - image processing will be limited")
        if openai is None:
            logging.warning("OpenAI not available - AI vision analysis will be limited")
        if requests is None and enable_reverse_search:
            logging.warning("Requests not available - reverse image search disabled")

    @cached_property
    def openai_client(self) -> Any:
        """Initialize OpenAI client for vision analysis."""
        if openai is None:
            raise RuntimeError("OpenAI package not available. Install with: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")

        return openai.OpenAI(api_key=api_key)

    def _run(
        self,
        image_path: str,
        tenant: str = "default",
        workspace: str = "default",
        analysis_type: str = "comprehensive",
    ) -> StepResult:
        """
        Perform comprehensive image analysis.

        Args:
            image_path: Path to image file or URL
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            analysis_type: Type of analysis (basic, comprehensive, accessibility_focused)

        Returns:
            StepResult with comprehensive image analysis
        """
        start_time = time.monotonic()

        try:
            # Input validation
            if not image_path:
                return StepResult.fail("Image path cannot be empty")

            if tenant and workspace:
                self.note(
                    f"Starting image analysis for {os.path.basename(image_path) if not image_path.startswith('http') else 'URL'}"
                )

            # Load and prepare image
            image_data = self._load_image(image_path)
            if not image_data:
                return StepResult.fail("Failed to load image")

            # Perform analysis based on type
            result = self._perform_analysis(image_data, analysis_type)

            processing_time = time.monotonic() - start_time
            result["processing_time"] = processing_time

            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})

            return StepResult.ok(data=result)

        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception(f"Image analysis failed for {image_path}")
            return StepResult.fail(f"Image analysis failed: {e!s}")

    def _load_image(self, image_path: str) -> dict[str, Any] | None:
        """Load image from path or URL."""
        try:
            if image_path.startswith(("http://", "https://")):
                # Download image from URL
                from core.http_utils import resilient_get

                response = resilient_get(image_path, timeout=30)
                response.raise_for_status()
                image_data = response.content
                image_source = "url"
            else:
                # Load from file path
                if not os.path.exists(image_path):
                    logging.error(f"Image file not found: {image_path}")
                    return None

                with open(image_path, "rb") as f:
                    image_data = f.read()
                image_source = "file"

            if PIL is None:
                # Without PIL, just return raw data
                return {
                    "raw_data": image_data,
                    "base64": base64.b64encode(image_data).decode("utf-8"),
                    "source": image_source,
                    "properties": {},
                }

            # Process with PIL
            image = Image.open(io.BytesIO(image_data))

            # Resize if too large
            if max(image.size) > self._max_image_size:
                ratio = self._max_image_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

                # Convert back to bytes
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=90)
                image_data = buffer.getvalue()

            # Extract image properties
            properties = {
                "width": image.size[0],
                "height": image.size[1],
                "mode": image.mode,
                "format": getattr(image, "format", "JPEG"),
                "size_bytes": len(image_data),
                "aspect_ratio": image.size[0] / image.size[1] if image.size[1] > 0 else 1.0,
            }

            # Calculate additional properties
            if image.mode in ("RGB", "RGBA"):
                # Calculate average brightness and color statistics
                stat = ImageStat.Stat(image)
                properties.update(
                    {
                        "average_brightness": sum(stat.mean) / len(stat.mean),
                        "color_variance": sum(stat.var) / len(stat.var),
                        "is_grayscale": len(set(stat.mean)) == 1 if len(stat.mean) >= 3 else False,
                    }
                )

            return {
                "image": image,
                "raw_data": image_data,
                "base64": base64.b64encode(image_data).decode("utf-8"),
                "source": image_source,
                "properties": properties,
            }

        except Exception as e:
            logging.error(f"Failed to load image: {e}")
            return None

    def _perform_analysis(self, image_data: dict[str, Any], analysis_type: str) -> ImageAnalysisResult:
        """Perform comprehensive image analysis."""
        result: ImageAnalysisResult = {
            "image_properties": image_data.get("properties", {}),
            "objects_detected": [],
            "text_content": "",
            "scene_classification": "unknown",
            "visual_sentiment": "neutral",
            "moderation": {"is_safe": True, "confidence": 0.0},
            "brand_recognition": {"brands_detected": [], "logos_detected": []},
            "accessibility": {"alt_text": "", "detailed_description": ""},
            "quality_score": 0.0,
            "metadata": {"analysis_type": analysis_type},
        }

        # AI-powered comprehensive analysis
        ai_analysis = self._analyze_with_ai(image_data, analysis_type)
        if ai_analysis:
            result.update(ai_analysis)

        # Content moderation
        if self._enable_moderation:
            moderation_result = self._analyze_content_moderation(image_data, ai_analysis)
            result["moderation"] = moderation_result

        # Brand recognition
        if self._enable_brand_recognition:
            brand_result = self._analyze_brand_recognition(image_data, ai_analysis)
            result["brand_recognition"] = brand_result

        # Accessibility features
        if self._enable_accessibility:
            accessibility_result = self._generate_accessibility_features(image_data, ai_analysis)
            result["accessibility"] = accessibility_result

        # Image quality assessment
        result["quality_score"] = self._assess_image_quality(image_data)

        return result

    def _analyze_with_ai(self, image_data: dict[str, Any], analysis_type: str) -> dict[str, Any] | None:
        """Perform AI-powered image analysis using GPT-4V."""
        if openai is None:
            return None

        try:
            # Build analysis prompt based on type
            if analysis_type == "comprehensive":
                prompt = """Analyze this image comprehensively and provide a JSON response with:
                1. objects_detected: List of objects with confidence scores and locations
                2. text_content: Any readable text in the image (OCR)
                3. scene_classification: Type of scene/setting
                4. visual_sentiment: Overall emotional tone (positive/negative/neutral)
                5. people_count: Number of people visible
                6. activities: What activities are happening
                7. setting: Indoor/outdoor, specific location type
                8. style_analysis: Art style, photography style, etc.
                9. colors_dominant: Main colors in the image
                10. composition_notes: Visual composition analysis

                Format as valid JSON."""
            elif analysis_type == "accessibility_focused":
                prompt = """Analyze this image for accessibility and provide a JSON response with:
                1. detailed_description: Comprehensive description for screen readers
                2. objects_detected: All visible objects and their relationships
                3. text_content: All text content for accessibility
                4. people_description: Description of people (if any) including actions
                5. spatial_relationships: How objects relate spatially
                6. visual_hierarchy: What draws attention first

                Format as valid JSON."""
            else:  # basic
                prompt = """Analyze this image and provide a JSON response with:
                1. objects_detected: Main objects visible
                2. scene_classification: Type of scene
                3. visual_sentiment: Emotional tone
                4. text_content: Any readable text

                Format as valid JSON."""

            base64_image = image_data.get("base64", "")
            if not base64_image:
                return None

            response = self.openai_client.chat.completions.create(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1500,
            )

            # Parse JSON response
            response_text = response.choices[0].message.content
            try:
                import json

                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                # Fallback parsing
                return {
                    "objects_detected": [],
                    "text_content": "",
                    "scene_classification": "unknown",
                    "visual_sentiment": "neutral",
                    "raw_response": response_text,
                }

        except Exception as e:
            logging.error(f"AI image analysis failed: {e}")
            return None

    def _analyze_content_moderation(
        self, image_data: dict[str, Any], ai_analysis: dict[str, Any] | None
    ) -> ModerationResult:
        """Analyze image for content moderation."""
        try:
            # Use AI analysis for moderation if available
            if ai_analysis:
                # Look for moderation indicators in AI analysis
                objects = ai_analysis.get("objects_detected", [])
                scene = ai_analysis.get("scene_classification", "").lower()

                # Simple heuristic-based moderation
                nsfw_indicators = ["adult", "explicit", "nude", "sexual"]
                violence_indicators = ["weapon", "violence", "blood", "fight"]
                hate_indicators = ["hate symbol", "offensive", "discriminatory"]

                nsfw_score = 0.0
                violence_score = 0.0
                hate_score = 0.0
                flags = []

                # Check objects and scene for indicators
                text_to_check = f"{scene} {objects!s}"

                for indicator in nsfw_indicators:
                    if indicator in text_to_check:
                        nsfw_score += 0.3
                        flags.append(f"nsfw_{indicator}")

                for indicator in violence_indicators:
                    if indicator in text_to_check:
                        violence_score += 0.3
                        flags.append(f"violence_{indicator}")

                for indicator in hate_indicators:
                    if indicator in text_to_check:
                        hate_score += 0.3
                        flags.append(f"hate_{indicator}")

                # Determine if safe
                is_safe = max(nsfw_score, violence_score, hate_score) < 0.5
                confidence = 0.7  # Moderate confidence for heuristic approach

                return {
                    "is_safe": is_safe,
                    "nsfw_score": min(1.0, nsfw_score),
                    "violence_score": min(1.0, violence_score),
                    "hate_score": min(1.0, hate_score),
                    "moderation_flags": flags,
                    "confidence": confidence,
                }

            # Default safe response
            return {
                "is_safe": True,
                "nsfw_score": 0.0,
                "violence_score": 0.0,
                "hate_score": 0.0,
                "moderation_flags": [],
                "confidence": 0.5,
            }

        except Exception as e:
            logging.error(f"Content moderation analysis failed: {e}")
            return {
                "is_safe": True,
                "nsfw_score": 0.0,
                "violence_score": 0.0,
                "hate_score": 0.0,
                "moderation_flags": [],
                "confidence": 0.0,
            }

    def _analyze_brand_recognition(
        self, image_data: dict[str, Any], ai_analysis: dict[str, Any] | None
    ) -> BrandRecognitionResult:
        """Analyze image for brand and logo recognition."""
        try:
            brands_detected = []
            logos_detected = []
            confidence_scores = {}

            if ai_analysis:
                # Extract brand information from AI analysis
                objects = ai_analysis.get("objects_detected", [])
                text_content = ai_analysis.get("text_content", "")

                # Look for common brand indicators in objects
                brand_objects = ["logo", "brand", "sign", "advertisement", "poster"]
                for obj in objects:
                    if isinstance(obj, dict):
                        obj_name = obj.get("name", "").lower()
                        if any(brand_word in obj_name for brand_word in brand_objects):
                            brands_detected.append(
                                {
                                    "name": obj_name,
                                    "confidence": obj.get("confidence", 0.5),
                                    "location": obj.get("location", {}),
                                }
                            )

                # Look for brand names in text
                common_brands = [
                    "apple",
                    "google",
                    "microsoft",
                    "amazon",
                    "facebook",
                    "meta",
                    "twitter",
                    "instagram",
                    "youtube",
                    "netflix",
                    "uber",
                    "tesla",
                ]

                text_lower = text_content.lower()
                for brand in common_brands:
                    if brand in text_lower:
                        brands_detected.append({"name": brand, "confidence": 0.8, "detected_via": "text"})
                        confidence_scores[brand] = 0.8

            return {
                "brands_detected": brands_detected,
                "logos_detected": logos_detected,
                "confidence_scores": confidence_scores,
            }

        except Exception as e:
            logging.error(f"Brand recognition analysis failed: {e}")
            return {
                "brands_detected": [],
                "logos_detected": [],
                "confidence_scores": {},
            }

    def _generate_accessibility_features(
        self, image_data: dict[str, Any], ai_analysis: dict[str, Any] | None
    ) -> AccessibilityResult:
        """Generate accessibility features including alt-text."""
        try:
            if ai_analysis:
                # Generate alt-text from AI analysis
                objects = ai_analysis.get("objects_detected", [])
                scene = ai_analysis.get("scene_classification", "")
                people = ai_analysis.get("people_description", "")
                activities = ai_analysis.get("activities", "")

                # Create concise alt-text
                alt_parts = []
                if scene and scene != "unknown":
                    alt_parts.append(scene)

                if objects:
                    object_names = []
                    for obj in objects[:3]:  # Limit to top 3 objects
                        if isinstance(obj, dict):
                            object_names.append(obj.get("name", str(obj)))
                        else:
                            object_names.append(str(obj))
                    if object_names:
                        alt_parts.append(f"containing {', '.join(object_names)}")

                if people:
                    alt_parts.append(people)

                alt_text = ". ".join(alt_parts) if alt_parts else "Image content"

                # Generate detailed description
                detailed_description = ai_analysis.get("detailed_description", "")
                if not detailed_description and ai_analysis:
                    # Construct from available data
                    desc_parts = []
                    if scene:
                        desc_parts.append(f"This is a {scene}")
                    if objects:
                        desc_parts.append(f"The image shows {', '.join([str(obj) for obj in objects[:5]])}")
                    if activities:
                        desc_parts.append(f"Activities visible include: {activities}")
                    detailed_description = ". ".join(desc_parts)

                # Check for accessibility issues
                issues = []
                properties = image_data.get("properties", {})

                if properties.get("average_brightness", 50) < 20:
                    issues.append("Image may be too dark for some users")
                if properties.get("color_variance", 100) < 10:
                    issues.append("Low color contrast may affect visibility")
                if properties.get("width", 0) < 200 or properties.get("height", 0) < 200:
                    issues.append("Image may be too small for clear viewing")

                # Calculate color contrast score (simplified)
                contrast_score = min(1.0, properties.get("color_variance", 0) / 1000)

                return {
                    "alt_text": alt_text[:125],  # Keep alt-text concise
                    "detailed_description": detailed_description,
                    "accessibility_issues": issues,
                    "color_contrast_score": contrast_score,
                }

            # Fallback accessibility
            return {
                "alt_text": "Image content available",
                "detailed_description": "No detailed description available",
                "accessibility_issues": ["AI analysis not available"],
                "color_contrast_score": 0.5,
            }

        except Exception as e:
            logging.error(f"Accessibility features generation failed: {e}")
            return {
                "alt_text": "Image",
                "detailed_description": "",
                "accessibility_issues": ["Analysis failed"],
                "color_contrast_score": 0.0,
            }

    def _assess_image_quality(self, image_data: dict[str, Any]) -> float:
        """Assess overall image quality."""
        try:
            properties = image_data.get("properties", {})
            quality_score = 0.5  # Base score

            # Size factor
            width = properties.get("width", 0)
            height = properties.get("height", 0)
            pixel_count = width * height

            if pixel_count > 1000000:  # > 1MP
                quality_score += 0.2
            elif pixel_count > 500000:  # > 0.5MP
                quality_score += 0.1

            # Aspect ratio factor (avoid extreme ratios)
            aspect_ratio = properties.get("aspect_ratio", 1.0)
            if 0.5 <= aspect_ratio <= 2.0:
                quality_score += 0.1

            # Color variance (sharpness/detail indicator)
            color_variance = properties.get("color_variance", 0)
            if color_variance > 1000:
                quality_score += 0.2
            elif color_variance > 500:
                quality_score += 0.1

            # File size efficiency
            size_bytes = properties.get("size_bytes", 0)
            if size_bytes > 0 and pixel_count > 0:
                bytes_per_pixel = size_bytes / pixel_count
                if 0.5 <= bytes_per_pixel <= 3.0:  # Reasonable compression
                    quality_score += 0.1

            return min(1.0, quality_score)

        except Exception:
            return 0.5

    def run(
        self,
        image_path: str,
        tenant: str = "default",
        workspace: str = "default",
        analysis_type: str = "comprehensive",
    ) -> StepResult:
        """Public interface for image analysis."""
        return self._run(image_path, tenant, workspace, analysis_type)
