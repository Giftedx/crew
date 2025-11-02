"""Universal file operations tool compatible with all frameworks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

import structlog

from ai.frameworks.tools import BaseUniversalTool, ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class FileOperationsTool(BaseUniversalTool):
    """Universal file operations tool for reading, writing, and managing files.

    This tool provides safe file operations that work across all supported
    AI frameworks.

    Example:
        ```python
        tool = FileOperationsTool()
        content = await tool.run(operation="read", path="/tmp/test.txt")
        ```
    """

    name = "file-operations"
    description = (
        "Perform file operations: read, write, append, delete, list, or check existence of files and directories."
    )

    parameters: ClassVar[dict[str, ParameterSchema]] = {
        "operation": ParameterSchema(
            type="string",
            description="Operation to perform",
            required=True,
            enum=["read", "write", "append", "delete", "list", "exists", "mkdir"],
        ),
        "path": ParameterSchema(
            type="string",
            description="File or directory path",
            required=True,
        ),
        "content": ParameterSchema(
            type="string",
            description="Content to write or append (for write/append operations)",
            required=False,
        ),
        "encoding": ParameterSchema(
            type="string",
            description="File encoding",
            required=False,
            default="utf-8",
        ),
    }

    metadata = ToolMetadata(
        category="system",
        return_type="string | list[str] | bool",
        examples=[
            {"operation": "read", "path": "/tmp/test.txt", "result": "File contents"},
            {"operation": "write", "path": "/tmp/test.txt", "content": "Hello", "result": "success"},
            {"operation": "list", "path": "/tmp", "result": ["file1.txt", "file2.txt"]},
        ],
        requires_auth=False,
        version="1.0.0",
        tags=["filesystem", "io", "files", "storage"],
    )

    async def run(
        self,
        operation: str,
        path: str,
        content: str | None = None,
        encoding: str = "utf-8",
    ) -> str | list[str] | bool:
        """Execute file operation.

        Args:
            operation: Operation to perform (read, write, append, delete, list, exists, mkdir)
            path: File or directory path
            content: Content for write/append operations
            encoding: File encoding (default: utf-8)

        Returns:
            Operation result:
            - read: File contents (str)
            - write/append: Success message (str)
            - delete/mkdir: Success message (str)
            - list: List of files/directories (list[str])
            - exists: Boolean indicating existence (bool)

        Raises:
            ValueError: If operation is invalid or required parameters missing
            FileNotFoundError: If file doesn't exist (for read operation)
            PermissionError: If insufficient permissions
        """
        logger.info(
            "file_operation_executing",
            operation=operation,
            path=path,
        )

        try:
            if operation == "read":
                return await self._read_file(path, encoding)
            elif operation == "write":
                if content is None:
                    raise ValueError("content parameter required for write operation")
                return await self._write_file(path, content, encoding, mode="w")
            elif operation == "append":
                if content is None:
                    raise ValueError("content parameter required for append operation")
                return await self._write_file(path, content, encoding, mode="a")
            elif operation == "delete":
                return await self._delete_path(path)
            elif operation == "list":
                return await self._list_directory(path)
            elif operation == "exists":
                return os.path.exists(path)
            elif operation == "mkdir":
                return await self._make_directory(path)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(
                "file_operation_failed",
                operation=operation,
                path=path,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _read_file(self, path: str, encoding: str) -> str:
        """Read file contents."""
        with open(path, encoding=encoding) as f:
            return f.read()

    async def _write_file(self, path: str, content: str, encoding: str, mode: str) -> str:
        """Write or append to file."""
        # Create parent directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode, encoding=encoding) as f:
            f.write(content)

        action = "written" if mode == "w" else "appended"
        return f"Content {action} to {path}"

    async def _delete_path(self, path: str) -> str:
        """Delete file or directory."""
        if os.path.isfile(path):
            os.remove(path)
            return f"File deleted: {path}"
        elif os.path.isdir(path):
            os.rmdir(path)
            return f"Directory deleted: {path}"
        else:
            raise FileNotFoundError(f"Path not found: {path}")

    async def _list_directory(self, path: str) -> list[str]:
        """List directory contents."""
        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")

        return sorted(os.listdir(path))

    async def _make_directory(self, path: str) -> str:
        """Create directory."""
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"Directory created: {path}"
