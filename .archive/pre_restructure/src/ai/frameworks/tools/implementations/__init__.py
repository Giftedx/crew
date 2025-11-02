"""Universal tool implementations.

This package contains ready-to-use tools that work across all supported frameworks.
"""

from __future__ import annotations

from ai.frameworks.tools.implementations.api_client_tool import APIClientTool
from ai.frameworks.tools.implementations.audio_transcription_tool import AudioTranscriptionTool
from ai.frameworks.tools.implementations.code_analysis_tool import CodeAnalysisTool
from ai.frameworks.tools.implementations.data_validation_tool import DataValidationTool
from ai.frameworks.tools.implementations.database_query_tool import DatabaseQueryTool
from ai.frameworks.tools.implementations.document_processing_tool import DocumentProcessingTool
from ai.frameworks.tools.implementations.file_operations_tool import FileOperationsTool
from ai.frameworks.tools.implementations.image_analysis_tool import ImageAnalysisTool
from ai.frameworks.tools.implementations.metrics_collection_tool import MetricsCollectionTool
from ai.frameworks.tools.implementations.web_search_tool import WebSearchTool


__all__ = [
    "APIClientTool",
    "AudioTranscriptionTool",
    "CodeAnalysisTool",
    "DataValidationTool",
    "DatabaseQueryTool",
    "DocumentProcessingTool",
    "FileOperationsTool",
    "ImageAnalysisTool",
    "MetricsCollectionTool",
    "WebSearchTool",
]
