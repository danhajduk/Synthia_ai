#backend/app/addons/models.py
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal  # 🔹 added Literal

from pydantic import BaseModel, Field, ConfigDict


CATALOG_SCHEMA_V1 = "synthia.addons.catalog.v1"


class CatalogAddon(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    repo: HttpUrl

    # Optional in input, REQUIRED after normalization
    ref: Optional[str] = None
    path: Optional[str] = None

    types: List[str]

    min_core_version: str
    max_core_version: Optional[str] = None

    class Config:
        extra = "allow"


class CatalogDocument(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    schema_: Literal["synthia.addons.catalog.v1"] = Field(
        alias="schema"
    )

    generated_at: Optional[str] = None
    catalog_name: Optional[str] = None
    catalog_id: Optional[str] = None
    signature: Optional[dict] = None

    addons: List[CatalogAddon]

# -----------------------------
# Enums
# -----------------------------

class AddonType(str, Enum):
    LLM = "llm"
    VOICE = "voice"
    KNOWLEDGE = "knowledge"
    ACTION = "action"
    UI = "ui"


class SummarySize(str, Enum):
    SM = "sm"
    MD = "md"
    LG = "lg"


# -----------------------------
# Frontend manifest
# -----------------------------

class FrontendManifest(BaseModel):
    """
    Describes how the addon integrates into the Synthia frontend.

    - basePath: root route for the addon in the frontend router, e.g. "/addons/hello-llm".
    - hasSettingsPage: whether this addon exposes a settings/details page.
    - showInSidebar: if true, the addon should be added to the sidebar nav.
    - sidebarLabel: label for the sidebar item (falls back to addon.name if missing).
    - showOnFrontpage: if true, addon can render a summary widget on the main dashboard.
    - summaryComponent: name of the React component used for the summary widget.
    - summarySize: size hint for the summary widget ("sm" | "md" | "lg").
    """

    basePath: str

    hasSettingsPage: bool = False
    showInSidebar: bool = False
    sidebarLabel: Optional[str] = None

    showOnFrontpage: bool = False
    summaryComponent: Optional[str] = None
    summarySize: Optional[SummarySize] = None


# -----------------------------
# Backend manifest
# -----------------------------

class BackendManifest(BaseModel):
    """
    Declares how the backend side of the addon integrates with Synthia.

    - entry: required. Path to the backend entry module file, relative to the addon dir,
      e.g. "./backend/addon.py". This module must export an `addon` object with a router.

    - setup: optional. Path to a setup script/module file, relative to the addon dir,
      e.g. "./backend/setup.py".

      Minimal contract for the setup script:
      - It must be executable in isolation.
      - It must define a `def main():` function.
      - The core will invoke it in a separate process (e.g. `python setup.py`),
        and treat an exit code of 0 as success. Non-zero exit code = setup failure.

    - healthPath: path within the mounted router for health checks,
      e.g. "/health". The core will hit `/api/addons/{id}{healthPath}`.

    - requiresConfig: list of configuration keys that must be provided before the addon
      can be fully installed / used (e.g. ["apiKey", "tenantId"]).
    """

    entry: str                                   # "./backend/addon.py"
    setup: Optional[str] = None                 # "./backend/setup.py" (optional)
    healthPath: str = "/health"
    requiresConfig: List[str] = Field(default_factory=list)


# -----------------------------
# Root addon manifest
# -----------------------------

class CoreCompatibility(BaseModel):
    min_version: Optional[str] = None
    max_version: Optional[str] = None

class AddonAssets(BaseModel):
    # Repo-relative path, e.g. "frontend/img/icon.svg"
    icon: Optional[str] = None

class AddonManifest(BaseModel):
    """
    Top-level manifest for a Synthia addon.

    Mirrors the manifest.json structure found under /addons/<addon-id>/manifest.json.
    """

    # (Optional but recommended) Manifest schema identifier
    schema_: Optional[str] = None  # e.g. "synthia.addon.manifest.v1"

    id: str
    name: str
    version: str

    description: Optional[str] = None

    # One or more of: "llm", "voice", "knowledge", "action", "ui"
    types: List[AddonType]

    # Other addons this one depends on (by ID)
    dependsOn: List[str] = Field(default_factory=list)

    # --- New repo-owned metadata ---
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    docs: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Core compatibility (repo is source of truth)
    core: Optional[CoreCompatibility] = None

    # Assets (icon path, etc.)
    assets: Optional[AddonAssets] = None

    # Deprecation
    deprecated: bool = False
    replaced_by: Optional[str] = None

    frontend: Optional[FrontendManifest] = None
    backend: Optional[BackendManifest] = None

    class Config:
        # IMPORTANT: allow unknown fields so we don’t break older/newer manifests.
        extra = "allow"


# -----------------------------
# Setup / install result models
# -----------------------------

class AddonInstallResult(BaseModel):
    # Accept 'uninstalled' here because the uninstall flow returns that status.
    status: Literal["installed", "failed", "uninstalled"]
    manifest: Optional[AddonManifest] = None
    warnings: List[str] = Field(default_factory=list)


class AddonSetupResult(BaseModel):
    """
    Result of running an addon's setup script.

    This is what you'll attach to runtime state and/or expose via the API
    so the UI can show badges, details, etc.
    """

    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""

# -----------------------------
# Frontend registration DTOs
# -----------------------------
from typing import List  # already imported at top
from pydantic import BaseModel, Field  # already imported


class FrontendMainRoute(BaseModel):
    """
    Describes a main UI route exposed by an addon.
    """
    addon_id: str
    name: str
    base_path: str
    has_settings_page: bool = False


class FrontendHeaderWidget(BaseModel):
    """
    Describes a header-level widget/badge contributed by an addon.
    For now we piggy-back on summaryComponent; later we can add
    dedicated header-specific fields if needed.
    """
    addon_id: str
    component: str
    size: Optional[SummarySize] = None


class FrontendSidebarItem(BaseModel):
    """
    Describes a sidebar nav item contributed by an addon.
    """
    addon_id: str
    label: str
    path: str


class FrontendRoutesResponse(BaseModel):
    """
    Aggregated frontend registration for all addons.
    The frontend can use this to dynamically build:
      - main route table
      - header widgets
      - sidebar navigation
    """
    main: List[FrontendMainRoute] = Field(default_factory=list)
    header: List[FrontendHeaderWidget] = Field(default_factory=list)
    sidebar: List[FrontendSidebarItem] = Field(default_factory=list)
