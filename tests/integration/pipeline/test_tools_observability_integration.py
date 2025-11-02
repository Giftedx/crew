from __future__ import annotations

import json
import logging
from typing import Any

import pytest

from ultimate_discord_intelligence_bot.tools.text_analysis_tool import (
    TextAnalysisTool,
)
from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
    YtDlpDownloadTool,
)


@pytest.fixture(autouse=True)
def enable_observer_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_OBSERVABILITY_WRAPPER", "1")
    yield


def _extract_logged(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rec in caplog.records:
        try:
            payload = json.loads(rec.getMessage())
            if isinstance(payload, dict) and payload.get("event") == "stepresult":
                out.append(payload)
        except Exception:
            continue
    return out


def test_text_analysis_observed_success(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    # Force degraded mode allowed
    monkeypatch.setenv("ALLOW_NLTK_DEGRADED_MODE", "1")
    logger = logging.getLogger("observability")
    caplog.set_level(logging.INFO, logger=logger.name)

    tool = TextAnalysisTool()
    res = tool._run("good good text")
    assert res.success

    payloads = _extract_logged(caplog)
    assert any(p.get("tool") == "text_analysis" and p.get("success") is True for p in payloads)


def test_ytdlp_observed_error_path(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("observability")
    caplog.set_level(logging.INFO, logger=logger.name)

    tool = YtDlpDownloadTool()
    # Provide an invalid URL so subprocess returns non-zero and results in fail
    res = tool._run("https://invalid.localhost/not-real", quality="1080p")
    assert not res.success

    payloads = _extract_logged(caplog)
    assert any(p.get("tool") == "yt_dlp_download" and p.get("success") is False for p in payloads)
