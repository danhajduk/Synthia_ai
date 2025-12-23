import { useEffect, useMemo, useState } from "react";

export type AddonMainRoute = {
  addon_id: string;
  name: string;
  base_path: string; // e.g. "/addons/visuals"
  has_settings_page?: boolean;
};

export type AddonSidebarItem = {
  addon_id: string;
  label: string;
  path: string; // e.g. "/addons/visuals"
};

export type FrontendRoutesResponse = {
  main: AddonMainRoute[];
  header: any[];
  sidebar: AddonSidebarItem[];
};

export function useAddonFrontendRoutes() {
  const [data, setData] = useState<FrontendRoutesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      const res = await fetch("/api/addons/frontend-routes");
      if (!res.ok) throw new Error(`frontend-routes fetch failed: ${res.status}`);
      const json = (await res.json()) as FrontendRoutesResponse;
      setData(json);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return useMemo(() => ({ data, error, refresh }), [data, error]);
}
