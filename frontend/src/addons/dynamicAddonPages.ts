import React from "react";

/**
 * Vite needs static knowledge of possible import targets.
 * This creates a map of all addon MainPage.tsx files that exist at build time.
 *
 * IMPORTANT:
 * Your sync-addons-frontend.sh must symlink addons to:
 *   frontend/src/addons/<addonId>/...
 *
 * Example expected path:
 *   frontend/src/addons/visuals/MainPage.tsx
 */
const pages = import.meta.glob("./*/MainPage.tsx");

export function getAddonMainPageLazy(addonId: string) {
  const key = `./${addonId}/MainPage.tsx`;
  const loader = pages[key] as undefined | (() => Promise<{ default: React.ComponentType<any> }>);

  if (!loader) return null;

  return React.lazy(loader);
}
