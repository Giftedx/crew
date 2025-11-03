"""CLI entrypoints for the ingestion pipeline.

Allows running either:

    python -m ingest.pipeline <url> --tenant <tenant> --workspace <ws>
    python -m ingest <url> --tenant <tenant> --workspace <ws>

The second form is a convenience wrapper forwarding to the pipeline module.
"""

from __future__ import annotations

import argparse

from domains.memory import vector_store

from . import pipeline
from .pipeline import IngestJob


def _parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Run a single ingestion job")
    p.add_argument("url", help="Source URL to ingest (YouTube/Twitch/TikTok)")
    p.add_argument("--tenant", required=True, help="Tenant slug")
    p.add_argument("--workspace", required=True, help="Workspace name")
    p.add_argument("--source", help="Override source type (auto-detected if omitted)")
    p.add_argument("--tags", nargs="*", default=[], help="Optional tag list")
    return p.parse_args(argv)


def _infer_source(url: str) -> str:
    if "youtube" in url or "youtu.be" in url:
        return "youtube"
    if "twitch.tv" in url:
        return "twitch"
    raise SystemExit("Could not infer source; specify --source explicitly")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source = args.source or _infer_source(args.url)
    job = IngestJob(
        source=source, external_id="manual", url=args.url, tenant=args.tenant, workspace=args.workspace, tags=args.tags
    )
    store = vector_store.VectorStore()
    result = pipeline.run(job, store)
    print(f"Ingest complete: namespace={result['namespace']} chunks={result['chunks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
