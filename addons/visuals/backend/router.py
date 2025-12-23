from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from .paths import ensure_dirs
from .config import DEFAULT_CONFIG
from .publisher import publish_placeholder

router = APIRouter()

@router.get("/status")
def status():
    paths = ensure_dirs()
    cfg = DEFAULT_CONFIG.model_dump()

    # Ensure we have something published
    current_path = paths["published"] / cfg["weather_scene"]["publish_filename"]
    if not current_path.exists():
        publish_placeholder(current_path, subtitle="Step 0: addon online")

    return {
        "status": "ok",
        "enabled_renderers": cfg["enabled_renderers"],
        "paths": {k: str(v) for k, v in paths.items()},
        "published_current": str(current_path),
    }

@router.get("/current.jpg")
def current_image():
    paths = ensure_dirs()
    current_path = paths["published"] / DEFAULT_CONFIG.weather_scene.publish_filename

    if not current_path.exists():
        publish_placeholder(current_path, subtitle="Auto-created placeholder")

    return FileResponse(str(current_path), media_type="image/jpeg")

@router.post("/publish/placeholder")
def force_placeholder():
    paths = ensure_dirs()
    current_path = paths["published"] / DEFAULT_CONFIG.weather_scene.publish_filename
    publish_placeholder(current_path, subtitle="Forced placeholder")
    return JSONResponse({"ok": True, "path": str(current_path)})
