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
    assert document["processing_status"] == "Completed"
    saved_file = Path(document["file_url"])
    assert saved_file == tmp_path / f"{document['document_id']}.pdf"
    assert saved_file.read_bytes() == b"pdf-content"


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