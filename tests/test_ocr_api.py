"""
API / integration tests for Backend Member 2's OCR endpoint and upload integration.

Coverage:
  - GET /api/v1/documents/{document_id}/text  (success, auth, ownership, 404s)
  - POST /api/v1/documents  (upload->OCR integration, OCR failure status)
"""
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.document import Document
from app.services import document_service
from app.services.ocr_service import OCRResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ocr_result(
    raw_text: str = "Patient: John Doe\nDiagnosis: Hypertension",
    confidence: float = 0.95,
    ocr_engine: str = "tesseract",
) -> OCRResult:
    return OCRResult(
        raw_text=raw_text,
        page_count=1,
        confidence=confidence,
        ocr_engine=ocr_engine,
        processing_time_ms=42,
        layout={
            "pages": 1,
            "tables_detected": 0,
            "page_confidences": [{"page": 1, "confidence": confidence}],
            "word_confidences": [{"text": "Patient:", "confidence": confidence, "page": 1}],
        },
    )


def _upload_with_mock_ocr(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch,
    ocr_result: OCRResult | None = None,
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
) -> dict:
    """Upload a file with OCR mocked; returns the parsed JSON response."""
    monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)
    result = ocr_result or _make_ocr_result()
    # Patch the name as it is bound in document_service's namespace,
    # not in ocr_service, because document_service does `from ... import extract_text`.
    monkeypatch.setattr(document_service, "extract_text", lambda fp, ft: result)
    response = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": (filename, b"dummy-content", content_type)},
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Fixtures - second user for ownership tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def second_user_auth_headers(client: TestClient) -> dict[str, str]:
    """Register and log in a second user."""
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Second User",
            "email": "second@example.com",
            "password": "password456",
            "role": "doctor",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "second@example.com", "password": "password456"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{document_id}/text  -  Success
# ---------------------------------------------------------------------------

