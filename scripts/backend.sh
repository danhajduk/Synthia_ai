#!/usr/bin/env bash
set -e

PROJECT_ROOT="/home/dan/Projects/Synthia"
VENV="$PROJECT_ROOT/.venv"
BACKEND_DIR="$PROJECT_ROOT/backend"
REQ_FILE="$PROJECT_ROOT/requirements.txt"

echo "[SYNTHIA] Ensuring virtual environment exists..."
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

echo "[SYNTHIA] Activating virtual environment..."
source "$VENV/bin/activate"

if [ -f "$REQ_FILE" ]; then
    echo "[SYNTHIA] Installing/updating Python dependencies..."
    pip install --upgrade pip >/dev/null
    pip install -r "$REQ_FILE"
else
    echo "[SYNTHIA] WARNING: No requirements.txt found at $REQ_FILE"
fi

echo "[SYNTHIA] Stopping any existing backend on port 9001 (if running)..."
pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 9001" 2>/dev/null || true
pkill -f "uvicorn app.main:app --host 0.0.0.0 --port 9001" 2>/dev/null || true

echo "[SYNTHIA] Starting backend on 0.0.0.0:9001 (with reload)..."
cd "$BACKEND_DIR"

# Making sure backend root is importable
export PYTHONPATH="$BACKEND_DIR:$PROJECT_ROOT"
rm -f "$PROJECT_ROOT/backend.log"

# Start uvicorn in the background and log to file
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload \
  >> "$PROJECT_ROOT/backend.log" 2>&1 &

UVICORN_PID=$!

echo "[SYNTHIA] Backend started with PID $UVICORN_PID"
echo "[SYNTHIA] Tailing last 30 log lines (Ctrl+C to stop tail, backend keeps running)..."

# Follow the log live
tail -n 30 -f "$PROJECT_ROOT/backend.log"

# If you press Ctrl+C, tail stops — backend keeps running
wait $UVICORN_PID
