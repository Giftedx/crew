"""Type stubs for crewai library."""

from collections.abc import Callable
from typing import Any

class Agent:
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: list[Any],
        verbose: bool = True,
        allow_delegation: bool = False,
        **kwargs: Any,
    ) -> None: ...

class Task:
    def __init__(
        self,
        description: str,
        expected_output: str,
        agent: Agent | Callable[[], Agent],
        context: list[Task] | None = None,
        human_input: bool = False,
        async_execution: bool = False,
        **kwargs: Any,
    ) -> None: ...

class Crew:
    def __init__(
        self,
        agents: list[Agent],
        tasks: list[Task],
        process: str = "sequential",
        verbose: bool = True,
        planning: bool = False,
        memory: bool = False,
        cache: bool = False,
        max_rpm: int = 10,
        step_callback: Callable[[Any], None] | None = None,
        embedder: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None: ...
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any: ...

class Process:
    sequential: str
