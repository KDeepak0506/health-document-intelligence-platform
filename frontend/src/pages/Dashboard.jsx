import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listDocuments, getDocumentStatus } from "../api/documents";
import DocumentList from "../components/DocumentList";
import Toast from "../components/Toast";

const POLL_INTERVAL_MS = 4000;
const ACTIVE_STATUSES = ["Pending", "Processing"];

export default function Dashboard() {
  const { email } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const pollRef = useRef(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await listDocuments();
      setDocuments(data || []);
    } catch (err) {
      setToast({ message: err.message || "Couldn't load documents.", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Poll status for any document still Pending/Processing
  useEffect(() => {
    const activeDocs = documents.filter((d) =>
      ACTIVE_STATUSES.includes(d.processing_status)
    );

    if (activeDocs.length === 0) {
      clearInterval(pollRef.current);
      return;
    }

    pollRef.current = setInterval(async () => {
      try {
        const updates = await Promise.all(
          activeDocs.map((d) => getDocumentStatus(d.document_id).catch(() => null))
        );
        setDocuments((prev) =>
          prev.map((doc) => {
            const update = updates.find((u) => u && u.document_id === doc.document_id);
            return update ? { ...doc, processing_status: update.status } : doc;
          })
        );
      } catch {
        // silent retry
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(pollRef.current);
  }, [documents.map((d) => d.processing_status).join(",")]);

  // Calculate statistics from actual document state
  const totalCount = documents.length;
  const completedCount = documents.filter((d) => d.processing_status === "Completed").length;
  const processingCount = documents.filter((d) =>
    ACTIVE_STATUSES.includes(d.processing_status)
  ).length;
  const failedCount = documents.filter((d) => d.processing_status === "Failed").length;

  return (
    <div>
      <div className="hp-section-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="hp-page-title" style={{ fontSize: "1.5rem" }}>Welcome back</h1>
          <p style={{ color: "var(--hp-text-500)", fontSize: "0.875rem", margin: "4px 0 0" }}>
            Overview of clinical documents and intake activity for {email}
          </p>
        </div>
        <Link to="/upload" className="hp-btn-primary" style={{ width: "auto" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span>Upload New Document</span>
        </Link>
      </div>

      {/* Real Stats Cards */}
      <div className="hp-stats-grid">
        <div className="hp-stat-card">
          <div className="hp-stat-icon-wrapper hp-stat-icon-total">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          </div>
          <div className="hp-stat-info">
            <div className="hp-stat-value">{loading ? "-" : totalCount}</div>
            <div className="hp-stat-label">Total Documents</div>
          </div>
        </div>

        <div className="hp-stat-card">
          <div className="hp-stat-icon-wrapper hp-stat-icon-processing">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div className="hp-stat-info">
            <div className="hp-stat-value">{loading ? "-" : processingCount}</div>
            <div className="hp-stat-label">Processing</div>
          </div>
        </div>

        <div className="hp-stat-card">
          <div className="hp-stat-icon-wrapper hp-stat-icon-completed">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <div className="hp-stat-info">
            <div className="hp-stat-value">{loading ? "-" : completedCount}</div>
            <div className="hp-stat-label">Completed</div>
          </div>
        </div>

        <div className="hp-stat-card">
          <div className="hp-stat-icon-wrapper hp-stat-icon-failed">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          </div>
          <div className="hp-stat-info">
            <div className="hp-stat-value">{loading ? "-" : failedCount}</div>
            <div className="hp-stat-label">Failed</div>
          </div>
        </div>
      </div>

      {/* Recent Documents Table Section */}
      <div className="hp-section-header" style={{ marginTop: 32 }}>
        <h2 className="hp-section-title">Recent Documents</h2>
        <Link to="/documents" className="hp-btn-secondary" style={{ padding: "6px 14px", fontSize: "0.8125rem" }}>
          View All ({totalCount})
        </Link>
      </div>

      <DocumentList
        documents={documents.slice(0, 5)}
        loading={loading}
      />

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onClose={() => setToast(null)}
      />
    </div>
  );
}
