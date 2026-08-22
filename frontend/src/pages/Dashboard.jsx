import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { listDocuments, getDocumentStatus } from "../api/documents";
import UploadForm from "../components/UploadForm";
import DocumentList from "../components/DocumentList";
import Toast from "../components/Toast";

const POLL_INTERVAL_MS = 4000;
const ACTIVE_STATUSES = ["Pending", "Processing"];

export default function Dashboard() {
  const { logout } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newestId, setNewestId] = useState(null);
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

  // Poll status for any document still Pending/Processing, so the UI reflects
  // pipeline progress without a manual refresh. Stops itself once nothing is active.
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
        // silent — next tick will retry
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents.map((d) => d.processing_status).join(",")]);

  function handleUploaded(result) {
    setNewestId(result.document_id);
    setToast({ message: "Document uploaded — processing started.", variant: "success" });
    setDocuments((prev) => [result, ...prev]);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <h1>Document Intelligence</h1>
        </div>
        <div className="who">
          <button className="link-btn" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="content">
        <UploadForm onUploaded={handleUploaded} />

        <div className="list-header">
          <div className="section-label" style={{ marginBottom: 0 }}>
            Documents
          </div>
          <span className="count">{documents.length} total</span>
        </div>
        <DocumentList documents={documents} loading={loading} newestId={newestId} />
      </main>

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onClose={() => setToast(null)}
      />
    </div>
  );
}
