#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT_DIR/app"

FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"

is_port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv was not found. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ ! -f "$APP_DIR/package.json" ]]; then
  echo "Error: app/package.json not found." >&2
  exit 1
fi

if [[ ! -d "$APP_DIR/node_modules" ]]; then
  echo "Error: app/node_modules not found. Run 'cd app && npm install' first." >&2
  exit 1
fi

if is_port_in_use "$API_PORT"; then
  echo "Error: API port $API_PORT is already in use. Stop the existing process first." >&2
  exit 1
fi

if is_port_in_use "$FRONTEND_PORT"; then
  echo "Error: Frontend port $FRONTEND_PORT is already in use. Stop the existing process first." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo
    echo "Stopping backend (pid: $BACKEND_PID)..."
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting backend on http://$API_HOST:$API_PORT ..."
(
  cd "$ROOT_DIR"
  uv run python scripts/api/run_api.py
) &
BACKEND_PID=$!

echo ""
echo "Frontend link: http://localhost:$FRONTEND_PORT"
echo "Backend docs: http://localhost:$API_PORT/docs"
echo "Press Ctrl+C to stop both services."
echo ""

cd "$APP_DIR"
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort
