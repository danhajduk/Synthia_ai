from pathlib import Path

# addons/visuals/backend/paths.py
# Runtime storage kept inside the addon folder: addons/visuals/runtime/...

ADDON_ROOT = Path(__file__).resolve().parents[1]     # .../addons/visuals
RUNTIME_ROOT = ADDON_ROOT / "runtime"

def ensure_dirs() -> dict[str, Path]:
    paths = {
        "root": RUNTIME_ROOT,
        "weather": RUNTIME_ROOT / "weather",
        "avatar": RUNTIME_ROOT / "avatar",
        "gen": RUNTIME_ROOT / "gen",
        "published": RUNTIME_ROOT / "published",
        "meta": RUNTIME_ROOT / "meta",
        "tmp": RUNTIME_ROOT / "tmp",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths
