from __future__ import annotations
import shutil
import logging
logger = logging.getLogger("synthia.store.service")

import asyncio
import json
import requests

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..domain.models import AddonInstallResult
# Source of truth for backend-loaded addons in this running process
from ..services.loader import get_loaded_backends
from .catalog_sources import CatalogSourcesIO, _utcnow_iso
from .installed_store import get_installed_addons
from .installer import install_addon_from_repo
from .models import (
    AddonFrontend,
    Health,
    CATALOG_SCHEMA_V1,
    CatalogAddon,
    CatalogDocument,
    CatalogStatus,
    StoreEntry,
    StoreResponse,
    StoreSource,
)
from .normalize import normalize_catalog_entry


class CatalogLoadError(RuntimeError):
    pass


class StoreService:
    """
    Store backed by a local catalog file (for now).
    Keeps a normalized, validated copy in memory.
    """

    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self._loaded: bool = False
        self._source_error: Optional[str] = None
        self._addons_by_id: Dict[str, CatalogAddon] = {}
        self._doc_meta: Dict[str, str] = {}
        self._last_loaded_at: Optional[str] = None

    def _probe_addon_health(
        self,
        *,
        addon_id: str,
        addon: CatalogAddon,
        core_root: Path,
        timeout: float = 1.5,
    ) -> Health:
        """
        Probe addon backend health endpoint.

        Returns a Health object.
        Never raises.
        """

        # Default: unknown
        health = Health(
            status="unknown",
            last_checked=_utcnow_iso(),
            error_code=None,
            error_message=None,
        )

        # Extract healthPath from installed manifest (not catalog)
        manifest_path = core_root / "data" / "addons" / addon_id / "manifest.json"
        if not manifest_path.exists():
            health.error_code = "NO_MANIFEST"
            health.error_message = "Installed manifest not found"
            return health

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            backend = manifest.get("backend") or {}
            health_path = backend.get("healthPath")
        except Exception as exc:
            health.error_code = "MANIFEST_PARSE_ERROR"
            health.error_message = str(exc)
            return health

        if not health_path:
            health.error_code = "NO_HEALTH_PATH"
            health.error_message = "No backend.healthPath defined"
            return health

        # Build URL (local backend)
        url = f"http://127.0.0.1:9001/api/addons/{addon_id}{health_path}"

        try:
            resp = requests.get(url, timeout=timeout)

            if resp.status_code != 200:
                health.status = "error"
                health.error_code = f"HTTP_{resp.status_code}"
                health.error_message = resp.text[:200]
                return health

            # Optional: validate response body shape here
            health.status = "ok"
            return health

        except RequestException as exc:
            health.status = "error"
            health.error_code = "CONNECTION_ERROR"
            health.error_message = str(exc)
            return health
    # ----------------------------
    # Catalog loading
    # ----------------------------

    def load_local(self) -> None:
        logger.info("Loading local catalog")
        if not self.catalog_path.exists():
            logger.error(f"Catalog path does not exist: {self.catalog_path}")
            raise FileNotFoundError(f"Catalog path does not exist: {self.catalog_path}")

        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        doc = CatalogDocument.parse_obj(raw)

        # IMPORTANT: schema check must use schema_ (not doc.schema)
        if doc.schema_ != CATALOG_SCHEMA_V1:
            raise CatalogLoadError(f"Unsupported catalog schema: {doc.schema_}")

        seen = set()
        normalized: Dict[str, CatalogAddon] = {}

        for addon in doc.addons:
            # normalize local entries (no core_root needed in current normalizer)
            addon = normalize_catalog_entry(addon)

            if addon.id in seen:
                raise CatalogLoadError(f"Duplicate addon id in catalog: {addon.id}")
            seen.add(addon.id)

            normalized[addon.id] = addon

        self._addons_by_id = normalized
        self._doc_meta = {
            "catalog_id": doc.catalog_id or "dev-local",
            "catalog_name": doc.catalog_name or "Local Catalog",
        }
        self._source_error = None
        self._loaded = True
        self._last_loaded_at = datetime.now(timezone.utc).isoformat()

    def startup_load(self) -> None:
        try:
            self.load_local()
        except Exception as e:
            self._addons_by_id = {}
            self._doc_meta = {"catalog_id": "dev-local", "catalog_name": "Local Catalog"}
            self._source_error = str(e)
            self._loaded = True
            self._last_loaded_at = datetime.now(timezone.utc).isoformat()

    def reload(self) -> None:
        logger.info("Reloading local catalog")
        self.load_local()
        logger.info("Catalog reloaded successfully")

    # ----------------------------
    # Status + store views
    # ----------------------------

    def get_status(self) -> CatalogStatus:
        logger.debug("Fetching catalog status")
        catalog_id = self._doc_meta.get("catalog_id", "dev-local")
        catalog_name = self._doc_meta.get("catalog_name", "Local Catalog")
        logger.info(f"Catalog status: id={catalog_id}, name={catalog_name}")
        return CatalogStatus(
            id=catalog_id,
            name=catalog_name,
            trusted=True,
            enabled=True,
            loaded=self._loaded,
            addons_count=len(self._addons_by_id),
            last_loaded_at=self._last_loaded_at,
            error=self._source_error,
            path=str(self.catalog_path),
        )

    def get_source(self) -> StoreSource:
        catalog_id = self._doc_meta.get("catalog_id", "dev-local")
        catalog_name = self._doc_meta.get("catalog_name", "Local Catalog")

        return StoreSource(
            id=catalog_id,
            name=catalog_name,
            trusted=True,
            enabled=True,
            error=self._source_error,
            addons_count=len(self._addons_by_id),
            generated_at=None,
        )

    def _entry_for_addon(
        self,
        *,
        addon_id: str,
        addon: CatalogAddon,
        source: StoreSource,
        installed,
        loaded_backends: set[str],
        core_root: Path,
    ) -> StoreEntry:
        """
        Build a StoreEntry for one addon.

        - installed: output of get_installed_addons() (currently list[str])
        - loaded_backends: set of addon ids whose backend router is loaded right now
        """
        # installed can be list[str] or dict or list[objects] depending on earlier iterations
        installed_ids: set[str] = set()
        try:
            if isinstance(installed, dict):
                installed_ids = {str(k) for k in installed.keys()}
            else:
                for item in installed:
                    if isinstance(item, str):
                        installed_ids.add(item)
                    elif hasattr(item, "id"):
                        mid = getattr(item, "id", None)
                        if mid:
                            installed_ids.add(str(mid))
                    elif hasattr(item, "addon"):
                        mid = getattr(item.addon, "id", None)
                        if mid:
                            installed_ids.add(str(mid))
        except Exception:
            installed_ids = set()

        installed_ids.discard("catalog_cache")
        installed_ids.discard("__pycache__")

        is_installed = addon_id in installed_ids
        is_loaded = addon_id in loaded_backends

        # lifecycle heuristic (matches what your UI expects today)
        if is_installed and is_loaded:
            lifecycle: LifecyclePhase = "ready"
        elif is_installed:
            lifecycle = "installed"
        else:
            lifecycle = "available"

        install_path = str(core_root / "data" / "addons" / addon_id) if is_installed else None
        backend_prefix = f"/api/addons/{addon_id}" if is_installed else None

        # Health: if backend not loaded, report unknown; if loaded, try probing known endpoint if you have it.
        # Right now your response includes health with ok; you likely fill this somewhere else.
        # We'll keep it safe and consistent:
        # Always produce a Health object
        if not is_installed:
            health = Health(status="unknown")

        elif not is_loaded:
            health = Health(
                status="unknown",
                error_code="NOT_LOADED",
                error_message="Backend router not loaded",
            )

        else:
            # Backend loaded → probe real health
            health = self._probe_addon_health(
                addon_id=addon_id,
                addon=addon,
                core_root=core_root,
            )
        
        return StoreEntry(
            catalog_id=source.id,
            trusted=source.trusted,
            addon=addon,
            installed=is_installed,
            backend_loaded=is_loaded,
            setup_success=None,
            lifecycle=lifecycle,
            install_path=install_path,
            backend_prefix=backend_prefix,
            health=health,
        )


    def get_store(self, q: Optional[str] = None) -> StoreResponse:
        core_root = Path(__file__).resolve().parents[4]
        installed = get_installed_addons()

        logger.debug("Building store view")

        # ------------------------------------------------------------------
        # Normalize installed addons -> installed_ids
        # Your get_installed_addons() returns list[str] (addon ids/dirs).
        # Also support dict/list of objects defensively.
        # ------------------------------------------------------------------
        installed_ids: set[str] = set()

        try:
            items = installed
            if isinstance(installed, dict):
                items = installed.keys()  # likely {id: ...}

            for m in items:
                if isinstance(m, str):
                    installed_ids.add(m)
                    continue

                mid = None
                if hasattr(m, "id"):
                    mid = getattr(m, "id", None)
                elif hasattr(m, "addon"):
                    mid = getattr(m.addon, "id", None)

                if mid:
                    installed_ids.add(str(mid))

        except Exception as exc:
            logger.warning("Failed to normalize installed addons: %s", exc)
            installed_ids = set()

        # ignore non-addon dirs
        installed_ids.discard("catalog_cache")
        installed_ids.discard("__pycache__")

        logger.debug("Installed addon IDs: %s", sorted(installed_ids))

        # ------------------------------------------------------------------
        # Load installed addon frontend blocks from manifest.json
        # Installed manifest = source of truth for runtime UI behavior.
        # ------------------------------------------------------------------
        installed_frontend_raw: dict[str, dict] = {}
        for addon_id in installed_ids:
            manifest_path = core_root / "data" / "addons" / addon_id / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                fe = data.get("frontend")
                if isinstance(fe, dict):
                    installed_frontend_raw[addon_id] = fe
            except Exception as exc:
                logger.debug("Failed reading manifest.json for %s: %s", addon_id, exc)

        logger.debug("Installed frontend loaded for: %s", sorted(installed_frontend_raw.keys()))

        # ------------------------------------------------------------------
        # Determine which addon backends are currently loaded
        # ------------------------------------------------------------------
        loaded_backends: set[str] = set()
        try:
            loaded_backends = set(get_loaded_backends().keys())
        except Exception:
            try:
                loaded_backends = _read_loaded_backends_marker(core_root)
            except Exception:
                loaded_backends = set()

        logger.debug("Loaded backend addons: %s", sorted(loaded_backends))

        # ------------------------------------------------------------------
        # Build merged catalog view
        # ------------------------------------------------------------------
        sources, chosen = self._build_merged_view(core_root)

        entries: List[StoreEntry] = []
        for addon_id, (src, addon) in chosen.items():
            # --------------------------------------------------------------
            # Merge installed manifest frontend -> catalog addon frontend
            # (installed wins)
            # --------------------------------------------------------------
            try:
                fe_installed = installed_frontend_raw.get(addon_id)
                if fe_installed:
                    current = getattr(addon, "frontend", None)

                    if current is None:
                        merged = dict(fe_installed)
                    elif isinstance(current, dict):
                        merged = {**current, **fe_installed}
                    else:
                        # Pydantic model -> dump to dict, then merge
                        merged = {**current.model_dump(exclude_none=True), **fe_installed}

                    # Normalize and validate into AddonFrontend (if available)
                    try:
                        addon.frontend = AddonFrontend.model_validate(merged)
                    except Exception:
                        addon.frontend = merged

            except Exception as exc:
                logger.debug("Failed merging installed frontend for %s: %s", addon_id, exc)

            # --------------------------------------------------------------
            # Ensure we have a usable basePath (fallback if missing)
            # --------------------------------------------------------------
            try:
                frontend = getattr(addon, "frontend", None)

                base_path = None
                if isinstance(frontend, dict):
                    base_path = frontend.get("basePath") or frontend.get("base_path")
                else:
                    base_path = getattr(frontend, "basePath", None) or getattr(frontend, "base_path", None)

                if not base_path and addon_id in installed_ids:
                    # fallback convention
                    try:
                        addon.frontend = AddonFrontend(basePath=f"/addons/{addon_id}")
                    except Exception:
                        addon.frontend = {"basePath": f"/addons/{addon_id}"}

                    logger.debug("Injected frontend fallback: %s -> /addons/%s", addon_id, addon_id)

            except Exception as exc:
                logger.debug("Failed ensuring basePath for %s: %s", addon_id, exc)

            # --------------------------------------------------------------
            # Build store entry
            # --------------------------------------------------------------
            entries.append(
                self._entry_for_addon(
                    addon_id=addon_id,
                    addon=addon,
                    source=src,
                    installed=installed,
                    loaded_backends=loaded_backends,
                    core_root=core_root,
                )
            )

        # ------------------------------------------------------------------
        # Optional search filter
        # ------------------------------------------------------------------
        if q:
            qq = q.lower().strip()
            entries = [
                e
                for e in entries
                if qq in e.addon.id.lower()
                or qq in e.addon.name.lower()
                or qq in (e.addon.description or "").lower()
            ]

        entries.sort(key=lambda e: e.addon.id)

        # ------------------------------------------------------------------
        # Final debug summary (what the UI actually sees)
        # ------------------------------------------------------------------
        logger.debug("Store response summary:")
        for e in entries:
            frontend = getattr(e.addon, "frontend", None)

            base_path = None
            show_in_sidebar = None
            sidebar_label = None

            if isinstance(frontend, dict):
                base_path = frontend.get("basePath") or frontend.get("base_path")
                show_in_sidebar = frontend.get("showInSidebar") or frontend.get("show_in_sidebar")
                sidebar_label = frontend.get("sidebarLabel") or frontend.get("sidebar_label")
            else:
                base_path = getattr(frontend, "basePath", None) or getattr(frontend, "base_path", None)
                show_in_sidebar = getattr(frontend, "showInSidebar", None) or getattr(frontend, "show_in_sidebar", None)
                sidebar_label = getattr(frontend, "sidebarLabel", None) or getattr(frontend, "sidebar_label", None)

            logger.debug(
                "  addon=%s installed=%s loaded=%s lifecycle=%s basePath=%s showInSidebar=%s sidebarLabel=%s",
                e.addon.id,
                e.installed,
                e.backend_loaded,
                e.lifecycle,
                base_path,
                show_in_sidebar,
                sidebar_label,
            )

        return StoreResponse(sources=sources, addons=entries)

    # ----------------------------
    # Install
    # ----------------------------

    def install_from_store(self, addon_id: str, force: bool = False) -> AddonInstallResult:
        logger.info(f"Installing addon from store: id={addon_id}, force={force}")
        item = self._addons_by_id.get(addon_id)
        if not item:
            return AddonInstallResult(status="failed", errors=[f"Addon not found in store: {addon_id}"])

        result = install_addon_from_repo(
            addon_id=addon_id,
            repo=item.repo,
            ref=item.ref or "main",
            path_in_repo=item.path or ".",
            core_root=Path(__file__).resolve().parents[4],
            force=force,
        )

        if result.status != "installed":
            logger.warning(f"Failed to install addon: id={addon_id}, errors={result.errors}")
        else:
            logger.info(f"Addon installed successfully: id={addon_id}")

        return result

    def uninstall_from_store(self, addon_id: str, remove_files: bool = True) -> AddonInstallResult:
        """
        Mark addon as uninstalled/disabled, and optionally remove files on disk.
        """
        # If you have a manifest store / marker system, call it here.
        # This MUST make get_installed_addons() stop returning this addon id.
        try:
            from .installed_store import mark_uninstalled
            mark_uninstalled(addon_id)
        except Exception as e:
            return AddonInstallResult(status="failed", errors=[f"Failed to mark uninstalled: {e}"])

        if remove_files:
            core_root = Path(__file__).resolve().parents[4]
            try:
                from .installer import uninstall_addon

                ok, warnings, errors = uninstall_addon(addon_id=addon_id, core_root=core_root)
                if not ok and errors:
                    return AddonInstallResult(status="failed", errors=errors, warnings=warnings)
                return AddonInstallResult(status="uninstalled", manifest=None, errors=errors, warnings=warnings)
            except Exception as e:
                return AddonInstallResult(status="uninstalled", manifest=None, errors=[], warnings=[f"Failed during uninstall: {e}"])

        return AddonInstallResult(status="uninstalled", manifest=None, errors=[], warnings=[])

    # ----------------------------
    # Merged store view helpers
    # ----------------------------

    def _parse_generated_at(self, v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        try:
            if v.endswith("Z"):
                v = v.replace("Z", "+00:00")
            return datetime.fromisoformat(v)
        except Exception:
            return None

    def _load_catalog_doc_from_path(self, path: Path) -> CatalogDocument:
        raw = json.loads(path.read_text(encoding="utf-8"))
        doc = CatalogDocument.parse_obj(raw)
        if doc.schema_ != CATALOG_SCHEMA_V1:
            raise CatalogLoadError(f"Unsupported catalog schema: {doc.schema_}")
        return doc

    def _read_cached_remote_catalog(self, core_root: Path, catalog_id: str) -> Optional[CatalogDocument]:
        cache_path = core_root / "data" / "addons" / "catalog_cache" / f"{catalog_id}.json"
        if not cache_path.exists():
            return None
        try:
            return self._load_catalog_doc_from_path(cache_path)
        except Exception:
            return None

    def _build_merged_view(self, core_root: Path) -> Tuple[List[StoreSource], Dict[str, Tuple[StoreSource, CatalogAddon]]]:
        """
        Returns:
          sources: list of StoreSource status objects (dev local + enabled remote)
          chosen:  dict addon_id -> (winning_source, winning_addon)
        Collision rules:
          1) trusted wins
          2) newest generated_at wins
          3) deterministic tie-breaker: lower catalog_id wins
        """
        io = CatalogSourcesIO(core_root=core_root)

        sources: List[StoreSource] = []
        candidates: Dict[str, List[Tuple[StoreSource, CatalogAddon]]] = {}

        # ---- DEV LOCAL ----
        try:
            doc = self._load_catalog_doc_from_path(self.catalog_path)
            src = StoreSource(
                id=doc.catalog_id or "dev-local",
                name=doc.catalog_name or "Local Catalog",
                trusted=True,
                enabled=True,
                error=None,
                addons_count=len(doc.addons),
                generated_at=doc.generated_at,
            )
            sources.append(src)

            for a in doc.addons:
                try:
                    norm = normalize_catalog_entry(a)
                except Exception:
                    continue
                candidates.setdefault(a.id, []).append((src, norm))

        except Exception as e:
            sources.append(
                StoreSource(
                    id="dev-local",
                    name="Local Catalog",
                    trusted=True,
                    enabled=True,
                    error=str(e),
                    addons_count=0,
                    generated_at=None,
                )
            )

        # ---- REMOTE CACHED (enabled sources only) ----
        try:
            cfg = io.load()
            for s in cfg.sources:
                if not s.enabled or s.type != "remote":
                    continue

                cached_doc = self._read_cached_remote_catalog(core_root, s.id)
                if cached_doc is None:
                    sources.append(
                        StoreSource(
                            id=s.id,
                            name=s.name,
                            trusted=s.trusted,
                            enabled=s.enabled,
                            error=s.last_error or "No cached catalog yet",
                            addons_count=0,
                            generated_at=None,
                        )
                    )
                    continue

                src = StoreSource(
                    id=s.id,
                    name=s.name,
                    trusted=s.trusted,
                    enabled=s.enabled,
                    error=s.last_error,
                    addons_count=len(cached_doc.addons),
                    generated_at=cached_doc.generated_at,
                )
                sources.append(src)

                for a in cached_doc.addons:
                    try:
                        norm = normalize_catalog_entry(a)
                    except Exception:
                        continue
                    candidates.setdefault(a.id, []).append((src, norm))

        except Exception as e:
            sources.append(
                StoreSource(
                    id="catalogs",
                    name="Catalog Sources",
                    trusted=True,
                    enabled=True,
                    error=str(e),
                    addons_count=0,
                    generated_at=None,
                )
            )

        # ---- COLLISION RESOLUTION ----
        chosen: Dict[str, Tuple[StoreSource, CatalogAddon]] = {}

        for addon_id, opts in candidates.items():
            if not opts:
                continue

            def sort_key(item: Tuple[StoreSource, CatalogAddon]):
                src, _ = item
                gen = self._parse_generated_at(src.generated_at)
                gen_ts = gen.timestamp() if gen else 0
                return (0 if src.trusted else 1, -gen_ts, src.id)

            chosen[addon_id] = sorted(opts, key=sort_key)[0]

        return sources, chosen


# ----------------------------
# Periodic refresh task (remote catalogs)
# ----------------------------

async def _catalog_refresh_loop(interval_seconds: int) -> None:
    from .router import get_catalog_sources_io
    from .catalog_fetcher import CatalogFetcher

    io = get_catalog_sources_io()
    fetcher = CatalogFetcher(io)

    while True:
        try:
            fetcher.fetch_enabled()
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)


