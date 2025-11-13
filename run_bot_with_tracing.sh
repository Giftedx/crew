#!/bin/bash
# Comprehensive bot runner with exit tracing

set -x  # Enable command tracing
trap 'echo "EXIT TRAP: Script exiting with code $?"' EXIT
trap 'echo "ERR TRAP: Command failed with code $?"' ERR
trap 'echo "INT TRAP: Received SIGINT"' INT
trap 'echo "TERM TRAP: Received SIGTERM"' TERM
trap 'echo "HUP TRAP: Received SIGHUP"' HUP

cd /home/crew
export PYTHONPATH=/home/crew/src

echo "=== Starting bot at $(date) ==="
echo "PID: $$"

# Run bot and capture exit code
.venv/bin/python -m app.discord.runner
EXIT_CODE=$?

echo "=== Bot exited with code $EXIT_CODE at $(date) ==="
echo "Sleeping 10 seconds to preserve output..."
sleep 10
