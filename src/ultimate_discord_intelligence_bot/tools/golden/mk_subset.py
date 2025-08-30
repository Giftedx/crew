"""Sample a subset of a golden dataset."""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--infile", required=True)
    p.add_argument("--outfile", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    random.seed(a.seed)  # noqa: S311 (non-crypto sampling)
    lines = Path(a.infile).read_text().splitlines()
    sample = random.sample(lines, min(a.n, len(lines)))
    Path(a.outfile).write_text("\n".join(sample) + ("\n" if sample else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
