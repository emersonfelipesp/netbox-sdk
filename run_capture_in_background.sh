#!/usr/bin/env sh
# Run command-doc capture in the background; log to docs/generated/capture-run.log
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p docs/generated
LOG="docs/generated/capture-run.log"
PIDFILE="docs/generated/capture-run.pid"
# Prefer project venv / active venv so typer/textual are available (system python3 may lack deps).
if [ -n "${NBX_DOC_PYTHON}" ]; then
  PY="${NBX_DOC_PYTHON}"
elif [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
elif [ -n "${VIRTUAL_ENV}" ] && [ -x "${VIRTUAL_ENV}/bin/python" ]; then
  PY="${VIRTUAL_ENV}/bin/python"
else
  PY=python3
fi
if ! command -v "$PY" >/dev/null 2>&1 && [ ! -x "$PY" ]; then
  echo "Python not found (set NBX_DOC_PYTHON or create .venv). Tried: $PY" >&2
  exit 1
fi
# Same as: nbx docs generate-capture
nohup "$PY" docs/generate_command_docs.py >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "Started 'python docs/generate_command_docs.py' as PID $(cat "$PIDFILE")"
echo "Log: $ROOT/$LOG"
