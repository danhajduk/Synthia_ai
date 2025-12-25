from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from pydantic.config import ConfigDict


CATALOG_SCHEMA_V1 = "synthia.addons.catalog.v1"


class CatalogAddon(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    repo: HttpUrl
    ref: Optional[str] = None        # defaulted by normalization
    path: Optional[str] = None       # defaulted by normalization

    types: List[str] = Field(default_factory=list)

    min_core_version: str
    max_core_version: Optional[str] = None

    class Config:
        extra = "allow"



class CatalogDocument(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    schema_: str = Field(alias="schema")
    generated_at: Optional[str] = None
    catalog_name: Optional[str] = None
    catalog_id: Optional[str] = None
    signature: Optional[dict] = None

    addons: List[CatalogAddon] = Field(default_factory=list)


# --- API response models (read-only store for now) ---

class StoreSource(BaseModel):
    id: str
    name: str
    trusted: bool = True
    enabled: bool = True
    error: Optional[str] = None
    addons_count: int = 0
    generated_at: Optional[str] = None


class StoreItem(BaseModel):
    catalog_id: str
    trusted: bool
    addon: CatalogAddon


class StoreResponse(BaseModel):
    sources: List[StoreSource] = Field(default_factory=list)
    addons: List[StoreEntry] = Field(default_factory=list)

class StoreItemResponse(BaseModel):
    source: StoreSource
    item: StoreItem

class CatalogStatus(BaseModel):
    id: str
    name: str
    trusted: bool = True
    enabled: bool = True
    loaded: bool = False
    addons_count: int = 0
    last_loaded_at: Optional[str] = None
    error: Optional[str] = None
    path: Optional[str] = None


class StoreInstallRequest(BaseModel):
    addon_id: str
    force: bool = False  # if true, overwrite existing install



from typing import Optional, Literal

LifecyclePhase = Literal["available", "installed", "online", "error", "unknown"]

class StoreEntry(BaseModel):
    catalog_id: str
    trusted: bool
    addon: CatalogAddon

    installed: bool = False
    backend_loaded: bool = False
    setup_success: Optional[bool] = None
    lifecycle: LifecyclePhase = "available"

    install_path: Optional[str] = None
    backend_prefix: Optional[str] = None
