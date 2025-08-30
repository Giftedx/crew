"""Debate package exposing panel helpers."""

from .panel import AgentResult, DebateReport, PanelConfig, run_panel  # noqa: F401

__all__ = ["PanelConfig", "DebateReport", "AgentResult", "run_panel"]
