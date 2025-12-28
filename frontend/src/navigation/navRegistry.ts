// src/navigation/navRegistry.ts
import type { NavItem } from "../components/navigation/SidebarNav";

export type SidebarRouteItem = {
  addon_id: string;
  label: string;
  path: string;
};

export function buildNavFromSidebarRoutes(sidebarItems: SidebarRouteItem[]): NavItem[] {
  const coreItems: NavItem[] = [
    { id: "home", label: "Home", path: "/" },
    { id: "addons", label: "Addons", path: "/addons" },
  ];

  const addonItems: NavItem[] = sidebarItems.map((item) => ({
    id: `addon-${item.addon_id}`,
    label: item.label,
    path: item.path,
  }));

  const tailItems: NavItem[] = [
    { id: "settings", label: "Settings", path: "/settings" },
  ];

  return [...coreItems, ...addonItems, ...tailItems];
}
