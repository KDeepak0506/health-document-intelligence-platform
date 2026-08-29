import shutil
from pathlib import Path
from uuid import uuid4

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw
import pytest
import pytesseract
from sqlalchemy.orm import Session, sessionmaker

from app.models.document import Document
from app.models.user import User
from app.services import ocr_service
from app.services.document_service import get_document_text, store_ocr_result
from app.services.ocr_service import OCRResult, extract_text, _deskew_fine


def _is_tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def test_ocr_on_native_pdf(tmp_path: Path) -> None:
    # 1. Create a native PDF with embedded searchable text
    pdf_path = tmp_path / "native_prescription.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), "Hospital Discharge Summary\nPatient: Jane Doe\nDiagnosis: Hypertension\nMedication: Lisinopril 10mg daily")
    doc.save(pdf_path)
    doc.close()

    # 2. Extract text
    result = extract_text(pdf_path, "application/pdf")

    # 3. Assertions
    assert result.ocr_engine == "pymupdf-native"
    assert result.page_count == 1
    assert result.confidence == 1.0
    assert "Hospital Discharge Summary" in result.raw_text
    assert "Lisinopril 10mg daily" in result.raw_text
    assert result.layout is not None
    assert result.layout["pages"] == 1
    assert result.layout["tables_detected"] == 0
    assert result.layout["page_confidences"] == [{"page": 1, "confidence": 1.0}]
    assert result.layout["word_confidences"] is None


