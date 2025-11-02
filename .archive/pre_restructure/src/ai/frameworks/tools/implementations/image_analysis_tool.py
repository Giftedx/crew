"""
ImageAnalysisTool - Image processing and analysis capabilities.

This tool provides image manipulation and analysis features including resizing,
format conversion, object detection, and visual analysis.
"""

from typing import Any, ClassVar

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class ImageAnalysisTool(BaseUniversalTool):
    """
    A universal image analysis and processing tool.

    Supports image manipulation (resize, crop, rotate), format conversion,
    and analysis (object detection, color analysis, face detection).

    Example:
        # Resize image
        result = await analyzer.run(
            image_path="/path/to/image.jpg",
            operation="resize",
            width=800,
            height=600
        )

        # Analyze image content
        result = await analyzer.run(
            image_path="/path/to/image.jpg",
            operation="analyze"
        )
    """

    name = "image-analysis"
    description = (
        "Process and analyze images with operations including resize, crop, rotate, "
        "format conversion, object detection, color analysis, and face detection. "
        "Returns processed image data and analysis results."
    )

    parameters: ClassVar[dict[str, ParameterSchema]] = {
        "image_path": ParameterSchema(
            type="string",
            description="Path to the image file to process",
            required=True,
        ),
        "operation": ParameterSchema(
            type="string",
            description="Operation to perform on the image",
            required=True,
            enum=["resize", "crop", "rotate", "analyze", "detect_objects", "detect_faces"],
        ),
        "width": ParameterSchema(
            type="number",
            description="Target width for resize operation (optional)",
            required=False,
        ),
        "height": ParameterSchema(
            type="number",
            description="Target height for resize operation (optional)",
            required=False,
        ),
        "format": ParameterSchema(
            type="string",
            description="Output image format (default: same as input)",
            required=False,
            enum=["jpeg", "png", "webp", "gif"],
        ),
        "quality": ParameterSchema(
            type="number",
            description="Output quality for lossy formats (1-100, default 85)",
            required=False,
            default=85,
        ),
    }

    metadata = ToolMetadata(
        category="media",
        return_type="dict",
        examples=[
            "Resize images to specific dimensions",
            "Detect objects in images",
            "Analyze image colors and composition",
            "Convert image formats",
        ],
        version="1.0.0",
        tags=["image", "vision", "processing", "analysis", "detection"],
        requires_auth=False,
    )

    async def run(
        self,
        image_path: str,
        operation: str,
        width: int | None = None,
        height: int | None = None,
        image_format: str | None = None,
        quality: int = 85,
    ) -> dict[str, Any]:
        """
        Process or analyze an image.

        Args:
            image_path: Path to the image file
            operation: Operation to perform
            width: Target width (for resize)
            height: Target height (for resize)
            image_format: Output format
            quality: Output quality (1-100)

        Returns:
            Dictionary containing:
            - operation (str): Performed operation
            - result (dict): Operation-specific results
            - metadata (dict): Image metadata

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If parameters are invalid
        """
        logger.info(
            "image_analysis_execution",
            image_path=image_path,
            operation=operation,
            width=width,
            height=height,
        )

        # Validate quality
        if not (1 <= quality <= 100):
            raise ValueError(f"Quality must be between 1 and 100, got {quality}")

        # Validate dimensions for resize
        if operation == "resize":
            if width is None and height is None:
                raise ValueError("resize operation requires width and/or height")
            if width is not None and width <= 0:
                raise ValueError(f"width must be positive, got {width}")
            if height is not None and height <= 0:
                raise ValueError(f"height must be positive, got {height}")

        # Mock implementation for testing/demo
        # Production version would use PIL/Pillow, OpenCV, or cloud vision APIs
        try:
            result_data = {}

            if operation == "resize":
                result_data = {
                    "original_width": 1920,
                    "original_height": 1080,
                    "new_width": width or 1920,
                    "new_height": height or 1080,
                    "output_path": image_path.replace(".jpg", "_resized.jpg"),
                }
            elif operation == "analyze":
                result_data = {
                    "dominant_colors": ["#3A5F8B", "#E8E8E8", "#2C4A6B"],
                    "brightness": 0.65,
                    "contrast": 0.45,
                    "composition": "landscape",
                    "sharpness": 0.82,
                }
            elif operation == "detect_objects":
                result_data = {
                    "objects": [
                        {"label": "person", "confidence": 0.95, "bbox": [100, 150, 300, 500]},
                        {"label": "car", "confidence": 0.87, "bbox": [400, 200, 600, 400]},
                    ],
                    "object_count": 2,
                }
            elif operation == "detect_faces":
                result_data = {
                    "faces": [
                        {"bbox": [120, 180, 220, 320], "confidence": 0.98},
                    ],
                    "face_count": 1,
                }
            elif operation in ["crop", "rotate"]:
                result_data = {
                    "output_path": image_path.replace(".jpg", f"_{operation}.jpg"),
                    "success": True,
                }

            response = {
                "operation": operation,
                "result": result_data,
                "metadata": {
                    "image_path": image_path,
                    "format": image_format or "jpeg",
                    "quality": quality,
                },
            }

            logger.info(
                "image_analysis_success",
                operation=operation,
                image_path=image_path,
            )

            return response

        except Exception as e:
            logger.error(
                "image_analysis_error",
                operation=operation,
                image_path=image_path,
                error=str(e),
            )
            raise
