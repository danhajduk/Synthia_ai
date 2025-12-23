import { useEffect, useState, useCallback } from "react";
import type {
  AddonRuntimeState,
  AddonLoadError,
} from "../types/addons";

interface AddonStatusState {
  addons: AddonRuntimeState[];
  loadErrors: AddonLoadError[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useAddonStatus(
  pollIntervalMs: number = 10000
): AddonStatusState {
  const [addons, setAddons] = useState<AddonRuntimeState[]>([]);
  const [loadErrors, setLoadErrors] = useState<AddonLoadError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [statusRes, errorsRes] = await Promise.all([
        fetch("/api/addons/status"),
        fetch("/api/addons/registry/_errors"),
      ]);

      if (!statusRes.ok) {
        throw new Error(`Failed to load addon status: ${statusRes.status}`);
      }

      const statusJson = (await statusRes.json()) as AddonRuntimeState[];

      let loadErrorsJson: AddonLoadError[] = [];
      if (errorsRes.ok) {
        const errBody = await errorsRes.json();
        loadErrorsJson = errBody.errors ?? [];
      }

      setAddons(statusJson);
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

    // initial load
    wrappedFetch();

    // polling
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
