"""Steelman argument tool following Copilot instructions.

Instrumentation:
    * tool_runs_total{tool="steelman_argument", outcome}
    * Outcomes: success | error | skipped
    * No latency histogram (pure CPU, fast)
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


class SteelmanArgumentTool:
    """Tool to generate steelman arguments for positions."""

    def __init__(self):
        # Analyzer dependency removed (original DebateAnalyzer not present in repo).
        # If future advanced debate analysis is required, inject a strategy object here.
        self._metrics = get_metrics()

    def run(self, claim: str, evidence: list[dict] | None = None, context: str | None = None) -> StepResult:
        """Generate a steelman argument given a claim and supporting evidence.

        Test expectations (see tests/test_steelman_argument_tool.py):
            * When evidence list is non-empty -> status == "success"
            * When evidence list is empty -> status == "uncertain", argument == claim, notes mention lack of evidence
        """
        evidence = evidence or []
        if not claim:
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "steelman_argument", "outcome": "skipped"},
            ).inc()
            return StepResult.skip(
                message="No claim provided",
                argument="",
                evidence=[],
                platform="internal",
                command="steelman",
            )

        try:
            if not evidence:
                # Uncertain outcome due to no evidence
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "steelman_argument", "outcome": "success"},
                ).inc()
                return StepResult.uncertain(
                    argument=claim,
                    notes="no supporting evidence provided; cannot strengthen beyond original claim",
                    evidence=[],
                )

            # Combine evidence snippets into a strengthened argument
            combined_points = "; ".join(snippet.get("snippet", "") for snippet in evidence if snippet.get("snippet"))
            argument = f"{claim} — Strongest Form: {combined_points}" if combined_points else claim
            if context:
                argument = f"[{context}] {argument}"

            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "steelman_argument", "outcome": "success"},
            ).inc()
            return StepResult.ok(argument=argument, evidence=evidence, claim=claim)
        except Exception as e:  # pragma: no cover - defensive
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "steelman_argument", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(e), platform="internal", command="steelman")

    def _generate_steelman(self, position: str, context: str | None) -> dict[str, Any]:
        """Generate steelman argument details."""
        # This would integrate with the debate analyzer
        # For now, return a structured response

        steelman = {
            "argument": f"The strongest form of '{position}' would be: [detailed steelman here]",
            "key_points": [
                "Point 1: Core assumption made explicit",
                "Point 2: Best evidence supporting the position",
                "Point 3: Addressing common counterarguments",
            ],
            "assumptions": [
                "Assumes rational actors",
                "Assumes available information is accurate",
            ],
            "confidence": 0.75,
        }

        if context:
            steelman["context_considered"] = True
            steelman["argument"] = f"In the context of {context}, {steelman['argument']}"

        return steelman
