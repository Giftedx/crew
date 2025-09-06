#!/usr/bin/env python3
"""Guardrail: forbid direct yt-dlp usage outside approved wrappers.

Scans Python sources under `src/` and fails if `yt-dlp` (or obvious
shell invocations thereof) are referenced outside the allowed modules:

- `src/ultimate_discord_intelligence_bot/tools/yt_dlp_download_tool.py`
- `src/ultimate_discord_intelligence_bot/tools/multi_platform_download_tool.py`

Tests under `tests/` are ignored, as are non-Python files.
"""

from __future__ import annotations

import pathlib
import sys

ALLOWED = {
    "src/ultimate_discord_intelligence_bot/tools/yt_dlp_download_tool.py",
    "src/ultimate_discord_intelligence_bot/tools/multi_platform_download_tool.py",
}


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    violations: list[str] = []
    skip_dirs = {"venv", ".venv", "site-packages", ".git", "build", "dist"}
    for path in src_root.rglob("*.py"):
        rel = str(path.relative_to(repo_root))
        parts = set(rel.split("/"))
        if parts & skip_dirs:
            continue
        if rel in ALLOWED:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lowered = text.lower()
        # Flag only clear import or shell invocation patterns; allow incidental strings/paths
        has_import = ("import yt_dlp" in lowered) or ("from yt_dlp" in lowered)
        has_shell_call = False
        for ln in lowered.splitlines():
            if ("subprocess.run(" in ln or "subprocess.call(" in ln or "popen(" in ln or "os.system(" in ln) and "yt-dlp" in ln:
                has_shell_call = True
                break
        if has_import or has_shell_call:
            violations.append(rel)

    if violations:
        print("Direct yt-dlp references found outside dispatcher/wrapper modules:")
        for v in sorted(violations):
            print(f" - {v}")
        print("Use MultiPlatformDownloadTool and yt_dlp_download_tool wrappers.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
