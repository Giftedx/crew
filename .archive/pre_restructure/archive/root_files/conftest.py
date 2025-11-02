"""Pytest configuration shims for local src-layout imports.

Enhancements in this file also provide hang protection during tests:
- Global faulthandler dump after a long delay (diagnostics)
- Per-test timeout using POSIX signals on Linux (raises TimeoutError)
- Safe fallbacks when signals are unavailable

You can control these with environment variables:
- PYTEST_TEST_TIMEOUT_SECONDS (default: 120, or 300 when FULL_STACK_TEST=1)
- PYTEST_GLOBAL_TRACEBACK_TIMEOUT_SECONDS (default: 900)
- PYTEST_DISABLE_TIMEOUT (set to 1 to disable per-test timeout)
- PYTEST_DISABLE_GLOBAL_TRACEBACK (set to 1 to disable global dumps)
"""

from __future__ import annotations

import contextlib
import faulthandler
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest


try:
    import signal

    _HAS_SIGNAL = True
except Exception:  # pragma: no cover - non-POSIX fallback
    signal = None  # type: ignore
    _HAS_SIGNAL = False

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# ---------------------------------------------------------------------------
# Lightweight CrewAI stub for test environments
# ---------------------------------------------------------------------------
# Some environments lack compiled numpy wheels required by chromadb, which
# CrewAI imports transitively. That makes importing the real 'crewai' package
# fail during test collection. To keep our tests hermetic and fast, provide a
# minimal stub that satisfies the surfaces our code and tests rely on.


def _install_crewai_stub() -> None:
    if "crewai" in sys.modules:
        return  # already present (real or stub)

    crewai = ModuleType("crewai")

    class Agent:  # minimal constructor-compatible stub
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class Task:  # placeholder object used in crew construction
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class Process:
        sequential = "sequential"

    class Crew:
        def __init__(self, *args, **kwargs):
            # Store kwargs for tests that introspect .embedder etc.
            for k, v in kwargs.items():
                setattr(self, k, v)

        def kickoff(self, *args, **kwargs):
            return {"status": "ok"}

    # Decorators in crewai.project simply return the function unmodified
    project = ModuleType("crewai.project")

    def _identity(fn):
        return fn

    project.agent = _identity
    project.task = _identity
    project.crew = _identity

    # tools.BaseTool required by our wrappers in some code paths
    tools = ModuleType("crewai.tools")

    class BaseTool:  # pragma: no cover - trivial shim
        def __init__(self, *args, **kwargs):
            pass

        def _run(self, *args, **kwargs):
            return None

    tools.BaseTool = BaseTool

    # Export into the stub module
    crewai.Agent = Agent
    crewai.Task = Task
    crewai.Process = Process
    crewai.Crew = Crew
    crewai.project = project
    crewai.tools = tools

    # Register in sys.modules so imports resolve to the stub
    sys.modules["crewai"] = crewai
    sys.modules["crewai.project"] = project
    sys.modules["crewai.tools"] = tools


# Install the stub unless explicitly disabled
if os.getenv("PYTEST_DISABLE_CREWAI_STUB", "0").lower() not in {"1", "true", "yes"}:
    _install_crewai_stub()


