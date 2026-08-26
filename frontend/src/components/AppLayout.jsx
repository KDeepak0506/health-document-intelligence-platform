import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AppLayout({ children }) {
  const { email, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Helper to determine page titles
  const getPageTitle = () => {
    switch (location.pathname) {
      case "/dashboard":
        return "Dashboard Overview";
      case "/documents":
        return "Healthcare Documents";
      case "/upload":
        return "Upload Document";
      default:
        return "HealthParse";
    }
  };

  const getInitials = (userEmail) => {
    if (!userEmail) return "HP";
    return userEmail.substring(0, 2).toUpperCase();
  };

  return (
    <div className="hp-app-shell">
      {/* Sidebar */}
      <aside className={`hp-sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="hp-sidebar-header">
          <NavLink to="/dashboard" className="hp-brand-logo" onClick={() => setMobileOpen(false)}>
            <div className="hp-brand-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
            <span className="hp-brand-text">HealthParse</span>
          </NavLink>
        </div>

        <nav className="hp-sidebar-nav">
          <div className="hp-nav-section-title">Navigation</div>
          
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `hp-nav-item ${isActive ? "active" : ""}`}
            onClick={() => setMobileOpen(false)}
          >
            <span className="hp-nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="9"></rect>
                <rect x="14" y="3" width="7" height="5"></rect>
                <rect x="14" y="12" width="7" height="9"></rect>
                <rect x="3" y="16" width="7" height="5"></rect>
              </svg>
            </span>
            Dashboard
          </NavLink>

          <NavLink
            to="/documents"
            className={({ isActive }) => `hp-nav-item ${isActive ? "active" : ""}`}
            onClick={() => setMobileOpen(false)}
          >
            <span className="hp-nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            </span>
            Documents
          </NavLink>

          <NavLink
            to="/upload"
            className={({ isActive }) => `hp-nav-item ${isActive ? "active" : ""}`}
            onClick={() => setMobileOpen(false)}
          >
            <span className="hp-nav-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </span>
            Upload Document
          </NavLink>
        </nav>

        <div className="hp-sidebar-footer">
          <div className="hp-user-profile">
            <div className="hp-avatar">{getInitials(email)}</div>
            <div className="hp-user-info">
              <div className="hp-user-name">Authorized User</div>
              <div className="hp-user-email">{email || "user@hospital.org"}</div>
            </div>
            <button className="hp-logout-btn" onClick={logout} title="Sign out" aria-label="Sign out">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Wrapper */}
      <div className="hp-main-wrapper">
        <header className="hp-topbar">
          <div className="hp-topbar-left">
            <button
              className="hp-mobile-toggle"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle Navigation"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <h1 className="hp-page-title">{getPageTitle()}</h1>
          </div>

          <div className="hp-topbar-right">
            <span className="hp-topbar-badge">Clinical Workspace</span>
          </div>
        </header>

        <main className="hp-main-content">{children}</main>
      </div>
    </div>
  );
}
