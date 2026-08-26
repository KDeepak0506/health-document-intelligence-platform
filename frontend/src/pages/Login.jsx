import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login({ email, password });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(
        err.status === 401
          ? "Incorrect email or password."
          : err.message || "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="hp-auth-shell">
      {/* Left side healthcare banner */}
      <div className="hp-auth-banner">
        <div className="hp-auth-banner-header">
          <div className="hp-brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </div>
          <span className="hp-brand-text" style={{ fontSize: "1.5rem" }}>HealthParse</span>
        </div>

        <div className="hp-auth-banner-body">
          <h2>Automated Healthcare Document Workspace</h2>
          <p>
            Secure, centralized document ingestion and tracking built for healthcare professionals, clinical staff, and medical records administrators.
          </p>

          <div className="hp-auth-feature-list">
            <div className="hp-auth-feature-item">
              <div className="hp-auth-feature-icon">✓</div>
              <span>Streamlined lab reports, prescriptions & records</span>
            </div>
            <div className="hp-auth-feature-item">
              <div className="hp-auth-feature-icon">✓</div>
              <span>HIPAA-aligned security & role controls</span>
            </div>
            <div className="hp-auth-feature-item">
              <div className="hp-auth-feature-icon">✓</div>
              <span>Real-time processing status tracking</span>
            </div>
          </div>
        </div>

        <div className="hp-auth-banner-footer">
          HealthParse Clinical Document Intelligence Platform &copy; {new Date().getFullYear()}
        </div>
      </div>

      {/* Right side login form */}
      <div className="hp-auth-form-container">
        <div className="hp-auth-card">
          <h1>Sign in</h1>
          <p className="hp-auth-subtitle">Access your clinical document portal</p>

          {error && (
            <div className="hp-error-banner" role="alert">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="hp-field">
              <label htmlFor="email">Work Email</label>
              <input
                id="email"
                className="hp-input"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@hospital.org"
              />
            </div>
            <div className="hp-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                className="hp-input"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <button className="hp-btn-primary" type="submit" disabled={loading}>
              {loading ? <span className="hp-spinner" /> : "Sign in to HealthParse"}
            </button>
          </form>

          <p className="hp-hint">
            Need access? <Link to="/register">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
