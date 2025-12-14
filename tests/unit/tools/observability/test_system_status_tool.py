import builtins
import io
import os
import shutil
from types import SimpleNamespace

from ultimate_discord_intelligence_bot.tools.observability.system_status_tool import SystemStatusTool


def test_system_status_tool_reports_metrics(monkeypatch):
    monkeypatch.setattr(os, "getloadavg", lambda: (1.0, 0.5, 0.2))
    monkeypatch.setattr(shutil, "disk_usage", lambda path: SimpleNamespace(total=100, used=40, free=60))

    def fake_open(path, *args, **kwargs):
        if path == "/proc/meminfo":
            return io.StringIO("MemTotal: 1000 kB\nMemAvailable: 250 kB\n")
        return builtins.open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    tool = SystemStatusTool()
    result = tool._run()
    assert result["status"] == "success"
    assert result["load_avg_1m"] == 1.0
    assert result["disk_free"] == 60
    assert result["mem_total"] == 1000 * 1024
    assert result["mem_free"] == 250 * 1024


def test_system_status_tool_handles_missing_loadavg(monkeypatch):
    def raise_error():
        raise OSError

    monkeypatch.setattr(os, "getloadavg", raise_error)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: SimpleNamespace(total=100, used=40, free=60))
    tool = SystemStatusTool()
    result = tool._run()
    assert result["load_avg_1m"] == 0.0
