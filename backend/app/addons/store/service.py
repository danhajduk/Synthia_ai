from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..domain.models import AddonInstallResult
from .catalog_sources import CatalogSourcesIO
from .installed_store import get_installed_addons
from .installer import install_addon_from_repo
from .models import (
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

    # ----------------------------
    # Catalog loading
    # ----------------------------

    def load_local(self) -> None:
        if not self.catalog_path.exists():
            raise CatalogLoadError(f"Catalog file not found: {self.catalog_path}")

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
        self.load_local()

    # ----------------------------
    # Status + store views
    # ----------------------------

    def get_status(self) -> CatalogStatus:
        catalog_id = self._doc_meta.get("catalog_id", "dev-local")
        catalog_name = self._doc_meta.get("catalog_name", "Local Catalog")

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

    def get_store(self, q: Optional[str] = None) -> StoreResponse:
        core_root = Path(__file__).resolve().parents[4]
        installed = get_installed_addons()

        try:
            loaded_backends = _read_loaded_backends_marker(core_root)
        except Exception:
            loaded_backends = set()

        sources, chosen = self._build_merged_view(core_root)

        entries: List[StoreEntry] = []
        for addon_id, (src, addon) in chosen.items():
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

        return StoreResponse(sources=sources, addons=entries)

    def get_store_item(self, addon_id: str) -> StoreEntry:
        core_root = Path(__file__).resolve().parents[4]
        installed = get_installed_addons()

        try:
            loaded_backends = _read_loaded_backends_marker(core_root)
        except Exception:
            loaded_backends = set()

        _sources, chosen = self._build_merged_view(core_root)
        if addon_id not in chosen:
            raise KeyError(addon_id)

        src, addon = chosen[addon_id]
        return self._entry_for_addon(
            addon_id=addon_id,
            addon=addon,
            source=src,
            installed=installed,
            loaded_backends=loaded_backends,
            core_root=core_root,
        )

    def _entry_for_addon(
        self,
        addon_id: str,
        addon: CatalogAddon,
        source: StoreSource,
        installed: set[str],
        loaded_backends: set[str],
        core_root: Path,
    ) -> StoreEntry:
        is_installed = addon_id in installed
        is_loaded = addon_id in loaded_backends

        # If you have setup state tracking elsewhere, keep it. Default: None.
        setup_success = None

        lifecycle = "available"
        if is_installed:
            lifecycle = "installed"
        if is_loaded:
            lifecycle = "online"
        if is_installed and setup_success is False:
            lifecycle = "error"

        return StoreEntry(
            catalog_id=source.id,
            trusted=source.trusted,
            addon=addon,
            installed=is_installed,
            backend_loaded=is_loaded,
            setup_success=setup_success,
            lifecycle=lifecycle,
            install_path=str(core_root / "data" / "addons" / addon_id) if is_installed else None,
            backend_prefix=f"/api/addons/{addon_id}" if is_loaded else None,
        )

    # ----------------------------
    # Install
    # ----------------------------

    def install_from_store(self, addon_id: str, force: bool = False) -> AddonInstallResult:
        item = self._addons_by_id.get(addon_id)
        if not item:
            return AddonInstallResult(status="failed", errors=[f"Addon not found in store: {addon_id}"])

        core_root = Path(__file__).resolve().parents[4]

        return install_addon_from_repo(
            addon_id=addon_id,
            repo=str(item.repo),
            ref=item.ref or "main",
            path_in_repo=item.path or ".",
            core_root=core_root,
            force=force,
        )

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
