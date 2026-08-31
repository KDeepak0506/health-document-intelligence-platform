from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.services import document_service
from app.services.ocr_service import OCRResult


def test_upload_document_persists_metadata_and_file(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)
    # Mock OCR so the test is deterministic and does not require Tesseract
    # Patch in document_service's namespace (where the name is bound via `from ... import`).
    monkeypatch.setattr(
        document_service,
        "extract_text",
        lambda file_path, file_type: OCRResult(
            raw_text="Mocked OCR text",
            page_count=1,
            confidence=1.0,
            ocr_engine="pymupdf-native",
            processing_time_ms=1,
            layout={"pages": 1, "tables_detected": 0, "page_confidences": [], "word_confidences": None},
        ),
    )

    response = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": ("scan.pdf", b"pdf-content", "application/pdf")},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["file_name"] == "scan.pdf"
    assert document["file_type"] == "application/pdf"
    assert document["processing_status"] == "Processing"
    saved_file = Path(document["file_url"])
    assert saved_file == tmp_path / f"{document['document_id']}.pdf"
    assert saved_file.read_bytes() == b"pdf-content"

    # Verify background task finished OCR and updated document status to Completed
    fetched = client.get(f"/api/v1/documents/{document['document_id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["processing_status"] == "Completed"


def test_upload_rejects_unsupported_file_type(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not a document", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_document_listing_and_status_update(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)
    # Mock OCR so the upload completes without requiring Tesseract
    # Patch in document_service's namespace (where the name is bound via `from ... import`).
    monkeypatch.setattr(
        document_service,
        "extract_text",
        lambda file_path, file_type: OCRResult(
            raw_text="Lab report",
            page_count=1,
            confidence=0.95,
            ocr_engine="tesseract",
            processing_time_ms=50,
            layout={"pages": 1, "tables_detected": 0, "page_confidences": [], "word_confidences": []},
        ),
    )
    upload = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": ("report.png", b"image-content", "image/png")},
    )
    document_id = upload.json()["document_id"]

    listing = client.get("/api/v1/documents", headers=auth_headers)
    update = client.patch(
        f"/api/v1/documents/{document_id}/status",
        headers=auth_headers,
        params={"status": "Completed"},
    )

    assert listing.status_code == 200
    assert [item["document_id"] for item in listing.json()] == [document_id]
    assert update.status_code == 200
    assert update.json()["processing_status"] == "Completed"


def test_missing_document_returns_not_found(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    missing_id = uuid4()

    response = client.get(f"/api/v1/documents/{missing_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_background_task_creates_own_db_session(
    database,
    tmp_path: Path,
    monkeypatch,
    registered_user: dict,
) -> None:
    """Verify that _run_ocr_and_store creates and closes its own DB session cleanly."""
    from uuid import UUID
    from app.models.document import Document
    from app.models.document_text import DocumentText

    db = database()
    doc_id = None
    try:
        user_id = UUID(registered_user["user_id"])
        doc = Document(
            uploaded_by=user_id,
            file_name="bg_test.pdf",
            file_type="application/pdf",
            file_url=str(tmp_path / "bg_test.pdf"),
            processing_status="Processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.document_id
    finally:
        db.close()

    mock_result = OCRResult(
        raw_text="Background session text",
        page_count=1,
        confidence=0.99,
        ocr_engine="pymupdf-native",
        processing_time_ms=10,
        layout={"pages": 1, "tables_detected": 0, "page_confidences": [], "word_confidences": None},
    )
    monkeypatch.setattr(document_service, "extract_text", lambda fp, ft: mock_result)

    # Invoke _run_ocr_and_store directly without passing a request DB session
    document_service._run_ocr_and_store(
        document_id=doc_id,
        file_path=tmp_path / "bg_test.pdf",
        file_type="application/pdf",
    )

    # Verify background task persisted results in DB using its own session
    check_db = database()
    try:
        updated_doc = check_db.query(Document).filter(Document.document_id == doc_id).first()
        assert updated_doc is not None
        assert updated_doc.processing_status == "Completed"
        assert updated_doc.processed_at is not None

        doc_text = check_db.query(DocumentText).filter(DocumentText.document_id == doc_id).first()
        assert doc_text is not None
        assert doc_text.raw_text == "Background session text"
    finally:
        check_db.close()