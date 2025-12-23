import { useEffect, useState } from "react";
import type { AddonManifest, AddonLoadError } from "../types/addons";

interface AddonRegistryState {
  addons: AddonManifest[];
  loadErrors: AddonLoadError[];
  loading: boolean;
  error: string | null;
}

export function useAddonRegistry(): AddonRegistryState {
  const [addons, setAddons] = useState<AddonManifest[]>([]);
  const [loadErrors, setLoadErrors] = useState<AddonLoadError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const [addonsRes, errorsRes] = await Promise.all([
          fetch("/api/addons/registry"),
          fetch("/api/addons/registry/_errors"),
        ]);

        if (!addonsRes.ok) {
          throw new Error(`Failed to load addons: ${addonsRes.status}`);
        }

        const addonsJson = (await addonsRes.json()) as AddonManifest[];

        let loadErrorsJson: AddonLoadError[] = [];
        if (errorsRes.ok) {
          const errorsBody = await errorsRes.json();
          loadErrorsJson = (errorsBody.errors ?? []) as AddonLoadError[];
        }

        if (!cancelled) {
          setAddons(addonsJson);
          setLoadErrors(loadErrorsJson);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.message ?? "Failed to load addon registry");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, []);

  return { addons, loadErrors, loading, error };
}
