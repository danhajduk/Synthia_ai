from fastapi import FastAPI
import logging

from backend.app.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="Synthia",
    response_model_by_alias=False,
)


logger = logging.getLogger("synthia.core")
logger.info("Synthia backend starting")

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Running application startup tasks") 
    # Delayed imports to avoid importing the addons package at module import time.
    from .addons.services.registry import load_addon_registry
    from .addons.services.loader import load_backend_addons
    from .addons.store.router import router as store_router
    from .addons.store.service import startup_store
    from .addons.api.router import router as addons_router
    logger.info("Imported addon services and routers")  

    try:
        # Load registry and backends
        load_addon_registry()
        load_backend_addons(app)
        logger.info("Loaded addon registry and backend addons")

        # Mount routers early so endpoints exist even if subsequent startup steps fail
        app.include_router(store_router, prefix="/api/addons", tags=["addons-store"])
        app.include_router(addons_router)
        logger.info("Mounted addon routers")

        # Perform store startup (may load catalog, etc.)
        startup_store()
        logger.info("Completed addon store startup tasks")

        # Periodic remote catalog refresh (best-effort)
        try:
            logger.info("Starting catalog refresh task")
            from .addons.store.service import start_catalog_refresh_task
            start_catalog_refresh_task(app, interval_seconds=6 * 60 * 60)
        except Exception:
            pass

    except Exception:
        logger.exception("Application startup failed")
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    try:
        logger.info("Running application shutdown tasks")
        from .addons.store.service import stop_catalog_refresh_task
        await stop_catalog_refresh_task(app)
    except Exception:
        pass


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Synthia"}
