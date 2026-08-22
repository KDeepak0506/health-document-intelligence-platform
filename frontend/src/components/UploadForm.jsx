import { useRef, useState } from "react";
import { uploadDocument } from "../api/documents";

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
const ACCEPTED_EXT = [".pdf", ".jpg", ".jpeg", ".png"];
const MAX_SIZE_MB = 20;

function validateFile(file) {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return "Unsupported file type. Upload a PDF, JPG, JPEG, or PNG.";
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File exceeds the ${MAX_SIZE_MB}MB limit.`;
  }
  return null;
}

export default function UploadForm({ onUploaded, onError }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  function handleFile(selected) {
    setError(null);
    const validationError = validateFile(selected);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }
    setFile(selected);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFile(dropped);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadDocument(file);
      onUploaded?.(result);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      const msg = err.message || "Upload failed. Please try again.";
      setError(msg);
      onError?.(msg);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="upload-card">
      <div className="section-label">Upload document</div>

      {error && <div className="error-banner">{error}</div>}

      <label
        className={`dropzone ${dragActive ? "active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(",")}
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        <div className="instruction">
          {dragActive ? "Drop to select" : "Drag a file here, or click to browse"}
        </div>
        <div className="formats">PDF · JPG · JPEG · PNG — up to {MAX_SIZE_MB}MB</div>
      </label>

      {file && (
        <div className="selected-file">
          <span>{file.name} · {(file.size / 1024).toFixed(0)} KB</span>
          <button onClick={() => setFile(null)} disabled={uploading}>
            Remove
          </button>
        </div>
      )}

      <div className="upload-actions">
        <button
          className="btn-primary"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? <span className="spinner" /> : "Upload document"}
        </button>
      </div>
    </div>
  );
}
