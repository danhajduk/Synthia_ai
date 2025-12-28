# Synthia Backend Functions and Methods

Generated from the uploaded backend source tree. Signatures are taken directly from the code (AST), and descriptions come from docstrings when present; otherwise they're inferred from the name.

## app/addons/api/router.py

### `_find_manifest` (function)

```python
def _find_manifestaddon_id: str -> Optional[AddonManifest]:
```

- **Location:** `app/addons/api/router.py:27`
- **What it does:** Helper to resolve a manifest by ID.
- **Docstring:** Helper to resolve a manifest by ID.

### `api_list_addons` (function)

```python
def api_list_addonstype: Optional[str]=Query(default=None, alias='type'):
```

- **Location:** `app/addons/api/router.py:35`
- **What it does:** Return all valid addon manifests.
- **Docstring:** Return all valid addon manifests.
Optional filter: ?type=llm|voice|knowledge|action|ui

### `api_get_addon` (function)

```python
def api_get_addonaddon_id: str:
```

- **Location:** `app/addons/api/router.py:48`
- **What it does:** Return a single addon manifest by ID.
- **Docstring:** Return a single addon manifest by ID.

### `api_get_addon_errors` (function)

```python
def api_get_addon_errors():
```

- **Location:** `app/addons/api/router.py:59`
- **What it does:** Optional helper: expose manifest load errors to the frontend.
- **Docstring:** Optional helper: expose manifest load errors to the frontend.

### `api_install_addon_from_zip` (function)

```python
async def api_install_addon_from_zipfile: UploadFile=File(...):
```

- **Location:** `app/addons/api/router.py:68`
- **What it does:** Install an addon from an uploaded ZIP.
- **Docstring:** Install an addon from an uploaded ZIP.

Example:
  curl -X POST http://localhost:9001/api/addons/install/upload-zip       -F "file=@/path/to/addon.zip"

### `api_mark_installed` (function)

```python
def api_mark_installedaddon_id: str -> AddonInstallResult:
```

- **Location:** `app/addons/api/router.py:81`
- **What it does:** Mark an addon as installed and run its optional setup script.
- **Docstring:** Mark an addon as installed and run its optional setup script.

- If the addon does not exist -> 404.
- If setup script is defined:
    - Run in isolated subprocess.
    - On non-zero exit -> status="failed" with error message.
- If setup passes or there is no setup script -> status="installed".

### `api_mark_uninstalled` (function)

```python
def api_mark_uninstalledaddon_id: str -> AddonRuntimeState:
```

- **Location:** `app/addons/api/router.py:123`
- **What it does:** Mark an addon as uninstalled/disabled in the installed store.
- **Docstring:** Mark an addon as uninstalled/disabled in the installed store.

### `api_addon_status` (function)

```python
def api_addon_status() -> list[AddonRuntimeState]:
```

- **Location:** `app/addons/api/router.py:142`
- **What it does:** Return runtime state for all addons:
- **Docstring:** Return runtime state for all addons:

- manifest info
- lifecycle: available / installed / ready / error
- health snapshot

### `api_frontend_routes` (function)

```python
def api_frontend_routes() -> FrontendRoutesResponse:
```

- **Location:** `app/addons/api/router.py:152`
- **What it does:** Return frontend integration metadata for all addons.
- **Docstring:** Return frontend integration metadata for all addons.

Surfaces:
- main: main UI routes
- header: header badges/widgets (for now derived from summaryComponent)
- sidebar: sidebar nav items

This allows the frontend to:
- auto-register routes
- build sidebar nav dynamically
- render header/frontpage widgets from addon metadata

### `debug_installed_addons` (function)

```python
def debug_installed_addons():
```

- **Location:** `app/addons/api/router.py:220`
- **What it does:** Debug installed addons.


---

## app/addons/installed_store.py

### `_core_root` (function)

```python
def _core_root() -> Path:
```

- **Location:** `app/addons/installed_store.py:4`
- **What it does:** Core root.

### `_loaded_backends_path` (function)

```python
def _loaded_backends_path() -> Path:
```

- **Location:** `app/addons/installed_store.py:8`
- **What it does:** Loaded backends path.

### `_mark_backend_loaded` (function)

```python
def _mark_backend_loadedaddon_id: str -> None:
```

- **Location:** `app/addons/installed_store.py:11`
- **What it does:** Mark backend loaded.


---

## app/addons/runtime/frontend_linker.py

### `sync_frontend_addons` (function)

