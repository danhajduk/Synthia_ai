import VisualsPage from "./VisualsPage";

export const meta = {
  id: "visuals",
  name: "Visuals",
  basePath: "/addons/visuals",
};

export const routes = [
  { path: meta.basePath, element: <VisualsPage /> },
];

export const navItem = {
  label: "Visuals",
  path: meta.basePath,
};