# ---------------------------------------------------------------------------
# Minimal stubs for third-party heavy deps pulled in transitively by crewai
# ---------------------------------------------------------------------------
def _install_third_party_stubs() -> None:
    # Stub for chromadb (imported by crewai rag modules); expose minimal surface
    if "chromadb" not in sys.modules:
        chromadb = ModuleType("chromadb")
        chromadb.__path__ = []  # mark as package

        class PersistentClient:  # pragma: no cover - shim
            def __init__(self, *args, **kwargs):
                pass

        chromadb.PersistentClient = PersistentClient
        sys.modules["chromadb"] = chromadb

        # Provide chromadb.api.* placeholders expected by crewai
        api = ModuleType("chromadb.api")
        sys.modules["chromadb.api"] = api
        api_client = ModuleType("chromadb.api.client")

        class Client:  # minimal shim
            def __init__(self, *args, **kwargs):
                pass

        api_client.Client = Client
        sys.modules["chromadb.api.client"] = api_client
        api_types = ModuleType("chromadb.api.types")
        sys.modules["chromadb.api.types"] = api_types
        # Provide a minimal 'chromadb.test' package stub for libraries that import it.
        # We intentionally do NOT provide 'chromadb.test.conftest' to avoid pytest plugin conflicts.
        if "chromadb.test" not in sys.modules:
            chromadb_test = ModuleType("chromadb.test")
            chromadb_test.__path__ = [str(ROOT / "_chromadb_test_stub")]  # mark as package
            chromadb_test.__file__ = str(ROOT / "_chromadb_test_stub" / "__init__.py")
            sys.modules["chromadb.test"] = chromadb_test
    # Create a stub for 'chromadb.test.conftest' with an expected site-packages path
    # to avoid ImportPathMismatch errors during pytest collection.
    if "chromadb.test.conftest" not in sys.modules:
        import sys as _sys

        venv_root = os.environ.get("VIRTUAL_ENV") or str(Path(__file__).resolve().parent / ".venv")
        # Prefer python3.11 path if present (observed in CI), else current interpreter's version
        p311 = Path(venv_root) / "lib" / "python3.11" / "site-packages" / "chromadb" / "test" / "conftest.py"
        pcur = (
            Path(venv_root)
            / "lib"
            / f"python{_sys.version_info.major}.{_sys.version_info.minor}"
            / "site-packages"
            / "chromadb"
            / "test"
            / "conftest.py"
        )
        expected = p311 if p311.exists() else pcur
        chromadb_test_conftest = ModuleType("chromadb.test.conftest")
        chromadb_test_conftest.__file__ = str(expected)
        sys.modules["chromadb.test.conftest"] = chromadb_test_conftest

    # Stub numpy.typing used by chromadb
    if "numpy" not in sys.modules:
        numpy = ModuleType("numpy")

        class _NPArray:
            pass

        numpy.ndarray = _NPArray  # type: ignore[attr-defined]
        sys.modules["numpy"] = numpy
    if "numpy.typing" not in sys.modules:
        np_typing = ModuleType("numpy.typing")

        class NDArray:  # type: ignore
            pass

        np_typing.NDArray = NDArray
        sys.modules["numpy.typing"] = np_typing

    # Stub pyarrow to avoid binary dependency import errors triggered by 'lance'
    if "pyarrow" not in sys.modules:
        pyarrow = ModuleType("pyarrow")

        # Minimal attributes used by lancedb typing
        class _Dummy:
            pass

        pyarrow.Table = _Dummy
        pyarrow.RecordBatch = _Dummy
        pyarrow.RecordBatchReader = _Dummy
        pyarrow.Array = _Dummy
        pyarrow.ChunkedArray = _Dummy
        pyarrow.Schema = _Dummy
        pyarrow.DataType = _Dummy
        sys.modules["pyarrow"] = pyarrow
    if "pyarrow.lib" not in sys.modules:
        pyarrow_lib = ModuleType("pyarrow.lib")
        sys.modules["pyarrow.lib"] = pyarrow_lib
    if "pyarrow.dataset" not in sys.modules:
        pyarrow_dataset = ModuleType("pyarrow.dataset")
        sys.modules["pyarrow.dataset"] = pyarrow_dataset
    if "pyarrow.fs" not in sys.modules:
        pyarrow_fs = ModuleType("pyarrow.fs")

        class FileSystem:  # type: ignore
            pass

        pyarrow_fs.FileSystem = FileSystem
        sys.modules["pyarrow.fs"] = pyarrow_fs

    # Stub lance which imports pyarrow at import time and may expose pytest plugins
    if "lance" not in sys.modules:
        lance = ModuleType("lance")
        lance.__path__ = [str(ROOT / "_lance_stub")]  # mark as package
        lance.__file__ = str(ROOT / "_lance_stub" / "__init__.py")
        sys.modules["lance"] = lance
    # Provide a lance.conftest stub with real site-packages path to avoid ImportPathMismatch
    if "lance.conftest" not in sys.modules:
        import sys as _sys

        venv_root = os.environ.get("VIRTUAL_ENV") or str(Path(__file__).resolve().parent / ".venv")
        p311 = Path(venv_root) / "lib" / "python3.11" / "site-packages" / "lance" / "conftest.py"
        pcur = (
            Path(venv_root)
            / "lib"
            / f"python{_sys.version_info.major}.{_sys.version_info.minor}"
            / "site-packages"
            / "lance"
            / "conftest.py"
        )
        expected = p311 if p311.exists() else pcur
        lance_conftest = ModuleType("lance.conftest")
        lance_conftest.__file__ = str(expected)
        sys.modules["lance.conftest"] = lance_conftest

    # Stub lancedb to avoid importing heavy deps (pydantic_core, pyarrow, etc.)
    if "lancedb" not in sys.modules:
        import sys as _sys

        venv_root = os.environ.get("VIRTUAL_ENV") or str(Path(__file__).resolve().parent / ".venv")
        p311_pkg = Path(venv_root) / "lib" / "python3.11" / "site-packages" / "lancedb"
        pcur_pkg = (
            Path(venv_root)
            / "lib"
            / f"python{_sys.version_info.major}.{_sys.version_info.minor}"
            / "site-packages"
            / "lancedb"
        )
        pkg_dir = p311_pkg if p311_pkg.exists() else pcur_pkg
        lancedb = ModuleType("lancedb")
        lancedb.__path__ = [str(pkg_dir)]  # treat as package
        lancedb.__file__ = str(pkg_dir / "__init__.py")
        sys.modules["lancedb"] = lancedb
        # Provide common submodules imported during package init
        lancedb_db = ModuleType("lancedb.db")
        sys.modules["lancedb.db"] = lancedb_db
        lancedb_embeddings = ModuleType("lancedb.embeddings")
        sys.modules["lancedb.embeddings"] = lancedb_embeddings
        lancedb_embeddings_registry = ModuleType("lancedb.embeddings.registry")
        sys.modules["lancedb.embeddings.registry"] = lancedb_embeddings_registry
        lancedb_embeddings_base = ModuleType("lancedb.embeddings.base")
        sys.modules["lancedb.embeddings.base"] = lancedb_embeddings_base
        lancedb_common = ModuleType("lancedb.common")
        sys.modules["lancedb.common"] = lancedb_common
        lancedb_util = ModuleType("lancedb.util")
        sys.modules["lancedb.util"] = lancedb_util
    # Point conftest to real site-packages to satisfy pytest import path checks
    lancedb_conftest = ModuleType("lancedb.conftest")
    lancedb_conftest.__file__ = str(pkg_dir / "conftest.py")
    sys.modules["lancedb.conftest"] = lancedb_conftest


