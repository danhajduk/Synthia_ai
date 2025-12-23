// frontend/src/pages/AddonsRegistryPage.tsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { useAddonStatus } from "../hooks/useAddonStatus";
import { formatLocalTime } from "../utils/format";

import type {
  AddonRuntimeState,
  AddonLifecycleStatus,
  AddonType,
} from "../types/addons";

function lifecycleLabel(status: AddonLifecycleStatus): string {
  switch (status) {
    case "available":
      return "Available";
    case "installed":
      return "Installed";
    case "ready":
      return "Ready";
    case "error":
      return "Error";
  }
}

function lifecycleClass(status: AddonLifecycleStatus): string {
  switch (status) {
    case "available":
      return "addon-status-available";
    case "installed":
      return "addon-status-installed";
    case "ready":
      return "addon-status-ready";
    case "error":
      return "addon-status-error";
  }
}

function lifecycleIcon(status: AddonLifecycleStatus): string {
  switch (status) {
    case "available":
      return "📦";
    case "installed":
      return "📥";
    case "ready":
      return "✅";
    case "error":
      return "⚠️";
  }
}

function typeIcon(t: AddonType): string {
  switch (t) {
    case "llm":
      return "🧠";
    case "voice":
      return "🎙️";
    case "knowledge":
      return "📚";
    case "action":
      return "⚙️";
    case "ui":
      return "🖥️";
  }
}

function healthIcon(status: "unknown" | "ok" | "error"): string {
  switch (status) {
    case "ok":
      return "🩺"; // healthy
    case "error":
      return "⚠️"; // error
    case "unknown":
    default:
      return "❔"; // unknown / not applicable
  }
}

function formatHealthTooltip(health: AddonRuntimeState["health"]): string {
  if (health.status === "ok") {
    if (health.last_checked) {
      return `Healthy (last checked: ${formatLocalTime(health.last_checked)})`;
    }
    return "Healthy";
  }

  if (health.status === "error") {
    const base = "Health check failed";
    if (health.error_code && health.error_message) {
      return `${base}: [${health.error_code}] ${health.error_message}`;
    }
    if (health.error_message) {
      return `${base}: ${health.error_message}`;
    }
    if (health.error_code) {
      return `${base}: [${health.error_code}]`;
    }
    return base;
  }

  // unknown
  return "Health status unknown";
}

const typeLabels: Record<AddonType, string> = {
  llm: "LLM",
  voice: "Voice",
  knowledge: "Knowledge",
  action: "Action",
  ui: "UI",
};

function hasSetupFailure(runtime: AddonRuntimeState): boolean {
  const r = (runtime as any).setup_result;
  return !!(r && r.success === false);
}

