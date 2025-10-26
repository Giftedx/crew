"""Result processing and transformation pipeline.

This module provides comprehensive result processing capabilities for transforming,
validating, and optimizing results from various tools and agents.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .step_result import StepResult


if TYPE_CHECKING:
    from .tenancy.context import TenantContext


logger = logging.getLogger(__name__)


class ResultProcessor:
    """Base result processor for transforming and validating results."""

    def __init__(self, tenant_context: TenantContext):
        """Initialize result processor with tenant context.

        Args:
            tenant_context: Tenant context for data isolation
        """
        self.tenant_context = tenant_context
        self.processors: list[Any] = []
        self._initialize_processors()

    def _initialize_processors(self) -> None:
        """Initialize processing pipeline."""
        self.processors = [
            ValidationProcessor(),
            TransformationProcessor(),
            QualityProcessor(),
            OptimizationProcessor(),
            FormattingProcessor(),
        ]

    def process_result(
        self,
        result: StepResult,
        result_type: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Process result through the processing pipeline.

        Args:
            result: Result to process
            result_type: Type of result (analysis, verification, etc.)
            metadata: Additional metadata

        Returns:
            Processed result
        """
        try:
            if not result.success:
                return result

            processed_data = result.data
            processing_steps: list[dict[str, Any]] = []
            processing_metadata: dict[str, Any] = {
                "original_result_type": result_type,
                "tenant": self.tenant_context.tenant,
                "workspace": self.tenant_context.workspace,
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_steps": processing_steps,
            }

            if metadata:
                processing_metadata.update(metadata)

            # Process through each processor
            for processor in self.processors:
                try:
                    step_result = processor.process(
                        data=processed_data,
                        result_type=result_type,
                        metadata=processing_metadata,
                        tenant_context=self.tenant_context,
                    )

                    if step_result.success:
                        processed_data = step_result.data
                        processing_steps.append(
                            {
                                "processor": processor.__class__.__name__,
                                "status": "success",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    else:
                        processing_steps.append(
                            {
                                "processor": processor.__class__.__name__,
                                "status": "failed",
                                "error": step_result.error,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                        logger.warning(f"Processor {processor.__class__.__name__} failed: {step_result.error}")

                except Exception as e:
                    logger.error(f"Processor {processor.__class__.__name__} error: {e}")
                    processing_steps.append(
                        {
                            "processor": processor.__class__.__name__,
                            "status": "error",
                            "error": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            return StepResult.ok(
                data={
                    "processed_data": processed_data,
                    "processing_metadata": processing_metadata,
                    "original_result": result.data,
                }
            )

        except Exception as e:
            logger.error(f"Result processing failed: {e}")
            return StepResult.fail(f"Result processing failed: {e!s}")


class ValidationProcessor:
    """Validates result data structure and content."""

    def process(
        self,
        data: Any,
        result_type: str,
        metadata: dict[str, Any],
        tenant_context: TenantContext,
    ) -> StepResult:
        """Validate result data.

        Args:
            data: Data to validate
            result_type: Type of result
            metadata: Processing metadata
            tenant_context: Tenant context

        Returns:
            Validation result
        """
        try:
            issues: list[str] = []
            validation_results: dict[str, Any] = {
                "structure_valid": True,
                "content_valid": True,
                "type_valid": True,
                "issues": issues,
            }

            # Validate data structure
            if not isinstance(data, (dict, list, str, int, float, bool)):
                validation_results["structure_valid"] = False
                issues.append("Invalid data structure")

            # Validate content based on result type
            if result_type == "analysis" and isinstance(data, dict):
                required_fields = ["content", "analysis_type"]
                for field in required_fields:
                    if field not in data:
                        validation_results["content_valid"] = False
                        issues.append(f"Missing required field: {field}")

            elif result_type == "verification" and isinstance(data, dict):
                required_fields = ["claim", "verdict", "confidence"]
                for field in required_fields:
                    if field not in data:
                        validation_results["content_valid"] = False
                        issues.append(f"Missing required field: {field}")

            # Check for empty or null values
            if isinstance(data, dict):
                for key, value in data.items():
                    if value is None or (isinstance(value, str) and not value.strip()):
                        issues.append(f"Empty value for field: {key}")

            return StepResult.ok(data={"validated_data": data, "validation_results": validation_results})

        except Exception as e:
            return StepResult.fail(f"Validation failed: {e!s}")


class TransformationProcessor:
    """Transforms result data into standardized formats."""

    def process(
        self,
        data: Any,
        result_type: str,
        metadata: dict[str, Any],
        tenant_context: TenantContext,
    ) -> StepResult:
        """Transform result data.

        Args:
            data: Data to transform
            result_type: Type of result
            metadata: Processing metadata
            tenant_context: Tenant context

        Returns:
            Transformation result
        """
        try:
            transformed_data = data

            # Apply type-specific transformations
            if result_type == "analysis":
                transformed_data = self._transform_analysis_data(data)
            elif result_type == "verification":
                transformed_data = self._transform_verification_data(data)
            elif result_type == "content":
                transformed_data = self._transform_content_data(data)

            # Standardize common fields
            if isinstance(transformed_data, dict):
                transformed_data = self._standardize_fields(transformed_data, tenant_context)

            return StepResult.ok(data=transformed_data)

        except Exception as e:
            return StepResult.fail(f"Transformation failed: {e!s}")

    def _transform_analysis_data(self, data: Any) -> dict[str, Any]:
        """Transform analysis data."""
        if isinstance(data, dict):
            return {
                "analysis_type": data.get("analysis_type", "general"),
                "content": data.get("content", ""),
                "insights": data.get("insights", []),
                "confidence": data.get("confidence", 0.0),
                "metadata": data.get("metadata", {}),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
        return {"content": str(data), "analysis_type": "text"}

    def _transform_verification_data(self, data: Any) -> dict[str, Any]:
        """Transform verification data."""
        if isinstance(data, dict):
            return {
                "claim": data.get("claim", ""),
                "verdict": data.get("verdict", "unknown"),
                "confidence": data.get("confidence", 0.0),
                "evidence": data.get("evidence", []),
                "sources": data.get("sources", []),
                "reasoning": data.get("reasoning", ""),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
        return {"claim": str(data), "verdict": "unknown", "confidence": 0.0}

    def _transform_content_data(self, data: Any) -> dict[str, Any]:
        """Transform content data."""
        if isinstance(data, dict):
            return {
                "content": data.get("content", ""),
                "content_type": data.get("content_type", "text"),
                "metadata": data.get("metadata", {}),
                "quality_score": data.get("quality_score", 0.0),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
        return {"content": str(data), "content_type": "text"}

    def _standardize_fields(self, data: dict[str, Any], tenant_context: TenantContext) -> dict[str, Any]:
        """Standardize common fields."""
        standardized = data.copy()

        # Ensure timestamp is present
        if "timestamp" not in standardized:
            standardized["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Ensure tenant context is present
        standardized["tenant"] = tenant_context.tenant
        standardized["workspace"] = tenant_context.workspace

        return standardized


class QualityProcessor:
    """Assesses and improves result quality."""

    def process(
        self,
        data: Any,
        result_type: str,
        metadata: dict[str, Any],
        tenant_context: TenantContext,
    ) -> StepResult:
        """Assess and improve result quality.

        Args:
            data: Data to assess
            result_type: Type of result
            metadata: Processing metadata
            tenant_context: Tenant context

        Returns:
            Quality assessment result
        """
        try:
            quality_metrics = self._assess_quality(data, result_type)

            # Apply quality improvements if needed
            improved_data = self._improve_quality(data, quality_metrics)

            return StepResult.ok(
                data={
                    "improved_data": improved_data,
                    "quality_metrics": quality_metrics,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Quality processing failed: {e!s}")

    def _assess_quality(self, data: Any, result_type: str) -> dict[str, Any]:
        """Assess data quality."""
        metrics = {
            "completeness": 0.0,
            "accuracy": 0.0,
            "relevance": 0.0,
            "clarity": 0.0,
            "overall_score": 0.0,
        }

        if isinstance(data, dict):
            # Assess completeness
            required_fields = self._get_required_fields(result_type)
            present_fields = sum(1 for field in required_fields if data.get(field))
            metrics["completeness"] = present_fields / len(required_fields) if required_fields else 1.0

            # Assess clarity (based on content length and structure)
            content = data.get("content", "")
            if isinstance(content, str):
                metrics["clarity"] = min(1.0, len(content) / 100)  # Simple heuristic

            # Calculate overall score
            metrics["overall_score"] = sum(metrics.values()) / len(metrics)

        return metrics

    def _get_required_fields(self, result_type: str) -> list[str]:
        """Get required fields for result type."""
        field_mapping = {
            "analysis": ["content", "analysis_type"],
            "verification": ["claim", "verdict", "confidence"],
            "content": ["content", "content_type"],
        }
        return field_mapping.get(result_type, ["content"])

    def _improve_quality(self, data: Any, metrics: dict[str, Any]) -> Any:
        """Improve data quality based on metrics."""
        if not isinstance(data, dict):
            return data

        improved = data.copy()

        # Add quality score if missing
        if "quality_score" not in improved:
            improved["quality_score"] = metrics["overall_score"]

        # Improve content if clarity is low
        if metrics["clarity"] < 0.5 and "content" in improved:
            content = improved["content"]
            if isinstance(content, str) and len(content) < 50:
                improved["content"] = f"{content} [Content may need expansion]"

        return improved


class OptimizationProcessor:
    """Optimizes result data for performance and efficiency."""

    def process(
        self,
        data: Any,
        result_type: str,
        metadata: dict[str, Any],
        tenant_context: TenantContext,
    ) -> StepResult:
        """Optimize result data.

        Args:
            data: Data to optimize
            result_type: Type of result
            metadata: Processing metadata
            tenant_context: Tenant context

        Returns:
            Optimization result
        """
        try:
            optimized_data = self._optimize_data(data, result_type)

            return StepResult.ok(data=optimized_data)

        except Exception as e:
            return StepResult.fail(f"Optimization failed: {e!s}")

    def _optimize_data(self, data: Any, result_type: str) -> Any:
        """Optimize data structure and content."""
        if not isinstance(data, dict):
            return data

        optimized = data.copy()

        # Remove unnecessary fields
        unnecessary_fields = ["temp_data", "debug_info", "internal_notes"]
        for field in unnecessary_fields:
            optimized.pop(field, None)

        # Compress large text content
        if "content" in optimized and isinstance(optimized["content"], str) and len(optimized["content"]) > 10000:
            optimized["content"] = optimized["content"][:10000] + "... [truncated]"
            optimized["content_truncated"] = True

        # Optimize metadata
        if "metadata" in optimized and isinstance(optimized["metadata"], dict):
            # Keep only essential metadata
            essential_metadata = {}
            essential_fields = ["source", "timestamp", "version", "type"]
            for field in essential_fields:
                if field in optimized["metadata"]:
                    essential_metadata[field] = optimized["metadata"][field]
            optimized["metadata"] = essential_metadata

        return optimized


class FormattingProcessor:
    """Formats result data for final output."""

    def process(
        self,
        data: Any,
        result_type: str,
        metadata: dict[str, Any],
        tenant_context: TenantContext,
    ) -> StepResult:
        """Format result data for final output.

        Args:
            data: Data to format
            result_type: Type of result
            metadata: Processing metadata
            tenant_context: Tenant context

        Returns:
            Formatting result
        """
        try:
            formatted_data = self._format_data(data, result_type)

            return StepResult.ok(data=formatted_data)

        except Exception as e:
            return StepResult.fail(f"Formatting failed: {e!s}")

    def _format_data(self, data: Any, result_type: str) -> Any:
        """Format data for final output."""
        if not isinstance(data, dict):
            return data

        formatted = data.copy()

        # Add formatting metadata
        formatted["formatted_at"] = datetime.now(timezone.utc).isoformat()
        formatted["format_version"] = "1.0"

        # Ensure consistent field ordering
        ordered_fields = [
            "content",
            "analysis_type",
            "claim",
            "verdict",
            "confidence",
            "insights",
            "evidence",
            "sources",
            "reasoning",
            "metadata",
            "quality_score",
            "timestamp",
            "tenant",
            "workspace",
        ]

        ordered_data = {}
        for field in ordered_fields:
            if field in formatted:
                ordered_data[field] = formatted[field]

        # Add remaining fields
        for key, value in formatted.items():
            if key not in ordered_data:
                ordered_data[key] = value

        return ordered_data


class ResultProcessingManager:
    """Manager for result processing across tenants."""

    def __init__(self):
        """Initialize result processing manager."""
        self.processors: dict[str, ResultProcessor] = {}

    def get_processor(self, tenant_context: TenantContext) -> ResultProcessor:
        """Get or create result processor for tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            Result processor for the tenant
        """
        key = f"{tenant_context.tenant}:{tenant_context.workspace}"

        if key not in self.processors:
            self.processors[key] = ResultProcessor(tenant_context)

        return self.processors[key]

    def process_result(
        self,
        result: StepResult,
        tenant_context: TenantContext,
        result_type: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Process result for tenant.

        Args:
            result: Result to process
            tenant_context: Tenant context
            result_type: Type of result
            metadata: Additional metadata

        Returns:
            Processed result
        """
        processor = self.get_processor(tenant_context)
        return processor.process_result(result, result_type, metadata)


# Global result processing manager
_result_manager = ResultProcessingManager()


def get_result_processor(tenant_context: TenantContext) -> ResultProcessor:
    """Get result processor for tenant.

    Args:
        tenant_context: Tenant context

    Returns:
        Result processor for the tenant
    """
    return _result_manager.get_processor(tenant_context)


def process_result(
    result: StepResult,
    tenant_context: TenantContext,
    result_type: str = "default",
    metadata: dict[str, Any] | None = None,
) -> StepResult:
    """Process result for tenant.

    Args:
        result: Result to process
        tenant_context: Tenant context
        result_type: Type of result
        metadata: Additional metadata

    Returns:
        Processed result
    """
    return _result_manager.process_result(result, tenant_context, result_type, metadata)
