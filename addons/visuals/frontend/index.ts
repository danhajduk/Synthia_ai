import VisualsPage from "./VisualsPage";

export const meta = {
  id: "visuals",
  name: "Visuals",
  basePath: "/addons/visuals",
};

export const routes = [
  {
    path: meta.basePath,
    element: <VisualsPage />,
  },
];

// Optional: if your core uses a navItem pattern
export const navItem = {
  label: "Visuals",
  path: meta.basePath,
};
