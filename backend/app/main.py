from fastapi import FastAPI

from .addons.registry import load_addon_registry
from .addons.router import router as addons_router
from .addons.loader import load_backend_addons
from .addons.store import router as store_router, startup_store

app = FastAPI(title="Synthia")

# Addon store endpoints: /api/addons/store
app.include_router(store_router, prefix="/api/addons", tags=["addons-store"])

@app.on_event("startup")
async def startup_event():
    load_addon_registry()
    load_backend_addons(app)
    startup_store()

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Synthia"}

# Existing addon endpoints (whatever you already expose)
app.include_router(addons_router)
