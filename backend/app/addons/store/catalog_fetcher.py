from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from .catalog_sources import CatalogSource, CatalogSourcesIO
from .models import CatalogDocument, CATALOG_SCHEMA_V1


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class FetchResult:
    ok: bool
    changed: bool = False
    status_code: int = 0
    error: Optional[str] = None


class CatalogFetcher:
    """Fetch remote catalogs, maintain per-catalog cache + HTTP conditional headers."""

    def __init__(self, io: CatalogSourcesIO):
        self.io = io
        self.cache_dir = self.io.core_root / "data" / "addons" / "catalog_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_json_path(self, catalog_id: str) -> Path:
        return self.cache_dir / f"{catalog_id}.json"

    def _cache_headers_path(self, catalog_id: str) -> Path:
        return self.cache_dir / f"{catalog_id}.headers.json"

    def _load_cached_headers(self, catalog_id: str) -> dict:
        p = self._cache_headers_path(catalog_id)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_cached_headers(self, catalog_id: str, headers: dict) -> None:
        p = self._cache_headers_path(catalog_id)
        tmp = p.with_suffix(".headers.json.tmp")
        tmp.write_text(json.dumps(headers, indent=2), encoding="utf-8")
        tmp.replace(p)

    def _save_cached_catalog(self, catalog_id: str, body: str) -> None:
        p = self._cache_json_path(catalog_id)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(p)

    def _validate_catalog_body(self, body: str) -> None:
        raw = json.loads(body)
        doc = CatalogDocument.parse_obj(raw)
        if getattr(doc, "schema_", None) != CATALOG_SCHEMA_V1:
            raise ValueError(f"Unsupported catalog schema: {getattr(doc, 'schema_', None)}")

    def fetch_one(self, source: CatalogSource) -> FetchResult:
        if source.type != "remote" or source.url is None:
            return FetchResult(ok=True, changed=False, status_code=0)

        headers = {}
        cached_headers = self._load_cached_headers(source.id)

        # Conditional requests (optional but cheap)
        etag = cached_headers.get("etag")
        last_modified = cached_headers.get("last_modified")
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        req = urllib.request.Request(str(source.url), headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = getattr(resp, "status", 200)  # py<3.9 compat
                if status == 304:
                    return FetchResult(ok=True, changed=False, status_code=304)

                body = resp.read().decode("utf-8")
                # Validate before we cache (so cache is always last-good)
                self._validate_catalog_body(body)

                # Cache the validated body
                self._save_cached_catalog(source.id, body)

                # Cache conditional headers for next time
                new_headers = dict(cached_headers)
                if resp.headers.get("ETag"):
                    new_headers["etag"] = resp.headers.get("ETag")
                if resp.headers.get("Last-Modified"):
                    new_headers["last_modified"] = resp.headers.get("Last-Modified")
                new_headers["last_fetched_at"] = _utcnow_iso()
                self._save_cached_headers(source.id, new_headers)

                return FetchResult(ok=True, changed=True, status_code=status)
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return FetchResult(ok=True, changed=False, status_code=304)
            return FetchResult(ok=False, status_code=e.code, error=str(e))
        except Exception as e:
            return FetchResult(ok=False, status_code=0, error=str(e))

    def fetch_enabled(self) -> None:
        """Fetch all enabled remote sources. Updates last_loaded_at/last_error per source."""
        cfg = self.io.load()
        for s in cfg.sources:
            if not s.enabled:
                continue
            if s.type != "remote":
                continue

            result = self.fetch_one(s)
            if result.ok:
                self.io.set_source_runtime(s.id, last_loaded_at=_utcnow_iso(), last_error=None)
            else:
                self.io.set_source_runtime(
                    s.id,
                    last_loaded_at=None,
                    last_error=f"Fetch failed ({result.status_code}): {result.error}",
                )
