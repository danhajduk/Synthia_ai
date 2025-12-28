import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
ADDON_LOG_DIR = LOG_DIR / "addons"

LOG_DIR.mkdir(exist_ok=True)
ADDON_LOG_DIR.mkdir(exist_ok=True)

FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(name)s | "
    "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
)
formatter = logging.Formatter(FORMAT)


def _file_handler(path: Path, level=logging.INFO) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def _attach(logger: logging.Logger, handler: logging.Handler) -> None:
    for h in logger.handlers:
        if getattr(h, "baseFilename", None) == getattr(handler, "baseFilename", None):
            return
    logger.addHandler(handler)


_ADDON_FILE_HANDLERS: dict[str, RotatingFileHandler] = {}

def get_addon_handler(addon_id: str) -> RotatingFileHandler:
    h = _ADDON_FILE_HANDLERS.get(addon_id)
    if h:
        return h
    path = ADDON_LOG_DIR / f"{addon_id}.log"
    h = _file_handler(path)
    _ADDON_FILE_HANDLERS[addon_id] = h
    return h


def bind_addon_logger(addon_id: str) -> None:
    addon_parent = logging.getLogger(f"backend.app.addons.{addon_id}")
    handler = get_addon_handler(addon_id)
    _attach(addon_parent, handler)
    addon_parent.propagate = False


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # --- Core ---
    core_handler = _file_handler(LOG_DIR / "core.log")

    core_parent = logging.getLogger("backend.app")
    _attach(core_parent, core_handler)
    core_parent.propagate = False

    synthia_parent = logging.getLogger("synthia")
    _attach(synthia_parent, core_handler)
    synthia_parent.propagate = False

    # --- Store ---
    store_handler = _file_handler(LOG_DIR / "store.log", level=logging.DEBUG)

    store_parent = logging.getLogger("backend.app.addons.store")
    _attach(store_parent, store_handler)
    store_parent.propagate = False

    synthia_store = logging.getLogger("synthia.store")
    _attach(synthia_store, store_handler)
    synthia_store.propagate = False

    # --- Addons (catch-all parent) ---
    addons_handler = _file_handler(ADDON_LOG_DIR / "addons.log")

    addons_parent = logging.getLogger("backend.app.addons")
    _attach(addons_parent, addons_handler)
    addons_parent.propagate = False

    synthia_addons = logging.getLogger("synthia.addons")
    _attach(synthia_addons, addons_handler)
    synthia_addons.propagate = False

    # --- Uvicorn ---
    uvicorn_handler = _file_handler(LOG_DIR / "uvicorn.log")
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        ul = logging.getLogger(name)
        _attach(ul, uvicorn_handler)
        ul.propagate = False