if os.getenv("PYTEST_DISABLE_HEAVY_STUBS", "0").lower() not in {"1", "true", "yes"}:
    _install_third_party_stubs()


@pytest.hookimpl(tryfirst=True)
def pytest_ignore_collect(path, _config):
    """Optionally skip root-level tests unless FULL_STACK_TEST=1.

    pytest passes a py.path.LocalPath here, not a pathlib.Path. Normalize to
    pathlib for consistent attribute access across environments.
    """
    try:
        p = Path(str(path))
    except Exception:
        # Fallback: best-effort handling using string casting
        p = Path(os.fspath(path))

    # Only applies to root-level test_*.py files (not in subdirs)
    if (
        p.parent == ROOT
        and p.name.startswith("test_")
        and p.suffix == ".py"
        and os.environ.get("FULL_STACK_TEST", "0") != "1"
    ):
        # Print a message for developer clarity
        print(f"[pytest] Skipping root-level {p.name} (set FULL_STACK_TEST=1 to include)")
        return True
    return False


if SRC.exists():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # pragma: no cover - environment hygiene
    """Disable problematic third-party plugins like chromadb.*.

    Even with PYTEST_DISABLE_PLUGIN_AUTOLOAD, some environments pre-load
    plugins. Explicitly unregister any matching plugins to avoid import
    mismatches during collection.
    """
    try:
        pluginmanager = config.pluginmanager
        for name in list(pluginmanager.list_name_plugin()):
            lname = str(name).lower()
            if (
                lname.startswith(("chromadb", "lance", "lancedb", "pyarrow"))
                or ".chromadb" in lname
                or ".lance" in lname
                or ".lancedb" in lname
                or ".pyarrow" in lname
            ):
                try:
                    pluginmanager.unregister(name)
                except Exception:
                    continue
    except Exception:
        # Best-effort; safe to ignore if plugin manager APIs change
        pass


