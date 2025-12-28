Fix summary (Dec 25 2025)

Problem:
- Store lifecycle stayed "installed" because StoreService determined "ready" using only a marker file (loaded_backends.json),
  but that file was never written in your runtime.
- Meanwhile /store/install hot-loads the backend via load_backend_addon(), so the real source of truth is the in-process
  loader state (services.loader.get_loaded_backends()).

Changes:
1) addons/store/service.py
   - Prefer get_loaded_backends().keys() to detect loaded backends (supports hot-load).
   - Fall back to _read_loaded_backends_marker() if loader state isn't available.
   - Added a DEBUG log of loaded backend ids to store.log.

2) addons/services/registry.py
   - Made _read_loaded_backends_marker path consistent (loaded_backends.json without leading dot).
