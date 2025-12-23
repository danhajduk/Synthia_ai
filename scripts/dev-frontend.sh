#!/usr/bin/env bash
set -ex  # e = exit on error, x = log each command

PROJECT_ROOT="/home/dan/Projects/Synthia"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

export HOME="/home/dan"

# Explicitly load nvm
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  . "$NVM_DIR/nvm.sh"
else
  echo "[SYNTHIA] nvm.sh not found at $NVM_DIR/nvm.sh" >&2
  exit 1
fi

# ------------------------------------------------------------
# 🔪 Stop existing frontend dev server (safe version)
# ------------------------------------------------------------

echo "[SYNTHIA] Checking for running Vite dev server..."

# Detect Vite or Node processes running Vite
PIDS=$(pgrep -af "vite" | awk '{print $1}')

if [ -n "$PIDS" ]; then
  echo "[SYNTHIA] Killing existing Vite processes: $PIDS"
  kill $PIDS || true
  sleep 1
else
  echo "[SYNTHIA] No previous Vite process found."
fi

# Extra safety: free port 5173 if something is still stuck
if lsof -i :5173 > /dev/null 2>&1; then
  echo "[SYNTHIA] Port 5173 still in use. Force killing..."
  fuser -k 5173/tcp || true
  sleep 1
fi

# ------------------------------------------------------------
# 🚀 Start the frontend
# ------------------------------------------------------------

cd "$FRONTEND_DIR" || exit 1

echo "[SYNTHIA] Node version:"
node -v

echo "[SYNTHIA] NPM version:"
npm -v

echo "[SYNTHIA] Using Node 22..."
nvm use 22

echo "[SYNTHIA] Starting Vite dev server on 0.0.0.0:5173..."
exec npm run dev -- --host 0.0.0.0 --port 5173
