# backend/app/addons/installed_store.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set

# Store will live next to this file: backend/app/addons/installed.json
INSTALLED_FILE = Path(__file__).resolve().with_name("installed.json")

# Module docstring: explains the purpose of this module.
# This module manages a simple JSON-backed store of installed addon IDs.
# The JSON file maps addon_id -> bool (True means installed). Functions here
# read/write the file and expose helpers to mark addons installed/uninstalled.


def _read_raw() -> Dict[str, bool]:
    # Read the raw JSON file and return a dict mapping addon_id -> bool.
    # If the file doesn't exist or is corrupted, return an empty dict to avoid
    # crashing the application.
    if not INSTALLED_FILE.exists():
        return {}

    try:
        with INSTALLED_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Normalize keys to str and values to bool to ensure consistent types.
            return {str(k): bool(v) for k, v in data.items()}
    except Exception:
        # If anything goes wrong (parse error, IO error, etc.) return empty.
        # This defensive behavior prevents a corrupted file from crashing the app.
        return {}

    return {}


def _write_raw(data: Dict[str, bool]) -> None:
    # Write the provided dict to disk as JSON. Use an atomic replace strategy:
    # write to a temporary file next to the target, then replace the original.
    INSTALLED_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = INSTALLED_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        # Pretty-print and sort keys for readability and deterministic diffs.
        json.dump(data, f, indent=2, sort_keys=True)
    # Replace the old file with the new file atomically when possible.
    tmp.replace(INSTALLED_FILE)


def get_installed_addons() -> Set[str]:
    """
    Return a set of addon IDs that are currently marked as installed.
    """
    # Filter the raw dict to only those entries with a truthy value.
    raw = _read_raw()
    return {addon_id for addon_id, enabled in raw.items() if enabled}


def mark_installed(addon_id: str) -> None:
    """
    Mark the given addon ID as installed/enabled.
    """
    # Read current store, set the id to True, and write back.
    data = _read_raw()
    data[addon_id] = True
    _write_raw(data)


def mark_uninstalled(addon_id: str) -> None:
    """
    Mark the given addon ID as not installed.
    """
    # Remove the id from the store if present and write back.
    data = _read_raw()
    if addon_id in data:
        del data[addon_id]
        _write_raw(data)
