from __future__ import annotations
import json
import logging
from typing import Any
import pytest
from ultimate_discord_intelligence_bot.observability.stepresult_observer import observe_step_result
from platform.core.step_result import StepResult

@pytest.fixture(autouse=True)
def enable_observer_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ENABLE_OBSERVABILITY_WRAPPER', '1')
    monkeypatch.delenv('ENABLE_OTEL_EXPORT', raising=False)
    yield

def _extract_logged_json_records(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rec in caplog.records:
        try:
            payload = json.loads(rec.getMessage())
            if isinstance(payload, dict) and payload.get('event') == 'stepresult':
                records.append(payload)
        except Exception:
            continue
    return records

def test_observer_logs_success_and_metadata(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger('observability')
    caplog.set_level(logging.INFO, logger=logger.name)

    @observe_step_result(tool_name='unit.success')
    def do_ok() -> StepResult:
        return StepResult.ok(data={'x': 1})
    res = do_ok()
    assert res.success is True
    entries = _extract_logged_json_records(caplog)
    assert len(entries) == 1
    entry = entries[0]
    assert entry['tool'] == 'unit.success'
    assert entry['success'] is True
    assert 'duration_ms' in entry and isinstance(entry['duration_ms'], float)
    assert entry.get('tenant') in (None, 'unknown', 'default') or isinstance(entry.get('tenant'), str)
    assert entry.get('workspace') in (None, 'unknown', 'main') or isinstance(entry.get('workspace'), str)

def test_observer_logs_failure(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger('observability')
    caplog.set_level(logging.INFO, logger=logger.name)

    @observe_step_result(tool_name='unit.failure')
    def do_fail() -> StepResult:
        return StepResult.fail(error='boom')
    res = do_fail()
    assert res.success is False
    entries = _extract_logged_json_records(caplog)
    assert len(entries) == 1
    entry = entries[0]
    assert entry['tool'] == 'unit.failure'
    assert entry['success'] is False
    assert entry.get('error') == 'boom'

def test_observer_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger('observability')
    caplog.set_level(logging.ERROR, logger=logger.name)

    @observe_step_result(tool_name='unit.exception')
    def do_raise() -> StepResult:
        raise RuntimeError('kaboom')
    with pytest.raises(RuntimeError):
        do_raise()
    entries = _extract_logged_json_records(caplog)
    assert len(entries) >= 1
    entry = entries[-1]
    assert entry['tool'] == 'unit.exception'
    assert entry['success'] is False
    assert entry.get('status') == 'exception'