#!/usr/bin/env sh
# Run command-doc capture in the background; log to docs/generated/capture-run.log
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p docs/generated
LOG="docs/generated/capture-run.log"
PIDFILE="docs/generated/capture-run.pid"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install from https://docs.astral.sh/uv/ or run: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
# Same as: nbx docs generate-capture
nohup uv run nbx docs generate-capture >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "Started 'uv run nbx docs generate-capture' as PID $(cat "$PIDFILE")"
echo "Log: $ROOT/$LOG"
