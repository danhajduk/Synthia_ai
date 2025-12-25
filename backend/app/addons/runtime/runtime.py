# backend/app/addons/runtime.py
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from .models import AddonManifest
from .registry import list_addons
from .installed_store import get_installed_addons
from .loader import get_loaded_backends
from .health import check_addon_health, HealthCacheEntry

AddonLifecycleStatus = Literal["available", "installed", "ready", "error"]
HealthStatus = Literal["unknown", "ok", "error"]


class AddonHealthSnapshot(BaseModel):
    status: HealthStatus
    last_checked: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AddonRuntimeState(BaseModel):
    id: str
    manifest: AddonManifest
    lifecycle: AddonLifecycleStatus
    health: AddonHealthSnapshot


def _health_from_cache_entry(entry: HealthCacheEntry) -> AddonHealthSnapshot:
    return AddonHealthSnapshot(
        status=entry.status,
        last_checked=entry.last_checked,
        error_code=entry.error_code,
        error_message=entry.error_message,
    )


def get_addon_runtime_states() -> List[AddonRuntimeState]:
    """
    Combine manifest data, installed state, backend load info, and health checks
    into a runtime view for the UI and APIs.
    """
    manifests = list_addons()
    installed_ids = set(get_installed_addons())
    loaded_backends = get_loaded_backends()  # {addon_id: LoadedBackendAddon}

    states: List[AddonRuntimeState] = []

    for manifest in manifests:
        addon_id = manifest.id

        # Determine lifecycle
        if addon_id in installed_ids:
            if manifest.backend is None:
                lifecycle: AddonLifecycleStatus = "ready"
            elif addon_id in loaded_backends:
                lifecycle = "ready"
            else:
                lifecycle = "installed"
        else:
            lifecycle = "available"

        # Determine health
        if lifecycle in ("ready", "installed") and manifest.backend is not None:
            # only bother checking health for installed/ready backend addons
            cache_entry = check_addon_health(manifest)
            health = _health_from_cache_entry(cache_entry)
            # if health is error, reflect that in lifecycle
            if health.status == "error":
                lifecycle = "error"
        else:
            # No backend or not installed → health is "unknown"
            health = AddonHealthSnapshot(
                status="unknown",
                last_checked=None,
                error_code=None,
                error_message=None,
            )

        states.append(
            AddonRuntimeState(
                id=addon_id,
                manifest=manifest,
                lifecycle=lifecycle,
                health=health,
            )
        )

    return states
