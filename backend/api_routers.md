# Synthia API Routers (Detailed)

Generated from FastAPI OpenAPI schema (local build) using the same router mounting as `backend.app.main`.

## Groups
- Default
- Addons
- Store


---

# Default


## `GET /api/health` — Health

### Responses

- **200** — Successful Response (`application/json`)
**OperationId:** `health_api_health_get`


---

# Addons


## `GET /api/addons/debug/installed-addons` — Debug Installed Addons

### Responses

- **200** — Successful Response (`application/json`)
**OperationId:** `debug_installed_addons_api_addons_debug_installed_addons_get`


## `GET /api/addons/frontend-routes` — Api Frontend Routes

Return frontend integration metadata for all addons.

Surfaces:
- main: main UI routes
- header: header badges/widgets (for now derived from summaryComponent)
- sidebar: sidebar nav items

This allows the frontend to:
- auto-register routes
- build sidebar nav dynamically
- render header/frontpage widgets from addon metadata

### Responses

- **200** — Successful Response (`application/json`)
```
FrontendRoutesResponse {
  main?: [...]
  header?: [...]
  sidebar?: [...]
}
```
**OperationId:** `api_frontend_routes_api_addons_frontend_routes_get`


## `POST /api/addons/install/upload-zip` — Api Install Addon From Zip

Install an addon from an uploaded ZIP.

Example:
  curl -X POST http://localhost:9001/api/addons/install/upload-zip       -F "file=@/path/to/addon.zip"

### Request body

- Content-Type: `multipart/form-data` (required)

**Structure**
```
Body_api_install_addon_from_zip_api_addons_install_upload_zip_post {
  file: string
}
```
### Responses

