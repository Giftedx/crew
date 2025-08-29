from __future__ import annotations

"""Prompt evaluation harness for benchmarking models.

The :class:`EvaluationHarness` runs prompts across one or more models via the
:class:`OpenRouterService`, recording latency, token usage and responses. Results
are appended to a JSON Lines log so offline analysis and reinforcement learning
can consume the data."""

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .openrouter_service import OpenRouterService


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
    ) -> list[dict[str, Any]]:
        """Execute ``prompt`` against ``models`` and log the outcomes."""

        models_to_run = models or self.router.models_map.get(
            task_type, self.router.models_map["general"]
        )
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
            except Exception:
                pass
        return results
