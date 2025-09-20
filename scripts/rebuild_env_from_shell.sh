#!/usr/bin/env bash
# Reconstruct a .env file from current shell environment, using keys from .env.example
# - Does NOT print secrets
# - Only writes keys present in .env.example
# - Preserves comments and blank lines from the template
#
# Usage:
#   ./scripts/rebuild_env_from_shell.sh [output=.env]
#
# Exit codes:
#   0 = success
#   1 = template missing
#   2 = output path exists (won't overwrite)

set -euo pipefail

TEMPLATE=".env.example"
OUT_PATH="${1:-.env}"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Template $TEMPLATE not found. Run from repo root or provide the file." >&2
  exit 1
fi

if [[ -e "$OUT_PATH" ]]; then
  echo "Refusing to overwrite existing $OUT_PATH. Move it or pass a different path." >&2
  exit 2
fi

# Create output safely
umask 077
# Create/truncate the output file with secure permissions
: > "$OUT_PATH"

while IFS= read -r line; do
  # Preserve comments and blank lines verbatim
  if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
    printf '%s\n' "$line" >>"$OUT_PATH"
    continue
  fi

  # Expect KEY=VALUE format; keep original formatting for unknown lines
  if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    # Use existing env var if set; otherwise copy the template's value
    if [[ -n "${!key-}" ]]; then
      val="${!key}"
      # Write KEY=value without quotes; .env parsers handle raw values
      printf '%s=%s\n' "$key" "$val" >>"$OUT_PATH"
    else
      # Preserve the template default when env var is missing
      printf '%s\n' "$line" >>"$OUT_PATH"
    fi
  else
    # Fallback: just copy the line
    printf '%s\n' "$line" >>"$OUT_PATH"
  fi

done <"$TEMPLATE"

echo "Wrote $OUT_PATH using $TEMPLATE as the template."