```python
def sync_frontend_addons*, addons_dir: Path, frontend_addons_dir: Path -> list[str]:
```

- **Location:** `app/addons/runtime/frontend_linker.py:7`
- **What it does:** Ensure: <frontend_addons_dir>/<addonId> -> <addons_dir>/<addonId>/frontend (symlink)
- **Docstring:** Ensure: <frontend_addons_dir>/<addonId> -> <addons_dir>/<addonId>/frontend (symlink)


---

## app/addons/runtime/runtime.py

### `_health_from_cache_entry` (function)

```python
def _health_from_cache_entryentry: HealthCacheEntry -> AddonHealthSnapshot:
```

- **Location:** `app/addons/runtime/runtime.py:33`
- **What it does:** Health from cache entry.

### `get_addon_runtime_states` (function)

```python
def get_addon_runtime_states() -> List[AddonRuntimeState]:
```

- **Location:** `app/addons/runtime/runtime.py:42`
- **What it does:** Combine manifest data, installed state, backend load info, and health checks
- **Docstring:** Combine manifest data, installed state, backend load info, and health checks
into a runtime view for the UI and APIs.


---

## app/addons/services/health.py

### `_is_fresh` (function)

```python
def _is_freshentry: HealthCacheEntry -> bool:
```

- **Location:** `app/addons/services/health.py:37`
- **What it does:** Is fresh.

### `check_addon_health` (function)

```python
def check_addon_healthmanifest: AddonManifest -> HealthCacheEntry:
```

- **Location:** `app/addons/services/health.py:41`
- **What it does:** Check health for a single addon, with caching.
- **Docstring:** Check health for a single addon, with caching.

Rules:
- If addon has no backend: status = ok (nothing to probe).
- If addon backend is not loaded: status = unknown.
- Else: HTTP GET /api/addons/{id}{healthPath} and interpret JSON body.


---

## app/addons/services/install.py

### `_find_manifest` (function)

```python
def _find_manifestroot: Path -> Tuple[Path | None, Path | None]:
```

- **Location:** `app/addons/services/install.py:18`
- **What it does:** Try to find manifest.json in the extracted ZIP.
- **Docstring:** Try to find manifest.json in the extracted ZIP.

Returns (manifest_path, addon_root_dir).
- addon_root_dir is the folder that should become /addons/<id>.

### `install_addon_from_zip` (function)

```python
async def install_addon_from_zipfile: UploadFile, addons_dir: Path | None=None, *, config: Dict[str, Any] | None=None -> AddonInstallResult:
```

- **Location:** `app/addons/services/install.py:40`
- **What it does:** Install an addon from an uploaded ZIP file.
- **Docstring:** Install an addon from an uploaded ZIP file.

- Extracts to temp dir
- Validates manifest.json
- Moves to /addons/<id>
- Runs addon setup (installs deps) if configured
- Reloads registry

Very opinionated v1: no overwrite, no uninstall, no git.


---

## app/addons/services/loader.py

### `_resolve_entry_path` (function)

```python
def _resolve_entry_pathmanifest: AddonManifest -> Path | None:
```

- **Location:** `app/addons/services/loader.py:34`
- **What it does:** Resolve entry path.

### `_load_module_from_path` (function)

```python
def _load_module_from_pathmodule_name: str, path: Path -> types.ModuleType | None:
```

- **Location:** `app/addons/services/loader.py:43`
- **What it does:** Load module from path.

### `load_backend_addon` (function)

```python
def load_backend_addonapp: FastAPI, manifest: AddonManifest -> None:
```

- **Location:** `app/addons/services/loader.py:52`
- **What it does:** Load and mount backend router for ONE addon manifest.
- **Docstring:** Load and mount backend router for ONE addon manifest.

Safe to call at runtime after install.
No-ops if already mounted.

### `load_backend_addons` (function)

```python
def load_backend_addonsapp: FastAPI -> None:
```

- **Location:** `app/addons/services/loader.py:135`
- **What it does:** Discover and mount backend routers for all installed addons.
- **Docstring:** Discover and mount backend routers for all installed addons.

- Uses manifests + installed_store directly.
- If a backend.setup script is configured, runs it first in an
  isolated subprocess (see setup_runner.run_addon_setup).
- Expects each backend entry module to export an `addon` object
  with a `router` attribute (FastAPI APIRouter).
- Mounts each router under /api/addons/{addon_id}.

### `get_loaded_backends` (function)

```python
def get_loaded_backends() -> Dict[str, LoadedBackendAddon]:
```