# ---------------------------------------------------------------------------
# Hang protection: global traceback dump and per-test timeout
# ---------------------------------------------------------------------------


def _int_from_env(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, str(default))).strip())
    except Exception:
        return default


@pytest.fixture(autouse=True, scope="session")
def _global_traceback_dumps():  # pragma: no cover - diagnostic facility
    """Enable global traceback dumps to stderr if the test run stalls.

    Controlled by PYTEST_GLOBAL_TRACEBACK_TIMEOUT_SECONDS (default: 900).
    Disable via PYTEST_DISABLE_GLOBAL_TRACEBACK=1.
    """
    if os.getenv("PYTEST_DISABLE_GLOBAL_TRACEBACK", "0").lower() in {
        "1",
        "true",
        "yes",
    }:
        return
    delay = _int_from_env("PYTEST_GLOBAL_TRACEBACK_TIMEOUT_SECONDS", 900)
    with contextlib.suppress(Exception):
        faulthandler.enable()  # idempotent
        faulthandler.dump_traceback_later(delay, repeat=True)
    yield
    with contextlib.suppress(Exception):
        faulthandler.cancel_dump_traceback_later()


@pytest.fixture(autouse=True)
def _per_test_timeout(request):  # pragma: no cover - timing behavior
    """Enforce a per-test timeout to avoid indefinite hangs.

    Default: 120s (or 300s when FULL_STACK_TEST=1). Override with
    PYTEST_TEST_TIMEOUT_SECONDS. Disable with PYTEST_DISABLE_TIMEOUT=1.
    """
    if os.getenv("PYTEST_DISABLE_TIMEOUT", "0").lower() in {"1", "true", "yes"}:
        yield
        return

    # Longer default for full-stack mode
    default_timeout = 300 if os.getenv("FULL_STACK_TEST", "0") == "1" else 120
    timeout = _int_from_env("PYTEST_TEST_TIMEOUT_SECONDS", default_timeout)

    if _HAS_SIGNAL and hasattr(signal, "SIGALRM"):
        test_id = getattr(getattr(request, "node", None), "nodeid", "<unknown test>")

        def _on_timeout(*_):
            with contextlib.suppress(Exception):
                # Dump current stacks to help debugging
                faulthandler.dump_traceback()
            # Raise a TimeoutError to fail the test immediately
            raise TimeoutError(f"⏰ Test timed out after {timeout}s: {test_id}")

        prev_handler = signal.getsignal(signal.SIGALRM)
        try:
            signal.signal(signal.SIGALRM, _on_timeout)
            signal.alarm(timeout)
            yield
        finally:
            with contextlib.suppress(Exception):
                signal.alarm(0)
            with contextlib.suppress(Exception):
                if prev_handler is not None:
                    signal.signal(signal.SIGALRM, prev_handler)  # type: ignore[arg-type]
    else:
        # Fallback: no reliable way to interrupt the test without signals.
        # We still enable faulthandler to provide diagnostics if a hang occurs.
        with contextlib.suppress(Exception):
            faulthandler.enable()
        yield
