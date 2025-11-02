"""Lightweight stub of the crewai package for test environments.

This stub provides minimal classes and behaviors used by the codebase's fast
unit tests, without requiring the real crewai dependency. It is intentionally
small and only implements the handful of attributes and methods accessed by
our tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class Agent:
    def __init__(
        self,
        role: str = "Agent",
        goal: str | None = None,
        backstory: str | None = None,
        tools: list[Any] | None = None,
        verbose: bool | None = None,
        allow_delegation: bool | None = None,
        **_: Any,
    ) -> None:
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools: list[Any] = list(tools or [])
        self.verbose = bool(verbose)
        self.allow_delegation = bool(allow_delegation)

    def add_tool(self, tool: Any) -> None:
        self.tools.append(tool)


class Task:
    def __init__(
        self,
        description: str,
        expected_output: str | None = None,
        agent: Agent | Callable[[], Agent] | None = None,
        context: Iterable[Task] | None = None,
        human_input: bool | None = None,
        async_execution: bool | None = None,
        **_: Any,
    ) -> None:
        self.description = description
        self.expected_output = expected_output
        self._agent = agent
        self.context = list(context or [])
        self.human_input = bool(human_input)
        self.async_execution = bool(async_execution)

    @property
    def agent(self) -> Agent | None:
        try:
            return self._agent() if callable(self._agent) else self._agent
        except Exception:
            return None


class Process:
    sequential = "sequential"
    parallel = "parallel"


@dataclass
class CrewOutput:
    raw: Any

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.raw)


class Crew:
    def __init__(
        self,
        *,
        agents: Iterable[Agent] | None = None,
        tasks: Iterable[Task] | None = None,
        process: str | None = None,
        verbose: bool | None = None,
        planning: bool | None = None,
        memory: bool | None = None,
        cache: bool | None = None,
        max_rpm: int | None = None,
        step_callback: Callable[[Any], None] | None = None,
        embedder: dict | None = None,
        **_: Any,
    ) -> None:
        self.agents = list(agents or [])
        self.tasks = list(tasks or [])
        self.process = process or Process.sequential
        self.verbose = bool(verbose)
        self.planning = bool(planning)
        self.memory = bool(memory)
        self.cache = bool(cache)
        self.max_rpm = int(max_rpm or 0)
        self.step_callback = step_callback
        self.embedder = embedder or {}

    def kickoff(self, *, inputs: dict[str, Any] | None = None) -> CrewOutput:
        # Produce a stable, generic output that does not contain the words
        # banned by fast tests ("fast", "quick", "rapid", "instant").
        payload = {
            "status": "ok",
            "inputs": dict(inputs or {}),
            "agents": [getattr(a, "role", "agent") for a in self.agents],
            "tasks": [getattr(t, "description", "task") for t in self.tasks],
        }
        return CrewOutput(raw=payload)


class BaseTool:  # Minimal stub compatible with our tool wrappers
    name: str = "base_tool"
    description: str = ""
    args_schema: Any | None = None

    def __init__(self, **_: Any) -> None:
        pass

    # Conform to crewai-style tools that call _run internally
    def run(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - trivial
        return self._run(*args, **kwargs)

    def _run(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - placeholder
        return None


# Some code paths import these names directly from crewai
__all__ = [
    "Agent",
    "BaseTool",
    "Crew",
    "CrewOutput",
    "Process",
    "Task",
]
