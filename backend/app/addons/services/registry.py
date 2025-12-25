from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import json
import logging

from pydantic import BaseModel, ValidationError  # ✅ this was missing

from ..domain.models import AddonManifest

logger = logging.getLogger(__name__)


class AddonLoadError(BaseModel):
    addon_path: str
    error: str


class AddonRegistry(BaseModel):
    addons: Dict[str, AddonManifest] = {}
    errors: List[AddonLoadError] = []


# You can wire this from settings or env
DEFAULT_ADDONS_DIR = Path(__file__).resolve().parents[4] / "addons"

# Internal mutable registry (hot-reloadable)
_registry: AddonRegistry | None = None


def load_addon_registry(addons_dir: Path | None = None) -> AddonRegistry:
    """
    Scan addons_dir/*/manifest.json and build a registry.

    - Invalid manifests are logged and added to .errors, but do not crash.
    - Duplicate IDs are skipped with an error.
    """

    global _registry

    if addons_dir is None:
        addons_dir = DEFAULT_ADDONS_DIR

    addons: dict[str, AddonManifest] = {}
    errors: list[AddonLoadError] = []

    logger.info("Loading addon manifests from %s", addons_dir)

    if not addons_dir.exists():
        logger.warning("Addons directory does not exist: %s", addons_dir)
        _registry = AddonRegistry(addons={}, errors=[])
        return _registry

    for manifest_path in addons_dir.glob("*/manifest.json"):
        addon_root = manifest_path.parent
        try:
            raw = manifest_path.read_text(encoding="utf-8")
        except Exception as e:
            msg = f"Failed to read {manifest_path}: {e}"
            logger.exception(msg)
            errors.append(AddonLoadError(addon_path=str(addon_root), error=msg))
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in {manifest_path}: {e}"
            logger.exception(msg)
            errors.append(AddonLoadError(addon_path=str(addon_root), error=msg))
            continue

        try:
            manifest = AddonManifest.model_validate(data)
        except ValidationError as e:
            msg = f"Invalid manifest in {manifest_path}: {e}"
            logger.warning(msg)
            errors.append(AddonLoadError(addon_path=str(addon_root), error=str(e)))
            continue

        # Attach root_dir for convenience
        # manifest.root_dir = addon_root

        if manifest.id in addons:
            msg = f"Duplicate addon id '{manifest.id}' in {manifest_path}"
            logger.error(msg)
            errors.append(AddonLoadError(addon_path=str(addon_root), error=msg))
            continue

        addons[manifest.id] = manifest
        logger.info("Loaded addon '%s' from %s", manifest.id, addon_root)

    _registry = AddonRegistry(addons=addons, errors=errors)
    return _registry


def get_registry() -> AddonRegistry:
    """Return the current registry, loading it if needed."""
    global _registry
    if _registry is None:
        return load_addon_registry()
    return _registry


def reload_registry(addons_dir: Path | None = None) -> AddonRegistry:
    """Force reload from disk (useful after install/uninstall)."""
    return load_addon_registry(addons_dir)


def get_addon(addon_id: str) -> AddonManifest | None:
    registry = get_registry()
    return registry.addons.get(addon_id)


def list_addons() -> list[AddonManifest]:
    return list(get_registry().addons.values())

# Global list of load errors (optional; stays empty unless populated)
_LOAD_ERRORS: List[AddonLoadError] = []


def list_errors() -> List[AddonLoadError]:
    """
    Return any manifest load errors collected during registry loading.

    For now, this will just return an empty list unless you start appending
    to _LOAD_ERRORS in `load_addon_registry()`.
    """
    return list(_LOAD_ERRORS)
