"""Debate package exposing panel helpers."""

from .panel import PanelConfig, DebateReport, AgentResult, run_panel  # noqa: F401

__all__ = ["PanelConfig", "DebateReport", "AgentResult", "run_panel"]