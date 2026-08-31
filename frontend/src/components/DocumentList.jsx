import React from "react";
import { Link } from "react-router-dom";

const STATUS_CLASS = {
  Pending: "hp-status-pending",
  Processing: "hp-status-processing",
  Completed: "hp-status-completed",
  Failed: "hp-status-failed",
};

export default function DocumentList({ documents, loading, newestId }) {
  if (loading) {
    return (
      <div className="hp-table-container">
        <div className="hp-empty-state">
          <div className="hp-spinner" style={{ width: 28, height: 28, borderTopColor: "var(--hp-primary)", borderColor: "var(--hp-border)" }} />
          <div className="hp-empty-title" style={{ marginTop: 16 }}>Loading clinical documents...</div>
        </div>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="hp-table-container">
        <div className="hp-empty-state">
          <div className="hp-empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="12" y1="18" x2="12" y2="12"></line>
              <line x1="9" y1="15" x2="15" y2="15"></line>
            </svg>
          </div>
          <h3 className="hp-empty-title">No healthcare documents yet</h3>
          <p className="hp-empty-text">
            Upload your first lab report, discharge summary, or prescription to begin automated intake and tracking.
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return "Just now";
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
  };

  return (
    <div className="hp-table-container">
      <table className="hp-doc-table">
        <thead>
          <tr>
            <th>Document Name</th>
            <th>Type</th>
            <th>Uploaded</th>
            <th>Processing Status</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => {
            const isNew = doc.document_id === newestId;
            const statusClass = STATUS_CLASS[doc.processing_status] || "hp-status-pending";
            
            return (
              <tr
                key={doc.document_id}
                className="hp-row-link"
                style={isNew ? { background: "var(--hp-primary-50)" } : undefined}
              >
                <td>
                  <Link to={`/documents/${doc.document_id}`} className="hp-file-cell hp-file-cell-link">
                    <div className="hp-doc-type-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                      </svg>
                    </div>
                    <span className="hp-filename-text" title={doc.file_name || doc.document_id}>
                      {doc.file_name || doc.document_id}
                    </span>
                  </Link>
                </td>
                <td>
                  <span style={{ fontSize: "0.8125rem", color: "var(--hp-text-700)" }}>
                    {doc.document_type || "General Medical"}
                  </span>
                </td>
                <td>
                  <span style={{ fontSize: "0.8125rem", color: "var(--hp-text-500)" }}>
                    {formatDate(doc.uploaded_at)}
                  </span>
                </td>
                <td>
                  <span className={`hp-status-badge ${statusClass}`}>
                    <span className="hp-status-dot" />
                    <span>{doc.processing_status || "Pending"}</span>
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}