def start_catalog_refresh_task(app, interval_seconds: int = 6 * 60 * 60) -> None:
    try:
        task = asyncio.create_task(_catalog_refresh_loop(interval_seconds))
        app.state.catalog_refresh_task = task
    except Exception:
        pass


async def stop_catalog_refresh_task(app) -> None:
    task = getattr(app.state, "catalog_refresh_task", None)
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        # Task was cancelled during shutdown; swallow to avoid bubbling
        return
    except Exception:
        pass


def startup_store() -> None:
    """
    Called from app startup.

    Phase 1:
    - Ensure `<core>/data/addons/catalogs.json` exists (bootstraps default 'dev' source).
    - Fetch enabled remote catalogs once (best-effort, cached).
    - Load the local dev catalog into memory (best-effort).
    """
    from .router import get_store_service, get_catalog_sources_io

    try:
        get_catalog_sources_io().load()
    except Exception:
        pass

    try:
        from .catalog_fetcher import CatalogFetcher

        fetcher = CatalogFetcher(get_catalog_sources_io())
        fetcher.fetch_enabled()
    except Exception:
        pass

    get_store_service().startup_load()

def _read_loaded_backends_marker(core_root: Path) -> set[str]:
    """
    Read the list of backend-loaded addons from a marker file written at startup.
    Returns a set of addon IDs.
    """
    candidates = [
        core_root / "data" / "addons" / "loaded_backends.json",
        core_root / "data" / "addons" / "runtime" / "loaded_backends.json",
        core_root / "data" / "addons" / "loaded_backends.txt",
    ]

    path = next((p for p in candidates if p.exists()), None)
    if not path:
        logger.debug("No loaded_backends marker found (checked: %s)", [str(p) for p in candidates])
        return set()

    try:
        if path.suffix == ".txt":
            return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}

        raw = json.loads(path.read_text(encoding="utf-8"))

        # Accept: ["a","b"] or {"loaded":["a","b"]} or {"a":true,"b":true}
        if isinstance(raw, list):
            return {str(x) for x in raw}
        if isinstance(raw, dict):
            if "loaded" in raw and isinstance(raw["loaded"], list):
                return {str(x) for x in raw["loaded"]}
            return {str(k) for k, v in raw.items() if v}

        return set()
    except Exception:
        logger.exception("Failed reading loaded_backends marker at %s", path)
        return set()
