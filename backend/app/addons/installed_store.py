import json
from pathlib import Path

def _core_root() -> Path:
    # loader.py lives at: <core>/backend/app/addons/services/loader.py
    return Path(__file__).resolve().parents[4]

def _loaded_backends_path() -> Path:
    return _core_root() / "data" / "addons" / ".loaded_backends.json"

def _mark_backend_loaded(addon_id: str) -> None:
    p = _loaded_backends_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    loaded = set()
    if p.exists():
        try:
            loaded = set(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            loaded = set()

    loaded.add(addon_id)
    p.write_text(json.dumps(sorted(loaded), indent=2), encoding="utf-8")
