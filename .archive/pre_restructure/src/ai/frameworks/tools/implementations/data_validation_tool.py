"""Universal data validation tool compatible with all frameworks."""

from __future__ import annotations

import re
from typing import Any, ClassVar

import structlog

from ai.frameworks.tools import BaseUniversalTool, ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class DataValidationTool(BaseUniversalTool):
    """Universal data validation tool for common validation patterns.

    This tool validates various data types (email, URL, phone, credit card, etc.)
    and works across all supported AI frameworks.

    Example:
        ```python
        tool = DataValidationTool()
        is_valid = await tool.run(data_type="email", value="test@example.com")
        ```
    """

    name = "data-validation"
    description = "Validate common data types including email addresses, URLs, phone numbers, credit cards, dates, and custom regex patterns."

    parameters: ClassVar[dict[str, ParameterSchema]] = {
        "data_type": ParameterSchema(
            type="string",
            description="Type of data to validate",
            required=True,
            enum=["email", "url", "phone", "credit_card", "date", "ipv4", "ipv6", "regex"],
        ),
        "value": ParameterSchema(
            type="string",
            description="Value to validate",
            required=True,
        ),
        "pattern": ParameterSchema(
            type="string",
            description="Custom regex pattern (only for data_type='regex')",
            required=False,
        ),
    }

    metadata = ToolMetadata(
        category="data",
        return_type="dict",
        examples=[
            {
                "data_type": "email",
                "value": "user@example.com",
                "result": {"valid": True, "message": "Valid email address"},
            },
            {
                "data_type": "url",
                "value": "https://example.com",
                "result": {"valid": True, "message": "Valid URL"},
            },
        ],
        requires_auth=False,
        version="1.0.0",
        tags=["validation", "data-quality", "regex", "verification"],
    )

    # Validation patterns
    PATTERNS: ClassVar[dict[str, str]] = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "url": r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$",
        "phone": r"^\+?1?\d{9,15}$",
        "credit_card": r"^\d{13,19}$",
        "date": r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
        "ipv4": r"^(\d{1,3}\.){3}\d{1,3}$",
        "ipv6": r"^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$",
    }

    async def run(
        self,
        data_type: str,
        value: str,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """Validate data.

        Args:
            data_type: Type of data to validate
            value: Value to validate
            pattern: Custom regex pattern (for data_type='regex')

        Returns:
            Dictionary with validation result:
            - valid: Boolean indicating if value is valid
            - message: Human-readable validation message
            - details: Additional validation details (optional)

        Raises:
            ValueError: If data_type is invalid or pattern is missing for regex type
        """
        logger.info(
            "data_validation_executing",
            data_type=data_type,
            value_length=len(value),
        )

        try:
            if data_type == "regex":
                if pattern is None:
                    raise ValueError("pattern parameter required for regex data_type")
                regex_pattern = pattern
            elif data_type in self.PATTERNS:
                regex_pattern = self.PATTERNS[data_type]
            else:
                raise ValueError(f"Unknown data_type: {data_type}")

            # Perform validation
            is_valid = bool(re.match(regex_pattern, value))

            # Build result
            result = {
                "valid": is_valid,
                "message": self._get_validation_message(data_type, is_valid),
                "data_type": data_type,
            }

            # Add specific validation details
            if data_type == "email" and is_valid:
                result["details"] = {
                    "domain": value.split("@")[1] if "@" in value else None,
                }
            elif data_type == "ipv4" and is_valid:
                result["details"] = {
                    "octets": value.split("."),
                }

            logger.info(
                "data_validation_completed",
                data_type=data_type,
                is_valid=is_valid,
            )

            return result

        except Exception as e:
            logger.error(
                "data_validation_failed",
                data_type=data_type,
                error=str(e),
                exc_info=True,
            )
            raise

    def _get_validation_message(self, data_type: str, is_valid: bool) -> str:
        """Get human-readable validation message."""
        if is_valid:
            return f"Valid {data_type}"
        else:
            return f"Invalid {data_type} format"
