from __future__ import annotations

import importlib.util
import logging
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, APIRouter

from .models import AddonManifest, AddonSetupResult
from .registry import list_addons, DEFAULT_ADDONS_DIR
from .installed_store import get_installed_addons
from .setup_runner import run_addon_setup

logger = logging.getLogger(__name__)


@dataclass
class LoadedBackendAddon:
    id: str
    manifest: AddonManifest
    router: APIRouter
    module: types.ModuleType


_LOADED_BACKENDS: Dict[str, LoadedBackendAddon] = {}

# Setup results per addon (whether or not backend loaded successfully)
_SETUP_RESULTS: Dict[str, AddonSetupResult] = {}


def _resolve_entry_path(manifest: AddonManifest) -> Path | None:
    backend = manifest.backend
    if backend is None or not backend.entry:
        return None
    addon_dir = DEFAULT_ADDONS_DIR / manifest.id
    entry_path = (addon_dir / backend.entry).resolve()
    return entry_path


def _load_module_from_path(module_name: str, path: Path) -> types.ModuleType | None:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def load_backend_addon(app: FastAPI, manifest: AddonManifest) -> None:
    """
    Load and mount backend router for ONE addon manifest.

    Safe to call at runtime after install.
    No-ops if already mounted.
    """
    addon_id = manifest.id

    # Already loaded? do nothing.
    if addon_id in _LOADED_BACKENDS:
        return

    backend = manifest.backend
    if backend is None:
        return  # UI-only addon

    # ----------------------------
    # 1) Run optional setup script
    # ----------------------------
    try:
        setup_result = run_addon_setup(manifest)
    except Exception:
        logger.exception("Unexpected exception while running setup for addon '%s'", addon_id)
        setup_result = AddonSetupResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr="Unexpected exception while running setup (see server logs).",
        )

    if setup_result is not None:
        _SETUP_RESULTS[addon_id] = setup_result

        if not setup_result.success:
            logger.error(
                "Setup for addon '%s' failed (exit %s). Stderr: %s",
                addon_id,
                setup_result.exit_code,
                (setup_result.stderr or "").strip(),
            )
            # NOTE: still attempt to load backend router (same as bulk loader)

    # ----------------------------
    # 2) Load backend entry module
    # ----------------------------
    entry_path = _resolve_entry_path(manifest)
    if entry_path is None or not entry_path.is_file():
        logger.warning("Addon '%s' backend entry not found at %s", addon_id, entry_path)
        return

    module_name = f"synthia_addons.{addon_id}.backend"
    try:
        module = _load_module_from_path(module_name, entry_path)
        if module is None:
            logger.error("Failed to load backend module for addon '%s' from %s", addon_id, entry_path)
            return

        backend_addon = getattr(module, "addon", None)
        if backend_addon is None:
            logger.error("Backend module for addon '%s' has no 'addon' attribute", addon_id)
            return

        router = getattr(backend_addon, "router", None)
        if router is None or not isinstance(router, APIRouter):
            logger.error("Backend addon '%s' has no valid 'router' on its 'addon' object", addon_id)
            return

        prefix = f"/api/addons/{addon_id}"
        app.include_router(router, prefix=prefix)

        _LOADED_BACKENDS[addon_id] = LoadedBackendAddon(
            id=addon_id,
            manifest=manifest,
            router=router,
            module=module,
        )

        logger.info("Mounted backend router for addon '%s' at prefix %s", addon_id, prefix)

    except Exception:
        logger.exception("Exception while loading backend for addon '%s' from %s", addon_id, entry_path)

def load_backend_addons(app: FastAPI) -> None:
    """
    Discover and mount backend routers for all installed addons.

    - Uses manifests + installed_store directly.
    - If a backend.setup script is configured, runs it first in an
      isolated subprocess (see setup_runner.run_addon_setup).
    - Expects each backend entry module to export an `addon` object
      with a `router` attribute (FastAPI APIRouter).
    - Mounts each router under /api/addons/{addon_id}.
    """
    global _LOADED_BACKENDS, _SETUP_RESULTS
    _LOADED_BACKENDS = {}
    _SETUP_RESULTS = {}

    manifests = list_addons()
    installed_ids = set(get_installed_addons())

    for manifest in manifests:
        # Only load addons that are installed in Synthia
        if manifest.id not in installed_ids:
            continue

        backend = manifest.backend
        if backend is None:
            # UI-only addon, nothing to mount
            continue

        # ----------------------------
        # 1) Run optional setup script
        # ----------------------------
        try:
            setup_result = run_addon_setup(manifest)
        except Exception:
            # Hard guard: setup_runner itself should swallow and wrap, but don’t trust it blindly
            logger.exception("Unexpected exception while running setup for addon '%s'", manifest.id)
            setup_result = AddonSetupResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Unexpected exception while running setup (see server logs).",
            )

        if setup_result is not None:
            _SETUP_RESULTS[manifest.id] = setup_result

            if not setup_result.success:
                logger.error(
                    "Setup for addon '%s' failed (exit %s). Stderr: %s",
                    manifest.id,
                    setup_result.exit_code,
                    (setup_result.stderr or "").strip(),
                )
                # NOTE: We still attempt to load the backend router so the UI
                # can show a proper error state and possibly expose a "retry setup"
                # action later. Lifecycle will be marked as 'error' elsewhere
                # using this setup result.

        # ----------------------------
        # 2) Load backend entry module
        # ----------------------------
        entry_path = _resolve_entry_path(manifest)
        if entry_path is None or not entry_path.is_file():
            logger.warning(
                "Addon '%s' backend entry not found at %s",
                manifest.id,
                entry_path,
            )
            continue

        module_name = f"synthia_addons.{manifest.id}.backend"
        try:
            module = _load_module_from_path(module_name, entry_path)
            if module is None:
                logger.error(
                    "Failed to load backend module for addon '%s' from %s",
                    manifest.id,
                    entry_path,
                )
                continue

            backend_addon = getattr(module, "addon", None)
            if backend_addon is None:
                logger.error(
                    "Backend module for addon '%s' has no 'addon' attribute",
                    manifest.id,
                )
                continue

            router = getattr(backend_addon, "router", None)
            if router is None or not isinstance(router, APIRouter):
                logger.error(
                    "Backend addon '%s' has no valid 'router' on its 'addon' object",
                    manifest.id,
                )
                continue

            prefix = f"/api/addons/{manifest.id}"
            app.include_router(router, prefix=prefix)

            _LOADED_BACKENDS[manifest.id] = LoadedBackendAddon(
                id=manifest.id,
                manifest=manifest,
                router=router,
                module=module,
            )

            logger.info(
                "Mounted backend router for addon '%s' at prefix %s",
                manifest.id,
                prefix,
            )

        except Exception:
            logger.exception(
                "Exception while loading backend for addon '%s' from %s",
                manifest.id,
                entry_path,
            )


def get_loaded_backends() -> Dict[str, LoadedBackendAddon]:
    """
    Return a shallow copy of the loaded backend addons map.
    """
    return dict(_LOADED_BACKENDS)


def get_setup_results() -> Dict[str, AddonSetupResult]:
    """
    Return a shallow copy of setup results per addon.

    This is used by the runtime/lifecycle/status layer to:
    - mark lifecycle='error' when setup_result.success is False
    - expose setup stdout/stderr/exit_code to the UI
    """
    return dict(_SETUP_RESULTS)
