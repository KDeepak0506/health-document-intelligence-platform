import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getDocument, getDocumentText } from "../api/documents";
import Toast from "../components/Toast";

const POLL_INTERVAL_MS = 4000;
const ACTIVE_STATUSES = ["Pending", "Processing"];

const STATUS_CLASS = {
  Pending: "hp-status-pending",
  Processing: "hp-status-processing",
  Completed: "hp-status-completed",
  Failed: "hp-status-failed",
};

function formatDate(dateStr) {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export default function DocumentDetailPage() {
  const { documentId } = useParams();

  const [document, setDocument] = useState(null);
  const [text, setText] = useState(null);
  const [loading, setLoading] = useState(true);
  const [textError, setTextError] = useState(null);
  const [toast, setToast] = useState(null);
  const pollRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const doc = await getDocument(documentId);
      setDocument(doc);

      if (doc.processing_status === "Completed") {
        try {
          const ocrText = await getDocumentText(documentId);
          setText(ocrText);
          setTextError(null);
        } catch (err) {
          setTextError(err.message || "Couldn't load OCR text.");
        }
      }
    } catch (err) {
      setToast({ message: err.message || "Couldn't load document.", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while the document is still Pending/Processing.
  useEffect(() => {
    if (!document || !ACTIVE_STATUSES.includes(document.processing_status)) {
      clearInterval(pollRef.current);
      return;
    }

    pollRef.current = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(pollRef.current);
  }, [document, load]);

  if (loading) {
    return (
      <div className="hp-table-container">
        <div className="hp-empty-state">
          <div
            className="hp-spinner"
            style={{ width: 28, height: 28, borderTopColor: "var(--hp-primary)", borderColor: "var(--hp-border)" }}
          />
          <div className="hp-empty-title" style={{ marginTop: 16 }}>Loading document...</div>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="hp-table-container">
        <div className="hp-empty-state">
          <h3 className="hp-empty-title">Document not found</h3>
          <p className="hp-empty-text">This document may have been removed, or the link is incorrect.</p>
          <Link to="/documents" className="hp-btn-secondary" style={{ width: "auto", display: "inline-flex" }}>
            Back to Documents
          </Link>
        </div>
      </div>
    );
  }

  const statusClass = STATUS_CLASS[document.processing_status] || "hp-status-pending";

  return (
    <div>
      <div className="hp-section-header" style={{ marginBottom: 24 }}>
        <div>
          <Link to="/documents" style={{ fontSize: "0.8125rem", color: "var(--hp-text-500)" }}>
            ← Back to Documents
          </Link>
          <h1 className="hp-page-title" style={{ fontSize: "1.5rem", marginTop: 8 }}>
            {document.file_name || "Untitled document"}
          </h1>
        </div>
        <span className={`hp-status-badge ${statusClass}`}>
          <span className="hp-status-dot" />
          <span>{document.processing_status || "Pending"}</span>
        </span>
      </div>

      <div className="hp-card" style={{ marginBottom: 24 }}>
        <div className="hp-doc-meta-grid">
          <div>
            <div className="hp-doc-meta-label">Document Type</div>
            <div className="hp-doc-meta-value">{document.document_type || "General Medical"}</div>
          </div>
          <div>
            <div className="hp-doc-meta-label">File Type</div>
            <div className="hp-doc-meta-value">{document.file_type || "—"}</div>
          </div>
          <div>
            <div className="hp-doc-meta-label">Uploaded</div>
            <div className="hp-doc-meta-value">{formatDate(document.uploaded_at)}</div>
          </div>
          {text && (
            <>
              <div>
                <div className="hp-doc-meta-label">Pages</div>
                <div className="hp-doc-meta-value">{text.page_count ?? "—"}</div>
              </div>
              <div>
                <div className="hp-doc-meta-label">OCR Engine</div>
                <div className="hp-doc-meta-value">{text.ocr_engine}</div>
              </div>
              <div>
                <div className="hp-doc-meta-label">Confidence</div>
                <div className="hp-doc-meta-value">
                  {text.confidence != null ? `${Math.round(text.confidence * 100)}%` : "—"}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {ACTIVE_STATUSES.includes(document.processing_status) && (
        <div className="hp-table-container">
          <div className="hp-empty-state">
            <div
              className="hp-spinner"
              style={{ width: 28, height: 28, borderTopColor: "var(--hp-warning)", borderColor: "var(--hp-border)" }}
            />
            <h3 className="hp-empty-title" style={{ marginTop: 16 }}>Processing document...</h3>
            <p className="hp-empty-text">
              Extracting text from this document. This page will update automatically.
            </p>
          </div>
        </div>
      )}

      {document.processing_status === "Failed" && (
        <div className="hp-table-container">
          <div className="hp-empty-state">
            <div className="hp-empty-icon" style={{ color: "var(--hp-error)" }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <h3 className="hp-empty-title">Processing failed</h3>
            <p className="hp-empty-text">
              This document couldn't be processed. Try re-uploading it, or contact support if the issue continues.
            </p>
          </div>
        </div>
      )}

      {document.processing_status === "Completed" && (
        <div className="hp-card">
          <div className="hp-section-header" style={{ marginBottom: 16 }}>
            <span className="hp-section-title">Extracted Text</span>
          </div>

          {textError && (
            <div className="hp-empty-state" style={{ padding: "var(--space-6)" }}>
              <p className="hp-empty-text" style={{ color: "var(--hp-error)" }}>{textError}</p>
            </div>
          )}

          {!textError && text && text.raw_text?.trim() && (
            <pre className="hp-ocr-text">{text.raw_text}</pre>
          )}

          {!textError && text && !text.raw_text?.trim() && (
            <div className="hp-empty-state" style={{ padding: "var(--space-6)" }}>
              <p className="hp-empty-text">
                No text could be extracted from this document.
              </p>
            </div>
          )}
        </div>
      )}

      <Toast message={toast?.message} variant={toast?.variant} onClose={() => setToast(null)} />
    </div>
  );
}