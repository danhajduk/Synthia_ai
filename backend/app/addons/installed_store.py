from __future__ import annotations

from pathlib import Path
from typing import List


def _core_root() -> Path:
    return Path(__file__).resolve().parents[3]  # -> /home/dan/Projects/Synthia


def get_installed_addons() -> List[str]:
    """
    Installed addons are those present on disk in: <core>/data/addons/<addon-id>/
    """
    install_dir = _core_root() / "data" / "addons"
    if not install_dir.exists():
        return []
    return sorted([p.name for p in install_dir.iterdir() if p.is_dir()])


def mark_installed(addon_id: str) -> None:
    """
    No-op for now. Disk presence is the source of truth.
    Kept for API compatibility.
    """
    return


def mark_uninstalled(addon_id: str) -> None:
    """
    No-op for now. Disk presence is the source of truth.
    Kept for API compatibility.
    """
    return
