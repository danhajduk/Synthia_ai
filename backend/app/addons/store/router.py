from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..domain.models import AddonInstallResult
from ..services.loader import load_backend_addon

from .service import StoreService
from .models import StoreEntry, StoreResponse, StoreInstallRequest, CatalogStatus

router = APIRouter()

# Simple singleton service (local catalog file only for now)
_store_service = StoreService(
    catalog_path=Path(__file__).resolve().parent / "dev_catalog.json"
)

def get_store_service() -> StoreService:
    return _store_service


@router.get("/store", response_model=StoreResponse)
def get_store(
    q: str | None = Query(default=None, description="Search query (id/name/description)"),
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
def get_catalog_status(
    svc: StoreService = Depends(get_store_service),
) -> CatalogStatus:
    return svc.get_status()


@router.post("/catalog/reload", response_model=CatalogStatus)
def reload_catalog(
    svc: StoreService = Depends(get_store_service),
) -> CatalogStatus:
    try:
        svc.reload()
        return svc.get_status()
    except Exception as e:
        # keep the old data; just report failure
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/store/install", response_model=AddonInstallResult)
def install_from_store(
    req: StoreInstallRequest,
    request: Request,
    svc: StoreService = Depends(get_store_service),
) -> AddonInstallResult:
    result = svc.install_from_store(addon_id=req.addon_id, force=req.force)

    # Activate backend immediately (no restart)
    if result.status == "installed" and result.manifest is not None:
        try:
            load_backend_addon(request.app, result.manifest)
            # Replace the old warning since we *did* mount it
            result.warnings = [w for w in result.warnings if "restart Synthia" not in w]
        except Exception as e:
            result.warnings.append(f"Backend hot-load failed: {e}")

    return result