- **Location:** `app/addons/services/loader.py:256`
- **What it does:** Return a shallow copy of the loaded backend addons map.
- **Docstring:** Return a shallow copy of the loaded backend addons map.

### `get_setup_results` (function)

```python
def get_setup_results() -> Dict[str, AddonSetupResult]:
```

- **Location:** `app/addons/services/loader.py:263`
- **What it does:** Return a shallow copy of setup results per addon.
- **Docstring:** Return a shallow copy of setup results per addon.

This is used by the runtime/lifecycle/status layer to:
- mark lifecycle='error' when setup_result.success is False
- expose setup stdout/stderr/exit_code to the UI


---

## app/addons/services/registry.py

### `load_addon_registry` (function)

```python
def load_addon_registryaddons_dir: Path | None=None -> AddonRegistry:
```

- **Location:** `app/addons/services/registry.py:36`
- **What it does:** Scan addons_dir/*/manifest.json and build a registry.
- **Docstring:** Scan addons_dir/*/manifest.json and build a registry.

- Invalid manifests are logged and added to .errors, but do not crash.
- Duplicate IDs are skipped with an error.

### `get_registry` (function)

```python
def get_registry() -> AddonRegistry:
```

- **Location:** `app/addons/services/registry.py:101`
- **What it does:** Return the current registry, loading it if needed.
- **Docstring:** Return the current registry, loading it if needed.

### `reload_registry` (function)

```python
def reload_registryaddons_dir: Path | None=None -> AddonRegistry:
```

- **Location:** `app/addons/services/registry.py:109`
- **What it does:** Force reload from disk (useful after install/uninstall).
- **Docstring:** Force reload from disk (useful after install/uninstall).

### `get_addon` (function)

```python
def get_addonaddon_id: str -> AddonManifest | None:
```

- **Location:** `app/addons/services/registry.py:114`
- **What it does:** Get addon.

### `list_addons` (function)

```python
def list_addons() -> list[AddonManifest]:
```

- **Location:** `app/addons/services/registry.py:119`
- **What it does:** List addons.

### `list_errors` (function)

```python
def list_errors() -> List[AddonLoadError]:
```

- **Location:** `app/addons/services/registry.py:126`
- **What it does:** Return any manifest load errors collected during registry loading.
- **Docstring:** Return any manifest load errors collected during registry loading.

For now, this will just return an empty list unless you start appending
to _LOAD_ERRORS in `load_addon_registry()`.

### `_read_loaded_backends_marker` (function)

```python
def _read_loaded_backends_markercore_root: Path -> set[str]:
```

- **Location:** `app/addons/services/registry.py:135`
- **What it does:** Read loaded backends marker.

### `write_loaded_backends_marker` (function)

```python
def write_loaded_backends_markercore_root: Path, loaded_ids: set[str] -> None:
```

- **Location:** `app/addons/services/registry.py:144`
- **What it does:** Write loaded backends marker.


---

## app/addons/services/setup_runner.py

### `_get_addon_dir` (function)

```python
def _get_addon_dirmanifest: AddonManifest -> Path:
```

- **Location:** `app/addons/services/setup_runner.py:18`
- **What it does:** Resolve the root directory for this addon on disk.
- **Docstring:** Resolve the root directory for this addon on disk.

For now, we derive it directly from DEFAULT_ADDONS_DIR / manifest.id.

### `_requirements_hash` (function)

```python
def _requirements_hashaddon_dir: Path -> str:
```

