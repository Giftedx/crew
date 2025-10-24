"""Type stubs for crewai_tools library."""

from typing import Any

class BaseTool:
    def __init__(self, **kwargs: Any) -> None: ...
    def _run(self, *args: Any, **kwargs: Any) -> Any: ...