def test_get_ocr_text_success(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Authenticated owner receives 200 with DocumentTextResponse fields."""
    expected_text = "Blood Pressure: 140/90 mmHg"
    doc = _upload_with_mock_ocr(
        client, auth_headers, tmp_path, monkeypatch,
        ocr_result=_make_ocr_result(raw_text=expected_text),
    )
    document_id = doc["document_id"]

    response = client.get(
        f"/api/v1/documents/{document_id}/text",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["raw_text"] == expected_text
    assert body["ocr_engine"] == "tesseract"
    assert body["confidence"] == pytest.approx(0.95)
    assert body["page_count"] == 1
    assert body["layout"] is not None
    assert "page_confidences" in body["layout"]
    assert "id" in body
    assert "created_at" in body


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{document_id}/text  -  Authentication
# ---------------------------------------------------------------------------

def test_get_ocr_text_unauthenticated(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Unauthenticated request is rejected with 401."""
    doc = _upload_with_mock_ocr(client, auth_headers, tmp_path, monkeypatch)
    document_id = doc["document_id"]

    response = client.get(f"/api/v1/documents/{document_id}/text")

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{document_id}/text  -  Ownership
# ---------------------------------------------------------------------------

def test_get_ocr_text_wrong_owner(
    client: TestClient,
    auth_headers: dict[str, str],
    second_user_auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    """User B cannot read User A's document OCR text - expects 403."""
    doc = _upload_with_mock_ocr(client, auth_headers, tmp_path, monkeypatch)
    document_id = doc["document_id"]

    response = client.get(
        f"/api/v1/documents/{document_id}/text",
        headers=second_user_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{document_id}/text  -  Nonexistent document
# ---------------------------------------------------------------------------

def test_get_ocr_text_nonexistent_document(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Request for an unknown document_id returns 404."""
    missing_id = uuid4()

    response = client.get(
        f"/api/v1/documents/{missing_id}/text",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{document_id}/text  -  Document without OCR result
# ---------------------------------------------------------------------------

def test_get_ocr_text_no_ocr_result(
    client: TestClient,
    auth_headers: dict[str, str],
    database: sessionmaker[Session],
    registered_user: dict,
) -> None:
    """A document that exists but has no OCR record returns 404 with the
    existing service message 'OCR text not found for this document'."""
    from uuid import UUID as _UUID
    db = database()
    try:
        doc = Document(
            uploaded_by=_UUID(registered_user["user_id"]),
            file_name="bare.pdf",
            file_type="application/pdf",
            file_url="/uploads/bare.pdf",
            processing_status="Pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        document_id = str(doc.document_id)
    finally:
        db.close()

    response = client.get(
        f"/api/v1/documents/{document_id}/text",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "OCR text not found for this document"


# ---------------------------------------------------------------------------
# Full integration: upload -> OCR -> retrieve
# ---------------------------------------------------------------------------

def test_upload_triggers_ocr_and_stores_text(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Full flow: upload -> mocked OCR -> GET /text returns the stored result."""
    expected_text = "Glucose: 110 mg/dL\nHbA1c: 6.2%"
    ocr_result = OCRResult(
        raw_text=expected_text,
        page_count=1,
        confidence=0.9800,
        ocr_engine="tesseract",
        processing_time_ms=123,
        layout={
            "pages": 1,
            "tables_detected": 0,
            "page_confidences": [{"page": 1, "confidence": 0.9800}],
            "word_confidences": [
                {"text": "Glucose:", "confidence": 0.98, "page": 1},
                {"text": "110", "confidence": 0.99, "page": 1},
            ],
        },
    )

    doc = _upload_with_mock_ocr(
        client, auth_headers, tmp_path, monkeypatch,
        ocr_result=ocr_result,
        filename="lab_results.pdf",
    )
    document_id = doc["document_id"]

    # Upload endpoint returns immediately with status Processing
    assert doc["processing_status"] == "Processing"

    # Verify document status becomes Completed after background OCR task finishes
    doc_res = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert doc_res.status_code == 200
    assert doc_res.json()["processing_status"] == "Completed"

    # OCR text must be retrievable
    response = client.get(
        f"/api/v1/documents/{document_id}/text",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["raw_text"] == expected_text
    assert body["ocr_engine"] == "tesseract"
    assert body["confidence"] == pytest.approx(0.9800)
    assert body["processing_time_ms"] == 123
    assert body["page_count"] == 1
    # Layout must be preserved as-is (no transformation in the API layer)
    assert body["layout"]["pages"] == 1
    assert body["layout"]["word_confidences"][0]["text"] == "Glucose:"
    assert body["layout"]["word_confidences"][0]["confidence"] == pytest.approx(0.98)


# ---------------------------------------------------------------------------
# OCR failure: document ends in "Failed" status
# ---------------------------------------------------------------------------

def test_upload_ocr_failure_sets_failed_status(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
    database: sessionmaker[Session],
) -> None:
    """When OCR raises an exception in the background task, the upload request still
    returns 201 Created immediately, and the document's processing_status becomes 'Failed'."""
    monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)

    def _raise(*args, **kwargs):
        raise RuntimeError("Simulated OCR failure")

    # Patch in document_service's namespace (where the name is bound via `from ... import`).
    monkeypatch.setattr(document_service, "extract_text", _raise)

    response = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": ("broken.pdf", b"not-a-real-pdf", "application/pdf")},
    )

    # HTTP request succeeds with 201 Created and initial status Processing
    assert response.status_code == 201
    assert response.json()["processing_status"] == "Processing"

    # Verify background exception handled and document record status updated to "Failed"
    db = database()
    try:
        failed_doc = (
            db.query(Document)
            .filter(Document.file_name == "broken.pdf")
            .first()
        )
        assert failed_doc is not None
        assert failed_doc.processing_status == "Failed"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Native PDF: confidence and layout preserved without transformation
# ---------------------------------------------------------------------------

def test_get_ocr_text_native_pdf_null_word_confidences(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Native PDFs have word_confidences=None; the API returns null without
    errors (no iterable assumption in the API layer)."""
    native_result = OCRResult(
        raw_text="Hospital Discharge Summary",
        page_count=2,
        confidence=1.0,
        ocr_engine="pymupdf-native",
        processing_time_ms=10,
        layout={
            "pages": 2,
            "tables_detected": 0,
            "page_confidences": [
                {"page": 1, "confidence": 1.0},
                {"page": 2, "confidence": 1.0},
            ],
            "word_confidences": None,
        },
    )

    doc = _upload_with_mock_ocr(
        client, auth_headers, tmp_path, monkeypatch,
        ocr_result=native_result,
        filename="discharge.pdf",
    )
    document_id = doc["document_id"]

    response = client.get(
        f"/api/v1/documents/{document_id}/text",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ocr_engine"] == "pymupdf-native"
    assert body["confidence"] == pytest.approx(1.0)
    assert body["layout"]["word_confidences"] is None
    assert len(body["layout"]["page_confidences"]) == 2
