# Synthia Core TODO (Next Steps)

Last updated: 2025-12-23

## Dynamic Addon UI System

### 1) Sidebar integration
- [ ] Stop using static `registeredAddons: []` for sidebar nav.
- [ ] Fetch `/api/addons/frontend-routes` in the frontend (once) and build sidebar items from `sidebar[]`.
- [ ] Add ordering support (`order` field recommended) and sort server-side or client-side.
- [ ] Add UI states:
  - [ ] loading skeleton/placeholder
  - [ ] empty state (“No addons installed”)
  - [ ] error state + retry
- [ ] Decide how to handle `showInSidebar` from manifest vs backend computed list (prefer backend as source of truth).

### 2) Settings page (dynamic)
- [ ] Add route convention:
  - `addons/<id>/frontend/SettingsPage.tsx`
- [ ] Extend backend response (or derive) to include settings route:
  - `/addons/<id>/settings`
- [ ] Frontend loader:
  - `import.meta.glob("./*/SettingsPage.tsx")`
- [ ] Only register settings route if:
  - backend says `has_settings_page=true` AND component exists
- [ ] Decide routing style:
  - [ ] nested under addon main route
  - [ ] separate standalone route

### 3) Home page widget system (dynamic)
- [ ] Add widget convention:
  - `addons/<id>/frontend/HomeWidget.tsx`
- [ ] Extend backend metadata to include `showOnFrontpage` + optional `order`.
- [ ] Frontend loader:
  - `import.meta.glob("./*/HomeWidget.tsx")`
- [ ] Home page renders widgets:
  - [ ] sorted by `order`
  - [ ] with error boundary per widget

### 4) Header widget system (dynamic)
- [ ] Add widget convention:
  - `addons/<id>/frontend/HeaderWidget.tsx`
- [ ] Backend provides header widget list:
  - `{ addon_id, slot(left|center|right), order }`
- [ ] Frontend loader:
  - `import.meta.glob("./*/HeaderWidget.tsx")`
- [ ] Header renders widgets by slot and order.

---

## Frontend Symlink Lifecycle

### 5) Remove symlink on uninstall
- [ ] In backend uninstall flow:
  - [ ] remove `frontend/src/addons/<addonId>` ONLY if it is a symlink
  - [ ] refuse to delete if it’s a real directory (safety)
- [ ] (Optional) run “sync frontend symlinks” after uninstall for consistency.

### 6) Ensure symlinks aren’t committed to git
- [ ] Add to `.gitignore`:
  - `frontend/src/addons/*`
  - `!frontend/src/addons/.gitkeep`
- [ ] Add `.gitkeep`:
  - `frontend/src/addons/.gitkeep`
- [ ] Confirm git status stays clean after symlink sync.

---

## Addon Install From Git Repos (Default)

### 7) Manifest / metadata support
- [ ] Add optional manifest block:
  - `source: { type: "git", repo, ref, path }`
- [ ] Store resolved source metadata on install:
  - pinned commit SHA in `addons/<id>/runtime/meta/source.json`
- [ ] Track “dirty” status for local modifications (for safe updates).

### 8) Install/update flows
- [ ] Make repo-based install the default installer path.
- [ ] Implement:
  - [ ] clone/fetch to `addons/.sources/...`
  - [ ] copy payload into `addons/<id>/`
  - [ ] run addon setup
  - [ ] run frontend symlink sync
- [ ] Add update endpoint:
  - [ ] `POST /api/addons/update/<id>`
  - [ ] refuse update if dirty unless `force=true` (or stash option)

---

## Addon Store (Catalog System)

### 9) Official “Approved Addons” catalog
- [ ] Define catalog format:
  - `schema: synthia.addons.catalog.v1`
  - `addons: [{ id, name, description, repo, ref, path, types, min_core_version }]`
- [ ] Host official catalog online (GitHub raw or pages).
- [ ] Backend fetch + cache:
  - [ ] fetch on startup
  - [ ] periodic refresh (e.g., every 6 hours)
  - [ ] cache last-good copy on disk

### 10) 3rd-party catalogs (custom repos)
- [ ] Support multiple catalogs in config:
  - [ ] `official` (trusted)
  - [ ] user-added catalogs (untrusted by default)
- [ ] Backend endpoints:
  - [ ] `GET /api/addons/catalogs`
  - [ ] `POST /api/addons/catalogs` (add url)
  - [ ] `PATCH /api/addons/catalogs/<id>` (enable/disable/trust/rename)
  - [ ] `DELETE /api/addons/catalogs/<id>`
  - [ ] `GET /api/addons/store` (merged view)
  - [ ] `POST /api/addons/install-from-store` ({ catalog_id, addon_id })
- [ ] UI:
  - [ ] Store page with catalog selector + search + install buttons
  - [ ] Trusted vs untrusted warnings
  - [ ] show Installed / Update available badges

### 11) Security (later, but plan now)
- [ ] Add “trusted catalog” flag and warnings for untrusted.
- [ ] (Future) Signed catalogs:
  - [ ] `catalog.json` + `catalog.json.sig`
  - [ ] verify signature using a built-in public key

---

## Quality / Maintenance

### 12) Developer ergonomics
- [ ] Add a dev-only endpoint or CLI command:
  - [ ] “sync frontend symlinks now”
- [ ] Improve logging around setup/linking:
  - [ ] show exact symlink created/removed
  - [ ] clear permission error messages
- [ ] Add unit tests for:
  - [ ] catalog parsing
  - [ ] frontend linker safety rules
  - [ ] install/update metadata persistence
