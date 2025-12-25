from fastapi import FastAPI
import logging
from typing import Dict

# Application entry for the Synthia backend.
# Keep startup sequence lazy to avoid import-time side-effects from the addons package.
app: FastAPI = FastAPI(title="Synthia")
logger: logging.Logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event() -> None:
    # Delayed imports to avoid importing the addons package at module import time.
    from .addons.services.registry import load_addon_registry
    from .addons.services.loader import load_backend_addons
    from .addons.store.router import router as store_router
    from .addons.store.service import startup_store
    from .addons.api.router import router as addons_router

    try:
        # Load registry and backends
        load_addon_registry()
        load_backend_addons(app)

        # Mount routers early so endpoints exist even if subsequent startup steps fail
        app.include_router(store_router, prefix="/api/addons", tags=["addons-store"])
        app.include_router(addons_router)

        # Perform store startup (may load catalog, etc.)
        startup_store()

    except Exception:
        logger.exception("Application startup failed")
        raise


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Synthia"}
