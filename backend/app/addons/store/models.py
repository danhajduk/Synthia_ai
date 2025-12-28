from __future__ import annotations

import logging
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field, HttpUrl
from pydantic.config import ConfigDict

logger = logging.getLogger("synthia.store.installed_store")

LifecyclePhase = Literal["available", "installed", "ready", "online", "error", "unknown"]
CATALOG_SCHEMA_V1 = "synthia.addons.catalog.v1"


# ------------------------------------------------------------------------------
# Core models
# ------------------------------------------------------------------------------

class Health(BaseModel):
    """
    Health probe snapshot for an addon backend.
    """
    model_config = ConfigDict(extra="forbid")

    status: Literal["unknown", "ok", "error"] = "unknown"
    last_checked: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AddonFrontend(BaseModel):
    """
    Frontend UI metadata for an addon.

    Supports both:
    - basePath (camelCase) preferred (matches TS)
    - base_path (snake_case) accepted via alias
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    basePath: str = Field(
        validation_alias="base_path",        # accept snake_case input
        serialization_alias="basePath",      # always output camelCase
    )
    hasSettingsPage: Optional[bool] = None
    showInSidebar: Optional[bool] = None
    sidebarLabel: Optional[str] = None
    showOnFrontpage: Optional[bool] = None
    summaryComponent: Optional[str] = None
    summarySize: Optional[Literal["sm", "md", "lg"]] = None


class CatalogAddon(BaseModel):
    """
    A single addon entry in a catalog.
    """
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: Optional[str] = None

    repo: HttpUrl
    ref: Optional[str] = None        # defaulted by normalization
    path: Optional[str] = None       # defaulted by normalization

    types: List[str] = Field(default_factory=list)

    min_core_version: str
    max_core_version: Optional[str] = None

    # ✅ Important: allows /api/addons/store to include frontend basePath for "Open"
    frontend: Optional[AddonFrontend] = None


class CatalogDocument(BaseModel):
    """
    Catalog document (the full file).
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # JSON uses "schema"; python uses schema_
    schema_: str = Field(alias="schema")
    generated_at: Optional[str] = None
    catalog_name: Optional[str] = None
    catalog_id: Optional[str] = None
    signature: Optional[dict] = None

    addons: List[CatalogAddon] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Store API models
# ------------------------------------------------------------------------------

class StoreSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    trusted: bool = True
    enabled: bool = True
    error: Optional[str] = None
    addons_count: int = 0
    generated_at: Optional[str] = None


class StoreInstallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    addon_id: str
    force: bool = False  # if true, overwrite existing install


class StoreUninstallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    addon_id: str
    remove_files: bool = True


class StoreEntry(BaseModel):
    """
    Store view row: a catalog addon enriched with local install/load/runtime info.
    """
    model_config = ConfigDict(extra="forbid")

    catalog_id: str
    trusted: bool
    addon: CatalogAddon

    installed: bool = False
    backend_loaded: bool = False
    setup_success: Optional[bool] = None
    lifecycle: LifecyclePhase = "available"

    install_path: Optional[str] = None
    backend_prefix: Optional[str] = None
    health: Health = Field(default_factory=Health)


class StoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: List[StoreSource] = Field(default_factory=list)
    addons: List[StoreEntry] = Field(default_factory=list)


class StoreItem(BaseModel):
    """
    If you need a single store item lookup by addon_id.
    """
    model_config = ConfigDict(extra="forbid")

    catalog_id: str
    trusted: bool
    addon: CatalogAddon


class StoreItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: StoreSource
    item: StoreItem


class CatalogStatus(BaseModel):
    """
    Status of a catalog source in the local system.
    """
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    trusted: bool = True
    enabled: bool = True
    loaded: bool = False
    addons_count: int = 0
    last_loaded_at: Optional[str] = None
    error: Optional[str] = None
    path: Optional[str] = None
