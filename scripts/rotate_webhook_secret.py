#!/usr/bin/env python
"""Rotate webhook shared secrets in .env (or specified env file).

Workflow:
 1. Generate a new backup secret.
 2. Promote existing WEBHOOK_SECRET_DEFAULT to WEBHOOK_SECRET_BACKUP (if different).
 3. Set new secret as WEBHOOK_SECRET_DEFAULT.
 4. Write updated file (preserving order & comments) to stdout or in-place.

Usage:
  python scripts/rotate_webhook_secret.py               # dry-run (prints diff)
  python scripts/rotate_webhook_secret.py --write       # in-place modify .env
  python scripts/rotate_webhook_secret.py -f .env.local --write

Security:
  - Does NOT commit changes; user must review.
  - Uses secrets.token_urlsafe for high-entropy random values.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

DEFAULT_FILE = Path(".env")


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def rotate_lines(lines: list[str]) -> list[str]:
    current_default = None
    current_backup = None
    default_idx = None
    backup_idx = None

    for i, line in enumerate(lines):
        if line.startswith("WEBHOOK_SECRET_DEFAULT="):
            current_default = line.split("=", 1)[1].strip()
            default_idx = i
        elif line.startswith("WEBHOOK_SECRET_BACKUP="):
            current_backup = line.split("=", 1)[1].strip()
            backup_idx = i

    new_secret = generate_secret()

    # Promote existing default to backup if it exists and differs
    if default_idx is not None:
        old_default_value = current_default or ""
        if backup_idx is None:
            # Insert a backup line right after default line
            insert_idx = default_idx + 1
            lines.insert(insert_idx, f"WEBHOOK_SECRET_BACKUP={old_default_value}\n")
            backup_idx = insert_idx
        elif current_backup != old_default_value and old_default_value:
            lines[backup_idx] = f"WEBHOOK_SECRET_BACKUP={old_default_value}\n"

        # Replace default with new secret
        lines[default_idx] = f"WEBHOOK_SECRET_DEFAULT={new_secret}\n"
    else:
        # Append both if absent
        lines.append(f"WEBHOOK_SECRET_DEFAULT={new_secret}\n")
        lines.append("WEBHOOK_SECRET_BACKUP=\n")

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate webhook shared secrets in env file.")
    parser.add_argument("-f", "--file", type=Path, default=DEFAULT_FILE, help="Env file path (default ./.env)")
    parser.add_argument("--write", action="store_true", help="Apply changes in-place (otherwise diff to stdout)")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"[rotate] File not found: {args.file}", file=sys.stderr)
        return 2

    original = args.file.read_text().splitlines(keepends=True)
    updated = rotate_lines(list(original))

    if args.write:
        args.file.write_text("".join(updated))
        print(f"[rotate] Updated {args.file}. Remember to deploy & revoke old secrets once traffic drains.")
    else:
        print("".join(updated), end="")
        print("\n[rotate] (Dry-run) Pass --write to modify the file in-place.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
