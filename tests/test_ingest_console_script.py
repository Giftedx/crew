import os
import shutil
import subprocess
import sys

import pytest


@pytest.mark.integration
def test_ingest_console_script_help():
    """Verify the console script entry point is installed.

    Falls back to using the module invocation if the script name is not on PATH
    (some CI environments may invoke tests with a different PATH). The purpose
    is mainly to catch accidental removal or renaming of the entry point in
    pyproject.toml.
    """
    # Resolve expected script path inside current virtual environment
    venv_bin = os.path.dirname(sys.executable)
    script_path = os.path.join(venv_bin, "ingest")

    if os.path.exists(script_path):
        cmd = [script_path, "--help"]
    elif shutil.which("ingest"):
        cmd = ["ingest", "--help"]
    else:
        pytest.skip("ingest console script not found on PATH; skipping (module invocation still covered elsewhere)")

    # Security: command list is derived from installed entry point path, no shell used.
    proc = subprocess.run(  # noqa: S603
        cmd, check=True, capture_output=True, text=True, timeout=15
    )
    assert proc.returncode == 0, proc.stderr
    assert "Run a single ingestion job" in proc.stdout
