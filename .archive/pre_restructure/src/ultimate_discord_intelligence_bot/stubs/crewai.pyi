"""Type stubs for crewai module."""

from abc import ABC, abstractmethod
from typing import Any

class Agent:
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: list[Any] | None = None,
        verbose: bool = False,
        allow_delegation: bool = True,
        max_iter: int = 25,
        memory: bool = True,
        **kwargs: Any,
    ) -> None: ...

class Task:
    def __init__(
        self,
        description: str,
        agent: Agent | None = None,
        expected_output: str = "",
        tools: list[Any] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Crew:
    def __init__(
        self,
        agents: list[Agent],
        tasks: list[Task],
        verbose: bool = False,
        memory: bool = True,
        planning: bool = True,
        **kwargs: Any,
    ) -> None: ...
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any: ...

class Process:
    def __init__(self, **kwargs: Any) -> None: ...

class CrewAI:
    def __init__(self, **kwargs: Any) -> None: ...

# Tool base class
class BaseTool(ABC):
    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> Any: ...
    def run(self, *args: Any, **kwargs: Any) -> Any: ...

# Memory classes
class Memory:
    def __init__(self, **kwargs: Any) -> None: ...

class LongTermMemory:
    def __init__(self, **kwargs: Any) -> None: ...

class CrewAIProcess(Process):
    def __init__(self, **kwargs: Any) -> None: ...
