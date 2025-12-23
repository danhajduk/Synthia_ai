import { useEffect, useState } from "react";

export default function VisualsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch("/api/addons/visuals/status")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ status: "error" }));
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>Visuals Engine</h2>

      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => fetch("/api/addons/visuals/publish/placeholder", { method: "POST" }).then(() => window.location.reload())}
        >
          Publish Placeholder
        </button>
      </div>

      <div style={{ marginTop: 16 }}>
        <img
          src="/api/addons/visuals/current.jpg"
          style={{ maxWidth: "100%", borderRadius: 12 }}
          alt="Current visuals"
        />
      </div>

      <pre style={{ marginTop: 16, background: "#111", color: "#ddd", padding: 12, borderRadius: 12 }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
