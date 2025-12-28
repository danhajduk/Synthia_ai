from __future__ import annotations
import logging

import logging
logger = logging.getLogger("synthia.store.router")

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pathlib import Path
from typing import Optional

from ..domain.models import AddonInstallResult
from ..services.loader import load_backend_addon
from .installer import uninstall_addon

from .service import StoreService
from .models import StoreEntry, StoreResponse, StoreInstallRequest, CatalogStatus
from .catalog_sources import (
    CatalogSourcesIO,
    CatalogSourcesConfig,
    CatalogSource,
    CreateCatalogSourceRequest,
    UpdateCatalogSourceRequest,
)
from .models import StoreEntry, StoreResponse, StoreInstallRequest, StoreUninstallRequest, CatalogStatus

router = APIRouter()

# ----------------------------
# Singletons (simple + safe)
# ----------------------------

def _default_catalog_path() -> Path:
    return Path(__file__).resolve().parent / "dev_catalog.json"


_store_service: StoreService = StoreService(catalog_path=_default_catalog_path())
_catalog_sources_io: CatalogSourcesIO = CatalogSourcesIO()


def get_store_service() -> StoreService:
    return _store_service


def get_catalog_sources_io() -> CatalogSourcesIO:
    return _catalog_sources_io


# ----------------------------
# Store (existing endpoints)
# ----------------------------

@router.get("/store", response_model=StoreResponse)
def get_store(
    q: Optional[str] = Query(default=None, description="Search query (id/name/description)"),
    svc: StoreService = Depends(get_store_service),
) -> StoreResponse:
    logger.info(f"GET /store called with query: {q}")
    return svc.get_store(q=q)


@router.get("/store/{addon_id}", response_model=StoreEntry)
def get_store_addon(addon_id: str, svc: StoreService = Depends(get_store_service)) -> StoreEntry:
    logger.info(f"GET /store/{addon_id} called")
    try:
        return svc.get_store_item(addon_id)
    except KeyError:
        logger.error(f"Addon not found: {addon_id}")
        raise HTTPException(status_code=404, detail=f"Addon not found in store: {addon_id}")


@router.get("/catalog", response_model=CatalogStatus)
def get_catalog_status(svc: StoreService = Depends(get_store_service)) -> CatalogStatus:
    return svc.get_status()


@router.post("/catalog/reload", response_model=CatalogStatus)
def reload_catalog(svc: StoreService = Depends(get_store_service)) -> CatalogStatus:
    logger.info("POST /catalog/reload called")
    svc.reload()
    logger.info("Catalog reloaded successfully")
    return svc.get_status()


@router.post("/store/install", response_model=AddonInstallResult)
def install_from_store(

    req: StoreInstallRequest,
    request: Request,
    svc: StoreService = Depends(get_store_service),
) -> AddonInstallResult:
    logger.info(f"POST /store/install called for addon_id: {req.addon_id}")
    result = svc.install_from_store(addon_id=req.addon_id, force=req.force)

    if getattr(result, "status", None) != "installed":
        logger.warning(f"Installation failed for addon_id: {req.addon_id}")
        return result

    addon_id = req.addon_id
    try:
        manifest = result.manifest
        loaded = getattr(request.app.state, "loaded_addon_backends", None)
        if loaded is None:
            loaded = set()
            request.app.state.loaded_addon_backends = loaded

        if addon_id not in loaded:
            load_backend_addon(request.app, manifest)
            loaded.add(addon_id)

        if getattr(result, "warnings", None):
            result.warnings = [w for w in result.warnings if "restart" not in w.lower()]

        logger.info(f"Addon {addon_id} installed and backend loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load backend for addon {addon_id}: {e}")
        if getattr(result, "warnings", None) is None:
            result.warnings = []
        result.warnings.append(f"Installed, but failed to load backend at runtime: {e}")

    return result

@router.post("/store/uninstall", response_model=AddonInstallResult)
def uninstall_from_store(
    req: StoreUninstallRequest,
    request: Request,
    svc: StoreService = Depends(get_store_service),
) -> AddonInstallResult:
    result = svc.uninstall_from_store(addon_id=req.addon_id, remove_files=req.remove_files)

    from ..services.loader import unload_backend_addon
    unload_backend_addon(req.addon_id)

    # Clear runtime-loaded state so store flips backend_loaded=false immediately
    try:
        loaded = getattr(request.app.state, "loaded_addon_backends", None)
        if isinstance(loaded, set):
            loaded.discard(req.addon_id)
    except Exception:
        pass

    # Clear persisted loaded marker (if used)
    try:
        from ..services.loader import unmark_backend_loaded
        unmark_backend_loaded(req.addon_id)
    except Exception:
        pass

    # Optional warning: routes may still exist until restart (FastAPI limitation)
    if getattr(result, "warnings", None) is None:
        result.warnings = []
    result.warnings.append("Addon disabled immediately; full route unmount may require restart (FastAPI limitation).")

    return result


@router.get("/catalogs", response_model=CatalogSourcesConfig)
def list_catalog_sources(io: CatalogSourcesIO = Depends(get_catalog_sources_io)) -> CatalogSourcesConfig:
    try:
        return io.load()
    except Exception as e:
        # Non-fatal: return empty list but surface error in HTTP detail
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/catalogs", response_model=CatalogSource, status_code=201)
def create_catalog_source(
    req: CreateCatalogSourceRequest,
    io: CatalogSourcesIO = Depends(get_catalog_sources_io),
) -> CatalogSource:
    try:
        return io.add_source(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/catalogs/{catalog_id}", response_model=CatalogSource)
def update_catalog_source(
    catalog_id: str,
    req: UpdateCatalogSourceRequest,
    io: CatalogSourcesIO = Depends(get_catalog_sources_io),
) -> CatalogSource:
    try:
        return io.update_source(catalog_id, req)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Catalog source not found: {catalog_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/catalogs/{catalog_id}")
def delete_catalog_source(
    catalog_id: str,
    io: CatalogSourcesIO = Depends(get_catalog_sources_io),
) -> dict:
    try:
        io.delete_source(catalog_id)
        return {"deleted": True}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Catalog source not found: {catalog_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _safe_unlink(path: Path) -> None:
    """Remove a symlink or file if it exists."""
    if path.is_symlink() or path.is_file():
        path.unlink()

def _safe_rmtree(path: Path) -> None:
    """Remove a directory tree if it exists."""
    if path.exists() and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=False)
