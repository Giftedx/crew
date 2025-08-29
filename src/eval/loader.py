from __future__ import annotations

"""Dataset loading helpers for the golden evaluation suite."""

import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        return items
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def load_cases(dataset_root: Path, tenant: str | None = None) -> dict[str, list[dict]]:
    """Load all task cases from ``dataset_root``.

    Parameters
    ----------
    dataset_root:
        Path to the ``datasets/golden/core/v1`` directory.
    tenant:
        Optional tenant slug.  If provided, overrides under
        ``datasets/golden/tenants/<tenant>/overrides`` are merged by ``id``.
    """

    cases: dict[str, list[dict]] = {}
    for file in dataset_root.glob("*.jsonl"):
        cases[file.stem] = _load_jsonl(file)

    if tenant:
        override_dir = (
            dataset_root.parent.parent / "tenants" / tenant / "overrides" / dataset_root.name
        )
        for file in override_dir.glob("*.jsonl"):
            base = cases.get(file.stem, [])
            overrides = {item["id"]: item for item in _load_jsonl(file)}
            merged: list[dict] = []
            seen = set()
            for item in base:
                if item["id"] in overrides:
                    merged.append(overrides[item["id"]])
                    seen.add(item["id"])
                else:
                    merged.append(item)
            for oid, item in overrides.items():
                if oid not in seen:
                    merged.append(item)
            cases[file.stem] = merged
    return cases


__all__ = ["load_cases"]
