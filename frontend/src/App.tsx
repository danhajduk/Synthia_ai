// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import Footer from "./components/layout/Footer";

import { buildNav, type RegisteredAddon } from "./navigation/navRegistry";
import { AddonsRegistryPage } from "./pages/AddonsRegistryPage";

// simple home page placeholder
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
              {/* fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
