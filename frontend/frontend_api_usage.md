# Synthia Frontend API Usage

This document lists every backend API call made by the current frontend, where it is used, and the **expected request/response payload structure** (derived from the backend OpenAPI schema).


---

## `src/hooks/useAddonRegistry.ts`


### `GET /api/addons/registry`

**Summary:** Api List Addons

Return all valid addon manifests.
Optional filter: ?type=llm|voice|knowledge|action|ui

**Request body:** none

**Response (200)**

- Content-Type: `application/json`

```
[AddonManifest {
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
}]
```

**Response (422)**

- Content-Type: `application/json`

```
HTTPValidationError {
  detail?: [ValidationError ...]
}
```


### `GET /api/addons/registry/_errors`

**Summary:** Api Get Addon Errors

Optional helper: expose manifest load errors to the frontend.

**Request body:** none

**Response (200):** (no schema declared)


---

## `src/hooks/useAddonStatus.ts`


### `GET /api/addons/store`

**Summary:** Get Store

**Request body:** none

**Response (200)**

- Content-Type: `application/json`

```
StoreResponse {
  sources?: [StoreSource ...]
  addons?: [StoreEntry ...]
}
```

**Response (422)**

- Content-Type: `application/json`

```
HTTPValidationError {
  detail?: [ValidationError ...]
}
```


### `GET /api/addons/registry/_errors`

**Summary:** Api Get Addon Errors

Optional helper: expose manifest load errors to the frontend.

**Request body:** none

**Response (200):** (no schema declared)


---

## `src/addons/useAddonMainRoutes.tsx`


### `GET /api/addons/frontend-routes`

**Summary:** Api Frontend Routes

Return frontend integration metadata for all addons.

Surfaces:
- main: main UI routes
- header: header badges/widgets (for now derived from summaryComponent)
- sidebar: sidebar nav items

This allows the frontend to:
- auto-register routes
- build sidebar nav dynamically
- render header/frontpage widgets from addon metadata

**Request body:** none

**Response (200)**

- Content-Type: `application/json`

```
FrontendRoutesResponse {
  main?: [FrontendMainRoute ...]
  header?: [FrontendHeaderWidget ...]
  sidebar?: [FrontendSidebarItem ...]
}
```


---

## `src/pages/AddonsRegistryPage.tsx`


### `POST /api/addons/store/install`

**Summary:** Install From Store

**Request body**

- Content-Type: `application/json` (required)

```
StoreInstallRequest {
  addon_id: string
  force?: boolean
}
```

**Response (200)**

- Content-Type: `application/json`

```
AddonInstallResult {
  status: string
  manifest?: AddonManifest ... | null
  warnings?: [string]
}
```

**Response (422)**

- Content-Type: `application/json`

```
HTTPValidationError {
  detail?: [ValidationError ...]
}
```


### `POST /api/addons/store/uninstall`

**Summary:** Uninstall From Store

**Request body**

- Content-Type: `application/json` (required)

```
StoreUninstallRequest {
  addon_id: string
  remove_files?: boolean
}
```

**Response (200)**

- Content-Type: `application/json`

```
AddonInstallResult {
  status: string
  manifest?: AddonManifest ... | null
  warnings?: [string]
}
```

**Response (422)**

- Content-Type: `application/json`

```
HTTPValidationError {
  detail?: [ValidationError ...]
}
```
