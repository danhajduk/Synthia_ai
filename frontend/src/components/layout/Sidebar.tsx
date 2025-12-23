// src/components/layout/Sidebar.tsx
import React from "react";
import SidebarNav, { type NavItem } from "../navigation/SidebarNav";
import { useBackendStatus } from "../../hooks/useBackendStatus";

type SidebarProps = {
  navItems: NavItem[];
};

const Sidebar: React.FC<SidebarProps> = ({ navItems }) => {
  // ✅ Call the hook once at the top of the component
  const backendStatus = useBackendStatus("/api/health", 10000); // 10s poll, tweak as needed

  return (
    <aside className="app-sidebar">
      <div>
        {/* Profile card */}
        <div className="profile-card">
          <div className="profile-avatar">
            <div className="avatar-glow"></div>
            <img src="/images/avatar.png" alt="Avatar" />
          </div>
          <div className="profile-name">Synthia</div>
          <div className="profile-role">Dev Console</div>

          <div className="profile-meta">
            <div className="profile-meta-row">
              <span className="profile-meta-label">Host</span>
              <span className="profile-meta-value">10.0.0.100</span>
            </div>
            <div className="profile-meta-row">
              <span className="profile-meta-label">Uptime</span>
              <span className="profile-meta-value">4d 17h 33m</span>
            </div>
          </div>
        </div>

        {/* Navigation injected from outside */}
        <SidebarNav items={navItems} />
      </div>

      {/* Status footer */}
      <div className="sidebar-footer">
        <div className="status-pill">
          <span
            className="status-dot"
            // ✅ Use the *value*, not the hook function
            data-status={backendStatus}
          />
          <span>
            Backend:{" "}
            {backendStatus === "online"
              ? "Online"
              : backendStatus === "loading"
              ? "Checking..."
              : backendStatus === "error"
              ? "Error"
              : "Offline"}
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
