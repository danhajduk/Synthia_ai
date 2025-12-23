from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..installed_store import get_installed_addons
from ..loader import get_loaded_backends, get_setup_results
from ..models import AddonInstallResult
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

        # NOTE: if you switch CatalogDocument to schema_ (Field(alias="schema")),
        # update this to: if doc.schema_ != CATALOG_SCHEMA_V1:
        if doc.schema != CATALOG_SCHEMA_V1:
            raise CatalogLoadError(f"Unsupported catalog schema: {doc.schema}")

        seen = set()
        normalized: Dict[str, CatalogAddon] = {}

        for addon in doc.addons:
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
        )

    def get_store(self, q: Optional[str] = None) -> StoreResponse:
        addons: List[CatalogAddon] = list(self._addons_by_id.values())

        if q:
            ql = q.lower().strip()
            addons = [
                a
                for a in addons
                if ql in a.id.lower()
                or ql in (a.name or "").lower()
                or ql in (a.description or "").lower()
            ]

        source = self.get_source()

        core_root = Path(__file__).resolve().parents[4]
        installed_ids = set(get_installed_addons())
        loaded = get_loaded_backends()
        setup = get_setup_results()

        entries: List[StoreEntry] = []

        for a in addons:
            addon_id = a.id
            is_installed = addon_id in installed_ids
            is_loaded = addon_id in loaded

            setup_result = setup.get(addon_id)
            setup_success = setup_result.success if setup_result else None

            # lifecycle rules
            lifecycle = "available"
            if is_installed:
                lifecycle = "installed"
            if is_installed and is_loaded:
                lifecycle = "online"
            if is_installed and setup_success is False:
                lifecycle = "error"

            entries.append(
                StoreEntry(
                    catalog_id=source.id,
                    trusted=source.trusted,
                    addon=a,
                    installed=is_installed,
                    backend_loaded=is_loaded,
                    setup_success=setup_success,
                    lifecycle=lifecycle,
                    install_path=str(core_root / "data" / "addons" / addon_id) if is_installed else None,
                    backend_prefix=f"/api/addons/{addon_id}" if is_loaded else None,
                )
            )

        return StoreResponse(sources=[source], addons=entries)

    def get_store_item(self, addon_id: str) -> StoreEntry:
        """
        Return a single lifecycle-aware store entry (not just raw catalog info).
        """
        addon = self._addons_by_id.get(addon_id)
        if not addon:
            raise KeyError(addon_id)

        # Build one entry using the same rules as get_store()
        core_root = Path(__file__).resolve().parents[4]
        installed_ids = set(get_installed_addons())
        loaded = get_loaded_backends()
        setup = get_setup_results()

        is_installed = addon_id in installed_ids
        is_loaded = addon_id in loaded

        setup_result = setup.get(addon_id)
        setup_success = setup_result.success if setup_result else None

        lifecycle = "available"
        if is_installed:
            lifecycle = "installed"
        if is_installed and is_loaded:
            lifecycle = "online"
        if is_installed and setup_success is False:
            lifecycle = "error"

        source = self.get_source()

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
