import React, { useEffect, useMemo, useState } from "react";
import { getAddonMainPageLazy } from "./dynamicAddonPages";

type FrontendRoutesResponse = {
  main: Array<{
    addon_id: string;
    name: string;
    base_path: string;
    has_settings_page: boolean;
  }>;
  header: any[];
  sidebar: any[];
};

function Loading({ name }: { name: string }) {
  return <div style={{ padding: 16 }}>Loading {name}…</div>;
}

function Missing({ addonId }: { addonId: string }) {
  return (
    <div style={{ padding: 16 }}>
      <h2>Addon UI not found</h2>
      <p>
        No <code>MainPage.tsx</code> found for <b>{addonId}</b>.
      </p>
    </div>
  );
}

export function useDynamicAddonRouteObjects() {
  const [data, setData] = useState<FrontendRoutesResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const res = await fetch("/api/addons/frontend-routes");
      if (!res.ok) throw new Error(`frontend-routes failed: ${res.status}`);
      const json = (await res.json()) as FrontendRoutesResponse;

      if (!cancelled) setData(json);
    })().catch((err) => {
      console.error(err);
      if (!cancelled) setData({ main: [], header: [], sidebar: [] });
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const routeObjects = useMemo(() => {
    if (!data) return [];

    return data.main.map((r) => {
      const C = getAddonMainPageLazy(r.addon_id);

      if (!C) {
        return { path: r.base_path, element: <Missing addonId={r.addon_id} /> };
      }

      return {
        path: r.base_path,
        element: (
          <React.Suspense fallback={<Loading name={r.name} />}>
            <C />
          </React.Suspense>
        ),
      };
    });
  }, [data]);

  return routeObjects;
}
