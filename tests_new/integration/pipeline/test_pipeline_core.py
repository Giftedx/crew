#!/usr/bin/env python3
import contextlib
from typing import Any

from pipeline.core import Executor


class DummyStep:
    idempotent = True

    def __init__(self) -> None:
        self.calls = 0

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return {
            "ok": True,
            "calls": self.calls,
            "started_at": context.get("started_at"),
        }


class SpyMiddleware:
    def __init__(self) -> None:
        self.before_called = 0
        self.after_called = 0
        self.errors: list[str] = []

    def before(self, context: dict[str, Any]) -> None:
        self.before_called += 1

    def after(self, context: dict[str, Any], result: dict[str, Any]) -> None:
        self.after_called += 1

    def on_error(self, context: dict[str, Any], error) -> None:
        self.errors.append(str(error))


def test_executor_runs_step_with_middleware():
    step = DummyStep()
    spy = SpyMiddleware()
    ex = Executor([spy])

    result = ex.execute(step, {"foo": "bar"})

    assert result["ok"] is True
    assert step.calls == 1
    assert spy.before_called == 1
    assert spy.after_called == 1
    assert isinstance(result.get("started_at"), str)


def test_executor_calls_on_error():
    class FailingStep:
        idempotent = False

        def run(self, context: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("boom")

    spy = SpyMiddleware()
    ex = Executor([spy])

    with contextlib.suppress(RuntimeError):
        ex.execute(FailingStep(), {})

    assert spy.errors and "boom" in spy.errors[-1]
