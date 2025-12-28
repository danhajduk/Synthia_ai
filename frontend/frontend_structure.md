# Synthia Frontend Structure

This document covers how the frontend is organized: routing, layout, navigation, addon UI loading, and where the primary logic lives.

## Key files

- `src/App.tsx` — App shell: layout + core routes + dynamic addon route injection.
- `src/components/layout/Header.tsx` — Header layout (top bar).
- `src/components/layout/Sidebar.tsx` — Sidebar layout container.
- `src/components/layout/Footer.tsx` — Footer layout.
- `src/components/navigation/SidebarNav.tsx` — Renders the nav list items.
- `src/navigation/navRegistry.ts` — Builds nav items from core + registered addons.
- `src/addons/useAddonMainRoutes.tsx` — Fetches `/api/addons/frontend-routes` and builds lazy-loaded addon route objects.
- `src/addons/dynamicAddonPages.ts` — Lazy loader helper(s) for addon pages.
- `src/pages/AddonsRegistryPage.tsx` — Main addons page: lists addons + install/uninstall actions.
- `src/hooks/useAddonStatus.ts` — Data hook: store view + lifecycle/health mapping for UI.
- `src/hooks/useAddonRegistry.ts` — Data hook: registry manifests + load errors.
- `src/types/addons.ts` — TypeScript types mirrored from backend models (manifest/runtime/lifecycle).

## Routing

Routing is handled with `react-router-dom` (`BrowserRouter`, `Routes`, `Route`).

### Core routes (in `src/App.tsx`)
- `/` → Home
- `/addons` → Addons registry/status page
- `/settings` → placeholder
- `*` → Not found

### Dynamic addon main routes

Addon routes are injected after `useAddonMainRoutes()` reports `ready`.

For each backend-provided route entry, the UI lazy-loads:
- `src/addons/<addon_id>/MainPage.tsx`

If the file does not exist, a **Missing** placeholder is rendered.

## Layout

- The layout is a standard 3-part shell: **Header**, **Sidebar**, **Main content**, with a **Footer**.

- Sidebar items come from `buildNav()` in `src/navigation/navRegistry.ts`.

## Addon UI conventions

To add a new addon main page:

1. Create: `src/addons/<addon_id>/MainPage.tsx`
2. Default-export a React component.
3. Ensure backend includes the addon in `GET /api/addons/frontend-routes` under `main[]` with matching `addon_id`.


### Planned 3-surface UI
Your backend contract already returns `main`, `header`, and `sidebar` arrays. The frontend currently consumes `main`; `header` and `sidebar` are scaffold-ready for:
- header widgets/badges
- sidebar widgets/menu entries
