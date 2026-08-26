import { useState } from "react";
import { useNavigate } from "react-router-dom";
import UploadForm from "../components/UploadForm";
import Toast from "../components/Toast";

export default function UploadPage() {
  const navigate = useNavigate();
  const [toast, setToast] = useState(null);

  function handleUploaded(result) {
    setToast({ message: "Document uploaded successfully! Redirecting...", variant: "success" });
    setTimeout(() => {
      navigate("/documents", { state: { newestId: result.document_id } });
    }, 1200);
  }

  function handleError(msg) {
    setToast({ message: msg, variant: "error" });
  }

  return (
    <div>
      <div className="hp-page-header">
        <h1>Document Ingestion Workspace</h1>
        <p>Upload lab reports, discharge summaries, prescriptions, or medical images for automated processing.</p>
      </div>

      <UploadForm onUploaded={handleUploaded} onError={handleError} />

      <div className="hp-card" style={{ marginTop: 24 }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--hp-text-900)", marginBottom: 12 }}>
          Document Intake Guidelines
        </h3>
        <ul style={{ margin: 0, paddingLeft: 20, color: "var(--hp-text-700)", fontSize: "0.875rem", lineHeight: 1.7 }}>
          <li>Ensure document files are legible and clear (300 DPI recommended for scanned papers).</li>
          <li>Supported file extensions: <strong>.PDF, .JPG, .JPEG, .PNG</strong> up to 20MB in size.</li>
          <li>Documents will be validated and queued for document intelligence processing.</li>
        </ul>
      </div>

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onClose={() => setToast(null)}
      />
    </div>
  );
}