def test_store_ocr_result_native_pdf(database: sessionmaker[Session]) -> None:
    db = database()
    try:
        # Create user
        user = User(
            name="Dr. Smith",
            email="smith@example.com",
            password_hash="fakehash",
            role="doctor",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create document
        document = Document(
            uploaded_by=user.user_id,
            file_name="discharge_summary.pdf",
            file_type="application/pdf",
            file_url="/uploads/discharge_summary.pdf",
            processing_status="Pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Store native OCR result
        ocr_res = OCRResult(
            raw_text="Hospital Discharge Summary\nMedication: Lisinopril 10mg",
            page_count=1,
            confidence=1.0,
            ocr_engine="pymupdf-native",
            processing_time_ms=45,
            layout={
                "pages": 1,
                "tables_detected": 0,
                "page_confidences": [{"page": 1, "confidence": 1.0}],
                "word_confidences": None,
            },
        )

        doc_text = store_ocr_result(db, document.document_id, ocr_res)

        # Verify document updates
        db.refresh(document)
        assert document.processing_status == "Completed"
        assert document.ocr_quality_score == 1.0
        assert document.processed_at is not None

        # Verify document_text record
        assert doc_text.document_id == document.document_id
        assert doc_text.ocr_engine == "pymupdf-native"
        assert doc_text.confidence == 1.0
        assert "Lisinopril" in doc_text.raw_text
        assert doc_text.layout["page_confidences"] == [{"page": 1, "confidence": 1.0}]

        # Test retrieval
        retrieved = get_document_text(db, document.document_id)
        assert retrieved.id == doc_text.id
        assert retrieved.raw_text == doc_text.raw_text
    finally:
        db.close()


def test_store_ocr_result_tesseract_confidence_scale(database: sessionmaker[Session]) -> None:
    db = database()
    try:
        user = User(
            name="Dr. Taylor",
            email="taylor@example.com",
            password_hash="fakehash",
            role="doctor",
        )
        db.add(user)
        db.commit()

        document = Document(
            uploaded_by=user.user_id,
            file_name="scanned_lab.png",
            file_type="image/png",
            file_url="/uploads/scanned_lab.png",
            processing_status="Processing",
        )
        db.add(document)
        db.commit()

        # Tesseract normalized confidence result (0.0 to 1.0 scale)
        ocr_res = OCRResult(
            raw_text="Glucose: 110 mg/dL",
            page_count=1,
            confidence=0.9425,
            ocr_engine="tesseract",
            processing_time_ms=320,
            layout={
                "pages": 1,
                "tables_detected": 0,
                "page_confidences": [{"page": 1, "confidence": 0.9425}],
                "word_confidences": [
                    {"text": "Glucose:", "confidence": 0.965, "page": 1},
                    {"text": "110", "confidence": 0.98, "page": 1},
                    {"text": "mg/dL", "confidence": 0.8825, "page": 1},
                ],
            },
        )

        doc_text = store_ocr_result(db, document.document_id, ocr_res)

        db.refresh(document)
        assert document.processing_status == "Completed"
        assert float(document.ocr_quality_score) == pytest.approx(0.9425)
        assert doc_text.confidence == pytest.approx(0.9425)
        assert doc_text.layout["word_confidences"][0]["page"] == 1
        assert doc_text.layout["word_confidences"][0]["confidence"] == pytest.approx(0.965)
    finally:
        db.close()


def _measure_tilt(gray: np.ndarray) -> float:
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    coords = cv2.findNonZero(thresh)
    rect = cv2.minAreaRect(coords)
    (w, h) = rect[1]
    angle = rect[-1]
    if w < h:
        angle = angle - 90.0
    return float(((angle + 90) % 180) - 90)



@pytest.mark.parametrize("tilt_angle", [5.0, -5.0])
def test_fine_deskew_correction(tilt_angle: float) -> None:
    # Create white image with black text lines
    img = np.full((300, 600), 255, dtype=np.uint8)
    for y in [80, 140, 200]:
        cv2.line(img, (50, y), (550, y), 0, 4)

    center = (300, 150)
    matrix = cv2.getRotationMatrix2D(center, tilt_angle, 1.0)
    tilted = cv2.warpAffine(img, matrix, (600, 300), borderMode=cv2.BORDER_CONSTANT, borderValue=255)

    deskewed = _deskew_fine(tilted)
    assert deskewed.shape == (300, 600)
    assert abs(_measure_tilt(deskewed)) < 1.0


def test_ocr_missing_file_raises_error(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.pdf"
    with pytest.raises(FileNotFoundError):
        extract_text(missing_file, "application/pdf")


@pytest.mark.skipif(not _is_tesseract_available(), reason="Tesseract OCR binary not found on system")
def test_tesseract_ocr_on_image(tmp_path: Path) -> None:
    # Create a synthetic image with legible text
    img_path = tmp_path / "test_rx.png"
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 80), "Metformin 500mg daily", fill=(0, 0, 0))
    img.save(img_path)

    result = extract_text(img_path, "image/png")

    assert result.ocr_engine == "tesseract"
    assert result.page_count == 1
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0
    assert "Metformin" in result.raw_text
    assert result.layout is not None
    assert len(result.layout["page_confidences"]) == 1
    assert result.layout["page_confidences"][0]["page"] == 1
    assert len(result.layout["word_confidences"]) > 0
    assert result.layout["word_confidences"][0]["page"] == 1
    assert 0.0 <= result.layout["word_confidences"][0]["confidence"] <= 1.0


def test_preprocessing_pipeline_produces_binary_image() -> None:
    synthetic_image = np.full((200, 400, 3), 240, dtype=np.uint8)
    cv2.putText(synthetic_image, "RX: Amoxicillin", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    processed = ocr_service._preprocess_image(synthetic_image)
    assert processed is not None
    assert processed.ndim == 2
    assert processed.shape == (200, 400)
    assert set(np.unique(processed)).issubset({0, 255})


def test_get_document_text_missing_raises_404(database: sessionmaker[Session]) -> None:
    from fastapi import HTTPException
    db = database()
    try:
        with pytest.raises(HTTPException) as exc_info:
            get_document_text(db, uuid4())
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "OCR text not found for this document"
    finally:
        db.close()


def test_store_ocr_result_updates_existing_record(database: sessionmaker[Session]) -> None:
    db = database()
    try:
        user = User(name="Nurse Joy", email="joy@example.com", password_hash="fake", role="nurse")
        db.add(user)
        db.commit()

        document = Document(
            uploaded_by=user.user_id,
            file_name="chart.pdf",
            file_type="application/pdf",
            file_url="/uploads/chart.pdf",
            processing_status="Pending",
        )
        db.add(document)
        db.commit()

        res1 = OCRResult(
            raw_text="Initial text",
            page_count=1,
            confidence=0.85,
            ocr_engine="tesseract",
            processing_time_ms=100,
            layout={"pages": 1, "tables_detected": 0, "page_confidences": [{"page": 1, "confidence": 0.85}], "word_confidences": []},
        )
        stored1 = store_ocr_result(db, document.document_id, res1)
        first_id = stored1.id

        res2 = OCRResult(
            raw_text="Updated text after re-run",
            page_count=1,
            confidence=0.98,
            ocr_engine="tesseract",
            processing_time_ms=120,
            layout={"pages": 1, "tables_detected": 0, "page_confidences": [{"page": 1, "confidence": 0.98}], "word_confidences": []},
        )
        stored2 = store_ocr_result(db, document.document_id, res2)

        # ID should remain identical (upsert behavior)
        assert stored2.id == first_id
        assert stored2.raw_text == "Updated text after re-run"
        assert stored2.confidence == pytest.approx(0.98)
    finally:
        db.close()

