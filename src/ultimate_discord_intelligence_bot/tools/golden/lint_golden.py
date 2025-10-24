"""Lint golden dataset files for basic issues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

import jsonschema


if TYPE_CHECKING:
    from collections.abc import Sequence


SCHEMA_PATH = Path(__file__).resolve().parents[4] / "datasets/schemas/task_record.schema.json"
with open(SCHEMA_PATH, encoding="utf-8") as fh:
    SCHEMA = json.load(fh)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True)
    a = p.parse_args(argv)
    ok = True
    for i, line in enumerate(Path(a.dataset).read_text().splitlines(), 1):
        try:
            jsonschema.validate(json.loads(line), SCHEMA)
        except jsonschema.ValidationError as e:
            print(f"line {i}: {e.message}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
