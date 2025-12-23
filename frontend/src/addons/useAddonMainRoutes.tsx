import React, { useEffect, useMemo, useState } from "react";
import { Route } from "react-router-dom";

const pages = import.meta.glob("./*/MainPage.tsx");

function getAddonMainPageLazy(addonId: string) {
  const key = `./${addonId}/MainPage.tsx`;
  const loader = pages[key] as undefined | (() => Promise<{ default: React.ComponentType<any> }>);

  if (!loader) return null;
  return React.lazy(loader);
}

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
  return <div className="p-4 text-sm text-gray-600">Loading {name}…</div>;
}

function Missing({ addonId }: { addonId: string }) {
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Addon UI not found</h2>
      <p className="text-sm text-gray-600 mt-1">
        Missing <code className="px-1 py-0.5 bg-gray-100 rounded">MainPage.tsx</code> for{" "}
        <b>{addonId}</b>.
      </p>
    </div>
  );
}

export function useAddonMainRouteElements() {
  const [data, setData] = useState<FrontendRoutesResponse | null>(null);
  const ready = data !== null;

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const res = await fetch("/api/addons/frontend-routes");
      if (!res.ok) throw new Error(`frontend-routes failed: ${res.status}`);
      const json = (await res.json()) as FrontendRoutesResponse;
      if (!cancelled) setData(json);
    })().catch((err) => {
      console.error("[addons] failed to load frontend-routes", err);
      if (!cancelled) setData({ main: [], header: [], sidebar: [] });
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const routes = useMemo(() => {
    if (!data) return [];

    return data.main.map((r) => {
      const C = getAddonMainPageLazy(r.addon_id);

      return (
        <Route
          key={`${r.addon_id}:${r.base_path}`}
          path={r.base_path}
          element={
            C ? (
              <React.Suspense fallback={<Loading name={r.name} />}>
                <C />
              </React.Suspense>
            ) : (
              <Missing addonId={r.addon_id} />
            )
          }
        />
      );
    });
  }, [data]);

  return { routes, ready };
}
