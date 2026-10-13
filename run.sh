#!/usr/bin/env bash
# Saathi — one command for Mac / Linux:   ./run.sh
# (If you get "permission denied":   bash run.sh)
set -e
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3 is not installed. On a Mac run:  xcode-select --install   then try again."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "First run: setting up (about 30 seconds)…"
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q --disable-pip-version-check -r requirements.txt

PORT="${PORT:-8000}"
export PORT
if command -v lsof >/dev/null 2>&1; then
  lsof -ti:"$PORT" | xargs kill 2>/dev/null || true   # free the port if an old Saathi is still running
fi

URL="http://localhost:$PORT"
( sleep 2
  if command -v open >/dev/null 2>&1; then open -a "Google Chrome" "$URL" 2>/dev/null || open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
  fi ) &

exec python backend/main.py
