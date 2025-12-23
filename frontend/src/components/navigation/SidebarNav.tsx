// src/components/navigation/SidebarNav.tsx
import React from "react";
import { NavLink } from "react-router-dom";

export type NavItem = {
  id: string;
  label: string;
  path: string;   // required now
};

type SidebarNavProps = {
  items: NavItem[];
};

const SidebarNav: React.FC<SidebarNavProps> = ({ items }) => {
  return (
    <nav className="sidebar-nav">
      {items.map((item) => (
        <NavLink
          key={item.id}
          to={item.path}
          end={item.path === "/"} // exact match for home
          className={({ isActive }) =>
            "sidebar-nav-button " + (isActive ? "primary" : "secondary")
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
};

export default SidebarNav;
