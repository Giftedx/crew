"""Unit tests for the StepResult helper."""

from ultimate_discord_intelligence_bot.step_result import StepResult


def test_skip_to_dict_preserves_status_and_payload():
    result = StepResult.skip(reason="graph_memory_disabled")
    payload = result.to_dict()

    assert payload["status"] == "skipped"
    assert payload["reason"] == "graph_memory_disabled"


def test_uncertain_to_dict_preserves_status():
    result = StepResult.uncertain(score=0.42)
    payload = result.to_dict()

    assert payload["status"] == "uncertain"
    assert payload["score"] == 0.42


def test_fail_to_dict_remains_error():
    result = StepResult.fail("boom", retries=1)
    payload = result.to_dict()

    assert payload["status"] == "error"
    assert payload["error"] == "boom"
    assert payload["retries"] == 1
