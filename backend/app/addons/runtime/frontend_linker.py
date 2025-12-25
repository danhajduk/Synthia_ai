from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def sync_frontend_addons(*, addons_dir: Path, frontend_addons_dir: Path) -> list[str]:
    """
    Ensure: <frontend_addons_dir>/<addonId> -> <addons_dir>/<addonId>/frontend (symlink)
    """
    logs: list[str] = []
    frontend_addons_dir.mkdir(parents=True, exist_ok=True)

    if not addons_dir.exists():
        msg = f"[frontend-link] addons dir missing: {addons_dir}"
        logger.warning(msg)
        return [msg]

    for addon_path in sorted(addons_dir.iterdir()):
        if not addon_path.is_dir():
            continue

        addon_id = addon_path.name
        src = addon_path / "frontend"
        if not src.is_dir():
            logs.append(f"[frontend-link] {addon_id}: no frontend/ -> skip")
            continue

        dest = frontend_addons_dir / addon_id

        # Replace existing symlink/file; refuse to delete real directories
        if dest.exists() or dest.is_symlink():
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            else:
                logs.append(f"[frontend-link] {addon_id}: dest is a directory, refusing: {dest}")
                continue

        rel_src = Path("../../../addons") / addon_id / "frontend"
        dest.symlink_to(rel_src, target_is_directory=True)
        logs.append(f"[frontend-link] {addon_id}: {dest} -> {rel_src}")

    return logs
