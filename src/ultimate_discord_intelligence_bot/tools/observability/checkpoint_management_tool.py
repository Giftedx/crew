"""Checkpoint management tool for LangGraph runs.

Actions:
- list: List thread_ids and latest step for each run.
- load: Load checkpoint metadata for a thread_id.
- delete: Delete checkpoint(s) for a thread_id.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class CheckpointArgs(BaseModel):
    action: Literal["list", "load", "delete"] = Field(..., description="Operation to perform")
    thread_id: str | None = Field(None, description="Thread ID to operate on (required for load/delete)")
    store_path: str | None = Field(
        "crew_data/langgraph/checkpoints.meta.json", description="Path to metadata store tracking checkpoints"
    )


class CheckpointManagementTool(BaseTool[dict]):
    name: str = "checkpoint_management_tool"
    description: str = "Manages LangGraph checkpoints (list/load/delete) using a simple JSON metadata store."
    args_schema: type[BaseModel] = CheckpointArgs

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._metrics = get_metrics()

    def _read_store(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    def _write_store(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def _run(
        self, action: Literal["list", "load", "delete"], thread_id: str | None = None, store_path: str | None = None
    ) -> StepResult:
        meta_path = Path(store_path or "crew_data/langgraph/checkpoints.meta.json")
        store = self._read_store(meta_path)
        result: StepResult

        if action == "list":
            runs = [
                {"thread_id": tid, **{k: v for k, v in rec.items() if k != "events"}}
                for tid, rec in store.items()
                if isinstance(rec, dict)
            ]
            result = StepResult.ok(data={"runs": runs})
        elif action == "load":
            if not thread_id:
                result = StepResult.fail("thread_id is required for load")
            else:
                rec = store.get(thread_id)
                if not isinstance(rec, dict):
                    result = StepResult.not_found("checkpoint not found", thread_id=thread_id)
                else:
                    result = StepResult.ok(data={"checkpoint": {k: v for k, v in rec.items() if k != "events"}})
        elif action == "delete":
            if not thread_id:
                result = StepResult.fail("thread_id is required for delete")
            elif thread_id in store:
                del store[thread_id]
                self._write_store(meta_path, store)
                result = StepResult.ok(data={"deleted": thread_id})
            else:
                result = StepResult.not_found("checkpoint not found", thread_id=thread_id)
        else:
            result = StepResult.fail(f"Unknown action: {action}")

        try:
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": self.name, "outcome": "success" if result.success else "failure"},
            ).inc()
        except Exception as exc:
            logging.debug("metrics emit failed: %s", exc)

        return result
