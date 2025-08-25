from __future__ import annotations

"""Lightweight helper to normalise tool responses across the pipeline.

The content pipeline interacts with a variety of tools that traditionally
return dictionaries with a ``status`` key.  This module introduces a
``StepResult`` dataclass that provides a consistent, typed representation of
those results while still allowing easy conversion back to dictionaries for
existing code and tests.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StepResult:
    """Container for the outcome of a pipeline step."""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, result: Dict[str, Any]) -> "StepResult":
        """Create a ``StepResult`` from a legacy ``dict`` response."""
        status = result.get("status")
        success = status == "success"
        error = result.get("error")
        data = {k: v for k, v in result.items() if k not in {"status", "error"}}
        return cls(success=success, data=data, error=error)

    @classmethod
    def ok(cls, **data: Any) -> "StepResult":
        """Shortcut for a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str, **data: Any) -> "StepResult":
        """Shortcut for a failed result."""
        return cls(success=False, error=str(error), data=data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result back to a ``dict`` for backward compatibility."""
        result = dict(self.data)
        result["status"] = "success" if self.success else "error"
        if self.error:
            result["error"] = self.error
        return result
