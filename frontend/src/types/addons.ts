// src/types/addons.ts
export type AddonType = "llm" | "voice" | "knowledge" | "action" | "ui";

export type AddonLifecycleStatus = "available" | "installed" | "ready" | "error";

export type AddonHealthStatus = "unknown" | "ok" | "error";

export type AddonHealthSnapshot = {
  status: AddonHealthStatus;
  last_checked: string | null;
  error_code: string | null;
  error_message: string | null;
};

export type AddonManifest = {
  id: string;
  name: string;
  version: string;
  description?: string;
  types: AddonType[];
  frontend?: {
    basePath: string;
    hasSettingsPage?: boolean;
    showInSidebar?: boolean;
    sidebarLabel?: string;
    showOnFrontpage?: boolean;
    summaryComponent?: string;
    summarySize?: "sm" | "md" | "lg";
  };
  backend?: {
    entry: string;
    setup?: string | null;
    healthPath?: string;
    requiresConfig?: string[];
  } | null;
};

export interface AddonSetupResult {
  success: boolean;
  exit_code: number;
  stdout: string;
  stderr: string;
}

export type AddonRuntimeState = {
  id: string;
  manifest: AddonManifest;
  lifecycle: AddonLifecycleStatus;
  health: AddonHealthSnapshot;
  setup_result?: AddonSetupResult | null;
};