- **200** — Successful Response (`application/json`)
```
AddonInstallResult {
  status: string
  manifest?: ... | ...
  warnings?: [...]
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `api_install_addon_from_zip_api_addons_install_upload_zip_post`


## `POST /api/addons/install/{addon_id}` — Api Mark Installed

Mark an addon as installed and run its optional setup script.

- If the addon does not exist -> 404.
- If setup script is defined:
    - Run in isolated subprocess.
    - On non-zero exit -> status="failed" with error message.
- If setup passes or there is no setup script -> status="installed".

### Parameters

- **addon_id** (path, required) — `string`

### Responses

- **200** — Successful Response (`application/json`)
```
AddonInstallResult {
  status: string
  manifest?: ... | ...
  warnings?: [...]
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `api_mark_installed_api_addons_install__addon_id__post`


## `GET /api/addons/registry` — Api List Addons

Return all valid addon manifests.
Optional filter: ?type=llm|voice|knowledge|action|ui

### Parameters

- **type** (query, optional) — `any`

### Responses

- **200** — Successful Response (`application/json`)
```
[AddonManifest {
  schema_?: ...
  id: ...
  name: ...
  version: ...
  description?: ...
  types: ...
  dependsOn?: ...
  author?: ...
  license?: ...
  homepage?: ...
  docs?: ...
  tags?: ...
  core?: ...
  assets?: ...
  deprecated?: ...
  replaced_by?: ...
  frontend?: ...
  backend?: ...
}]
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `api_list_addons_api_addons_registry_get`


## `GET /api/addons/registry/_errors` — Api Get Addon Errors

Optional helper: expose manifest load errors to the frontend.

### Responses

- **200** — Successful Response (`application/json`)
**OperationId:** `api_get_addon_errors_api_addons_registry__errors_get`


## `GET /api/addons/registry/{addon_id}` — Api Get Addon

Return a single addon manifest by ID.

### Parameters

- **addon_id** (path, required) — `string`

### Responses

- **200** — Successful Response (`application/json`)
```
AddonManifest {
  schema_?: ... | ...
  id: string
  name: string
  version: string
  description?: ... | ...
  types: [...]
  dependsOn?: [...]
  author?: ... | ...
  license?: ... | ...
  homepage?: ... | ...
  docs?: ... | ...
  tags?: [...]
  core?: ... | ...
  assets?: ... | ...
  deprecated?: boolean
  replaced_by?: ... | ...
  frontend?: ... | ...
  backend?: ... | ...
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `api_get_addon_api_addons_registry__addon_id__get`


## `GET /api/addons/status` — Api Addon Status

Return runtime state for all addons:

- manifest info
- lifecycle: available / installed / ready / error
- health snapshot

### Responses

- **200** — Successful Response (`application/json`)
```
[AddonRuntimeState {
  id: ...
  manifest: ...
  lifecycle: ...
  health: ...
}]
```
**OperationId:** `api_addon_status_api_addons_status_get`


## `POST /api/addons/uninstall/{addon_id}` — Api Mark Uninstalled

Mark an addon as uninstalled/disabled in the installed store.

### Parameters

- **addon_id** (path, required) — `string`

### Responses

- **200** — Successful Response (`application/json`)
```
AddonRuntimeState {
  id: string
  manifest: AddonManifest ...
  lifecycle: string
  health: AddonHealthSnapshot ...
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `api_mark_uninstalled_api_addons_uninstall__addon_id__post`


---

# Store


## `GET /api/addons/catalog` — Get Catalog Status

### Responses

- **200** — Successful Response (`application/json`)
```
CatalogStatus {
  id: string
  name: string
  trusted?: boolean
  enabled?: boolean
  loaded?: boolean
  addons_count?: integer
  last_loaded_at?: ... | ...
  error?: ... | ...
  path?: ... | ...
}
```
**OperationId:** `get_catalog_status_api_addons_catalog_get`


## `POST /api/addons/catalog/reload` — Reload Catalog

### Responses

- **200** — Successful Response (`application/json`)
```
CatalogStatus {
  id: string
  name: string
  trusted?: boolean
  enabled?: boolean
  loaded?: boolean
  addons_count?: integer
  last_loaded_at?: ... | ...
  error?: ... | ...
  path?: ... | ...
}
```
**OperationId:** `reload_catalog_api_addons_catalog_reload_post`


## `GET /api/addons/catalogs` — List Catalog Sources

### Responses

- **200** — Successful Response (`application/json`)
```
CatalogSourcesConfig {
  version?: integer
  sources?: [...]
}
```
**OperationId:** `list_catalog_sources_api_addons_catalogs_get`


## `POST /api/addons/catalogs` — Create Catalog Source

### Request body

- Content-Type: `application/json` (required)

**Structure**
```
CreateCatalogSourceRequest {
  name?: ... | ...
  type: string
  url?: ... | ...
  path?: ... | ...
  enabled?: boolean
  trusted?: boolean
}
```
### Responses

- **201** — Successful Response (`application/json`)
```
CatalogSource {
  id: string
  name: string
  type?: string
  url?: ... | ...
  path?: ... | ...
  enabled?: boolean
  trusted?: boolean
  created_at?: string
  updated_at?: string
  last_loaded_at?: ... | ...
  last_error?: ... | ...
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `create_catalog_source_api_addons_catalogs_post`


## `DELETE /api/addons/catalogs/{catalog_id}` — Delete Catalog Source

### Parameters

- **catalog_id** (path, required) — `string`

### Responses

- **200** — Successful Response (`application/json`)
```
{...}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `delete_catalog_source_api_addons_catalogs__catalog_id__delete`


## `PATCH /api/addons/catalogs/{catalog_id}` — Update Catalog Source

### Parameters

- **catalog_id** (path, required) — `string`

### Request body

- Content-Type: `application/json` (required)

**Structure**
```
UpdateCatalogSourceRequest {
  name?: ... | ...
  enabled?: ... | ...
  trusted?: ... | ...
  url?: ... | ...
  path?: ... | ...
}
```
### Responses

- **200** — Successful Response (`application/json`)
```
CatalogSource {
  id: string
  name: string
  type?: string
  url?: ... | ...
  path?: ... | ...
  enabled?: boolean
  trusted?: boolean
  created_at?: string
  updated_at?: string
  last_loaded_at?: ... | ...
  last_error?: ... | ...
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `update_catalog_source_api_addons_catalogs__catalog_id__patch`


## `GET /api/addons/store` — Get Store

### Parameters

- **q** (query, optional) — `any`: Search query (id/name/description)

### Responses

- **200** — Successful Response (`application/json`)
```
StoreResponse {
  sources?: [...]
  addons?: [...]
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `get_store_api_addons_store_get`


## `POST /api/addons/store/install` — Install From Store

### Request body

- Content-Type: `application/json` (required)

**Structure**
```
StoreInstallRequest {
  addon_id: string
  force?: boolean
}
```
### Responses

- **200** — Successful Response (`application/json`)
```
AddonInstallResult {
  status: string
  manifest?: ... | ...
  warnings?: [...]
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `install_from_store_api_addons_store_install_post`


## `POST /api/addons/store/uninstall` — Uninstall From Store

### Request body

- Content-Type: `application/json` (required)

**Structure**
```
StoreUninstallRequest {
  addon_id: string
  remove_files?: boolean
}
```
### Responses

- **200** — Successful Response (`application/json`)
```
AddonInstallResult {
  status: string
  manifest?: ... | ...
  warnings?: [...]
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `uninstall_from_store_api_addons_store_uninstall_post`


## `GET /api/addons/store/{addon_id}` — Get Store Addon

### Parameters

- **addon_id** (path, required) — `string`

### Responses

- **200** — Successful Response (`application/json`)
```
StoreEntry {
  catalog_id: string
  trusted: boolean
  addon: CatalogAddon ...
  installed?: boolean
  backend_loaded?: boolean
  setup_success?: ... | ...
  lifecycle?: string
  install_path?: ... | ...
  backend_prefix?: ... | ...
  health?: ... | ...
}
```
- **422** — Validation Error (`application/json`)
```
HTTPValidationError {
  detail?: [...]
}
```
**OperationId:** `get_store_addon_api_addons_store__addon_id__get`
