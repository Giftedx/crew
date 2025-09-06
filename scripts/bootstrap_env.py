#!/usr/bin/env python3
"""Create a virtualenv and install project dependencies.

This script standardizes environment setup across platforms.

Steps:
1) Create `.venv` (or reuse if present)
2) Upgrade pip/setuptools/wheel
3) Install the package in editable mode with dev extras: `.[dev]`
4) Install pre-commit hooks

Usage:
  python scripts/bootstrap_env.py
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    """Execute command with input validation."""
    # Basic validation to prevent command injection
    if not cmd or not all(isinstance(arg, str) for arg in cmd):
        raise ValueError("Command must be a non-empty list of strings")

    print("$", " ".join(cmd))
    subprocess.check_call(cmd, env=env)  # nosec: B603 - validated input


def main() -> int:
    if not (3, 10) <= sys.version_info < (3, 14):
        print("[!] Python version not supported. Required: >=3.10,<3.14")
        print(f"    Current: {platform.python_version()}")
        return 1

    project_root = Path(__file__).resolve().parents[1]
    venv_dir = project_root / ".venv"
    if not venv_dir.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)])

    # Determine venv Python
    if os.name == "nt":
        vpy = venv_dir / "Scripts" / "python.exe"
        pvc = venv_dir / "Scripts" / "pre-commit.exe"
        pip = [str(vpy), "-m", "pip"]
    else:
        vpy = venv_dir / "bin" / "python"
        pvc = venv_dir / "bin" / "pre-commit"
        pip = [str(vpy), "-m", "pip"]

    # Upgrade pip toolchain and install deps
    run(pip + ["install", "--upgrade", "pip", "setuptools", "wheel"])
    run([str(vpy), "-m", "pip", "install", "-e", ".[dev]"])

    # Install pre-commit hooks if available
    try:
        run([str(pvc), "install", "--install-hooks"])  # type: ignore[list-item]
    except Exception:
        print("[i] pre-commit not available yet; you can run `make pre-commit` later.")

    print("\n[✓] Environment ready.")
    if os.name == "nt":
        print("Activate: .venv\\Scripts\\activate")
    else:
        print("Activate: source .venv/bin/activate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

