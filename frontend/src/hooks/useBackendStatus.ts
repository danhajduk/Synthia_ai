import { useEffect, useState } from "react";

export type BackendStatus = "online" | "offline" | "error" | "loading";

export function useBackendStatus(
  url: string,
  intervalMs = 5000
): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>("loading");

  async function check() {
    try {
      const res = await fetch(url, { method: "GET" });

      if (!res.ok) {
        setStatus("error");
        return;
      }

      setStatus("online");
    } catch (err) {
      setStatus("offline");
    }
  }

  useEffect(() => {
    check(); // run immediately
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [url, intervalMs]);

  return status;
}
