import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import Footer from "./components/layout/Footer";

import { AddonsRegistryPage } from "./pages/AddonsRegistryPage";
import { useAddonMainRoutes } from "./addons/useAddonMainRoutes";

import {
  buildNavFromSidebarRoutes,
  type SidebarRouteItem,
} from "./navigation/navRegistry";

function HomePage() {
  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-2">Synthia</h1>
      <p className="text-sm text-gray-600">
        Welcome to Synthia. Use the sidebar to navigate.
      </p>
    </div>
  );
}

type FrontendRoutesResponse = {
  main: Array<any>;
  header: Array<any>;
  sidebar: SidebarRouteItem[];
};

function App() {
  const { routes: addonMainRoutes, ready } = useAddonMainRoutes();

  const [sidebarRoutes, setSidebarRoutes] = useState<SidebarRouteItem[]>([]);

  useEffect(() => {
    let cancelled = false;
    let inFlight = false;

    async function loadSidebarRoutes() {
      if (inFlight) return;
      inFlight = true;

      try {
        const res = await fetch("/api/addons/frontend-routes", {
          headers: { accept: "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = (await res.json()) as FrontendRoutesResponse;

        const sidebar = Array.isArray(data.sidebar) ? data.sidebar : [];
        if (!cancelled) setSidebarRoutes(sidebar);
      } catch (err) {
        console.error("Failed to load /api/addons/frontend-routes", err);
        if (!cancelled) setSidebarRoutes([]);
      } finally {
        inFlight = false;
      }
    }

    // run immediately
    loadSidebarRoutes();

    // refresh every 10s
    const id = window.setInterval(loadSidebarRoutes, 10_000);

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  const navItems = useMemo(
    () => buildNavFromSidebarRoutes(sidebarRoutes),
    [sidebarRoutes]
  );

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar navItems={navItems} />

        <div className="app-right">
          <Header />

          <main className="app-main">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/addons" element={<AddonsRegistryPage />} />

              {/* While loading addons, keep /addons/* from falling into "*" */}
              {!ready && (
                <Route
                  path="/addons/*"
                  element={
                    <div className="p-4 text-sm text-gray-600">
                      Loading addons…
                    </div>
                  }
                />
              )}

              {/* Once ready, register addon pages */}
              {ready &&
                addonMainRoutes
                  .filter((r) => typeof r.path === "string" && r.path.length > 0)
                  .map((r) => (
                    <Route
                      key={r.path as string}
                      path={r.path as string}
                      element={r.element}
                    />
                  ))}

              {/* Debug-friendly fallback */}
              <Route
                path="*"
                element={<div className="p-4 text-sm text-gray-600">Not found</div>}
              />
            </Routes>
          </main>

          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
