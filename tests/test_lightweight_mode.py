import importlib
import os


def test_lightweight_mode_skips_discord_import():
    # Ensure guard envs are in default lightweight state
    os.environ.pop("FULL_STACK_TEST", None)
    os.environ["LIGHTWEIGHT_IMPORT"] = "1"
    # Clear any cached modules to ensure clean import
    import sys

    modules_to_remove = [m for m in sys.modules if m == "discord" or m.startswith("discord.")]
    for mod in modules_to_remove:
        sys.modules.pop(mod, None)
    # Import the startup module that would normally pull discord heavy bits
    importlib.invalidate_caches()
    mod = importlib.import_module("scripts.start_full_bot")
    # Access a lightweight helper to ensure module executed
    assert hasattr(mod, "create_full_bot")
    # discord should not be in sys.modules if guarded

    assert not any(
        m for m in sys.modules if m == "discord" or m.startswith("discord.")
    ), "discord imported despite LIGHTWEIGHT_IMPORT=1; guard may have regressed"
