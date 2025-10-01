from __future__ import annotations

import json
from pathlib import Path

from scripts import run_agentevals_ci

DATASET_PATH = Path(__file__).resolve().parent / "data" / "trajectories" / "regression.json"


def test_run_agentevals_ci_writes_report(tmp_path):
    report_path = tmp_path / "report.json"
    exit_code = run_agentevals_ci.main([str(DATASET_PATH), "--report", str(report_path)])
    assert exit_code == 0
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_evaluations"] == len(payload["evaluations"])
    assert payload["summary"]["total_evaluations"] > 0
