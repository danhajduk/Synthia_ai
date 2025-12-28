// frontend/src/hooks/useAddonStatus.ts
import { useEffect, useState, useCallback } from "react";
import type { AddonRuntimeState, AddonLoadError } from "../types/addons";

interface AddonStatusState {
  addons: AddonRuntimeState[];
  loadErrors: AddonLoadError[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

type StoreResponse = {
  sources: any[];
  addons: Array<{
    addon: any; // manifest
    lifecycle: "available" | "installed" | "ready" | "error";
    health: {
      status: "unknown" | "ok" | "error";
      last_checked: string | null;
      error_code: string | null;
      error_message: string | null;
    };
  }>;
};

const DEFAULT_HEALTH = {
  status: "unknown",
  last_checked: null,
  error_code: null,
  error_message: null,
} as const;

export function useAddonStatus(pollIntervalMs: number = 10000): AddonStatusState {
  const [addons, setAddons] = useState<AddonRuntimeState[]>([]);
  const [loadErrors, setLoadErrors] = useState<AddonLoadError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [statusRes, errorsRes] = await Promise.all([
        fetch("/api/addons/store"),
        fetch("/api/addons/registry/_errors"),
      ]);

      if (!statusRes.ok) {
        const text = await statusRes.text().catch(() => "");
        throw new Error(`Failed to load addon store: ${statusRes.status} ${text}`);
      }

      const storeJson = (await statusRes.json()) as StoreResponse;

      if (!storeJson || !Array.isArray(storeJson.addons)) {
        throw new Error("Invalid store response: missing addons[]");
      }
      // 🔎 DEBUG: inspect what backend actually returned
      console.group("ADDON STORE DEBUG");
      console.log("Raw store response:", storeJson);
      console.table(
        storeJson.addons.map((a) => ({
          id: a.addon?.id,
          lifecycle: a.lifecycle,
          health_status: a.health?.status,
          error_code: a.health?.error_code,
          error_message: a.health?.error_message,
          last_checked: a.health?.last_checked,
        }))
      );
      console.groupEnd();

      // Map StoreEntry -> AddonRuntimeState (what the UI expects)
      const runtimeStates: AddonRuntimeState[] = storeJson.addons.map((e) => ({
        id: e.addon?.id,
        manifest: e.addon,
        lifecycle: e.lifecycle,
        health: e.health || DEFAULT_HEALTH,
      }));

      // load errors (optional endpoint)
      let loadErrorsJson: AddonLoadError[] = [];
      if (errorsRes.ok) {
        const errBody = await errorsRes.json();
        loadErrorsJson = errBody.errors ?? [];
      }

      setAddons(runtimeStates);
      setLoadErrors(loadErrorsJson);
    } catch (err: any) {
      setError(err?.message ?? "Failed to fetch addon status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const wrappedFetch = async () => {
      if (cancelled) return;
      await fetchStatus();
    };

    wrappedFetch(); // initial load

    const interval = setInterval(wrappedFetch, pollIntervalMs);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [fetchStatus, pollIntervalMs]);

  return {
    addons,
    loadErrors,
    loading,
    error,
    refresh: fetchStatus,
  };
}
