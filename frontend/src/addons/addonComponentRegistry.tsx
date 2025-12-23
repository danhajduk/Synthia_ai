import React from "react";
import VisualsPage from "./visuals/VisualsPage";

export function resolveAddonElement(addonId: string): React.ReactNode {
  switch (addonId) {
    case "visuals":
      return <VisualsPage />;
    default:
      return (
        <div className="p-4">
          <h2 className="text-lg font-semibold">Addon UI not registered</h2>
          <p className="text-sm text-gray-600">
            No frontend component mapped for <code>{addonId}</code>.
          </p>
        </div>
      );
  }
}
