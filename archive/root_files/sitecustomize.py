# Ensure reliable pytest startup by disabling third-party plugin auto-loading
# This avoids import-time crashes from environment-specific plugins (e.g., chromadb)
# while still allowing developers to override locally by setting the env var explicitly.
import os


# Force-disable third-party plugin autoloading which may import chromadb plugins
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

# Ensure no third-party plugins are force-loaded via env var
os.environ["PYTEST_PLUGINS"] = ""

# Add defensive flags to ignore problematic plugins if provided elsewhere
addopts = os.environ.get("PYTEST_ADDOPTS", "").strip()
flags = [
    "-p",
    "no:chromadb",
    "-p",
    "no:chromadb.test",
    "-p",
    "no:chromadb.test.conftest",
    "-p",
    "no:lance",
    "-p",
    "no:lancedb",
    "-p",
    "no:pyarrow",
]
joined_flags = " ".join(flags)
if joined_flags not in addopts:
    os.environ["PYTEST_ADDOPTS"] = (addopts + " " + joined_flags).strip()
