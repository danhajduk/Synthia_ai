#!/usr/bin/env bash
set -e

PROJECT_ROOT="/home/dan/Projects/Synthia"
ADDONS_DIR="$PROJECT_ROOT/addons"
FRONTEND_ADDONS_DIR="$PROJECT_ROOT/frontend/src/addons"

mkdir -p "$FRONTEND_ADDONS_DIR"

echo "[SYNTHIA] Syncing frontend addons..."

for addon in "$ADDONS_DIR"/*; do
  [ -d "$addon" ] || continue
  name="$(basename "$addon")"
  src="$addon/frontend"
  dest="$FRONTEND_ADDONS_DIR/$name"

  if [ -d "$src" ]; then
    echo "  - $name"

    # remove existing target
    rm -rf "$dest"

    # OPTION A: symlink (preferred)
    ln -s "../../../addons/$name/frontend" "$dest"

    # OPTION B: copy instead (uncomment if you want copying):
    # mkdir -p "$dest"
    # cp -r "$src/"* "$dest/"
  fi
done

echo "[SYNTHIA] Done."
