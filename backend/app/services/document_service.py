from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_text import DocumentText
from app.schemas.document import DocumentProcessingStatus
from app.services.ocr_service import OCRResult, extract_text



from datetime import datetime, timezone


UPLOAD_DIR = Path("uploads/documents")

ALLOWED_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


def upload_document(
    db: Session,
    file: UploadFile,
    patient_id: UUID | None,
    uploaded_by: UUID,
) -> Document:

    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type",
        )

    # 2. Make sure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Create database record
    document = Document(
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        file_name=file.filename,
        file_type=file.content_type,
        file_url="",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # 4. Create file path using document ID
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{document.document_id}{file_extension}"

    # 5. Save uploaded file
    try:
        with file_path.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)

    except Exception:
        db.delete(document)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file",
        )

    # 6. Store file path in database
    document.file_url = str(file_path)
    document.processing_status = DocumentProcessingStatus.PROCESSING.value

    db.commit()
    db.refresh(document)

    # 7. Run OCR and persist the result
    try:
        ocr_result = extract_text(file_path, document.file_type)
        store_ocr_result(db, document.document_id, ocr_result)
        db.refresh(document)
    except Exception as exc:
        _mark_document_failed(db, document.document_id)
        raise HTTPException(
            status_code=500,
            detail="OCR processing failed",
        ) from exc

    return document

def _mark_document_failed(
    db: Session,
    document_id: UUID,
) -> None:
    """Set the document's processing status to Failed without raising HTTP errors."""
    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )
    if document is not None:
        document.processing_status = DocumentProcessingStatus.FAILED.value
        db.commit()


def update_document_status(
    db: Session,
    document_id: UUID,
    status: DocumentProcessingStatus,
) -> Document:

    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document.processing_status = status.value

    if status == DocumentProcessingStatus.COMPLETED:
        document.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(document)

    return document

def get_all_documents(
    db: Session,
) -> list[Document]:

    documents = (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return documents

def get_document_by_id(
    db: Session,
    document_id: UUID,
) -> Document:

    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


def store_ocr_result(
    db: Session,
    document_id: UUID,
    ocr_result: OCRResult,
) -> DocumentText:
    document = (
        db.query(Document)
        .filter(Document.document_id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    doc_text = (
        db.query(DocumentText)
        .filter(DocumentText.document_id == document_id)
        .first()
    )

    if doc_text is None:
        doc_text = DocumentText(
            document_id=document_id,
            raw_text=ocr_result.raw_text,
            page_count=ocr_result.page_count,
            confidence=ocr_result.confidence,
            layout=ocr_result.layout,
            ocr_engine=ocr_result.ocr_engine,
            processing_time_ms=ocr_result.processing_time_ms,
        )
        db.add(doc_text)
    else:
        doc_text.raw_text = ocr_result.raw_text
        doc_text.page_count = ocr_result.page_count
        doc_text.confidence = ocr_result.confidence
        doc_text.layout = ocr_result.layout
        doc_text.ocr_engine = ocr_result.ocr_engine
        doc_text.processing_time_ms = ocr_result.processing_time_ms

    document.processing_status = DocumentProcessingStatus.COMPLETED.value
    document.processed_at = datetime.now(timezone.utc)

    # Explicit branch for native vs OCR confidence score
    if ocr_result.ocr_engine == "pymupdf-native":
        document.ocr_quality_score = 1.0
    else:
        document.ocr_quality_score = ocr_result.confidence

    db.commit()
    db.refresh(doc_text)
    db.refresh(document)

    return doc_text


def get_document_text(
    db: Session,
    document_id: UUID,
) -> DocumentText:
    doc_text = (
        db.query(DocumentText)
        .filter(DocumentText.document_id == document_id)
        .first()
    )

    if doc_text is None:
        raise HTTPException(
            status_code=404,
            detail="OCR text not found for this document",
        )

    return doc_text