from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_http_guard_detects_direct_requests(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    test_file = src / "bad.py"
    test_file.write_text("import requests\nrequests.get('https://example.com')\n", encoding="utf-8")

    # Run the guard script directly against our temp src directory by symlinking into repo-like structure
    # We invoke via Python to ensure module resolution is stable across environments.
    guard = Path("scripts/validate_http_wrappers_usage.py").resolve()
    # Copy guard to tmp and adjust ROOT to tmp for isolation
    guard_copy = tmp_path / "validate_http_wrappers_usage.py"
    text = guard.read_text(encoding="utf-8")
    # Force ROOT to tmp_path for the test execution
    text = text.replace("ROOT = pathlib.Path(__file__).resolve().parents[1]", f"ROOT = pathlib.Path('{tmp_path.as_posix()}')")
    guard_copy.write_text(text, encoding="utf-8")

    proc = subprocess.run([sys.executable, str(guard_copy)], check=False, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "bad.py" in proc.stdout

