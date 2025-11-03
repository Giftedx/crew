from __future__ import annotations

from platform.core.step_result import ErrorCategory, StepResult

from ultimate_discord_intelligence_bot.tools._base import BaseTool


class _DummyTool(BaseTool[StepResult]):
    name = "dummy"
    description = "dummy tool"

    def run(self, value):
        return self.ensure_step_result(value)


def test_ensure_step_result_passthrough_instance():
    tool = _DummyTool()
    original = StepResult.ok(message="hello")
    coerced = tool.ensure_step_result(original)
    assert coerced is original
    assert coerced.success
    assert coerced.data["message"] == "hello"


def test_ensure_step_result_from_status_mapping():
    tool = _DummyTool()
    coerced = tool.ensure_step_result({"status": "success", "payload": 123})
    assert coerced.success
    assert coerced.data["payload"] == 123


def test_ensure_step_result_from_success_flag():
    tool = _DummyTool()
    coerced = tool.ensure_step_result({"success": True, "value": "ok"})
    assert coerced.success
    assert coerced.data["value"] == "ok"


def test_ensure_step_result_from_failure_mapping_preserves_metadata():
    tool = _DummyTool()
    coerced = tool.ensure_step_result(
        {
            "success": False,
            "error": "boom",
            "details": {"step": 3},
            "metadata": {"legacy": True},
            "retryable": True,
            "error_category": ErrorCategory.NETWORK,
        }
    )
    assert not coerced.success
    assert coerced.error == "boom"
    assert coerced.retryable is True
    assert coerced.error_category == ErrorCategory.NETWORK
    assert coerced.data["details"] == {"step": 3}
    assert coerced.metadata["legacy"] is True


def test_ensure_step_result_normalises_metadata_scalar():
    tool = _DummyTool()
    coerced = tool.ensure_step_result({"success": False, "error": "bad", "metadata": "legacy"})
    assert coerced.metadata["value"] == "legacy"


def test_ensure_step_result_none_defaults_to_success():
    tool = _DummyTool()
    coerced = tool.ensure_step_result(None)
    assert coerced.success
    assert coerced.data == {}


def test_ensure_step_result_wraps_non_mapping_value():
    tool = _DummyTool()
    coerced = tool.ensure_step_result("payload")
    assert coerced.success
    assert coerced.data["result"] == "payload"


def test_helper_factory_methods():
    tool = _DummyTool()
    ok = tool.result_ok(foo=1)
    assert ok.success and ok.data["foo"] == 1
    skipped = tool.result_skip(reason="not-applicable")
    assert skipped.success and skipped.custom_status == "skipped"
    uncertain = tool.result_uncertain(confidence=0.4)
    assert uncertain.success and uncertain.custom_status == "uncertain"
    failed = tool.result_fail("nope", error_category=ErrorCategory.PROCESSING)
    assert not failed.success
    assert failed.error == "nope"
    assert failed.error_category == ErrorCategory.PROCESSING
