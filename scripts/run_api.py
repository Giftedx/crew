#!/usr/bin/env python3
"""Programmatic API server launcher that ensures platform proxy bootstrap
executes before uvicorn loads optional websocket stacks.

This avoids stdlib 'platform' name collisions caused by the local 'platform/'
package when running under tools that import websockets (which imports
uuid/platform) prior to importing our app module.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure virtual environment packages come before src to avoid stub conflicts
# This must happen BEFORE any other imports
venv_path = os.path.join(os.path.dirname(__file__), '..', '.venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

# Temporarily remove src from path to avoid stub conflicts with FastAPI
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path in sys.path:
    sys.path.remove(src_path)

try:
    # Ensure platform proxy bootstrap runs early
    from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy  # type: ignore
except Exception:
    ensure_platform_proxy = None  # type: ignore

if callable(ensure_platform_proxy):  # type: ignore
    try:
        ensure_platform_proxy()  # type: ignore
    except Exception:
        # Non-fatal: best-effort bootstrap
        pass

import uvicorn  # noqa: E402
from server.app import create_app  # noqa: E402

# Restore src path now that critical imports are done
sys.path.insert(0, src_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FastAPI server with safe bootstrap")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    # Note: We deliberately do not force websocket protocols here; uvicorn may
    # still import its auto websocket resolver, but our early bootstrap ensures
    # stdlib platform resolution is correct before that happens.

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
