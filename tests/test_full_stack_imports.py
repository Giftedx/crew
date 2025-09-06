import importlib
import os


def test_full_stack_imports_present():
    # Force full-stack path by ensuring LIGHTWEIGHT_IMPORT is not set
    os.environ.pop("LIGHTWEIGHT_IMPORT", None)
    os.environ.pop("FULL_STACK_TEST", None)
    # Import the startup module; this should pull in heavy deps
    importlib.invalidate_caches()
    mod = importlib.import_module("scripts.start_full_bot")
    assert hasattr(mod, "create_full_bot")
    # Now discord should be present (fastapi is not imported in this module)
    import sys

    assert "discord" in sys.modules, "discord not imported in full-stack mode"
