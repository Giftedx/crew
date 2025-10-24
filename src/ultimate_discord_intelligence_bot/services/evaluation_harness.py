"""Prompt evaluation harness for benchmarking models.

The :class:`EvaluationHarness` runs prompts across one or more models via the
:class:`OpenRouterService`, recording latency, token usage and responses. Results
are appended to a JSON Lines log so offline analysis and reinforcement learning
can consume the data.

Import ordering: module docstring precedes ``__future__`` import per Ruff E402 guidance.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .openrouter_service import OpenRouterService


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class EvaluationHarness:
    """Benchmark prompts across multiple models."""

    router: OpenRouterService = field(default_factory=OpenRouterService)
    log_path: str = "evaluation_log.jsonl"

    def run(
        self,
        prompt: str,
        task_type: str = "general",
        models: list[str] | None = None,
    ) -> StepResult:
        """Execute ``prompt`` against ``models`` and log the outcomes.

        Keeping parameters explicit (vs a config dict) improves discoverability for
        callers / tests and avoids secondary validation layer.
        """

        models_to_run = models or self.router.models_map.get(task_type, self.router.models_map["general"])
        results: list[dict[str, Any]] = []
        for model in models_to_run:
            start = time.perf_counter()
            response = self.router.route(prompt, task_type=task_type, model=model)
            latency = time.perf_counter() - start
            record: dict[str, Any] = {
                "prompt": prompt,
                "model": model,
                "task_type": task_type,
                "latency": latency,
                **response,
            }
            results.append(record)
            try:
                with open(self.log_path, "a", encoding="utf-8") as fh:
                    json.dump(record, fh)
                    fh.write("\n")
            except OSError as exc:
                # Logging failure should not abort benchmark loop; emit structured
                # diagnostic for observability instead of swallowing silently.
                # Using print keeps harness dependency‑light; upstream caller can
                # redirect stdout to logging if desired.
                print(
                    json.dumps(
                        {
                            "event": "evaluation_harness_log_error",
                            "error": str(exc),
                            "path": self.log_path,
                        }
                    )
                )
        return results
