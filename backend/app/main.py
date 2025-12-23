from fastapi import FastAPI

from .addons.registry import load_addon_registry
from .addons.router import router as addons_router
from .addons.loader import load_backend_addons

app = FastAPI(title="Synthia")


@app.on_event("startup")
async def startup_event():
    load_addon_registry()
    load_backend_addons(app)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Synthia"}


app.include_router(addons_router)
