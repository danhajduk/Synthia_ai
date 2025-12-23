#!/usr/bin/env bash
set -e  # e = exit on error, x = print each command

PROJECT_ROOT="/home/dan/Projects/Synthia"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "[SYNTHIA] Using PROJECT_ROOT=$PROJECT_ROOT"
echo "[SYNTHIA] Using FRONTEND_DIR=$FRONTEND_DIR"

# --- Load nvm properly (non-interactive safe) ---
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  . "$NVM_DIR/nvm.sh"
else
  echo "[SYNTHIA] ERROR: nvm.sh not found at $NVM_DIR/nvm.sh"
  exit 1
fi

# --- Move into frontend directory ---
cd "$FRONTEND_DIR"

echo "[SYNTHIA] Node version:"
node -v || { echo "[SYNTHIA] ERROR: node not found"; exit 1; }

echo "[SYNTHIA] NPM version:"
npm -v || { echo "[SYNTHIA] ERROR: npm not found"; exit 1; }

echo "[SYNTHIA] Switching to Node 22..."
nvm use 22

echo "[SYNTHIA] Cleaning old build (dist)..."
rm -rf dist

echo "[SYNTHIA] Installing frontend dependencies..."
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "[SYNTHIA] Building production frontend..."
npm run build

if [ ! -d dist ]; then
  echo "[SYNTHIA] ERROR: Build did not produce a dist/ folder"
  exit 1
fi

echo "[SYNTHIA] Reloading nginx..."
sudo systemctl reload nginx

echo "[SYNTHIA] ✔ Done. Production UI is live on port 80."
