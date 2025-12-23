from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal  # 🔹 added Literal

from pydantic import BaseModel, Field


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

class AddonManifest(BaseModel):
    """
    Top-level manifest for a Synthia addon.

    Mirrors the manifest.json structure found under /addons/<addon-id>/manifest.json.

    Example:

    {
      "id": "hello-llm",
      "name": "Hello LLM Provider",
      "version": "0.1.0",
      "description": "Demo LLM provider that just echoes text back.",
      "types": ["llm"],
      "dependsOn": [],
      "frontend": { ... },
      "backend": { ... }
    }
    """

    id: str
    name: str
    version: str

    description: Optional[str] = None

    # One or more of: "llm", "voice", "knowledge", "action", "ui"
    types: List[AddonType]

    # Other addons this one depends on (by ID)
    dependsOn: List[str] = Field(default_factory=list)

    frontend: Optional[FrontendManifest] = None
    backend: Optional[BackendManifest] = None


# -----------------------------
# Setup / install result models
# -----------------------------

class AddonInstallResult(BaseModel):
    status: Literal["installed", "failed"]
    manifest: Optional[AddonManifest] = None
    errors: List[str] = Field(default_factory=list)
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
