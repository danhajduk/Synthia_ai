from __future__ import annotations
import logging
logger = logging.getLogger("synthia.store.normalize")

from .models import CatalogAddon


def normalize_catalog_entry(addon: CatalogAddon) -> CatalogAddon:
    logger.debug(f"Normalizing CatalogAddon: id={addon.id}, name={addon.name}")

    # Defaults
    if not addon.ref:
        addon.ref = "main"
        logger.info(f"Set default ref for CatalogAddon {addon.id} to 'main'")
    if not addon.path:
        addon.path = "."
        logger.info(f"Set default path for CatalogAddon {addon.id} to '.'")

    # Basic path safety (avoid traversal)
    norm = addon.path.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("~") or "://" in norm:
        logger.error(f"Invalid addon path for {addon.id}: {addon.path}")
        raise ValueError(f"Invalid addon path (must be repo-relative): {addon.path}")
    if ".." in norm.split("/"):
        logger.error(f"Invalid addon path for {addon.id}: {addon.path}")
        raise ValueError(f"Invalid addon path (no '..' allowed): {addon.path}")

    logger.info(f"CatalogAddon {addon.id} normalized successfully")
    return addon
