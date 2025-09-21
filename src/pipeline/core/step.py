from __future__ import annotations

from typing import Any, Protocol


class Step(Protocol):
    """A minimal Step contract for modular pipelines.

    Implementations should be small, testable units of work.
    Inputs/outputs may be plain dicts or typed models.
    """

    idempotent: bool

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the step with the provided context and return outputs."""
        ...