def uninstall_from_store(self, *, addon_id: str, remove_files: bool = True) -> AddonInstallResult:
    """
    Uninstall addon from store.

    remove_files=True:
      - deletes data/addons/<id>
      - removes core/addons/<id> symlink
      - removes frontend/src/addons/<id> symlink

    Note: If backend was hot-loaded, FastAPI may keep routes active until restart.
    """
    warnings: list[str] = []
    errors: list[str] = []

    core_root: Path = self.core_root  # assumes StoreService already has this
    data_dir = core_root / "data" / "addons" / addon_id
    core_link = core_root / "addons" / addon_id
    fe_link = core_root / "frontend" / "src" / "addons" / addon_id

    logger.info("Uninstall requested: addon_id=%s remove_files=%s", addon_id, remove_files)

    if not remove_files:
        # “logical uninstall” only (if you ever support disabling without deleting)
        try:
            from .installed_store import mark_uninstalled
            mark_uninstalled(addon_id)
        except Exception:
            logger.exception("Failed to mark addon uninstalled (logical)")
            errors.append("Failed to mark addon uninstalled")
        status = "installed" if errors else "uninstalled"
        return AddonInstallResult(status=status, errors=errors or None, warnings=warnings or None)

    # 1) Frontend addon link
    try:
        if fe_link.is_symlink():
            _safe_unlink(fe_link)
            logger.info("Removed frontend symlink: %s", fe_link)
        elif fe_link.exists():
            # In case you ever used copy instead of symlink
            _safe_rmtree(fe_link)
            logger.info("Removed frontend directory: %s", fe_link)
    except Exception as e:
        logger.exception("Failed removing frontend link/dir: %s", fe_link)
        warnings.append(f"Failed removing frontend link/dir: {fe_link} ({e})")

    # 2) Core addon symlink
    try:
        if core_link.is_symlink():
            _safe_unlink(core_link)
            logger.info("Removed core symlink: %s", core_link)
        elif core_link.exists():
            # Safety: don’t delete real directories under /addons
            warnings.append(f"Core addon path exists but is not a symlink: {core_link} (not removed)")
            logger.warning("Core addon path exists but is not a symlink (not removed): %s", core_link)
    except Exception as e:
        logger.exception("Failed removing core link: %s", core_link)
        warnings.append(f"Failed removing core link: {core_link} ({e})")

    # 3) Installed payload
    try:
        if data_dir.exists():
            _safe_rmtree(data_dir)
            logger.info("Removed addon data dir: %s", data_dir)
        else:
            warnings.append(f"Addon data dir not found: {data_dir}")
            logger.warning("Addon data dir not found: %s", data_dir)
    except Exception as e:
        logger.exception("Failed removing addon data dir: %s", data_dir)
        errors.append(f"Failed removing addon data dir: {data_dir} ({e})")

    # If we got here, filesystem is removed (or attempted)
    status = "uninstalled" if not errors else "failed"
    if status == "uninstalled":
        warnings.append("Addon removed from disk. If backend was hot-loaded, restart may be required to fully unload routes.")

    return AddonInstallResult(status=status, errors=errors or None, warnings=warnings or None)
