import client from "./client";

// POST /api/v1/documents
export async function uploadDocument(file, patientId) {
  const form = new FormData();
  form.append("file", file);
  if (patientId) form.append("patient_id", patientId);

  const { data } = await client.post("/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { document_id, status, uploaded_at }
}

// GET /api/v1/documents — backend returns a raw array, no pagination yet.
export async function listDocuments() {
  const { data } = await client.get("/documents");
  return data; // DocumentResponse[]
}

// No dedicated /status endpoint yet — reuse GET /{id} and read .processing_status.
export async function getDocumentStatus(documentId) {
  const { data } = await client.get(`/documents/${documentId}`);
  return { document_id: data.document_id, status: data.processing_status };
}
