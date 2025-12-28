from __future__ import annotations
import logging
logger = logging.getLogger("synthia.store.installed_store")

from pathlib import Path
from typing import List
logger = logging.getLogger("synthia.store")


def _core_root() -> Path:
    return Path(__file__).resolve().parents[4]  # -> /home/dan/Projects/Synthia


def get_installed_addons() -> List[str]:
    """
    Installed addons are those present on disk in: <core>/data/addons/<addon-id>/
    """
    install_dir = _core_root() / "data" / "addons"
    logger.debug(f"Checking installed addons directory: {install_dir}")
    if not install_dir.exists():
        logger.debug("Install directory does not exist; returning empty list")
        return []
    names = sorted([p.name for p in install_dir.iterdir() if p.is_dir()])
    logger.info(f"Found {len(names)} installed addon(s): {names}")
    return names


def mark_installed(addon_id: str) -> None:
    """
    No-op for now. Disk presence is the source of truth.
    Kept for API compatibility.
    """
    logger.debug(f"mark_installed called for {addon_id} (noop)")
    return


def mark_uninstalled(addon_id: str) -> None:
    """
    No-op for now. Disk presence is the source of truth.
    Kept for API compatibility.
    """
    logger.debug(f"mark_uninstalled called for {addon_id} (noop)")
    return