export const AddonsRegistryPage: React.FC = () => {
  const { addons, loadErrors, loading, error, refresh } = useAddonStatus(10_000);
  const navigate = useNavigate();

  const availableAddons = addons.filter((a) => a.lifecycle === "available");
  const activeAddons = addons.filter((a) => a.lifecycle !== "available");

  async function handleInstall(addon: AddonRuntimeState) {
    try {
      const res = await fetch(`/api/addons/install/${addon.id}`, {
        method: "POST",
      });
      if (!res.ok) {
        console.error("Failed to install addon", addon.id, res.status);
        return;
      }
      await refresh();
    } catch (err) {
      console.error("Error installing addon", addon.id, err);
    }
  }

  async function handleUninstall(addon: AddonRuntimeState) {
    try {
      const res = await fetch(`/api/addons/uninstall/${addon.id}`, {
        method: "POST",
      });
      if (!res.ok) {
        console.error("Failed to uninstall addon", addon.id, res.status);
        return;
      }
      await refresh();
    } catch (err) {
      console.error("Error uninstalling addon", addon.id, err);
    }
  }

  function handleOpen(addon: AddonRuntimeState) {
    const frontend = addon.manifest.frontend;
    if (!frontend?.basePath) return;
    navigate(frontend.basePath);
  }

  return (
    <div className="addons-page">
      <div className="addons-header">
        <div>
          <h1 className="addons-title">Addons</h1>
          <p className="addons-subtitle">
            Registered Synthia addons and their lifecycle status.
          </p>
        </div>
      </div>

      {loading && (
        <div className="addons-message addons-message-muted">
          Loading addons…
        </div>
      )}

      {error && (
        <div className="addons-message addons-message-error">
          Failed to load addons: {error}
        </div>
      )}

      {loadErrors.length > 0 && (
        <div className="addons-message addons-message-warning">
          <div className="addons-message-title">
            Some addons failed to load manifests:
          </div>
          <ul className="addons-error-list">
            {loadErrors.map((e, idx) => (
              <li key={idx}>
                <code className="addons-code">{e.addon_path}</code>: {e.error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && addons.length === 0 && (
        <div className="addons-message addons-message-muted">
          No addons registered yet.
        </div>
      )}

      {/* AVAILABLE SECTION */}
      {availableAddons.length > 0 && (
        <>
          <h2 className="addons-section-title">Available</h2>
          <div className="addons-grid">
            {availableAddons.map((runtime) => {
              const { manifest, lifecycle /*, health */ } = runtime;

              return (
                <div key={runtime.id} className="addon-card">
                  <div className="addon-card-header">
                    <div>
                      <div className="addon-id">{manifest.id}</div>
                      <div className="addon-name">{manifest.name}</div>
                      <div className="addon-version">v{manifest.version}</div>
                    </div>

                    <div className="addon-card-header-right">
                      <span
                        className={`addon-status ${lifecycleClass(lifecycle)}`}
                      >
                        <span className="addon-status-icon">
                          {lifecycleIcon(lifecycle)}
                        </span>
                        {lifecycleLabel(lifecycle)}
                      </span>

                      {/* health icon for available addons is currently disabled
                      <span
                        className={`addon-health-icon addon-health-${health.status}`}
                        title={formatHealthTooltip(health)}
                      >
                        {healthIcon(health.status)}
                      </span>
                      */}
                    </div>
                  </div>

                  {manifest.description && (
                    <p className="addon-description">{manifest.description}</p>
                  )}

                  <div className="addon-types">
                    {manifest.types.map((t) => (
                      <span key={t} className="addon-type-pill">
                        <span className="addon-type-icon">{typeIcon(t)}</span>
                        <span>{typeLabels[t]}</span>
                      </span>
                    ))}
                  </div>

                  <div className="addon-card-actions">
                    <button
                      className="addon-button addon-button-primary"
                      onClick={() => handleInstall(runtime)}
                    >
                      Install
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* INSTALLED / READY / ERROR SECTION */}
      {activeAddons.length > 0 && (
        <>
          <h2 className="addons-section-title">Installed</h2>
          <div className="addons-grid">
            {activeAddons.map((runtime) => {
              const { manifest, lifecycle, health } = runtime;
              const backend = manifest.backend;
              const frontend = manifest.frontend;
              const setupResult: any = (runtime as any).setup_result;

              return (
                <div key={runtime.id} className="addon-card">
                  <div className="addon-card-header">
                    <div>
                      <div className="addon-id">{manifest.id}</div>
                      <div className="addon-name">{manifest.name}</div>
                      <div className="addon-version">v{manifest.version}</div>
                    </div>

                    <div className="addon-card-header-right">
                      <span
                        className={`addon-status ${lifecycleClass(lifecycle)}`}
                      >
                        <span className="addon-status-icon">
                          {lifecycleIcon(lifecycle)}
                        </span>
                        {lifecycleLabel(lifecycle)}
                      </span>

                      <span
                        className={`addon-health-icon addon-health-${health.status}`}
                        title={formatHealthTooltip(health)}
                      >
                        {healthIcon(health.status)}
                      </span>

                      {hasSetupFailure(runtime) && (
                        <span className="addon-setup-badge">Setup failed</span>
                      )}
                    </div>
                  </div>

                  {manifest.description && (
                    <p className="addon-description">{manifest.description}</p>
                  )}

                  <div className="addon-types">
                    {manifest.types.map((t) => (
                      <span key={t} className="addon-type-pill">
                        <span className="addon-type-icon">{typeIcon(t)}</span>
                        <span>{typeLabels[t]}</span>
                      </span>
                    ))}
                  </div>

                  {lifecycle === "error" && health?.error_message && (
                    <div
                      className="addons-message addons-message-error"
                      style={{ marginTop: 8 }}
                    >
                      <div className="addons-message-title">Health error</div>
                      <div>
                        {health.error_code && (
                          <strong>{health.error_code}: </strong>
                        )}
                        {health.error_message}
                      </div>
                    </div>
                  )}

                  {hasSetupFailure(runtime) && setupResult && (
                    <div
                      className="addons-message addons-message-error"
                      style={{ marginTop: 8 }}
                    >
                      <div className="addons-message-title">
                        Setup failed (exit {setupResult.exit_code})
                      </div>
                      <details style={{ marginTop: 4 }}>
                        <summary>Show setup logs</summary>
                        {setupResult.stderr && (
                          <pre className="addons-log-block">
                            {setupResult.stderr}
                          </pre>
                        )}
                        {!setupResult.stderr && setupResult.stdout && (
                          <pre className="addons-log-block">
                            {setupResult.stdout}
                          </pre>
                        )}
                      </details>
                    </div>
                  )}

                  <div className="addon-card-actions">
                    {frontend?.basePath && (
                      <button
                        className="addon-button addon-button-secondary"
                        onClick={() => handleOpen(runtime)}
                      >
                        Open
                      </button>
                    )}
                    <button
                      className="addon-button addon-button-ghost"
                      onClick={() => handleUninstall(runtime)}
                    >
                      Uninstall
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
