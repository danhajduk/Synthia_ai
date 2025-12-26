# Synthia — Addon Store TODO (Updated Status)

Last updated: 2025-12-25

This file focuses on **Addon Store / Catalog** work. It reflects what’s already present in the current backend tree (based on `backend.zip`) and what’s still missing / next.

---

## Current status (what already exists)

### Store API (backend)
- [x] Store router is implemented and mounted under `/api/addons/*` (see `app/addons/store/router.py` + `app/main.py`).
- [x] Endpoints exist:
  - [x] `GET /api/addons/store` (optional `?q=` search)
  - [x] `GET /api/addons/store/{addon_id}`
  - [x] `GET /api/addons/catalog` (catalog load status)
  - [x] `POST /api/addons/catalog/reload`
  - [x] `POST /api/addons/store/install` (install-by-addon-id from the catalog)
- [x] Store “hot load” attempt:
  - [x] After a successful install, backend tries to mount the addon router immediately via `load_backend_addon(...)`
  - [x] If hot-load succeeds, it removes the “restart Synthia” warning from the install result.

### Catalog handling (currently local-only)
- [x] Catalog schema model exists (`synthia.addons.catalog.v1`).
- [x] Local catalog file exists: `app/addons/store/dev_catalog.json`.
- [x] Store service loads that local JSON into memory (best-effort on startup; failures are reported via `/api/addons/catalog`).
- [x] Basic normalization exists:
  - [x] Default `ref="main"`, `path="."`
  - [x] Repo-relative path safety (blocks traversal like `..`).

### Install engine (git repo → addon folder)
- [x] `install_addon_from_repo(...)` exists and is used by store installs.
- [x] Flow implemented:
  - [x] `git clone` (depth 1) and `git checkout` for commit SHA support
  - [x] copy addon payload from repo subpath into `<core>/data/addons/<id>/`
  - [x] read `manifest.json` from installed payload
  - [x] run optional backend setup script (subprocess `python <setup.py>`) if `manifest.backend.setup` exists
  - [x] create symlink `<core>/addons/<id>` → `<core>/data/addons/<id>` (best-effort; warning if fails)

### Installed/loaded state in the store list
- [x] Store entries include:
  - installed? (disk presence in `<core>/data/addons/`)
  - backend_loaded? (based on `get_loaded_backends()`)
  - setup_success? (pulled from runtime states if present)
  - lifecycle: `available | installed | online | error | unknown`

---
### Phase 1 — Make “catalog source” real (still no UI)
- [x] Define catalog source config + persistence on disk (e.g., `<core>/data/addons/catalogs.json`)
  - fields: `id, name, url, enabled, trusted, last_loaded_at, last_error`
- [x] Implement backend endpoints for catalog management:
  - [x] `GET /api/addons/catalogs` (list all sources)
  - [x] `POST /api/addons/catalogs` (add catalog URL)
  - [x] `PATCH /api/addons/catalogs/{id}` (enable/disable/trust/rename)
  - [x] `DELETE /api/addons/catalogs/{id}`
- [x] Implement remote fetch + cache:
  - [x] fetch on startup
  - [x] periodic refresh (e.g., every 6 hours)
  - [x] cache “last-good” copy on disk (per-catalog)
  - [x] use per-catalog `ETag/If-Modified-Since` if you want to get fancy (optional)
- [x] Implement merged store view:
  - [x] `GET /api/addons/store` returns `sources[]` + merged addon list
  - [x] collision rules (addon id exists in multiple catalogs):
    - recommend: prefer **trusted** sources, else newest `generated_at`, else deterministic tie-breaker

## Gaps / limitations discovered (aka “why it feels unfinished”)

- [ ] **Catalogs are not actually a “store” yet**:
  - Only a single local file (`dev_catalog.json`) is supported.
  - No remote fetch, no caching, no periodic refresh, no multiple catalogs.
- [ ] No persistence for:
  - user-added catalog URLs
  - enabled/disabled catalogs
  - trusted/untrusted catalogs
- [ ] No merged “store view” across multiple catalogs (only one source exists).
- [ ] No “update available” logic:
  - We don’t store install source metadata (repo/ref/path + pinned commit SHA)
  - No comparison between installed version vs catalog version
- [ ] Uninstall cleanup is not store-aware:
  - `/api/addons/uninstall/{addon_id}` currently only “marks uninstalled” (installed store is disk-based no-op), doesn’t remove installed payload or symlink safely.
- [ ] The install symlink code currently uses `unlink()` on anything that “exists” — that’s risky if it’s a real dir. Needs safety rules.
- [ ] Two different “Catalog / Store” model sets exist:
  - `app/addons/domain/models.py` contains catalog-ish models
  - `app/addons/store/models.py` also contains store models  
  This isn’t a blocker, but it’s a code-smell and will bite later.

---

## Updated TODO — Addon Store Roadmap

### Phase 2 — Install metadata + update detection
- [ ] Add install metadata persistence per addon:
  - save to `<core>/data/addons/<id>/runtime/meta/source.json`
  - include: `repo, ref, path, installed_at, installed_commit_sha, catalog_id`
- [ ] Add “dirty” detection (local modifications) for safe updates:
  - simplest: store checksum/manifest hash on install and compare
  - better: keep the addon as a git repo in `.sources/` and copy/symlink payload
- [ ] Implement update endpoint:
  - [ ] `POST /api/addons/update/{id}` with `{ force?: bool }`
  - [ ] refuse update if dirty unless `force=true`
- [ ] Store view improvements:
  - [ ] include `update_available: bool`
  - [ ] include `installed_version` or installed commit SHA display

### Phase 3 — Security knobs (warning system first, crypto later)
- [ ] Trusted vs untrusted catalogs in response payload + UI-facing warnings
- [ ] Add allowlist option for catalogs when running in “locked down” mode
- [ ] (Future) signed catalogs:
  - `catalog.json` + `catalog.json.sig`
  - verify signature with built-in public key

### Phase 4 — UX endpoints (what the frontend will love you for)
- [ ] Add a clean “one call” endpoint for store UI:
  - [ ] `GET /api/addons/store` should already be it, once multi-catalog + update detection lands
- [ ] Add a store install endpoint that’s explicit about catalog selection:
  - [ ] `POST /api/addons/store/install` accepts `{ catalog_id, addon_id, force? }`
  - keep current “single catalog” behavior as a fallback if `catalog_id` omitted
- [ ] Add “install from URL” shortcut (optional):
  - [ ] `POST /api/addons/install` accepts `{ repo, ref?, path? }`

### Phase 5 — Uninstall that doesn’t leave haunted symlinks
- [ ] Implement uninstall that actually removes installed payload:
  - [ ] delete `<core>/data/addons/<id>`
  - [ ] remove `<core>/addons/<id>` ONLY if it is a symlink
  - [ ] refuse to delete if `<core>/addons/<id>` is a real directory
- [ ] After uninstall, trigger a frontend symlink sync hook (if you keep that workflow)

---

## Notes / “gotchas” worth keeping in mind
- The store already tries hot-loading backend routers after install. That’s great — but it will only work reliably if:
  - the addon backend is importable immediately (dependencies installed, setup done)
  - the loader supports mounting multiple times without duplicate route conflicts
- For update detection: commit-SHA installs are easiest to compare (exact). Branch/tag installs require checking latest remote SHA (needs fetch).

