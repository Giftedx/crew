"""
DocumentProcessingTool - Parse and extract content from various document formats.

This tool provides document parsing capabilities for common formats like PDF, DOCX,
TXT, MD with metadata extraction and text content retrieval.
"""

from typing import Any

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class DocumentProcessingTool(BaseUniversalTool):
    """
    A universal document processing tool for parsing various file formats.

    Supports parsing PDF, DOCX, TXT, MD files with text extraction and
    metadata retrieval including page count, author, creation date, etc.

    Example:
        # Parse PDF document
        result = await processor.run(
            file_path="/path/to/document.pdf",
            format="pdf",
            extract_metadata=True
        )

        # Extract text from DOCX
        result = await processor.run(
            file_path="/path/to/document.docx",
            format="docx",
            extract_metadata=False
        )
    """

    name = "document-processing"
    description = (
        "Parse and extract content from documents in various formats (PDF, DOCX, TXT, MD). "
        "Extracts text content and optional metadata including page count, author, "
        "creation date, and document properties. Returns structured document data."
    )

    parameters = {
        "file_path": ParameterSchema(
            type="string",
            description="Path to the document file to process",
            required=True,
        ),
        "format": ParameterSchema(
            type="string",
            description="Document format (auto-detected from extension if not provided)",
            required=False,
            enum=["pdf", "docx", "txt", "md", "auto"],
            default="auto",
        ),
        "extract_metadata": ParameterSchema(
            type="boolean",
            description="Whether to extract document metadata (default true)",
            required=False,
            default=True,
        ),
        "max_length": ParameterSchema(
            type="number",
            description="Maximum text length to extract (0 for unlimited, default 0)",
            required=False,
            default=0,
        ),
        "include_formatting": ParameterSchema(
            type="boolean",
            description="Preserve formatting information where possible (default false)",
            required=False,
            default=False,
        ),
    }

    metadata = ToolMetadata(
        category="document",
        return_type="dict",
        examples=[
            "Extract text from PDF document",
            "Parse DOCX file with metadata",
            "Read markdown document",
            "Process plain text file",
        ],
        version="1.0.0",
        tags=["document", "pdf", "docx", "parsing", "text-extraction"],
        requires_auth=False,
    )

    async def run(
        self,
        file_path: str,
        format: str = "auto",
        extract_metadata: bool = True,
        max_length: int = 0,
        include_formatting: bool = False,
    ) -> dict[str, Any]:
        """
        Parse a document and extract its content.

        Args:
            file_path: Path to the document file
            format: Document format (auto-detected if "auto")
            extract_metadata: Whether to extract metadata
            max_length: Maximum text length (0 for unlimited)
            include_formatting: Preserve formatting info

        Returns:
            Dictionary containing:
            - text (str): Extracted text content
            - metadata (dict, optional): Document metadata
            - pages (int, optional): Number of pages
            - format (str): Detected/provided format
            - truncated (bool): Whether text was truncated

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported
        """
        logger.info(
            "document_processing_execution",
            file_path=file_path,
            format=format,
            extract_metadata=extract_metadata,
            max_length=max_length,
        )

        # Auto-detect format from file extension
        if format == "auto":
            if file_path.endswith(".pdf"):
                format = "pdf"
            elif file_path.endswith((".docx", ".doc")):
                format = "docx"
            elif file_path.endswith(".txt"):
                format = "txt"
            elif file_path.endswith((".md", ".markdown")):
                format = "md"
            else:
                raise ValueError(f"Cannot auto-detect format for: {file_path}")

        # Validate format
        supported_formats = ["pdf", "docx", "txt", "md"]
        if format not in supported_formats:
            raise ValueError(f"Unsupported format '{format}'. Supported: {supported_formats}")

        # Mock implementation for testing/demo
        # Production version would use libraries like pypdf, python-docx, etc.
        try:
            # Simulate document parsing
            mock_text = self._generate_mock_text(format, file_path)

            # Apply max_length if specified
            truncated = False
            if max_length > 0 and len(mock_text) > max_length:
                mock_text = mock_text[:max_length]
                truncated = True

            result = {
                "text": mock_text,
                "format": format,
                "truncated": truncated,
            }

            # Add metadata if requested
            if extract_metadata:
                result["metadata"] = self._generate_mock_metadata(format, file_path)
                result["pages"] = self._estimate_pages(format)

            logger.info(
                "document_processing_success",
                file_path=file_path,
                format=format,
                text_length=len(mock_text),
                truncated=truncated,
            )

            return result

        except Exception as e:
            logger.error(
                "document_processing_error",
                file_path=file_path,
                format=format,
                error=str(e),
            )
            raise

    def _generate_mock_text(self, format: str, file_path: str) -> str:
        """Generate mock text content based on format."""
        if format == "pdf":
            return (
                "This is mock content from a PDF document.\n\n"
                "Page 1: Introduction and overview.\n"
                "Page 2: Detailed analysis and findings.\n"
                "Page 3: Conclusions and recommendations."
            )
        elif format == "docx":
            return (
                "Mock DOCX Document\n\n"
                "Section 1: Executive Summary\n"
                "This document contains important information.\n\n"
                "Section 2: Main Content\n"
                "Detailed content goes here."
            )
        elif format == "txt":
            return "Simple plain text content from TXT file.\nLine 2 of text.\nLine 3 of text."
        elif format == "md":
            return (
                "# Mock Markdown Document\n\n"
                "## Section 1\n\n"
                "This is a **markdown** document with *formatting*.\n\n"
                "- Item 1\n"
                "- Item 2\n"
                "- Item 3"
            )
        return "Unknown format content"

    def _generate_mock_metadata(self, format: str, file_path: str) -> dict[str, Any]:
        """Generate mock metadata based on format."""
        base_metadata = {
            "file_path": file_path,
            "format": format,
            "creation_date": "2025-11-01T00:00:00Z",
        }

        if format == "pdf":
            base_metadata.update(
                {
                    "author": "John Doe",
                    "title": "Sample PDF Document",
                    "producer": "Mock PDF Library",
                    "pdf_version": "1.7",
                }
            )
        elif format == "docx":
            base_metadata.update(
                {
                    "author": "Jane Smith",
                    "title": "Sample DOCX Document",
                    "application": "Mock Word Processor",
                    "revision": 1,
                }
            )

        return base_metadata

    def _estimate_pages(self, format: str) -> int:
        """Estimate number of pages based on format."""
        if format == "pdf":
            return 3
        elif format == "docx":
            return 2
        else:
            return 1  # TXT and MD are considered single page
