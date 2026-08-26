import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { listDocuments, getDocumentStatus } from "../api/documents";
import DocumentList from "../components/DocumentList";
import Toast from "../components/Toast";

const POLL_INTERVAL_MS = 4000;
const ACTIVE_STATUSES = ["Pending", "Processing"];

export default function DocumentsPage() {
  const location = useLocation();
  const newestId = location.state?.newestId || null;

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

  return (
    <div>
      <div className="hp-section-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="hp-page-title" style={{ fontSize: "1.5rem" }}>Healthcare Document Repository</h1>
          <p style={{ color: "var(--hp-text-500)", fontSize: "0.875rem", margin: "4px 0 0" }}>
            Total registered documents: {documents.length}
          </p>
        </div>
        <Link to="/upload" className="hp-btn-primary" style={{ width: "auto" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span>Upload Document</span>
        </Link>
      </div>

      <DocumentList
        documents={documents}
        loading={loading}
        newestId={newestId}
      />

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onClose={() => setToast(null)}
      />
    </div>
  );
}
