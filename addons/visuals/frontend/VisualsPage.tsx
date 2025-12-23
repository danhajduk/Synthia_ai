import { useEffect, useMemo, useState } from "react";

type Status = {
  status: string;
  addon: string;
  runtime_root?: string;
  current_image?: string;
  current_exists?: boolean;
};

export default function VisualsPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imgBust, setImgBust] = useState<number>(() => Date.now());
  const [loading, setLoading] = useState(false);

  const statusUrl = "/api/addons/visuals/status";
  const imageUrl = useMemo(
    () => `/api/addons/visuals/current.jpg?t=${imgBust}`,
    [imgBust]
  );

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(statusUrl);
      if (!res.ok) throw new Error(`status fetch failed: ${res.status}`);
      const data = (await res.json()) as Status;
      setStatus(data);
      setImgBust(Date.now()); // force image refresh
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function publishPlaceholder() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/addons/visuals/publish/placeholder", {
        method: "POST",
      });
      if (!res.ok) throw new Error(`publish failed: ${res.status}`);
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ padding: 16, display: "grid", gap: 16 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Visuals Engine</h2>
        <button onClick={refresh} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
        <button onClick={publishPlaceholder} disabled={loading}>
          Publish placeholder
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, border: "1px solid #a33", borderRadius: 8 }}>
          <b>Error:</b> {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>
        <div style={{ border: "1px solid #333", borderRadius: 12, overflow: "hidden" }}>
          <img
            src={imageUrl}
            alt="current visuals"
            style={{ width: "100%", display: "block" }}
            onError={() => setError("Image failed to load (current.jpg).")}
          />
        </div>

        <div style={{ border: "1px solid #333", borderRadius: 12, padding: 12 }}>
          <h3 style={{ marginTop: 0 }}>Status</h3>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
            {status ? JSON.stringify(status, null, 2) : "Loading…"}
          </pre>
          <div style={{ marginTop: 12, fontSize: 12, opacity: 0.75 }}>
            <div>status: {status?.status ?? "—"}</div>
            <div>addon: {status?.addon ?? "—"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
