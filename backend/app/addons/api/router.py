# backend/app/addons/api/router.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, UploadFile, File, Query

from ..services.registry import get_registry, list_addons, get_addon
from ..services.install import install_addon_from_zip
from ..store.installed_store import mark_installed, mark_uninstalled, get_installed_addons
from ..runtime.runtime import get_addon_runtime_states, AddonRuntimeState
from ..services.setup_runner import run_addon_setup

from ..domain.models import (
    AddonManifest,
    AddonInstallResult,
    FrontendRoutesResponse,
    FrontendMainRoute,
    FrontendHeaderWidget,
    FrontendSidebarItem,
)

router = APIRouter(prefix="/api/addons", tags=["addons"])
logger = logging.getLogger("synthia.addons.api")


def _find_manifest(addon_id: str) -> Optional[AddonManifest]:
    """
    Helper to resolve a manifest by ID.
    """
    return get_addon(addon_id)


@router.get("/registry", response_model=list[AddonManifest])
def api_list_addons(type: Optional[str] = Query(default=None, alias="type")):
    """
    Return all valid addon manifests.
    Optional filter: ?type=llm|voice|knowledge|action|ui
    """
    addons = list_addons()
    if type is None:
        return addons
    return [a for a in addons if type in a.types]


@router.get("/registry/{addon_id}", response_model=AddonManifest)
def api_get_addon(addon_id: str):
    """
    Return a single addon manifest by ID.
    """
    addon = get_addon(addon_id)
    if addon is None:
        raise HTTPException(status_code=404, detail=f"Addon '{addon_id}' not found")
    return addon


@router.get("/registry/_errors")
def api_get_addon_errors():
    """
    Optional helper: expose manifest load errors to the frontend.
    """
    registry = get_registry()
    return {"errors": registry.errors}


@router.post("/install/upload-zip", response_model=AddonInstallResult)
async def api_install_addon_from_zip(file: UploadFile = File(...)):
    """
    Install an addon from an uploaded ZIP.

    Example:
      curl -X POST http://localhost:9001/api/addons/install/upload-zip \
        -F "file=@/path/to/addon.zip"
    """
    return await install_addon_from_zip(file)


@router.post("/install/{addon_id}", response_model=AddonInstallResult)
def api_mark_installed(addon_id: str) -> AddonInstallResult:
    """
    Mark an addon as installed and run its optional setup script.
    """
    manifest = _find_manifest(addon_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Addon not found")

    # Persist installation state first
    mark_installed(addon_id)

    # Run optional setup (subprocess-based)
    setup_result = run_addon_setup(manifest)

    errors: list[str] = []
    warnings: list[str] = []

    if setup_result is not None and not setup_result.success:
        msg = (setup_result.stderr or setup_result.stdout or "Setup failed").strip()
        errors.append(
            f"Setup failed for addon '{addon_id}' "
            f"(exit {setup_result.exit_code}): {msg}"
        )

    status: Literal["installed", "failed"] = "installed" if not errors else "failed"

    return AddonInstallResult(
        status=status,
        manifest=manifest if status == "installed" else None,
        errors=errors,
        warnings=warnings,
    )


@router.post("/uninstall/{addon_id}", response_model=AddonRuntimeState)
def api_mark_uninstalled(addon_id: str) -> AddonRuntimeState:
    """
    Mark an addon as uninstalled/disabled in the installed store.
    """
    manifest = get_addon(addon_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Addon not found")

    mark_uninstalled(addon_id)

    states = get_addon_runtime_states()
    for s in states:
        if s.id == addon_id:
            return s

    raise HTTPException(status_code=500, detail="Failed to resolve runtime state")


@router.get("/status", response_model=list[AddonRuntimeState])
def api_addon_status() -> list[AddonRuntimeState]:
    """
    Return runtime state for all addons.
    """
    return get_addon_runtime_states()


@router.get("/frontend-routes", response_model=FrontendRoutesResponse)
def api_frontend_routes() -> FrontendRoutesResponse:
    """
    Return frontend integration metadata for INSTALLED addons only.

    Surfaces:
    - main: main UI routes
    - header: header badges/widgets
    - sidebar: sidebar nav items
    """
    core_root = Path(__file__).resolve().parents[4]
    data_addons_dir = core_root / "data" / "addons"

    installed_ids = set(get_installed_addons())
    installed_ids.discard("catalog_cache")
    installed_ids.discard("__pycache__")

    main_routes: list[FrontendMainRoute] = []
    header_widgets: list[FrontendHeaderWidget] = []
    sidebar_items: list[FrontendSidebarItem] = []

    for addon_id in sorted(installed_ids):
        addon_dir = data_addons_dir / addon_id
        manifest_path = addon_dir / "manifest.json"

        if not addon_dir.exists():
            logger.debug("Skipping %s: data dir missing (%s)", addon_id, addon_dir)
            continue
        if not manifest_path.exists():
            logger.debug("Skipping %s: manifest.json missing (%s)", addon_id, manifest_path)
            continue

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = AddonManifest.model_validate(raw)
        except Exception as exc:
            logger.warning("Skipping %s: invalid manifest (%s): %s", addon_id, manifest_path, exc)
            continue

        f = manifest.frontend
        if f is None:
            continue

        base_path = getattr(f, "basePath", None) or getattr(f, "base_path", None)
        if isinstance(base_path, str):
            base_path = base_path.strip()
        if not base_path:
            base_path = None

        if base_path:
            main_routes.append(
                FrontendMainRoute(
                    addon_id=manifest.id,
                    name=manifest.name,
                    base_path=base_path,
                    has_settings_page=getattr(f, "hasSettingsPage", None),
                )
            )

        if getattr(f, "showOnFrontpage", False) and getattr(f, "summaryComponent", None):
            header_widgets.append(
                FrontendHeaderWidget(
                    addon_id=manifest.id,
                    component=f.summaryComponent,
                    size=getattr(f, "summarySize", None),
                )
            )

        if getattr(f, "showInSidebar", False):
            if not base_path:
                logger.debug(
                    "Skipping sidebar entry for %s: showInSidebar=true but basePath missing",
                    manifest.id,
                )
            else:
                label = getattr(f, "sidebarLabel", None) or manifest.name
                sidebar_items.append(
                    FrontendSidebarItem(
                        addon_id=manifest.id,
                        label=label,
                        path=base_path,
                    )
                )

    return FrontendRoutesResponse(
        main=main_routes,
        header=header_widgets,
        sidebar=sidebar_items,
    )


@router.get("/debug/installed-addons")
def debug_installed_addons():
    return {"installed": sorted(get_installed_addons())}
