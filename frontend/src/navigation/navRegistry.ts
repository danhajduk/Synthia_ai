// src/navigation/navRegistry.ts
import type { NavItem } from "../components/navigation/SidebarNav";

export type RegisteredAddon = {
  id: string;
  name: string;
  basePath: string; // e.g. "/addons/hello-llm"
};

export function buildNav(registeredAddons: RegisteredAddon[]): NavItem[] {
  const coreItems: NavItem[] = [
    { id: "home", label: "Home", path: "/" },
    { id: "addons", label: "Addons", path: "/addons" },
  ];

  const addonItems: NavItem[] = registeredAddons.map((addon) => ({
    id: `addon-${addon.id}`,
    label: addon.name,
    path: addon.basePath,
  }));

  const tailItems: NavItem[] = [
    { id: "settings", label: "Settings", path: "/settings" },
  ];

  return [...coreItems, ...addonItems, ...tailItems];
}
