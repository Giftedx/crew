import contextlib
import sys
from importlib import util
from io import StringIO
from pathlib import Path
from types import ModuleType


def _load_script_module(path: Path) -> ModuleType:
    spec = util.spec_from_file_location("validate_deprecation_schedule", path)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module  # Ensure available during exec for dataclasses processing
    spec.loader.exec_module(module)
    return module


def test_deprecation_schedule_validator_runs():
    script_path = Path("scripts/validate_deprecation_schedule.py")
    assert script_path.exists(), "validator script missing"
    module = _load_script_module(script_path)
    stdout = StringIO()
    with contextlib.redirect_stdout(stdout):
        rc = module.main()
    output = stdout.getvalue()
    assert rc == 0, output
    assert "Upcoming deprecations:" in output
    assert "ENABLE_HTTP_RETRY" in output
