from .router import router, get_store_service

def startup_store() -> None:
    # Load catalog into memory (non-fatal on error)
    get_store_service().startup_load()

