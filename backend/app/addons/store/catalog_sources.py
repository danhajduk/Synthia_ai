from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


import threading

# Store-wide logger
logger = logging.getLogger("synthia.store")

CATALOG_SOURCES_LOCK = threading.Lock()

CatalogSourceType = Literal["local", "remote"]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _core_root() -> Path:
    # store/catalog_sources.py -> store -> addons -> app -> backend -> <core_root>
    return Path(__file__).resolve().parents[4]


def _safe_id(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "catalog"


def _gen_id(name: str) -> str:
    import secrets
    return f"{_safe_id(name)}-{secrets.token_hex(2)}"


class CatalogSource(BaseModel):
    id: str
    name: str
    type: CatalogSourceType = "remote"

    # remote catalogs
    url: Optional[HttpUrl] = None

    # local catalogs (path may be absolute or relative to core root)
    path: Optional[str] = None

    enabled: bool = True
    trusted: bool = False

    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)

    # runtime-ish but persisted (helps UI and debugging)
    last_loaded_at: Optional[str] = None
    last_error: Optional[str] = None


class CatalogSourcesConfig(BaseModel):
    version: int = 1
    sources: List[CatalogSource] = Field(default_factory=list)


class CreateCatalogSourceRequest(BaseModel):
    name: Optional[str] = None
    type: CatalogSourceType
    url: Optional[HttpUrl] = None
    path: Optional[str] = None
    enabled: bool = True
    trusted: bool = False


class UpdateCatalogSourceRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    trusted: Optional[bool] = None
    url: Optional[HttpUrl] = None
    path: Optional[str] = None


class CatalogSourcesIO:
    """
    Handles reading/writing `<core>/data/addons/catalogs.json` atomically.

    Phase 1 (steps 1/2): we only manage sources; no fetching/merging yet.
    """

    def __init__(self, core_root: Optional[Path] = None):
        self.core_root = core_root or _core_root()
        self.catalogs_path = self.core_root / "data" / "addons" / "catalogs.json"
        self.catalogs_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"CatalogSourcesIO initialized, catalogs_path={self.catalogs_path}")

    def _default_config(self) -> CatalogSourcesConfig:
        # Keep the current dev catalog experience alive as a default local source.
        dev_catalog = self.core_root / "backend" / "app" / "addons" / "store" / "dev_catalog.json"
        if not dev_catalog.exists():
            # Fallback: relative to this module (useful in odd deployment layouts)
            dev_catalog = Path(__file__).resolve().parent / "dev_catalog.json"

        return CatalogSourcesConfig(
            version=1,
            sources=[
                CatalogSource(
                    id="dev",
                    name="Dev Catalog",
                    type="local",
                    path=str(dev_catalog),
                    enabled=True,
                    trusted=True,
                )
            ],
        )

    def load(self) -> CatalogSourcesConfig:
        logger.debug(f"Loading catalogs from {self.catalogs_path}")
        with CATALOG_SOURCES_LOCK:
            if not self.catalogs_path.exists():
                cfg = self._default_config()
                self.save(cfg)
                logger.info(f"Created default catalogs config at {self.catalogs_path}")
                return cfg

            try:
                raw = json.loads(self.catalogs_path.read_text(encoding="utf-8"))
                return CatalogSourcesConfig.parse_obj(raw)
            except Exception as e:
                logger.error(f"Failed to load catalogs config: {e}")
                raise RuntimeError(f"Failed to load catalogs config: {e}")

    def save(self, cfg: CatalogSourcesConfig) -> None:
        with CATALOG_SOURCES_LOCK:
            logger.debug(f"Saving catalogs config to {self.catalogs_path}")
            tmp = self.catalogs_path.with_suffix(".json.tmp")
            tmp.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
            tmp.replace(self.catalogs_path)

    def resolve_local_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p

        # relative paths are interpreted from core root
        resolved = (self.core_root / path_str).resolve()
        logger.debug(f"Resolved local catalog path: {path_str} -> {resolved}")
        # guard: prevent traversal outside core root for relative inputs
        core = self.core_root.resolve()
        if core not in resolved.parents and resolved != core:
            raise ValueError("Local catalog path escapes core root")
        return resolved

    def validate_new_source(self, req: CreateCatalogSourceRequest) -> None:
        if req.type == "remote":
            if req.url is None:
                raise ValueError("url is required for remote catalogs")
        elif req.type == "local":
            if req.path is None:
                raise ValueError("path is required for local catalogs")
            # validate traversal rules for relative, and existence if path points to a file
            p = self.resolve_local_path(req.path)
            # don't hard-fail if it doesn't exist; allow creating source before file appears
            # but if it exists and is not a file, fail
            if p.exists() and not p.is_file():
                raise ValueError("path must point to a file")

    def validate_update_source(self, existing: CatalogSource, req: UpdateCatalogSourceRequest) -> None:
        # disallow changing type (delete+recreate)
        if req.url is not None and existing.type != "remote":
            raise ValueError("Cannot set url on a non-remote catalog source")
        if req.path is not None and existing.type != "local":
            raise ValueError("Cannot set path on a non-local catalog source")

        if req.path is not None:
            p = self.resolve_local_path(req.path)
            if p.exists() and not p.is_file():
                raise ValueError("path must point to a file")

    def add_source(self, req: CreateCatalogSourceRequest) -> CatalogSource:
        cfg = self.load()
        name = req.name or (str(req.url) if req.url is not None else (req.path or "Catalog"))
        source = CatalogSource(
            id=_gen_id(name),
            name=name,
            type=req.type,
            url=req.url,
            path=req.path,
            enabled=req.enabled,
            trusted=req.trusted,
        )
        self.validate_new_source(req)
        logger.info(f"Adding catalog source: id={source.id} name={name} type={req.type}")
        cfg.sources.append(source)
        self.save(cfg)
        return source

    def update_source(self, source_id: str, req: UpdateCatalogSourceRequest) -> CatalogSource:
        cfg = self.load()
        for i, s in enumerate(cfg.sources):
            if s.id == source_id:
                self.validate_update_source(s, req)
                updated = s.copy(deep=True)
                if req.name is not None:
                    updated.name = req.name
                if req.enabled is not None:
                    updated.enabled = req.enabled
                if req.trusted is not None:
                    updated.trusted = req.trusted
                if req.url is not None:
                    updated.url = req.url
                if req.path is not None:
                    updated.path = req.path
                updated.updated_at = _utcnow_iso()
                cfg.sources[i] = updated
                self.save(cfg)
                logger.info(f"Updated catalog source: id={source_id}")
                return updated
        raise KeyError(source_id)

    def set_source_runtime(self, source_id: str, last_loaded_at: Optional[str], last_error: Optional[str]) -> CatalogSource:
        """Update persisted runtime fields for a source (best-effort)."""
        cfg = self.load()
        for i, s in enumerate(cfg.sources):
            if s.id == source_id:
                updated = s.copy(deep=True)
                updated.last_loaded_at = last_loaded_at
                updated.last_error = last_error
                updated.updated_at = _utcnow_iso()
                cfg.sources[i] = updated
                self.save(cfg)
                logger.debug(f"Set runtime for source {source_id}: last_loaded_at={last_loaded_at} last_error={last_error}")
                return updated
        raise KeyError(source_id)

    def delete_source(self, source_id: str) -> None:

        cfg = self.load()
        before = len(cfg.sources)
        cfg.sources = [s for s in cfg.sources if s.id != source_id]
        if len(cfg.sources) == before:
            raise KeyError(source_id)
        self.save(cfg)
        logger.info(f"Deleted catalog source: id={source_id}")
