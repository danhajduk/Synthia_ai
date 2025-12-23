# backend/app/addons/router.py
from __future__ import annotations

from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from .loader import load_backend_addons

from .models import AddonManifest, AddonInstallResult
from .registry import get_registry, list_addons, get_addon
from .install import install_addon_from_zip
from .installed_store import mark_installed, mark_uninstalled
from .runtime import get_addon_runtime_states, AddonRuntimeState
from .setup_runner import run_addon_setup

from .models import (
    AddonManifest,
    AddonInstallResult,
    FrontendRoutesResponse,
    FrontendMainRoute,
    FrontendHeaderWidget,
    FrontendSidebarItem,
)
from .registry import get_registry, list_addons, get_addon

router = APIRouter(prefix="/api/addons", tags=["addons"])


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
  result = await install_addon_from_zip(file)
  return result


@router.post("/install/{addon_id}", response_model=AddonInstallResult)
def api_mark_installed(addon_id: str) -> AddonInstallResult:
  """
  Mark an addon as installed and run its optional setup script.

  - If the addon does not exist -> 404.
  - If setup script is defined:
      - Run in isolated subprocess.
      - On non-zero exit -> status="failed" with error message.
  - If setup passes or there is no setup script -> status="installed".
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
    # Prefer stderr, then stdout, then a generic message
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

  # If uninstalled, it should still show as 'available' since manifest exists
  raise HTTPException(status_code=500, detail="Failed to resolve runtime state")

@router.get("/status", response_model=list[AddonRuntimeState])
def api_addon_status() -> list[AddonRuntimeState]:
    """
    Return runtime state for all addons:

    - manifest info
    - lifecycle: available / installed / ready / error
    - health snapshot
    """
    return get_addon_runtime_states()
@router.get("/frontend-routes", response_model=FrontendRoutesResponse)
def api_frontend_routes() -> FrontendRoutesResponse:
    """
    Return frontend integration metadata for all addons.

    Surfaces:
    - main: main UI routes
    - header: header badges/widgets (for now derived from summaryComponent)
    - sidebar: sidebar nav items

    This allows the frontend to:
    - auto-register routes
    - build sidebar nav dynamically
    - render header/frontpage widgets from addon metadata
    """
    manifests = list_addons()

    main_routes: list[FrontendMainRoute] = []
    header_widgets: list[FrontendHeaderWidget] = []
    sidebar_items: list[FrontendSidebarItem] = []

    for manifest in manifests:
        f = manifest.frontend
        if f is None:
            continue

        # MAIN UI
        if f.basePath:
            main_routes.append(
                FrontendMainRoute(
                    addon_id=manifest.id,
                    name=manifest.name,
                    base_path=f.basePath,
                    has_settings_page=f.hasSettingsPage,
                )
            )

        # HEADER WIDGETS / HOMEPAGE WIDGETS
        # For now: use showOnFrontpage + summaryComponent as the "widget" registration
        if f.showOnFrontpage and f.summaryComponent:
            header_widgets.append(
                FrontendHeaderWidget(
                    addon_id=manifest.id,
                    component=f.summaryComponent,
                    size=f.summarySize,
                )
            )

        # SIDEBAR NAV ITEMS
        if f.showInSidebar:
            label = f.sidebarLabel or manifest.name
            sidebar_items.append(
                FrontendSidebarItem(
                    addon_id=manifest.id,
                    label=label,
                    path=f.basePath,
                )
            )

    return FrontendRoutesResponse(
        main=main_routes,
        header=header_widgets,
        sidebar=sidebar_items,
    )

from .installed_store import get_installed_addons

@router.get("/debug/installed-addons")
def debug_installed_addons():
    return {"installed": get_installed_addons()}
