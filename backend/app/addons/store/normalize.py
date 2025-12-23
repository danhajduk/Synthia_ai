from __future__ import annotations

from .models import CatalogAddon


def normalize_catalog_entry(addon: CatalogAddon) -> CatalogAddon:
    # Defaults
    if not addon.ref:
        addon.ref = "main"
    if not addon.path:
        addon.path = "."

    # Basic path safety (avoid traversal)
    norm = addon.path.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("~") or "://" in norm:
        raise ValueError(f"Invalid addon path (must be repo-relative): {addon.path}")
    if ".." in norm.split("/"):
        raise ValueError(f"Invalid addon path (no '..' allowed): {addon.path}")

    return addon