- **Location:** `app/addons/services/setup_runner.py:31`
- **What it does:** Hash all requirements/*.txt files so we can detect changes and re-run setup only when needed.
- **Docstring:** Hash all requirements/*.txt files so we can detect changes and re-run setup only when needed.

### `_setup_stamp_path` (function)

```python
def _setup_stamp_pathaddon_dir: Path -> Path:
```

- **Location:** `app/addons/services/setup_runner.py:55`
- **What it does:** Store setup marker inside addon-local runtime.
- **Docstring:** Store setup marker inside addon-local runtime.

### `_read_setup_stamp` (function)

```python
def _read_setup_stampaddon_dir: Path -> Dict[str, Any]:
```

- **Location:** `app/addons/services/setup_runner.py:62`
- **What it does:** Read setup stamp.

### `_write_setup_stamp` (function)

```python
def _write_setup_stampaddon_dir: Path, payload: Dict[str, Any] -> None:
```

- **Location:** `app/addons/services/setup_runner.py:72`
- **What it does:** Write setup stamp.

### `_sync_frontend_links_safe` (function)

```python
def _sync_frontend_links_safe() -> str:
```

- **Location:** `app/addons/services/setup_runner.py:78`
- **What it does:** Try to sync frontend addon symlinks. Never raises.
- **Docstring:** Try to sync frontend addon symlinks. Never raises.
Returns a short message (for stdout).

### `run_addon_setup` (function)

```python
def run_addon_setupmanifest: AddonManifest, *, timeout: int=300, config: Optional[Dict[str, Any]]=None, force: bool=False -> Optional[AddonSetupResult]:
```

- **Location:** `app/addons/services/setup_runner.py:98`
- **What it does:** Run the optional backend setup hook for an addon, if configured.
- **Docstring:** Run the optional backend setup hook for an addon, if configured. Behavior: - If no backend/setup is configured: returns None - Otherwise: - Checks requirements hash + setup stamp and skips if already satisfied (unless force=True) - Dynamically imports the setup module from manifest.backend.setup - Calls run_setup(addon_id: str, addon_dir: Path, config: Dict[str, Any]) in-process - Interprets return value: * If it has attribute `.success` (bool) → use that * If it has attribute `.message` (str) → put into stdout on success, stderr on failure * If it returns None → treat as success - On success (and also on cached skip), sync frontend addon symlinks: frontend/src/addons/<addon_id> -> addons/<addon_id>/frontend Returns: - AddonSetupResult if setup is configured - None if no setup…


---

## app/addons/store/catalog_fetcher.py

### `_utcnow_iso` (function)

```python
def _utcnow_iso() -> str:
```

- **Location:** `app/addons/store/catalog_fetcher.py:18`
- **What it does:** Utcnow iso.

### `CatalogFetcher._cache_json_path` (method)

```python
def _cache_json_pathself, catalog_id: str -> Path:
```

- **Location:** `app/addons/store/catalog_fetcher.py:39`
- **What it does:** Cache json path.

### `CatalogFetcher._cache_headers_path` (method)

```python
def _cache_headers_pathself, catalog_id: str -> Path:
```

- **Location:** `app/addons/store/catalog_fetcher.py:42`
- **What it does:** Cache headers path.

### `CatalogFetcher._load_cached_headers` (method)

```python
def _load_cached_headersself, catalog_id: str -> dict:
```

- **Location:** `app/addons/store/catalog_fetcher.py:45`
- **What it does:** Load cached headers.

### `CatalogFetcher._save_cached_headers` (method)

```python
def _save_cached_headersself, catalog_id: str, headers: dict -> None:
```

- **Location:** `app/addons/store/catalog_fetcher.py:54`
- **What it does:** Save cached headers.

### `CatalogFetcher._save_cached_catalog` (method)

```python
def _save_cached_catalogself, catalog_id: str, body: str -> None:
```

- **Location:** `app/addons/store/catalog_fetcher.py:60`
- **What it does:** Save cached catalog.

### `CatalogFetcher._validate_catalog_body` (method)

```python
def _validate_catalog_bodyself, body: str -> None:
```

- **Location:** `app/addons/store/catalog_fetcher.py:66`
- **What it does:** Validate catalog body.

### `CatalogFetcher.fetch_one` (method)

```python
def fetch_oneself, source: CatalogSource -> FetchResult:
```

- **Location:** `app/addons/store/catalog_fetcher.py:72`
- **What it does:** Fetch one.

### `CatalogFetcher.fetch_enabled` (method)

```python
def fetch_enabledself -> None:
```

- **Location:** `app/addons/store/catalog_fetcher.py:124`
- **What it does:** Fetch all enabled remote sources. Updates last_loaded_at/last_error per source.
- **Docstring:** Fetch all enabled remote sources. Updates last_loaded_at/last_error per source.


---

## app/addons/store/catalog_sources.py

### `_utcnow_iso` (function)

```python
def _utcnow_iso() -> str:
```

- **Location:** `app/addons/store/catalog_sources.py:24`
- **What it does:** Utcnow iso.

### `_core_root` (function)

```python
def _core_root() -> Path:
```

- **Location:** `app/addons/store/catalog_sources.py:28`
- **What it does:** Core root.

### `_safe_id` (function)

```python
def _safe_ids: str -> str:
```

- **Location:** `app/addons/store/catalog_sources.py:33`
- **What it does:** Safe id.

### `_gen_id` (function)

```python
def _gen_idname: str -> str:
```

- **Location:** `app/addons/store/catalog_sources.py:39`
- **What it does:** Gen id.

### `CatalogSourcesIO._default_config` (method)

```python
def _default_configself -> CatalogSourcesConfig:
```

- **Location:** `app/addons/store/catalog_sources.py:101`
- **What it does:** Default config.

### `CatalogSourcesIO.load` (method)

```python
def loadself -> CatalogSourcesConfig:
```

- **Location:** `app/addons/store/catalog_sources.py:122`
- **What it does:** Load.

### `CatalogSourcesIO.save` (method)

```python
def saveself, cfg: CatalogSourcesConfig -> None:
```

- **Location:** `app/addons/store/catalog_sources.py:138`
- **What it does:** Save.

### `CatalogSourcesIO.resolve_local_path` (method)

```python
def resolve_local_pathself, path_str: str -> Path:
```

- **Location:** `app/addons/store/catalog_sources.py:145`
- **What it does:** Resolve local path.

### `CatalogSourcesIO.validate_new_source` (method)

```python
def validate_new_sourceself, req: CreateCatalogSourceRequest -> None:
```

- **Location:** `app/addons/store/catalog_sources.py:159`
- **What it does:** Validate new source.

### `CatalogSourcesIO.validate_update_source` (method)

```python
def validate_update_sourceself, existing: CatalogSource, req: UpdateCatalogSourceRequest -> None:
```

- **Location:** `app/addons/store/catalog_sources.py:173`
- **What it does:** Validate update source.

### `CatalogSourcesIO.add_source` (method)

```python
def add_sourceself, req: CreateCatalogSourceRequest -> CatalogSource:
```

- **Location:** `app/addons/store/catalog_sources.py:185`
- **What it does:** Add source.

### `CatalogSourcesIO.update_source` (method)

```python
def update_sourceself, source_id: str, req: UpdateCatalogSourceRequest -> CatalogSource:
```

- **Location:** `app/addons/store/catalog_sources.py:203`
- **What it does:** Update source.

### `CatalogSourcesIO.set_source_runtime` (method)

```python
def set_source_runtimeself, source_id: str, last_loaded_at: Optional[str], last_error: Optional[str] -> CatalogSource:
```

- **Location:** `app/addons/store/catalog_sources.py:226`
- **What it does:** Update persisted runtime fields for a source (best-effort).
- **Docstring:** Update persisted runtime fields for a source (best-effort).

### `CatalogSourcesIO.delete_source` (method)

```python
def delete_sourceself, source_id: str -> None:
```

- **Location:** `app/addons/store/catalog_sources.py:241`
- **What it does:** Delete source.


---

## app/addons/store/installed_store.py

### `_core_root` (function)

```python
def _core_root() -> Path:
```

- **Location:** `app/addons/store/installed_store.py:10`
- **What it does:** Core root.

### `get_installed_addons` (function)

```python
def get_installed_addons() -> List[str]:
```

- **Location:** `app/addons/store/installed_store.py:14`
- **What it does:** Installed addons are those present on disk in: <core>/data/addons/<addon-id>/
- **Docstring:** Installed addons are those present on disk in: <core>/data/addons/<addon-id>/

### `mark_installed` (function)

```python
def mark_installedaddon_id: str -> None:
```

- **Location:** `app/addons/store/installed_store.py:28`
- **What it does:** No-op for now. Disk presence is the source of truth.
- **Docstring:** No-op for now. Disk presence is the source of truth.
Kept for API compatibility.

### `mark_uninstalled` (function)

```python
def mark_uninstalledaddon_id: str -> None:
```

- **Location:** `app/addons/store/installed_store.py:37`
- **What it does:** No-op for now. Disk presence is the source of truth.
- **Docstring:** No-op for now. Disk presence is the source of truth.
Kept for API compatibility.


---

## app/addons/store/installer.py

### `_run` (function)

```python
def _runcmd: list[str], cwd: Optional[Path]=None -> subprocess.CompletedProcess:
```

- **Location:** `app/addons/store/installer.py:17`
- **What it does:** Run.

### `_looks_like_commit` (function)

```python
def _looks_like_commitref: str -> bool:
```

- **Location:** `app/addons/store/installer.py:27`
- **What it does:** Looks like commit.

### `_git_clone` (function)

```python
def _git_clonerepo: str, ref: str, dest: Path -> Tuple[bool, str]:
```

- **Location:** `app/addons/store/installer.py:32`
- **What it does:** Clone repo into dest. Supports branch/tag OR commit-ish.
- **Docstring:** Clone repo into dest. Supports branch/tag OR commit-ish.
Returns (ok, error_message).

### `_read_manifest` (function)

```python
def _read_manifestaddon_root: Path -> AddonManifest:
```

- **Location:** `app/addons/store/installer.py:68`
- **What it does:** Read manifest.

### `_run_setup` (function)

```python
def _run_setupaddon_root: Path, manifest: AddonManifest -> AddonSetupResult:
```

- **Location:** `app/addons/store/installer.py:77`
- **What it does:** Run setup.

### `install_addon_from_repo` (function)

```python
def install_addon_from_repo*, addon_id: str, repo: str, ref: str, path_in_repo: str, core_root: Path, force: bool=False -> AddonInstallResult:
```

- **Location:** `app/addons/store/installer.py:102`
- **What it does:** Installs addon repo into data/addons/<id> and symlinks into core /addons/<id>.
- **Docstring:** Installs addon repo into data/addons/<id> and symlinks into core /addons/<id>.
Does NOT hot-load backend routes yet; returns warnings for restart/sync.

### `_ensure_symlink` (function)

```python
def _ensure_symlinkdst: Path, src: Path -> None:
```

- **Location:** `app/addons/store/installer.py:206`
- **What it does:** Create/replace a symlink dst -> src.
- **Docstring:** Create/replace a symlink dst -> src.
If dst exists and is a real directory/file (not symlink), raise.

### `uninstall_addon` (function)

```python
def uninstall_addon*, addon_id: str, core_root: Path -> tuple[bool, list[str], list[str]]:
```

- **Location:** `app/addons/store/installer.py:224`
- **What it does:** Remove addon files and symlinks.
- **Docstring:** Remove addon files and symlinks.

Returns: (ok, warnings, errors)
Notes:
  - If backend routes are hot-loaded, they may remain active until restart.


---

## app/addons/store/models.py

### `CatalogAddon.validate` (method)

```python
def validateself -> None:
```

- **Location:** `app/addons/store/models.py:32`
- **What it does:** Validate.

### `CatalogDocument.validate` (method)

```python
def validateself -> None:
```

- **Location:** `app/addons/store/models.py:51`
- **What it does:** Validate.


---

## app/addons/store/normalize.py

### `normalize_catalog_entry` (function)

```python
def normalize_catalog_entryaddon: CatalogAddon -> CatalogAddon:
```

- **Location:** `app/addons/store/normalize.py:8`
- **What it does:** Normalize catalog entry.


---

## app/addons/store/router.py

### `_default_catalog_path` (function)

```python
def _default_catalog_path() -> Path:
```

- **Location:** `app/addons/store/router.py:32`
- **What it does:** Default catalog path.

### `get_store_service` (function)

```python
def get_store_service() -> StoreService:
```

- **Location:** `app/addons/store/router.py:40`
- **What it does:** Get store service.

### `get_catalog_sources_io` (function)

```python
def get_catalog_sources_io() -> CatalogSourcesIO:
```

- **Location:** `app/addons/store/router.py:44`
- **What it does:** Get catalog sources io.

### `get_store` (function)

```python
def get_storeq: Optional[str]=Query(default=None, description='Search query (id/name/description)'), svc: StoreService=Depends(get_store_service) -> StoreResponse:
```

- **Location:** `app/addons/store/router.py:53`
- **What it does:** Get store.

### `get_store_addon` (function)

```python
def get_store_addonaddon_id: str, svc: StoreService=Depends(get_store_service) -> StoreEntry:
```

- **Location:** `app/addons/store/router.py:62`
- **What it does:** Get store addon.

### `get_catalog_status` (function)

```python
def get_catalog_statussvc: StoreService=Depends(get_store_service) -> CatalogStatus:
```

- **Location:** `app/addons/store/router.py:72`
- **What it does:** Get catalog status.

### `reload_catalog` (function)

```python
def reload_catalogsvc: StoreService=Depends(get_store_service) -> CatalogStatus:
```

- **Location:** `app/addons/store/router.py:77`
- **What it does:** Reload catalog.

### `install_from_store` (function)

```python
def install_from_storereq: StoreInstallRequest, request: Request, svc: StoreService=Depends(get_store_service) -> AddonInstallResult:
```

- **Location:** `app/addons/store/router.py:85`
- **What it does:** Install from store.

### `uninstall_from_store` (function)

```python
def uninstall_from_storereq: StoreUninstallRequest, request: Request, svc: StoreService=Depends(get_store_service) -> AddonInstallResult:
```

- **Location:** `app/addons/store/router.py:123`
- **What it does:** Uninstall from store.

### `list_catalog_sources` (function)

```python
def list_catalog_sourcesio: CatalogSourcesIO=Depends(get_catalog_sources_io) -> CatalogSourcesConfig:
```

- **Location:** `app/addons/store/router.py:154`
- **What it does:** List catalog sources.

### `create_catalog_source` (function)

```python
def create_catalog_sourcereq: CreateCatalogSourceRequest, io: CatalogSourcesIO=Depends(get_catalog_sources_io) -> CatalogSource:
```

- **Location:** `app/addons/store/router.py:163`
- **What it does:** Create catalog source.

### `update_catalog_source` (function)

```python
def update_catalog_sourcecatalog_id: str, req: UpdateCatalogSourceRequest, io: CatalogSourcesIO=Depends(get_catalog_sources_io) -> CatalogSource:
```

- **Location:** `app/addons/store/router.py:176`
- **What it does:** Update catalog source.

### `delete_catalog_source` (function)

```python
def delete_catalog_sourcecatalog_id: str, io: CatalogSourcesIO=Depends(get_catalog_sources_io) -> dict:
```

- **Location:** `app/addons/store/router.py:192`
- **What it does:** Delete catalog source.

### `_safe_unlink` (function)

```python
def _safe_unlinkpath: Path -> None:
```

- **Location:** `app/addons/store/router.py:204`
- **What it does:** Remove a symlink or file if it exists.
- **Docstring:** Remove a symlink or file if it exists.

### `_safe_rmtree` (function)

```python
def _safe_rmtreepath: Path -> None:
```

- **Location:** `app/addons/store/router.py:209`
- **What it does:** Remove a directory tree if it exists.
- **Docstring:** Remove a directory tree if it exists.


---

## app/addons/store/service.py

### `StoreService.load_local` (method)

```python
def load_localself -> None:
```

- **Location:** `app/addons/store/service.py:52`
- **What it does:** Load local.

### `StoreService.startup_load` (method)

```python
def startup_loadself -> None:
```

- **Location:** `app/addons/store/service.py:87`
- **What it does:** Startup load.

### `StoreService.reload` (method)

```python
def reloadself -> None:
```

- **Location:** `app/addons/store/service.py:97`
- **What it does:** Reload.

### `StoreService.get_status` (method)

```python
def get_statusself -> CatalogStatus:
```

- **Location:** `app/addons/store/service.py:106`
- **What it does:** Get status.

### `StoreService.get_source` (method)

```python
def get_sourceself -> StoreSource:
```

- **Location:** `app/addons/store/service.py:123`
- **What it does:** Get source.

### `StoreService.get_store` (method)

```python
def get_storeself, q: Optional[str]=None -> StoreResponse:
```

- **Location:** `app/addons/store/service.py:137`
- **What it does:** Get store.

### `StoreService.get_store_item` (method)

```python
def get_store_itemself, addon_id: str -> StoreEntry:
```

- **Location:** `app/addons/store/service.py:190`
- **What it does:** Get store item.

### `StoreService._entry_for_addon` (method)

```python
def _entry_for_addonself, addon_id: str, addon: CatalogAddon, source: StoreSource, installed: set[str], loaded_backends: set[str], core_root: Path -> StoreEntry:
```

- **Location:** `app/addons/store/service.py:213`
- **What it does:** Entry for addon.

### `StoreService.install_from_store` (method)

```python
def install_from_storeself, addon_id: str, force: bool=False -> AddonInstallResult:
```

- **Location:** `app/addons/store/service.py:278`
- **What it does:** Install from store.

### `StoreService.uninstall_from_store` (method)

```python
def uninstall_from_storeself, addon_id: str, remove_files: bool=True -> AddonInstallResult:
```

- **Location:** `app/addons/store/service.py:300`
- **What it does:** Mark addon as uninstalled/disabled, and optionally remove files on disk.
- **Docstring:** Mark addon as uninstalled/disabled, and optionally remove files on disk.

### `StoreService._parse_generated_at` (method)

```python
def _parse_generated_atself, v: Optional[str] -> Optional[datetime]:
```

- **Location:** `app/addons/store/service.py:330`
- **What it does:** Parse generated at.

### `StoreService._load_catalog_doc_from_path` (method)

```python
def _load_catalog_doc_from_pathself, path: Path -> CatalogDocument:
```

- **Location:** `app/addons/store/service.py:340`
- **What it does:** Load catalog doc from path.

### `StoreService._read_cached_remote_catalog` (method)

```python
def _read_cached_remote_catalogself, core_root: Path, catalog_id: str -> Optional[CatalogDocument]:
```

- **Location:** `app/addons/store/service.py:347`
- **What it does:** Read cached remote catalog.

### `StoreService._build_merged_view` (method)

```python
def _build_merged_viewself, core_root: Path -> Tuple[List[StoreSource], Dict[str, Tuple[StoreSource, CatalogAddon]]]:
```

- **Location:** `app/addons/store/service.py:356`
- **What it does:** Returns:
- **Docstring:** Returns:
  sources: list of StoreSource status objects (dev local + enabled remote)
  chosen:  dict addon_id -> (winning_source, winning_addon)
Collision rules:
  1) trusted wins
  2) newest generated_at wins
  3) deterministic tie-breaker: lower catalog_id wins

### `_catalog_refresh_loop` (function)

```python
async def _catalog_refresh_loopinterval_seconds: int -> None:
```

- **Location:** `app/addons/store/service.py:480`
- **What it does:** Catalog refresh loop.

### `start_catalog_refresh_task` (function)

```python
def start_catalog_refresh_taskapp, interval_seconds: int=6 * 60 * 60 -> None:
```

- **Location:** `app/addons/store/service.py:495`
- **What it does:** Start catalog refresh task.

### `stop_catalog_refresh_task` (function)

```python
async def stop_catalog_refresh_taskapp -> None:
```

- **Location:** `app/addons/store/service.py:503`
- **What it does:** Stop catalog refresh task.

### `startup_store` (function)

```python
def startup_store() -> None:
```

- **Location:** `app/addons/store/service.py:517`
- **What it does:** Called from app startup.
- **Docstring:** Called from app startup.

Phase 1:
- Ensure `<core>/data/addons/catalogs.json` exists (bootstraps default 'dev' source).
- Fetch enabled remote catalogs once (best-effort, cached).
- Load the local dev catalog into memory (best-effort).

### `_read_loaded_backends_marker` (function)

```python
def _read_loaded_backends_markercore_root: Path -> set[str]:
```

- **Location:** `app/addons/store/service.py:543`
- **What it does:** Read the list of backend-loaded addons from a marker file written at startup.
- **Docstring:** Read the list of backend-loaded addons from a marker file written at startup.
Returns a set of addon IDs.

### `uninstall_from_store` (function)

```python
def uninstall_from_storeself, *, addon_id: str, remove_files: bool=True -> AddonInstallResult:
```

- **Location:** `app/addons/store/service.py:577`
- **What it does:** Uninstall addon from store.
- **Docstring:** Uninstall addon from store.

remove_files=True:
  - deletes data/addons/<id>
  - removes core/addons/<id> symlink
  - removes frontend/src/addons/<id> symlink

Note: If backend was hot-loaded, FastAPI may keep routes active until restart.


---

## app/logging_config.py

### `_file_handler` (function)

```python
def _file_handlerpath: Path, level=logging.INFO -> RotatingFileHandler:
```

- **Location:** `app/logging_config.py:18`
- **What it does:** File handler.

### `_attach` (function)

```python
def _attachlogger: logging.Logger, handler: logging.Handler -> None:
```

- **Location:** `app/logging_config.py:29`
- **What it does:** Attach.

### `get_addon_handler` (function)

```python
def get_addon_handleraddon_id: str -> RotatingFileHandler:
```

- **Location:** `app/logging_config.py:38`
- **What it does:** Get addon handler.

### `bind_addon_logger` (function)

```python
def bind_addon_loggeraddon_id: str -> None:
```

- **Location:** `app/logging_config.py:48`
- **What it does:** Bind addon logger.

### `setup_logging` (function)

```python
def setup_logging():
```

- **Location:** `app/logging_config.py:55`
- **What it does:** Setup logging.


---

## app/main.py

### `startup_event` (function)

```python
async def startup_event() -> None:
```

- **Location:** `app/main.py:14`
- **What it does:** Startup event.

### `shutdown_event` (function)

```python
async def shutdown_event() -> None:
```

- **Location:** `app/main.py:53`
- **What it does:** Shutdown event.

### `health` (function)

```python
def health() -> dict[str, str]:
```

- **Location:** `app/main.py:63`
- **What it does:** Health.


---

