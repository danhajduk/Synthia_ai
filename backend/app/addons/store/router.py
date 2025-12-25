from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pathlib import Path
from typing import Optional

from ..domain.models import AddonInstallResult
from ..services.loader import load_backend_addon

from .service import StoreService
from .models import StoreEntry, StoreResponse, StoreInstallRequest, CatalogStatus
from .catalog_sources import (
    CatalogSourcesIO,
    CatalogSourcesConfig,
    CatalogSource,
    CreateCatalogSourceRequest,
    UpdateCatalogSourceRequest,
)

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
    return svc.get_store(q=q)


@router.get("/store/{addon_id}", response_model=StoreEntry)
def get_store_addon(addon_id: str, svc: StoreService = Depends(get_store_service)) -> StoreEntry:
    try:
        return svc.get_store_item(addon_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Addon not found in store: {addon_id}")


@router.get("/catalog", response_model=CatalogStatus)
def get_catalog_status(svc: StoreService = Depends(get_store_service)) -> CatalogStatus:
    return svc.get_status()


@router.post("/catalog/reload", response_model=CatalogStatus)
def reload_catalog(svc: StoreService = Depends(get_store_service)) -> CatalogStatus:
    svc.reload()
    return svc.get_status()


@router.post("/store/install", response_model=AddonInstallResult)
def install_from_store(self, addon_id: str, force: bool = False) -> AddonInstallResult:
    core_root = Path(__file__).resolve().parents[4]

    # Install should follow the merged store winner (same view the UI sees)
    try:
        _sources, chosen = self._build_merged_view(core_root)
        if addon_id not in chosen:
            return AddonInstallResult(status="failed", errors=[f"Addon not found in store: {addon_id}"])
        _src, item = chosen[addon_id]
    except Exception as e:
        return AddonInstallResult(status="failed", errors=[f"Failed to resolve addon from merged store: {e}"])

    return install_addon_from_repo(
        addon_id=addon_id,
        repo=str(item.repo),
        ref=item.ref or "main",
        path_in_repo=item.path or ".",
        core_root=core_root,
        force=force,
    )


# ----------------------------
# Catalog Sources (NEW: Phase 1 steps 1/2)
# ----------------------------

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
