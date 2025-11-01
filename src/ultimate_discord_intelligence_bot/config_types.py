"""Typed configuration schema for CrewAI integration.

These TypedDicts narrow the dynamic ``agents_config`` and ``tasks_config``
structures injected by the CrewAI ``@CrewBase`` decorator so static type
checking can detect drift early. Only the fields *currently used* by the
project are modelled; additional vendor fields are preserved via ``total=False``.

Runtime code remains permissive- validation logic in ``crew.py`` (flag gated)
performs structural checks without rejecting unknown forward-compatible keys.
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class AgentConfig(TypedDict, total=False):
    role: str
    goal: str
    backstory: str
    allow_delegation: bool
    verbose: bool
    reasoning: bool
    inject_date: bool
    date_format: str
    # Optional future / vendor fields (examples):
    memory: NotRequired[bool]
    max_reasoning_attempts: NotRequired[int]
    respect_context_window: NotRequired[bool]
    max_rpm: NotRequired[int | None]


class TaskConfig(TypedDict, total=False):
    description: str
    expected_output: str
    agent: str
    human_input: bool
    output_file: str
    async_execution: bool
    context: list[str]


__all__ = ["AgentConfig", "TaskConfig"]
