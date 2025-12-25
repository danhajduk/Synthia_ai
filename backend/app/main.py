from fastapi import FastAPI

app = FastAPI(title="Synthia")

@app.on_event("startup")
async def startup_event():
    # Delayed imports to avoid importing the addons package at module import time.
    from .addons.services.registry import load_addon_registry
    from .addons.services.loader import load_backend_addons
    from .addons.store.router import router as store_router
    from .addons.store.service import startup_store
    from .addons.api.router import router as addons_router

    # Load registry and backends, startup store, and mount routers
    load_addon_registry()
    load_backend_addons(app)
    startup_store()

    # Mount addon store router and existing addon API router
    app.include_router(store_router, prefix="/api/addons", tags=["addons-store"])
    app.include_router(addons_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Synthia"}
