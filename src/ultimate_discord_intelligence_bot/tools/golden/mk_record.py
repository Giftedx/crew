"""Create a golden dataset record with schema validation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parents[4] / "datasets/schemas/task_record.schema.json"
SCHEMA = json.load(open(SCHEMA_PATH))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args(argv)
    record = {
        "task": args.task,
        "input": {"query": args.query},
        "expected": {},
    }
    jsonschema.validate(record, SCHEMA)
    print(json.dumps(record))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
