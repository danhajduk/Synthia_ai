import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import Footer from "./components/layout/Footer";

import { buildNav, type RegisteredAddon } from "./navigation/navRegistry";
import { AddonsRegistryPage } from "./pages/AddonsRegistryPage";
import { useAddonMainRouteElements } from "./addons/useAddonMainRoutes";

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

const registeredAddons: RegisteredAddon[] = [];
const navItems = buildNav(registeredAddons);

function App() {
  // ✅ hooks must be called INSIDE a component
  const { routes: addonMainRoutes, ready } = useAddonMainRouteElements();

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
                    <div className="p-4 text-sm text-gray-600">Loading addons…</div>
                  }
                />
              )}

              {/* Once ready, register addon pages */}
              {ready && addonMainRoutes}

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
