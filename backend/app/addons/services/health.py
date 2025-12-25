# backend/app/addons/health.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Literal

import requests

from .models import AddonManifest
from .loader import get_loaded_backends

logger = logging.getLogger(__name__)

HealthStatus = Literal["unknown", "ok", "error"]


@dataclass
class HealthCacheEntry:
    status: HealthStatus
    last_checked: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# in-memory cache per process
_HEALTH_CACHE: Dict[str, HealthCacheEntry] = {}

# how long a health check stays "fresh"
HEALTH_TTL = timedelta(seconds=10)

# local base URL for talking to our own backend
HEALTH_BASE_URL = "http://127.0.0.1:9001"


def _is_fresh(entry: HealthCacheEntry) -> bool:
    return datetime.utcnow() - entry.last_checked < HEALTH_TTL


def check_addon_health(manifest: AddonManifest) -> HealthCacheEntry:
    """
    Check health for a single addon, with caching.

    Rules:
    - If addon has no backend: status = ok (nothing to probe).
    - If addon backend is not loaded: status = unknown.
    - Else: HTTP GET /api/addons/{id}{healthPath} and interpret JSON body.
    """
    addon_id = manifest.id

    # no backend → treat as ok
    if manifest.backend is None:
        now = datetime.utcnow()
        entry = HealthCacheEntry(status="ok", last_checked=now)
        _HEALTH_CACHE[addon_id] = entry
        return entry

    # if not loaded, don't even try the HTTP call
    loaded = get_loaded_backends()
    if addon_id not in loaded:
        now = datetime.utcnow()
        entry = HealthCacheEntry(
            status="unknown",
            last_checked=now,
            error_code="NOT_LOADED",
            error_message="Backend router not loaded",
        )
        _HEALTH_CACHE[addon_id] = entry
        return entry

    # cached & fresh?
    cached = _HEALTH_CACHE.get(addon_id)
    if cached and _is_fresh(cached):
        return cached

    backend = manifest.backend
    health_path = backend.healthPath or "/health"
    url = f"{HEALTH_BASE_URL}/api/addons/{addon_id}{health_path}"

    now = datetime.utcnow()

    try:
        resp = requests.get(url, timeout=1.0)

        if 200 <= resp.status_code < 300:
            # ✅ Option B: interpret JSON `status` field
            entry_status: HealthStatus = "ok"
            error_code: Optional[str] = None
            error_message: Optional[str] = None

            data = None
            try:
                data = resp.json()
            except Exception:
                data = None

            if isinstance(data, dict):
                body_status_raw = data.get("status")
                body_status = str(body_status_raw).lower() if body_status_raw is not None else ""

                if body_status in ("error", "failed", "unhealthy"):
                    entry_status = "error"
                    error_code = (
                        data.get("error_code")
                        or data.get("code")
                        or "HEALTH_ERROR"
                    )
                    error_message = (
                        data.get("error_message")
                        or data.get("message")
                        or "Addon reported unhealthy status"
                    )
                elif body_status in ("ok", "healthy", ""):
                    entry_status = "ok"
                else:
                    # unknown status string → treat as error but keep info
                    entry_status = "error"
                    error_code = "UNKNOWN_STATUS"
                    error_message = f"Addon returned unexpected status value: {body_status_raw}"

            entry = HealthCacheEntry(
                status=entry_status,
                last_checked=now,
                error_code=error_code,
                error_message=error_message,
            )

        else:
            # non-2xx → error (keep your existing logic)
            msg = f"HTTP {resp.status_code}"
            try:
                data = resp.json()
                if isinstance(data, dict):
                    detail = data.get("detail")
                    if detail:
                        msg = f"{msg}: {detail}"
            except Exception:
                pass

            entry = HealthCacheEntry(
                status="error",
                last_checked=now,
                error_code=str(resp.status_code),
                error_message=msg,
            )

    except Exception as exc:
        logger.warning("Health check failed for addon '%s': %s", addon_id, exc)
        entry = HealthCacheEntry(
            status="error",
            last_checked=now,
            error_code="EXCEPTION",
            error_message=str(exc),
        )

    _HEALTH_CACHE[addon_id] = entry
    return entry
    """
    Check health for a single addon, with caching.

    Rules:
    - If addon has no backend: status = ok (nothing to probe).
    - If addon backend is not loaded: status = unknown.
    - Else: HTTP GET /api/addons/{id}{healthPath}.
    """
    addon_id = manifest.id

    # no backend → treat as ok
    if manifest.backend is None:
        now = datetime.utcnow()
        entry = HealthCacheEntry(status="ok", last_checked=now)
        _HEALTH_CACHE[addon_id] = entry
        return entry

    # if not loaded, don't even try the HTTP call
    loaded = get_loaded_backends()
    if addon_id not in loaded:
        now = datetime.utcnow()
        entry = HealthCacheEntry(
            status="unknown",
            last_checked=now,
            error_code="NOT_LOADED",
            error_message="Backend router not loaded",
        )
        _HEALTH_CACHE[addon_id] = entry
        return entry

    # cached & fresh?
    cached = _HEALTH_CACHE.get(addon_id)
    if cached and _is_fresh(cached):
        return cached

    backend = manifest.backend
    health_path = backend.healthPath or "/health"
    url = f"{HEALTH_BASE_URL}/api/addons/{addon_id}{health_path}"

    now = datetime.utcnow()

    try:
        resp = requests.get(url, timeout=1.0)
        if 200 <= resp.status_code < 300:
            entry = HealthCacheEntry(
                status="ok",
                last_checked=now,
                error_code=None,
                error_message=None,
            )
        else:
            # non-2xx → error
            msg = f"HTTP {resp.status_code}"
            try:
                data = resp.json()
                # try to extract something useful
                if isinstance(data, dict):
                    detail = data.get("detail")
                    if detail:
                        msg = f"{msg}: {detail}"
            except Exception:
                # ignore JSON parse errors
                pass

            entry = HealthCacheEntry(
                status="error",
                last_checked=now,
                error_code=str(resp.status_code),
                error_message=msg,
            )
    except Exception as exc:
        logger.warning("Health check failed for addon '%s': %s", addon_id, exc)
        entry = HealthCacheEntry(
            status="error",
            last_checked=now,
            error_code="EXCEPTION",
            error_message=str(exc),
        )

    _HEALTH_CACHE[addon_id] = entry
    return entry
