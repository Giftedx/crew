#!/usr/bin/env python3
"""Local runner for the Autonomous Intelligence Orchestrator.

This script mimics a Discord interaction and runs the full autointel workflow
for a given URL and depth, printing progress and final outputs to stdout.

Usage:
  python -m scripts.run_autointel_local --url https://youtu.be/VIDEO --depth experimental

Notes:
  - This does real work: will attempt to download/transcribe/analyse content.
  - Ensure ffmpeg and yt-dlp are available or expect acquisition to fail gracefully.
  - The script is resilient to Discord embed kwargs and will simply print them.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import sys
from pathlib import Path
from typing import Any


class _Response:
    async def defer(self) -> None:
        # No-op for local runner
        print("[interaction.response.defer] ok")

    async def send_message(self, content: str | None = None, **kwargs: Any) -> None:
        if content:
            print(f"[interaction.response.send_message] {content}")
        if kwargs:
            print(f"[interaction.response.send_message.kwargs] {kwargs}")


class _Followup:
    async def send(self, content: str | None = None, **kwargs: Any) -> None:
        # Accept arbitrary kwargs like embed/embeds/ephemeral
        if content:
            print(f"[interaction.followup.send] {content}")
        # Print simple summaries for embeds
        if "embed" in kwargs and kwargs["embed"] is not None:
            print("[interaction.followup.send.embed]", _summarize_obj(kwargs["embed"]))
        if kwargs.get("embeds"):
            print("[interaction.followup.send.embeds]")
            for i, e in enumerate(kwargs["embeds"], 1):
                print(f"  - embed[{i}]:", _summarize_obj(e))
        other = {k: v for k, v in kwargs.items() if k not in {"embed", "embeds"}}
        if other:
            print(f"[interaction.followup.send.kwargs] {other}")


def _summarize_obj(o: Any) -> str:
    try:
        # Discord Embed objects often have .title/.description
        title = getattr(o, "title", None)
        desc = getattr(o, "description", None)
        if title or desc:
            return json.dumps(
                {
                    "title": title,
                    "description": (desc[:180] + "…") if isinstance(desc, str) and len(desc) > 180 else desc,
                }
            )
        return repr(o)
    except Exception:
        return repr(o)


class LocalInteractionAdapter:
    def __init__(self) -> None:
        self.response = _Response()
        self.followup = _Followup()
        # Minimal guild/channel context for tenancy
        self.guild_id = "local"

        class _Chan:
            name = "local_runner"

        self.channel = _Chan()


async def _main(url: str, depth: str) -> int:
    # Ensure 'src' is on sys.path for local imports without installation
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Normalize depth like the Discord command parser
    depth_norm = depth.strip().lower()
    if depth_norm.startswith("exp") or "experimental" in depth_norm:
        depth_norm = "experimental"
    elif depth_norm.startswith("comp") or "comprehensive" in depth_norm:
        depth_norm = "comprehensive"
    elif depth_norm.startswith("deep"):
        depth_norm = "deep"
    else:
        depth_norm = "standard"

    adapter = LocalInteractionAdapter()

    with contextlib.suppress(Exception):
        await adapter.response.defer()

    print(f"[runner] Starting autointel for: {url} (depth: {depth_norm})")
    try:
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )

        orch = AutonomousIntelligenceOrchestrator()
        await orch.execute_autonomous_intelligence_workflow(adapter, url, depth_norm)
        print("[runner] Workflow completed")
        return 0
    except Exception as e:
        print(f"[runner] Workflow failed: {e}")
        return 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Autonomous Intelligence workflow locally")
    p.add_argument("--url", required=True, help="Target URL to analyze")
    p.add_argument(
        "--depth",
        default="standard",
        help="Analysis depth: standard|deep|comprehensive|experimental (accepts labels)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])
    return asyncio.run(_main(ns.url, ns.depth))


if __name__ == "__main__":
    sys.exit(main())
