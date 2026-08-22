import { useEffect, useRef } from "react";

const STATUS_LABEL = {
  Pending: "status-pending",
  Processing: "status-processing",
  Completed: "status-completed",
  Failed: "status-failed",
};

export default function DocumentList({ documents, loading, newestId }) {
  if (loading) {
    return <div className="empty-state">Loading documents…</div>;
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="empty-state">
        No documents yet. Upload one above to get started.
      </div>
    );
  }

  return (
    <table className="doc-table">
      <thead>
        <tr>
          <th>File</th>
          <th>Type</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.document_id} className={doc.document_id === newestId ? "new-row" : ""}>
            <td className="filename">{doc.file_name || doc.document_id}</td>
            <td>{doc.document_type || "Pending classification"}</td>
            <td>
              <span
                className={`status-pill ${STATUS_LABEL[doc.processing_status] || "status-pending"}`}
              >
                {doc.processing_status}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
